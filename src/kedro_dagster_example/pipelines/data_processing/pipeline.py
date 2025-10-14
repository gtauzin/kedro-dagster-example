from kedro.pipeline import Pipeline, node, pipeline

from kedro_dagster_example import settings

from .nodes import (
    concatenate_partitions,
    create_model_input_table,
    preprocess_companies,
    preprocess_shuttles,
)


def create_pipeline(**kwargs) -> Pipeline:
    data_processing = pipeline([
        node(
            func=preprocess_companies,
            inputs="companies_dagster_partition",
            outputs=["preprocessed_companies_dagster_partition", "is_company_preprocessing_done"],
            name="preprocess_companies_node",
        ),
        node(
            func=concatenate_partitions,
            inputs=["preprocessed_companies_partition", "is_company_preprocessing_done"],
            outputs="preprocessed_companies",
            name="concatenate_preprocessed_companies_partitions_node",
        ),
        # node(
        #     func=concatenate_partitions,
        #     inputs="companies_partition",
        #     outputs="companies",
        #     name="concatenate_companies_partitions_node",
        # ),
        # node(
        #     func=preprocess_companies,
        #     inputs="companies",
        #     outputs="preprocessed_companies",
        #     name="preprocess_companies_node",
        # ),
        node(
            func=concatenate_partitions,
            inputs="shuttles_partition",
            outputs="shuttles",
            name="concatenate_shuttless_partitions_node",
        ),
        node(
            func=concatenate_partitions,
            inputs="reviews_partition",
            outputs="reviews",
            name="concatenate_reviews_partitions_node",
        ),
        node(
            func=preprocess_shuttles,
            inputs="shuttles",
            outputs="preprocessed_shuttles",
            name="preprocess_shuttles_node",
        ),
        node(
            func=create_model_input_table,
            inputs=["preprocessed_shuttles", "preprocessed_companies", "reviews"],
            outputs="model_input_table",
            name="create_model_input_table_node",
        ),
    ])

    pipes = []
    for namespace in settings.DYNAMIC_PIPELINES_MAPPING.keys():
        pipes.append(
            pipeline(
                data_processing,
                inputs={
                    "companies_dagster_partition": "companies_dagster_partition",
                    # "companies_partition": "companies_partition",
                    "shuttles_partition": "shuttles_partition",
                    "reviews_partition": "reviews_partition",
                },
                namespace=namespace,
                tags=settings.DYNAMIC_PIPELINES_MAPPING[namespace],
            )
        )

    return sum(pipes)
