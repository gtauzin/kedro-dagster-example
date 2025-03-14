"""Project settings.

There is no need to edit this file
unless you want to change values from the Kedro defaults.
For further information, including these default values, see
https://docs.kedro.org/en/stable/kedro_project_setup/settings.html.
"""

# Hooks are executed in a Last-In-First-Out (LIFO) order.
# HOOKS = (ProjectHooks(),)

# Installed plugins for which to disable hook auto-registration.
# DISABLE_HOOKS_FOR_PLUGINS = ("kedro-viz",)

# Class that manages storing KedroSession data.
# from kedro.framework.session.store import BaseSessionStore
# SESSION_STORE_CLASS = BaseSessionStore
# Keyword arguments to pass to the `SESSION_STORE_CLASS` constructor.
# SESSION_STORE_ARGS = {
#     "path": "./sessions"
# }

# Directory that holds configuration.
# CONF_SOURCE = "conf"

import os

from kedro.config import OmegaConfigLoader
from kedro.io import KedroDataCatalog
from omegaconf.resolvers import oc

KEDRO_ENV = os.getenv("KEDRO_ENV")

CONFIG_LOADER_CLASS = OmegaConfigLoader
# Keyword arguments to pass to the `CONFIG_LOADER_CLASS` constructor.
CONFIG_LOADER_ARGS = {
    "base_env": "base",
    "default_run_env": "local",
    "custom_resolvers": {
        "oc.env": oc.env,
    },
}
DATA_CATALOG_CLASS = KedroDataCatalog

if KEDRO_ENV == "local":
    DYNAMIC_PIPELINES_MAPPING = {
        "reviews_predictor": ["base", "candidate1"],
        "price_predictor": [
            "base",
            "candidate1",
            "test1",
        ],
    }
elif KEDRO_ENV == "dev":
    DYNAMIC_PIPELINES_MAPPING = {
        "price_predictor": ["test1"],
    }
elif KEDRO_ENV == "staging":
    DYNAMIC_PIPELINES_MAPPING = {
        "reviews_predictor": ["candidate1"],
        "price_predictor": ["candidate1"],
    }
elif KEDRO_ENV == "prod":
    DYNAMIC_PIPELINES_MAPPING = {
        "reviews_predictor": ["base"],
        "price_predictor": ["base"],
    }
