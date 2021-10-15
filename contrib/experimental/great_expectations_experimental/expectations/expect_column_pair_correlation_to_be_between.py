import copy
import json
from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats as stats

from great_expectations.core import ExpectationConfiguration
from great_expectations.execution_engine import (
    ExecutionEngine,
    PandasExecutionEngine,
    SparkDFExecutionEngine,
)
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.expectation import (
    ColumnExpectation,
    ColumnPairExpectation,
    Expectation,
    ExpectationConfiguration,
    InvalidExpectationConfigurationError,
    _format_map_output,
)
from great_expectations.expectations.metrics import (
    column_condition_partial,
    column_function_partial,
)
from great_expectations.expectations.metrics.column_aggregate_metric_provider import (
    ColumnMetricProvider,
    ColumnPairAggregateMetricProvider,
    column_aggregate_value,
    column_pair_aggregate_value,
)
from great_expectations.expectations.metrics.import_manager import Bucketizer, F, sa
from great_expectations.expectations.metrics.metric_provider import (
    MetricProvider,
    metric_value,
)
from great_expectations.expectations.util import render_evaluation_parameter_string
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.types import RenderedStringTemplateContent
from great_expectations.render.util import (
    handle_strict_min_max,
    num_to_str,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)
from great_expectations.validator.validation_graph import MetricConfiguration


