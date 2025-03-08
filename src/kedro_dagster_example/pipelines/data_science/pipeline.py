from kedro.pipeline import Pipeline, node, pipeline

from kedro_dagster_example import settings

from .nodes import evaluate_model, split_data, train_model


def create_pipeline(**kwargs) -> Pipeline:
    data_science_pipeline = pipeline([
        node(
            func=split_data,
            inputs=["model_input_table", "params:model_options"],
            outputs=["X_train", "X_test", "y_train", "y_test"],
            name="split_data_node",
        ),
        node(
            func=train_model,
            inputs=["X_train", "y_train"],
            outputs="regressor",
            name="train_model_node",
        ),
        node(
            func=evaluate_model,
            inputs=["regressor", "X_test", "y_test"],
            outputs=None,
            name="evaluate_model_node",
        ),
    ])

    pipes = []
    for namespace, variants in settings.DYNAMIC_PIPELINES_MAPPING.items():
        for variant in variants:
            pipes.append(
                pipeline(
                    data_science_pipeline,
                    inputs={"model_input_table": f"{namespace}.model_input_table"},
                    namespace=f"{namespace}.{variant}",
                    tags=[variant, namespace],
                )
            )

    return sum(pipes)
