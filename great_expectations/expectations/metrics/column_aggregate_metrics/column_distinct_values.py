from typing import Any, Dict, Optional, Tuple

import pandas as pd

from great_expectations.core import ExpectationConfiguration
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.column_aggregate_metric import (
    ColumnMetricProvider,
    column_aggregate_metric,
)
from great_expectations.expectations.metrics.metric_provider import metric
from great_expectations.validator.validation_graph import MetricConfiguration


class ColumnDistinctValues(ColumnMetricProvider):
    metric_name = "column.distinct_values"

    @column_aggregate_metric(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return set(column.unique())

    @metric(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        execution_engine: "SqlAlchemyExecutionEngine",
        metric_domain_kwargs: Dict,
        metric_value_kwargs: Dict,
        metrics: Dict[Tuple, Any],
        runtime_configuration: Dict,
    ):
        observed_value_counts = metrics["column.value_counts"]
        return set(observed_value_counts.index)

    @metric(engine=SparkDFExecutionEngine)
    def _spark(
        cls,
        execution_engine: "SqlAlchemyExecutionEngine",
        metric_domain_kwargs: Dict,
        metric_value_kwargs: Dict,
        metrics: Dict[Tuple, Any],
        runtime_configuration: Dict,
    ):
        observed_value_counts = metrics["column.value_counts"]
        return set(observed_value_counts.index)

    @classmethod
    def get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[Dict] = None,
    ):
        """Returns a dictionary of given metric names and their corresponding configuration,
        specifying the metric types and their respective domains"""
        if isinstance(
            ExecutionEngine, (SqlAlchemyExecutionEngine, SparkDFExecutionEngine)
        ):
            return {
                "column.value_counts": MetricConfiguration(
                    metric_name="column.value_counts",
                    metric_domain_kwargs=metric.metric_domain_kwargs,
                    metric_value_kwargs={"sort": "value", "collate": None},
                )
            }

        return dict()
