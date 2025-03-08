# kedro-dagster-example

![Powered by Kedro](https://img.shields.io/badge/powered_by-kedro-ffc900?logo=kedro)

This repository aims is to demonstrate the [`kedro-dagster`](https://github.com/gtauzin/kedro-dagster)
plugin in the context of a real-life Kedro project. It is inspired by the
[Kedro Spaceflights tutorial](https://docs.kedro.org/en/stable/tutorial/spaceflights_tutorial.html)
augmented with dynamic pipelines as per the [GetInData blog post](https://getindata.com/blog/kedro-dynamic-pipelines/).

> [!NOTE]
> Here, the namespacing of the dynamic pipelines' parameters is handled using YAML inheritance
> rather than a custom `merge` resolver.

Additionally, this project makes use of:

- [`mlflow`](https://mlflow.org/) through the [`kedro-mlflow`](https://github.com/Galileo-Galilei/kedro-mlflow)
  for experiment tracking, model registry, and deployment.
- [`optuna`](https://optuna.org/) through a new Kedro dataset. See the `optuna.StudyDataset` 
  [documentation](https://docs.kedro.org/projects/kedro-datasets/en/latest/api/kedro_datasets_experimental.optuna.StudyDataset.html) for more details.

## Installation

`kedro_dagster_example` uses [uv](https://docs.astral.sh/uv/) for packaging, managing dependencies, and environments.
To install it, follow the [uv installation instructions](https://docs.astral.sh/uv/getting-started/installation/).

To install the dependencies based on the `uv.lock` lock file, run:

```bash
uv sync
```

Then, to create a virtual environment, run:

```bash
uv venv
```

To activate the virtual environment, follow the instructions provided:

```bash
source .venv/bin/activate
```

## Setup

Once the project is installed, initialize `kedro-dagster`:

```bash
kedro dagster init --env local
```

This will create a `dagster.yml` in the configuration folder corresponding to
the `local` Kedro environment and a `definitions.py` in the source of the Kedro
project.

You can explore the mapping of the Kedro-based Dagster code location by running:

```bash
kedro dagster dev
```

This will prompt you to open the Dagster UI. There, you'll be able to check your
Kedro datasets as Dagster assets and your Kedro pipelines as Dagster jobs.
