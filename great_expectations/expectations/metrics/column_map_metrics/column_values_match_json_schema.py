import json

import jsonschema

from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.expectations.metrics.column_map_metric import (
    ColumnMapMetricProvider,
    column_map_condition,
)
from great_expectations.expectations.metrics.import_manager import F, sparktypes


class ColumnValuesMatchJsonSchema(ColumnMapMetricProvider):
    condition_metric_name = "column_values.match_json_schema"

    @column_map_condition(engine=PandasExecutionEngine)
    def _pandas(cls, column, json_schema, **kwargs):
        def matches_json_schema(val):
            try:
                val_json = json.loads(val)
                jsonschema.validate(val_json, json_schema)
                # jsonschema.validate raises an error if validation fails.
                # So if we make it this far, we know that the validation succeeded.
                return True
            except jsonschema.ValidationError:
                return False
            except jsonschema.SchemaError:
                raise
            except:
                raise

        return column.map(matches_json_schema)

    @column_map_condition(engine=SparkDFExecutionEngine)
    def _spark(cls, column, json_schema, **kwargs):
        def matches_json_schema(val):
            try:
                val_json = json.loads(val)
                jsonschema.validate(val_json, json_schema)
                # jsonschema.validate raises an error if validation fails.
                # So if we make it this far, we know that the validation succeeded.
                return True
            except jsonschema.ValidationError:
                return False
            except jsonschema.SchemaError:
                raise
            except:
                raise

        matches_json_schema_udf = F.udf(matches_json_schema, sparktypes.BooleanType())

        return matches_json_schema_udf(column)
