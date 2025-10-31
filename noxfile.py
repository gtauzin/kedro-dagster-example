"""Nox sessions."""

import os

import nox

# Require Nox version 2024.3.2 or newer to support the 'default_venv_backend' option
nox.needs_version = ">=2024.3.2"

# Set 'uv' as the default backend for creating virtual environments
nox.options.default_venv_backend = "uv|virtualenv"

# Default sessions to run when nox is called without arguments
nox.options.sessions = ["fix", "tests"]


# Compute available Kedro environments from the `conf/` folder and parametrize tests
# Exclude `base` since it's shared config, not an environment to test.
conf_root = os.path.join(os.path.dirname(__file__), "conf")
# Only take actual directories under conf (skip files like README.md, logging.yml)
ENVIRONMENTS = sorted([d for d in os.listdir(conf_root) if os.path.isdir(os.path.join(conf_root, d)) and d != "base"])


# Test sessions for different Python versions and Kedro environments
@nox.session(python=["3.10", "3.11", "3.12", "3.13"], venv_backend="uv")
@nox.parametrize("kedro_env", ENVIRONMENTS)
def tests(session: nox.Session, kedro_env: str) -> None:
    """Run the tests with pytest under the specified Python version and Kedro environment.

    This session is parametrized with `kedro_env` (one of the subfolders under `conf/`).
    It sets the `KEDRO_ENV` environment variable so code/tests pick the correct configuration.
    """

    # Install dependencies
    session.run_install(
        "uv",
        "sync",
        "--no-default-groups",
        "--group",
        "tests",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )

    # Run unit tests under coverage
    session.run(
        "uv",
        "run",
        "pytest",
        "tests",
        "-k",
        kedro_env,
        *session.posargs,
    )


@nox.session(venv_backend="uv")
def fix(session: nox.Session) -> None:
    """Format the code base to adhere to our styles, and complain about what we cannot do automatically."""
    # Install dependencies
    session.run_install(
        "uv",
        "sync",
        "--no-default-groups",
        "--group",
        "fix",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    # Run pre-commit
    session.run("pre-commit", "run", "--all-files", "--show-diff-on-failure", *session.posargs, external=True)
