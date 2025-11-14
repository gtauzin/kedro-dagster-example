import importlib
import os

import pytest
from kedro.framework.project import configure_project
from kedro.framework.session import KedroSession

from .conftest import ALL_ENVS, PROJECT_PATH, _can_connect_to_postgres


def _env_tag_pipeline_triplets():
    """Build (env, tag, pipeline_name) triplets by inspecting settings per env.

    We reload the settings module for each env to read the available tags and
    derive the associated pipeline names for that environment.
    """
    triplets = []
    for env in ALL_ENVS:
        os.environ["KEDRO_ENV"] = env
        settings_mod = importlib.import_module("kedro_dagster_example.settings")
        importlib.reload(settings_mod)

        # Pipelines are registered in pipeline_registry; choose names per env
        pipeline_names = ["data_processing", "data_science"]
        if env in ("local", "dev"):
            pipeline_names.append("model_tuning")

        for tag in settings_mod.DYNAMIC_PIPELINES_MAPPING.keys():
            for pipeline_name in pipeline_names:
                triplets.append((env, tag, pipeline_name))

    return triplets


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


@pytest.mark.parametrize("env,tag,pipeline_name", _env_tag_pipeline_triplets())
def test_all_pipelines_run_for_all_tags(env, tag, pipeline_name):
    # Ensure modules reflect the selected env
    _reload_modules_for_env(env)

    # Create a Kedro session with the chosen env and run each pipeline once
    # Each pipeline definition already expands across namespaces/variants
    configure_project("kedro_dagster_example")

    # If this is the dev environment, the model_tuning pipeline relies on an
    # Optuna StudyDataset backed by PostgreSQL. When Postgres is not available
    # (e.g. on a developer machine without Docker running), we skip these tests
    # rather than fail the suite.
    if env == "dev" and pipeline_name == "model_tuning":
        # Re-evaluate the Postgres availability mark here to avoid importing
        # the helper directly in this module.
        if not _can_connect_to_postgres():
            pytest.skip("Postgres is not available; skipping dev environment tests for `model_tuning`.")

    with KedroSession.create(project_path=PROJECT_PATH, env=env) as session:
        run_kwargs = {"pipeline_name": pipeline_name}
        if pipeline_name in ("data_science", "model_tuning"):
            run_kwargs["tags"] = [tag]
        session.run(**run_kwargs)
