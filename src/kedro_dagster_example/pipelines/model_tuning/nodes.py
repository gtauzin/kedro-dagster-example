import importlib
from functools import partial
from typing import Any

import mlflow
import numpy as np
import optuna
import pandas as pd
from kedro_dagster import NOTHING_OUTPUT
from optuna.integration.mlflow import MLflowCallback
from sklearn.base import RegressorMixin, clone
from sklearn.metrics import make_scorer, root_mean_squared_error
from sklearn.model_selection import KFold, cross_val_score


def import_class_from_string(class_path):
    module_path, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def create_study():
    study = optuna.create_study(
        direction="maximize",
    )
    return study


def suggest_functions_from_param_spaces(param_spaces):
    SUGGEST_FUNCTION_MAP = {
        "categorical": optuna.Trial.suggest_categorical,
        "int": optuna.Trial.suggest_int,
        "float": optuna.Trial.suggest_float,
    }

    suggest_functions = {}
    for param, suggest_config in param_spaces.items():
        if "type" not in suggest_config:
            raise ValueError()

        suggest_function = SUGGEST_FUNCTION_MAP[suggest_config.pop("type")]
        suggest_functions[param] = partial(suggest_function, name=param, **suggest_config)

    return suggest_functions


def instantiate_model(model_class, model_params):
    deserialized_model_params = {}
    for name, params in model_params.items():
        if isinstance(params, dict) and "class" in params:
            param_class = params.pop("class")
            deserialized_model_params[name] = instantiate_model(
                model_class=param_class,
                model_params=params,
            )
        else:
            deserialized_model_params[name] = params

    model_class = import_class_from_string(model_class)
    model = model_class(**model_params)
    return model


def get_tried_model(model: RegressorMixin, trial: optuna.Trial, suggest_functions: dict[str, Any]) -> RegressorMixin:
    params = {}
    for param, suggest_function in suggest_functions.items():
        params[param] = suggest_function(trial)

    return model.set_params(**params)


def tune_model(
    X_train,
    y_train,
    study,
    study_params,
) -> dict[str, Any]:
    model_params = study_params["model"]
    model_class = model_params.pop("class")
    model = instantiate_model(model_class=model_class, model_params=model_params)

    param_spaces = study_params["param_spaces"]
    suggest_functions = suggest_functions_from_param_spaces(param_spaces)

    def objective(
        model: RegressorMixin,
        trial: optuna.Trial,
        X: pd.DataFrame,
        y: np.ndarray | pd.Series,
        random_state: int = 42,
    ) -> float:
        model = get_tried_model(model=clone(model), trial=trial, suggest_functions=suggest_functions)

        cv = KFold(n_splits=5, shuffle=True, random_state=random_state)
        rmse_scorer = make_scorer(root_mean_squared_error, greater_is_better=False)
        scores = cross_val_score(model, X, y, scoring=rmse_scorer, cv=cv)

        return np.mean(scores)

    mlflow_callback = MLflowCallback(
        tracking_uri=mlflow.get_tracking_uri(),
        metric_name="rmse",
        create_experiment=False,
        mlflow_kwargs={"nested": True},
    )
    study.optimize(
        lambda trial: objective(model, trial, X_train, y_train),
        n_trials=study_params["n_trials_per_process"],
        callbacks=[mlflow_callback],
    )

    return NOTHING_OUTPUT


def log_study(study, *tuning_nodes_done):
    return study
