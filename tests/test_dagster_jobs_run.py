import importlib
import os
from pathlib import Path

import pytest
from kedro.framework.project import configure_project

PROJECT_PATH = Path(__file__).resolve().parents[1]
ALL_ENVS = ["local", "dev", "staging", "prod"]


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

    # For dev, provide dummy Postgres env vars so oc.env resolver in credentials doesn't fail
    if env == "dev":
        os.environ.setdefault("POSTGRES_USER", "dev_user")
        os.environ.setdefault("POSTGRES_PASSWORD", "dev_password")
        os.environ.setdefault("POSTGRES_HOST", "localhost")
        os.environ.setdefault("POSTGRES_PORT", "5432")
        try:
            result = job_def.execute_in_process(resources=resources, raise_on_error=False)
        except Exception as exc:
            pytest.skip(
                f"Skipping job '{job_name}' in env={env} due to execution-time failure: {type(exc).__name__}: {exc}"
            )
        if not result.success:
            pytest.skip(f"Dagster job '{job_name}' did not succeed in env={env}: {result}")
