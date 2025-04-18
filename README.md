# kedro-dagster-example

![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)

This repository aims to demonstrate the [`kedro-dagster`](https://github.com/gtauzin/kedro-dagster) plugin in the context of a real‑world, deployed Kedro project.

## Setup

This repo builds on the [Kedro Spaceflights tutorial](https://docs.kedro.org/en/stable/tutorial/spaceflights_tutorial.html), augmented with dynamic pipelines following the [GetInData blog post](https://getindata.com/blog/kedro-dynamic-pipelines/).

> [!NOTE]
> Here, parameters for dynamic pipelines are namespaced via YAML inheritance rather than a custom `merge` resolver.

Additionally, this project makes use of:

- [`mlflow`](https://mlflow.org/) via the [`kedro-mlflow`](https://github.com/Galileo-Galilei/kedro-mlflow) plugin for experiment tracking, model registry, and deployment.
- [`optuna`](https://optuna.org/) through a new Kedro dataset. See the `optuna.StudyDataset` [documentation](https://docs.kedro.org/projects/kedro-datasets/en/latest/api/kedro_datasets_experimental.optuna.StudyDataset.html) for details.

A variety of Kedro environments highlight how a Kedro + Dagster deployment might look. We assume that each pipeline can be at a different stage—under development, in staging, or in production. The logic for separating dynamic pipelines across environments lives in `settings.py` and `pipeline_registry.py`. The available environments are:

- **local**: for developing and running all pipelines on local data.
- **dev**: for testing new or updated pipelines with larger datasets.
- **staging**: for pipelines ready for production‑like conditions before going live.
- **prod**: for fully deployed pipelines running in production.

In this repo, each environment’s `catalog.yml` points to local data. In practice, you might keep local data only in `local` and configure remote datasets for `dev`, `staging`, and `prod`.

> [!NOTE]
> You may also choose to use separate Git branches for `prod`, `staging`, and various `dev` environments.

## Installation

This project uses [uv](https://docs.astral.sh/uv/) for packaging and dependency management. To install:

1. Follow the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/).
2. Run the following to sync dependencies (from `uv.lock`) into a new virtual environment:

   ```bash
   uv sync
   ```

3. Activate the virtual environment:

   ```bash
   source .venv/bin/activate
   ```

## Quick Start

This repository already comes with `kedro-dasgter` initialized for each of the available Kedro environments. In practice, this means there is no need to run

```bash
kedro dagster init --env <KEDRO_ENV>
```

and the `definitions.py` file along with the `conf/<KEDRO_ENV>/dagster.yml` configuration files for each Kedro environment are already provided.

### Running the Pipelines

You can run the Kedro pipelines using `kedro run` as usual

```bash
uv run kedro run --env KEDRO_ENV
```

assuming KEDRO_ENV is an environmental variable set to your target environment (e.g. `local`)

To explore the pipelines in the Dagster UI:

```bash
export KEDRO_ENV=local
kedro dagster dev
```

You’ll see your Kedro datasets as Dagster assets and your pipelines as Dagster jobs.

### Deploying the Pipelines

Each Kedro environment maps to its own Dagster code location. If you’re using Dagster on Kubernetes, build a separate Docker image per environment (e.g., `local`, `dev`, `staging`, `prod`).

```bash
# Example Docker build for the staging environment
docker build \
  --build-arg KEDRO_ENV=staging \
  -t myrepo/kedro-dagster:staging .
```

See [`kedro-docker`](https://github.com/kedro-org/kedro-plugins/tree/main/kedro-docker) for more information on how to create a Docker image for your Kedro project.