class ColumnCorrelation(ColumnPairAggregateMetricProvider):
    """MetricProvider Class for column pair correlation"""

    metric_name = "column_pair.correlation"

    @column_pair_aggregate_value(engine=PandasExecutionEngine)
    def _pandas(cls, column_A, column_B, **kwargs):
        return column_A.corr(column_B)

    @column_pair_aggregate_value(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy(
        cls,
        column_A,
        column_B,
        _table=None,
        _dialect=None,
        _sqlalchemy_engine=None,
        _metrics=None,
        **kwargs
    ):
        # def get_query_result(f):
        #     # maybe add this to the engine object for convenience
        #     query = sa.select(f).select_from(_table)
        #     return _sqlalchemy_engine.execute(query).scalar()

        # add a way to make upstream column metrics dependencies
        # mean_a = get_query_result(sa.func.avg(column_A))
        # mean_b = get_query_result(sa.func.avg(column_B))

        mean_a = _metrics.get("column_A.mean")
        mean_b = _metrics.get("column_B.mean")

        ab, aa, bb = cls._sqlalchemy_anonymous_metric(
            [
                sa.func.avg((column_A - mean_a) * (column_B - mean_b)),
                sa.func.avg(sa.func.pow(column_A - mean_a, 2)),
                sa.func.avg(sa.func.pow(column_B - mean_b, 2)),
            ],
            _sqlalchemy_engine=_sqlalchemy_engine,
            _table=_table,
        )
        # ab = get_query_result(sa.func.avg((column_A - mean_a) * (column_B - mean_b)))
        # aa = get_query_result(sa.func.avg(sa.func.pow(column_A - mean_a, 2)))
        # bb = get_query_result(sa.func.avg(sa.func.pow(column_B - mean_b, 2)))

        corr = ab / (aa ** 0.5) / (bb ** 0.5)
        return corr

    @classmethod
    def _sqlalchemy_anonymous_metric(
        cls, f, _sqlalchemy_engine, _table=None, _dialect=None
    ):
        # maybe add this to the engine object for convenience
        query = sa.select(f).select_from(_table)
        return _sqlalchemy_engine.execute(query).fetchone()

    @column_function_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy_function(cls, column, _metrics, _dialect, **kwargs):
        mean = _metrics["column.mean"]
        standard_deviation = _metrics["column.standard_deviation"]
        return (column - mean) / standard_deviation

    @column_condition_partial(engine=SqlAlchemyExecutionEngine)
    def _sqlalchemy_condition(cls, column, _metrics, threshold, double_sided, **kwargs):

        z_score, _, _ = _metrics["column_values.z_score.map"]
        if double_sided:
            under_threshold = sa.func.abs(z_score) < abs(threshold)
        else:
            under_threshold = z_score < threshold

        return under_threshold

    @classmethod
    def _get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        """Returns a dictionary of given metric names and their corresponding configuration, specifying the metric
        types and their respective domains"""
        dependencies: dict = super()._get_evaluation_dependencies(
            metric=metric,
            configuration=configuration,
            execution_engine=execution_engine,
            runtime_configuration=runtime_configuration,
        )

        if metric.metric_name == "column_pair.m1":
            domain = copy.copy(metric.metric_domain_kwargs)
            column_A = domain.pop("column_A")
            column_B = domain.pop("column_B")

            column_A_domain = copy.copy(domain)
            column_A_domain.update({"column": column_A})

            column_B_domain = copy.copy(domain)
            column_B_domain.update({"column": column_B})

            dependencies["column_A.mean"] = MetricConfiguration(
                metric_name="column.mean",
                metric_domain_kwargs=column_A_domain,
            )

            dependencies["column_B.mean"] = MetricConfiguration(
                metric_name="column.mean",
                metric_domain_kwargs=column_B_domain,
            )

        return dependencies

    # def _sqlalchemy(
    #     cls,
    #     execution_engine: "SqlAlchemyExecutionEngine",
    #     metric_domain_kwargs: Dict,
    #     metric_value_kwargs: Dict,
    #     metrics: Dict[Tuple, Any],
    #     runtime_configuration: Dict,
    # ):
    #     (
    #         selectable,
    #         compute_domain_kwargs,
    #         accessor_domain_kwargs,
    #     ) = execution_engine.get_compute_domain(
    #         metric_domain_kwargs, MetricDomainTypes.COLUMN
    #     )
    #     column_name = accessor_domain_kwargs["column"]
    #     column = sa.column(column_name)
    #     sqlalchemy_engine = execution_engine.engine
    #     dialect = sqlalchemy_engine.dialect
    #
    #     column_median = None
    #
    #     # TODO: compute the value and return it
    #
    #     return column_median
    #
    # @metric_value(engine=SparkDFExecutionEngine, metric_fn_type="value")
    # def _spark(
    #     cls,
    #     execution_engine: "SqlAlchemyExecutionEngine",
    #     metric_domain_kwargs: Dict,
    #     metric_value_kwargs: Dict,
    #     metrics: Dict[Tuple, Any],
    #     runtime_configuration: Dict,
    # ):
    #     (
    #         df,
    #         compute_domain_kwargs,
    #         accessor_domain_kwargs,
    #     ) = execution_engine.get_compute_domain(
    #         metric_domain_kwargs, MetricDomainTypes.COLUMN
    #     )
    #     column = accessor_domain_kwargs["column"]
    #
    #     column_median = None
    #
    #     # TODO: compute the value and return it
    #
    #     return column_median
    #
    # @classmethod
    # def _get_evaluation_dependencies(
    #     cls,
    #     metric: MetricConfiguration,
    #     configuration: Optional[ExpectationConfiguration] = None,
    #     execution_engine: Optional[ExecutionEngine] = None,
    #     runtime_configuration: Optional[dict] = None,
    # ):
    #     """This should return a dictionary:
    #
    #     {
    #       "dependency_name": MetricConfiguration,
    #       ...
    #     }
    #     """
    #
    #     dependencies = super()._get_evaluation_dependencies(
    #         metric=metric,
    #         configuration=configuration,
    #         execution_engine=execution_engine,
    #         runtime_configuration=runtime_configuration,
    #     )
    #
    #     table_domain_kwargs = {
    #         k: v for k, v in metric.metric_domain_kwargs.items() if k != "column"
    #     }
    #
    #     dependencies.update(
    #         {
    #             "table.row_count": MetricConfiguration(
    #                 "table.row_count", table_domain_kwargs
    #             )
    #         }
    #     )
    #
    #     if isinstance(execution_engine, SqlAlchemyExecutionEngine):
    #         dependencies["column_values.nonnull.count"] = MetricConfiguration(
    #             "column_values.nonnull.count", metric.metric_domain_kwargs
    #         )
    #
    #     return dependencies


class ExpectColumnCorrelationToBeBetween(ColumnPairExpectation):
    """Test whether pearson correlation of columns is between a minimum and maximum value"""

    # These examples will be shown in the public gallery, and also executed as unit tests for your Expectation
    examples = [
        {
            "data": {
                "a": [  # this was drawn from the normal distribution
                    -0.42559356,
                    1.71053911,
                    -0.33074949,
                    -0.51614177,
                    -0.61934564,
                    1.1351354,
                    1.39973079,
                    -0.02995425,
                    0.84342204,
                    2.11280806,
                ],
                "b": [  # this was drawn from the gamma distribution
                    1.43829829,
                    5.73385056,
                    1.77222341,
                    0.50729875,
                    0.34536101,
                    1.54515905,
                    1.11811223,
                    0.8430591,
                    0.80270869,
                    1.02455144,
                ],
                "c": [  # this was drawn from the normal distribution
                    -0.42559356,
                    1.71053911,
                    -0.33074949,
                    -0.51614177,
                    -0.61934564,
                    1.1351354,
                    1.39973079,
                    -0.02995425,
                    0.84342204,
                    2.11280806,
                ],
            },
            "tests": [
                {
                    "title": "passes",
                    "include_in_gallery": True,
                    "exact_match_out": False,
                    "in": {
                        "column_A": "a",
                        "column_B": "c",
                        "min_value": 0.9,
                        "max_value": 1.0,
                    },
                    "out": {"success": True, "observed_value": 1.0},
                },
                {
                    "title": "fails",
                    "include_in_gallery": True,
                    "exact_match_out": False,
                    "in": {
                        "column_A": "a",
                        "column_B": "b",
                        "min_value": 0.5,
                        "max_value": 1.0,
                    },
                    "out": {"success": False},
                },
            ],
            "test_backends": [
                {
                    "backend": "pandas",
                    "dialects": None,
                },
                {
                    "backend": "sqlalchemy",
                    "dialects": ["mysql", "postgresql"],
                },
            ],
        },
    ]

    library_metadata = {
        "maturity": "experimental",
        "package": "great_expectations_experimental",
        "tags": ["experimental"],
        "contributors": ["@edjoesu"],
    }

    # Setting necessary computation metric dependencies and defining kwargs, as well as assigning kwargs default values\
    metric_dependencies = ("column_pair.correlation",)
    success_keys = (
        "min_value",
        "strict_min",
        "max_value",
        "strict_max",
    )

    # Default values
    default_kwarg_values = {
        "min_value": None,
        "max_value": None,
        "strict_min": None,
        "strict_max": None,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": True,
    }

    def validate_configuration(self, configuration: Optional[ExpectationConfiguration]):
        """
        Validates that a configuration has been set, and sets a configuration if it has yet to be set. Ensures that
        necessary configuration arguments have been provided for the validation of the expectation.

        Args:
            configuration (OPTIONAL[ExpectationConfiguration]): \
                An optional Expectation Configuration entry that will be used to configure the expectation
        Returns:
            True if the configuration has been validated successfully. Otherwise, raises an exception
        """
        super().validate_configuration(configuration)
        self.validate_metric_value_between_configuration(configuration=configuration)

    # @classmethod
    # @renderer(renderer_type="renderer.prescriptive")
    # @render_evaluation_parameter_string
    # def _prescriptive_renderer(
    #     cls,
    #     configuration=None,
    #     result=None,
    #     language=None,
    #     runtime_configuration=None,
    #     **kwargs,
    # ):
    #     runtime_configuration = runtime_configuration or {}
    #     include_column_name = runtime_configuration.get("include_column_name", True)
    #     include_column_name = (
    #         include_column_name if include_column_name is not None else True
    #     )
    #     styling = runtime_configuration.get("styling")
    #     params = substitute_none_for_missing(
    #         configuration.kwargs,
    #         [
    #             "column",
    #             "min_value",
    #             "max_value",
    #             "row_condition",
    #             "condition_parser",
    #             "strict_min",
    #             "strict_max",
    #         ],
    #     )
    #
    #     if (params["min_value"] is None) and (params["max_value"] is None):
    #         template_str = "median may have any numerical value."
    #     else:
    #         at_least_str, at_most_str = handle_strict_min_max(params)
    #         if params["min_value"] is not None and params["max_value"] is not None:
    #             template_str = f"median must be {at_least_str} $min_value and {at_most_str} $max_value."
    #         elif params["min_value"] is None:
    #             template_str = f"median must be {at_most_str} $max_value."
    #         elif params["max_value"] is None:
    #             template_str = f"median must be {at_least_str} $min_value."
    #
    #     if include_column_name:
    #         template_str = "$column " + template_str
    #
    #     if params["row_condition"] is not None:
    #         (
    #             conditional_template_str,
    #             conditional_params,
    #         ) = parse_row_condition_string_pandas_engine(params["row_condition"])
    #         template_str = conditional_template_str + ", then " + template_str
    #         params.update(conditional_params)
    #
    #     return [
    #         RenderedStringTemplateContent(
    #             **{
    #                 "content_block_type": "string_template",
    #                 "string_template": {
    #                     "template": template_str,
    #                     "params": params,
    #                     "styling": styling,
    #                 },
    #             }
    #         )
    #     ]

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: Dict,
        runtime_configuration: dict = None,
        execution_engine: ExecutionEngine = None,
    ):

        return self._validate_metric_value_between(
            metric_name="column_pair.correlation",
            configuration=configuration,
            metrics=metrics,
            runtime_configuration=runtime_configuration,
            execution_engine=execution_engine,
        )


if __name__ == "__main__":
    self_check_report = ExpectColumnCorrelationToBeBetween().run_diagnostics()
    print(json.dumps(self_check_report, indent=2))
