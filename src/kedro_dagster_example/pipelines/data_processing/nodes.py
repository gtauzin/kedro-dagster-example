from collections.abc import Callable
from typing import Any

import pandas as pd
from kedro_dagster import NOTHING_OUTPUT, logging


def _is_true(x: pd.Series) -> pd.Series:
    return x == "t"


def _parse_percentage(x: pd.Series) -> pd.Series:
    x = x.str.replace("%", "")
    x = x.astype(float) / 100
    return x


def _parse_money(x: pd.Series) -> pd.Series:
    x = x.str.replace("$", "").str.replace(",", "")
    x = x.astype(float)
    return x


def concatenate_partitions(
    df_partitions: dict[str, Callable[[], Any]],
    are_partitions_processed: None = None,
) -> pd.DataFrame:
    """Concatenate input partitions into one pandas DataFrame.

    Args:
        df_partitions: A dictionary with partition ids as keys and load functions as values.

    Returns:
        Pandas DataFrame representing a concatenation of all loaded partitions.
    """
    logger = logging.getLogger(__name__)

    df_list = []
    for partition_name, partition_val in sorted(df_partitions.items()):
        logger.info(f"Concatenating partition {partition_name}")
        if partition_name:
            if isinstance(partition_val, pd.DataFrame):
                df_partition = partition_val
            else:
                df_partition = partition_val()

            df_list.append(df_partition)

    df = pd.concat(df_list)

    return df


def preprocess_companies(companies: dict) -> pd.DataFrame:
    """Preprocesses the data for companies.

    Args:
        companies: Raw data.

    Returns
    -------
        Preprocessed data, with `company_rating` converted to a float and
        `iata_approved` converted to boolean.
    """
    logger = logging.getLogger(__name__)

    preprocess_companies = {}
    for upstream_partition_key, companies_df_load_fn in companies.items():
        logger.info(f"Preprocessing companies partition {upstream_partition_key}")
        preprocess_companies_df = companies_df_load_fn()
        preprocess_companies_df["iata_approved"] = _is_true(preprocess_companies_df["iata_approved"])
        preprocess_companies_df["company_rating"] = _parse_percentage(preprocess_companies_df["company_rating"])

        downstream_partition_key = upstream_partition_key.split(".csv")[0] + "0.csv"
        preprocess_companies[downstream_partition_key] = preprocess_companies_df
    return preprocess_companies, NOTHING_OUTPUT


def preprocess_shuttles(shuttles: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the data for shuttles.

    Args:
        shuttles: Raw data.

    Returns
    -------
        Preprocessed data, with `price` converted to a float and `d_check_complete`,
        `moon_clearance_complete` converted to boolean.
    """
    logger = logging.getLogger(__name__)

    logger.info("Preprocessing shuttles")
    shuttles["d_check_complete"] = _is_true(shuttles["d_check_complete"])
    shuttles["moon_clearance_complete"] = _is_true(shuttles["moon_clearance_complete"])
    shuttles["price"] = _parse_money(shuttles["price"])
    return shuttles


def create_model_input_table(shuttles: pd.DataFrame, companies: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    """Combines all data to create a model input table.

    Args:
        shuttles: Preprocessed data for shuttles.
        companies: Preprocessed data for companies.
        reviews: Raw data for reviews.

    Returns
    -------
        Model input table.

    """
    logger = logging.getLogger(__name__)

    logger.info("Creating model input table")
    rated_shuttles = shuttles.merge(reviews, left_on="id", right_on="shuttle_id")
    rated_shuttles = rated_shuttles.drop("id", axis=1)
    model_input_table = rated_shuttles.merge(companies, left_on="company_id", right_on="id")
    model_input_table = model_input_table.dropna()
    return model_input_table
