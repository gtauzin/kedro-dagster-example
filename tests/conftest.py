"""Pytest configuration and fixtures for the kedro-dagster-example project."""

from __future__ import annotations

import os
from pathlib import Path

import psycopg2
import pytest

ALL_ENVS = ["local", "dev", "staging", "prod"]
PROJECT_PATH = Path(__file__).resolve().parents[1]


# Ensure POSTGRES_* defaults are present as soon as the test suite imports
# this module. This is required because some tests (e.g. Dagster/Kedro
# translation in ``tests/test_dagster_jobs_run.py``) trigger Kedro context
# and credentials loading at *collection time*, before any fixtures run.
_POSTGRES_DEFAULTS = {
    "POSTGRES_USER": "dev_user",
    "POSTGRES_PASSWORD": "dev_password",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
}

for key, value in _POSTGRES_DEFAULTS.items():
    os.environ.setdefault(key, value)


@pytest.fixture(autouse=True, scope="session")
def _ensure_postgres_env() -> dict[str, str]:
    """Expose POSTGRES_* env vars for the whole test session.

    The actual defaulting is done at module import time (see
    ``_POSTGRES_DEFAULTS`` above) so that any Kedro/Dagster initialization
    that happens during test collection already sees the expected
    environment.

    Using ``setdefault`` at import time means real values from the
    developer or CI environment take precedence, while local runs still
    work out of the box.
    """

    # Return the final values for potential debugging/introspection
    return {key: os.environ[key] for key in _POSTGRES_DEFAULTS}


def _can_connect_to_postgres() -> bool:
    """Return True if a PostgreSQL server is reachable with current env vars.

    Uses the POSTGRES_* variables configured for the tests. This is a very
    small connectivity probe used only to decide whether to run or skip
    Postgres-dependent tests.
    """

    try:
        conn = psycopg2.connect(
            dbname=os.environ.get("POSTGRES_DB", "dev_db"),
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PASSWORD"],
            host=os.environ["POSTGRES_HOST"],
            port=int(os.environ.get("POSTGRES_PORT", "5432")),
            connect_timeout=1,
        )
    except Exception:
        return False
    else:
        conn.close()
        return True
