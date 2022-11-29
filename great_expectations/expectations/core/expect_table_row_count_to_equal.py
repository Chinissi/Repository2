from typing import Dict, List, Optional, Tuple, Union

from great_expectations.core import (
    ExpectationConfiguration,
    ExpectationValidationResult,
)
from great_expectations.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation import (
    InvalidExpectationConfigurationError,
    TableExpectation,
    render_evaluation_parameter_string,
)
from great_expectations.render import LegacyRendererType, RenderedStringTemplateContent
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.renderer_configuration import RendererConfiguration


class ExpectTableRowCountToEqual(TableExpectation):
    """Expect the number of rows to equal a value.

    expect_table_row_count_to_equal is a :func:`expectation \
    <great_expectations.validator.validator.Validator.expectation>`, not a
    ``column_map_expectation`` or ``column_aggregate_expectation``.

    Args:
        value (int): \
            The expected number of rows.

    Other Parameters:
        result_format (string or None): \
            Which output mode to use: `BOOLEAN_ONLY`, `BASIC`, `COMPLETE`, or `SUMMARY`.
            For more detail, see :ref:`result_format <result_format>`.
        include_config (boolean): \
            If True, then include the expectation config as part of the result object. \
            For more detail, see :ref:`include_config`.
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see :ref:`catch_exceptions`.
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the output without \
            modification. For more detail, see :ref:`meta`.

    Returns:
        An ExpectationSuiteValidationResult

        Exact fields vary depending on the values passed to :ref:`result_format <result_format>` and
        :ref:`include_config`, :ref:`catch_exceptions`, and :ref:`meta`.

    See Also:
        expect_table_row_count_to_be_between
    """

    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "table expectation"],
        "contributors": [
            "@great_expectations",
        ],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }

    metric_dependencies = ("table.row_count",)
    success_keys = ("value",)
    default_kwarg_values = {
        "value": None,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
        "meta": None,
    }
    args_keys = ("value",)

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration]
    ) -> None:
        """
        Validates that a configuration has been set, and sets a configuration if it has yet to be set. Ensures that
        necessary configuration arguments have been provided for the validation of the expectation.

        Args:
            configuration (OPTIONAL[ExpectationConfiguration]): \
                An optional Expectation Configuration entry that will be used to configure the expectation
        Returns:
            None. Raises InvalidExpectationConfigurationError if the config is not validated successfully
        """

        # Setting up a configuration
        super().validate_configuration(configuration)

        value = configuration.kwargs.get("value")

        try:
            assert value is not None, "An expected row count must be provided"

            if not isinstance(value, (int, dict)):
                raise ValueError("Provided row count must be an integer")

            if isinstance(value, dict):
                assert (
                    "$PARAMETER" in value
                ), 'Evaluation Parameter dict for value kwarg must have "$PARAMETER" key.'
        except AssertionError as e:
            raise InvalidExpectationConfigurationError(str(e))

    @classmethod
    def _atomic_prescriptive_template(
        cls,
        renderer_configuration: RendererConfiguration,
    ) -> Tuple[str, dict, Union[dict, None]]:
        kwargs: dict = renderer_configuration.kwargs
        template_str = "Must have exactly $value rows."
        renderer_configuration.add_param(
            name="value", schema_type="number", value=kwargs.get("value")
        )
        test = renderer_configuration.params.dict(by_alias=True)
        return (
            template_str,
            renderer_configuration.params.dict(by_alias=True),
            renderer_configuration.styling,
        )

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        language: Optional[str] = None,
        runtime_configuration: Optional[dict] = None,
    ) -> List[RenderedStringTemplateContent]:
        renderer_configuration = RendererConfiguration(
            configuration=configuration,
            result=result,
            language=language,
            runtime_configuration=runtime_configuration,
        )
        template_str = "Must have exactly $value rows."

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": renderer_configuration.params.dict(by_alias=True),
                        "styling": renderer_configuration.styling,
                    },
                }
            )
        ]

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: Dict,
        runtime_configuration: Optional[dict] = None,
        execution_engine: Optional[ExecutionEngine] = None,
    ):
        expected_table_row_count = self.get_success_kwargs().get("value")
        actual_table_row_count = metrics.get("table.row_count")

        return {
            "success": actual_table_row_count == expected_table_row_count,
            "result": {"observed_value": actual_table_row_count},
        }
