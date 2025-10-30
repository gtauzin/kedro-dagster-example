import importlib
import os
from pathlib import Path

import pytest
from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession

PROJECT_PATH = Path(__file__).resolve().parents[1]
ALL_ENVS = ["local", "dev", "staging", "prod"]


def _reload_modules_for_env(env: str):
    os.environ["KEDRO_ENV"] = env
    # Reload settings and all pipeline modules that depend on it
    settings_mod = importlib.import_module("kedro_dagster_example.settings")
    data_processing_mod = importlib.import_module("kedro_dagster_example.pipelines.data_processing.pipeline")
    data_science_mod = importlib.import_module("kedro_dagster_example.pipelines.data_science.pipeline")
    model_tuning_mod = importlib.import_module("kedro_dagster_example.pipelines.model_tuning.pipeline")
    registry_mod = importlib.import_module("kedro_dagster_example.pipeline_registry")

    importlib.reload(settings_mod)
    importlib.reload(data_processing_mod)
    importlib.reload(data_science_mod)
    importlib.reload(model_tuning_mod)
    importlib.reload(registry_mod)

    return registry_mod


@pytest.mark.parametrize("env", ALL_ENVS)
def test_all_pipelines_run_for_all_namespaces(env):
    # Ensure modules reflect the selected env
    _reload_modules_for_env(env)

    # Pipelines are registered in pipeline_registry; choose names per env
    pipeline_names = ["data_processing", "data_science"]
    if env in ("local", "dev"):
        pipeline_names.append("model_tuning")

    # Create a Kedro session with the chosen env and run each pipeline once
    # Each pipeline definition already expands across namespaces/variants
    configure_project("kedro_dagster_example")

    # For dev, provide dummy Postgres env vars so oc.env resolver in credentials doesn't fail
    if env == "dev":
        os.environ.setdefault("POSTGRES_USER", "dev_db")
        os.environ.setdefault("POSTGRES_PASSWORD", "dev_password")
        os.environ.setdefault("POSTGRES_HOST", "localhost")
        os.environ.setdefault("POSTGRES_PORT", "5432")

    # Run each pipeline in its own session (Kedro 1.0 allows one run per session)
    for pname in pipeline_names:
        with KedroSession.create(project_path=PROJECT_PATH, env=env) as session:
            session.run(pipeline_name=pname)
