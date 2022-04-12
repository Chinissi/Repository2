from typing import Any, Dict

from great_expectations import DataContext
from great_expectations.rule_based_profiler.data_assistant import (
    DataAssistant,
    VolumeDataAssistant,
)
from great_expectations.rule_based_profiler.types import Domain


def test_get_metrics(
    quentin_columnar_table_multi_batch_data_context,
):
    context: DataContext = quentin_columnar_table_multi_batch_data_context

    batch_request: dict = {
        "datasource_name": "taxi_pandas",
        "data_connector_name": "monthly",
        "data_asset_name": "my_reports",
    }

    expected_metrics: Dict[Domain, Dict[str, Any]] = {
        Domain(domain_type="table",): {
            "$parameter.table_row_count.value": [
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
                10000,
            ],
            "$parameter.table_row_count.details": {
                "metric_configuration": {
                    "metric_name": "table.row_count",
                    "domain_kwargs": {},
                    "metric_value_kwargs": None,
                    "metric_dependencies": None,
                },
                "num_batches": 36,
            },
        },
    }

    data_assistant: DataAssistant = VolumeDataAssistant(
        name="test_volume_data_assistant",
        batch_request=batch_request,
        data_context=context,
    )
    data_assistant.build()
    # TODO: <Alex>ALEX -- WILL_RETURN_RESULT_OBJECT</Alex>
    data_assistant.run()
    # TODO: <Alex>ALEX -- WILL_RETURN_RESULT_OBJECT</Alex>
    actual_metrics: Dict[Domain, Dict[str, Any]] = data_assistant.get_metrics()

    assert actual_metrics == expected_metrics
