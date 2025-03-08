from kedro.pipeline import Pipeline, node, pipeline

from kedro_dagster_example import settings
from kedro_dagster_example.pipelines.data_science.nodes import split_data

from .nodes import create_study, log_study, tune_model

n_tuning_processes = 2


def create_pipeline(**kwargs) -> Pipeline:
    model_tuning_pipeline = pipeline([
        node(
            func=split_data,
            inputs=["model_input_table", "params:model_options"],
            outputs=["X_train_tuning", "X_test_tuning", "y_train_tuning", "y_test_tuning"],
            name="split_data_tuning_node",
        ),
        node(
            func=create_study,
            inputs=None,
            outputs="study",
            name="create_study_node",
        ),
    ])

    for i_tuning_process in range(n_tuning_processes):
        model_tuning_pipeline += pipeline([
            node(
                func=tune_model,
                inputs=["X_train_tuning", "y_train_tuning", "study", "params:study_params"],
                outputs=f"tuning_node_done_{i_tuning_process}",
                name=f"tune_model_node_{i_tuning_process}",
            ),
        ])

    model_tuning_pipeline += pipeline([
        node(
            func=log_study,
            inputs=["study"]
            + [f"tuning_node_done_{i_tuning_process}" for i_tuning_process in range(n_tuning_processes)],
            outputs="study_artifact",
            name="log_study_node",
        ),
    ])

    pipes = []
    for namespace, variants in settings.DYNAMIC_PIPELINES_MAPPING.items():
        for variant in variants:
            pipes.append(
                pipeline(
                    model_tuning_pipeline,
                    inputs={"model_input_table": f"{namespace}.model_input_table"},
                    namespace=f"{namespace}.{variant}",
                    tags=[variant, namespace],
                )
            )

    return sum(pipes)
