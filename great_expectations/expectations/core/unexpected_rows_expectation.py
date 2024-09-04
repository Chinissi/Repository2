from __future__ import annotations

import logging
from string import Formatter
from typing import TYPE_CHECKING, ClassVar, Tuple, Union

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.typing_extensions import override
from great_expectations.expectations.expectation import BatchExpectation
from great_expectations.render.renderer_configuration import (
    AddParamArgs,
    RendererConfiguration,
    RendererValueType,
)

if TYPE_CHECKING:
    from great_expectations.core import ExpectationValidationResult
    from great_expectations.execution_engine import ExecutionEngine


logger = logging.getLogger(__name__)


class UnexpectedRowsExpectation(BatchExpectation):
    """
    UnexpectedRowsExpectations facilitate the execution of SQL or Spark-SQL queries as the core logic for an Expectation.

    If subclassing UnexpectedRowsExpectation, one can implement a `_validate(...)` method containing logic for determining whether data returned by the executed query is successfully validated.
    One is written by default, but can be overridden.
    A successful validation is one where the unexpected_rows_query returns no rows.

    Args:
        unexpected_rows_query (str): A SQL or Spark-SQL query to be executed for validation.
    """  # noqa: E501

    unexpected_rows_query: str

    metric_dependencies: ClassVar[Tuple[str, ...]] = ("unexpected_rows_query.table",)
    success_keys: ClassVar[Tuple[str, ...]] = ("unexpected_rows_query",)
    domain_keys: ClassVar[Tuple[str, ...]] = (
        "batch_id",
        "row_condition",
        "condition_parser",
    )

    @pydantic.validator("unexpected_rows_query")
    def _validate_query(cls, query: str) -> str:
        parsed_fields = [f[1] for f in Formatter().parse(query)]
        if "batch" not in parsed_fields:
            batch_warning_message = (
                "unexpected_rows_query should contain the {batch} parameter. "
                "Otherwise data outside of the configured batch will be queried."
            )
            # instead of raising a disruptive warning, we print and log info
            # in order to make the user aware of the potential for querying
            # data outside the configured batch
            print(batch_warning_message)
            logger.info(batch_warning_message)

        return query

    @classmethod
    @override
    def _prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> RendererConfiguration:
        add_param_args: AddParamArgs = (("unexpected_rows_query", RendererValueType.STRING),)
        for name, param_type in add_param_args:
            renderer_configuration.add_param(name=name, param_type=param_type)

        renderer_configuration.template_str = "$unexpected_rows_query"

        return renderer_configuration

    @override
    def _validate(
        self,
        metrics: dict,
        runtime_configuration: dict | None = None,
        execution_engine: ExecutionEngine | None = None,
    ) -> Union[ExpectationValidationResult, dict]:
        metric_value = metrics["unexpected_rows_query.table"]
        unexpected_row_count = len(metric_value)
        observed_value = f"{unexpected_row_count} unexpected "
        if unexpected_row_count == 1:
            observed_value += "row"
        else:
            observed_value += "rows"
        return {
            "success": unexpected_row_count == 0,
            "result": {
                "observed_value": observed_value,
                "details": {"unexpected_rows": metric_value},
            },
        }
