import json

from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.expectations.metrics.column_map_metric import (
    ColumnMapMetricProvider,
    column_map_condition,
)
from great_expectations.expectations.metrics.import_manager import F, sparktypes


class ColumnValuesJsonParseable(ColumnMapMetricProvider):
    condition_metric_name = "column_values.json_parseable"

    @column_map_condition(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        def is_json(val):
            try:
                json.loads(val)
                return True
            except:
                return False

        return column.map(is_json)

    @column_map_condition(engine=SparkDFExecutionEngine)
    def _spark(cls, column, json_schema, **kwargs):
        def is_json(val):
            try:
                json.loads(val)
                return True
            except:
                return False

        is_json_udf = F.udf(is_json, sparktypes.BooleanType())

        return is_json_udf(column)
