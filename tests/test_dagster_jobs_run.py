import importlib
import os

import pytest
from kedro.framework.project import configure_project

from .conftest import ALL_ENVS, _can_connect_to_postgres


def _env_job_pairs():
    """Build (env, (job_def, job_resources)) pairs by inspecting settings per env.

    We reload the settings module for each env to read the available jobs.
    """
    pairs = []
    for env in ALL_ENVS:
        # Reload dagster definitions for the selected environment
        dag_defs_mod = _reload_dagster_definitions_for_env(env)

        # Ensure the Kedro project is configured for imports
        configure_project("kedro_dagster_example")

        # Access the translated Kedro->Dagster code location and jobs
        dagster_code_location = dag_defs_mod.dagster_code_location
        job_resources = dag_defs_mod.resources

        # Sanity: there should be at least one job defined per env
        named_jobs = dagster_code_location.named_jobs
        assert named_jobs, f"No Dagster jobs found for env={env}"

        # Execute each job once in-process; rely on default io_manager and config
        for job_def in named_jobs.values():
            pairs.append((env, (job_def, job_resources)))

    return pairs


def _reload_dagster_definitions_for_env(env: str):
    os.environ["KEDRO_ENV"] = env

    # Reload settings and pipelines to ensure env-specific mapping is applied
    settings_mod = importlib.import_module("kedro_dagster_example.settings")
    data_processing_mod = importlib.import_module("kedro_dagster_example.pipelines.data_processing.pipeline")
    data_science_mod = importlib.import_module("kedro_dagster_example.pipelines.data_science.pipeline")
    model_tuning_mod = importlib.import_module("kedro_dagster_example.pipelines.model_tuning.pipeline")
    pipeline_registry_mod = importlib.import_module("kedro_dagster_example.pipeline_registry")
    definitions_mod = importlib.import_module("kedro_dagster_example.definitions")

    importlib.reload(settings_mod)
    importlib.reload(data_processing_mod)
    importlib.reload(data_science_mod)
    importlib.reload(model_tuning_mod)
    importlib.reload(pipeline_registry_mod)
    importlib.reload(definitions_mod)

    return definitions_mod


@pytest.mark.parametrize("env,job", _env_job_pairs())
def test_all_dagster_jobs_run_for_all_envs(env, job):
    job_def, resources = job
    job_name = job_def.name

    # If this is the dev environment, the model_tuning pipeline relies on an
    # Optuna StudyDataset backed by PostgreSQL. When Postgres is not
    # available (e.g. on a developer machine without Docker running), we
    # skip these tests rather than fail the suite.
    if env == "dev" and "model_tuning" in job_name:
        # Re-evaluate the Postgres availability mark here to avoid importing
        # the helper directly in this module.
        if not _can_connect_to_postgres():
            pytest.skip("Postgres is not available; skipping dev environment tests for `model_tuning`.")

    job_def.execute_in_process(resources=resources, raise_on_error=True)
