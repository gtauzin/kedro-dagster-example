"""Nox sessions."""

import nox

# Require Nox version 2024.3.2 or newer to support the 'default_venv_backend' option
nox.needs_version = ">=2024.3.2"

# Set 'uv' as the default backend for creating virtual environments
nox.options.default_venv_backend = "uv|virtualenv"

# Default sessions to run when nox is called without arguments
nox.options.sessions = ["fix", "tests"]


# Test sessions for different Python versions
@nox.session(python=["3.10", "3.11", "3.12", "3.13"], venv_backend="uv")
def tests_coverage(session: nox.Session) -> None:
    """Run the tests with pytest under the specified Python version."""
    session.env["COVERAGE_FILE"] = f".coverage.{session.python}"
    session.env["COVERAGE_PROCESS_START"] = "pyproject.toml"

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
