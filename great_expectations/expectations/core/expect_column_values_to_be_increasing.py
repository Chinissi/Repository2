import logging
from typing import Optional

from great_expectations.core import (
    ExpectationConfiguration,
    ExpectationValidationResult,
)
from great_expectations.expectations.expectation import (
    ColumnMapExpectation,
    render_evaluation_parameter_string,
)
from great_expectations.render import LegacyRendererType, RenderedStringTemplateContent
from great_expectations.render.renderer.renderer import renderer
from great_expectations.render.util import (
    num_to_str,
    parse_row_condition_string_pandas_engine,
    substitute_none_for_missing,
)

logger = logging.getLogger(__name__)


class ExpectColumnValuesToBeIncreasing(ColumnMapExpectation):
    """Expect the column values to be increasing.

    By default, this expectation only works for numeric or datetime data. \
    When 'parse_strings_as_datetimes=True', it can also parse strings to datetimes.

    If 'strictly=True', then this expectation is only satisfied if each consecutive value \
    is strictly increasing--equal values are treated as failures.

    expect_column_values_to_be_increasing is a \
    [Column Map Expectation](https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_column_map_expectations).

    Args:
        column (str): \
            The column name.

    Keyword Args:
        strictly (Boolean or None): \
            If True, values must be strictly greater than previous values
        parse_strings_as_datetimes (boolean or None) : \
            If True, all non-null column values to datetimes before making comparisons
        mostly (None or a float between 0 and 1): \
            Successful if at least mostly fraction of values match the expectation. \
            For more detail, see [mostly](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#mostly).

    Other Parameters:
        result_format (str or None): \
            Which output mode to use: BOOLEAN_ONLY, BASIC, COMPLETE, or SUMMARY. \
            For more detail, see [result_format](https://docs.greatexpectations.io/docs/reference/expectations/result_format).
        include_config (boolean): \
            If True, then include the expectation config as part of the result object.
        catch_exceptions (boolean or None): \
            If True, then catch exceptions and include them as part of the result object. \
            For more detail, see [catch_exceptions](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#catch_exceptions).
        meta (dict or None): \
            A JSON-serializable dictionary (nesting allowed) that will be included in the output without
            modification. For more detail, see [meta](https://docs.greatexpectations.io/docs/reference/expectations/standard_arguments/#meta).

    Returns:
        An [ExpectationSuiteValidationResult](https://docs.greatexpectations.io/docs/terms/validation_result)

        Exact fields vary depending on the values passed to result_format, include_config, catch_exceptions, and meta.

    See Also:
        [expect_column_values_to_be_decreasing](https://greatexpectations.io/expectations/expect_column_values_to_be_decreasing)
    """

    # This dictionary contains metadata for display in the public gallery
    library_metadata = {
        "maturity": "production",
        "tags": ["core expectation", "column map expectation"],
        "contributors": ["@great_expectations"],
        "requirements": [],
        "has_full_test_suite": True,
        "manually_reviewed_code": True,
    }

    map_metric = "column_values.increasing"
    success_keys = ("strictly", "mostly", "parse_strings_as_datetimes")
    default_kwarg_values = {
        "row_condition": None,
        "condition_parser": None,
        "strictly": None,
        "mostly": 1,
        "result_format": "BASIC",
        "include_config": True,
        "catch_exceptions": False,
        "parse_strings_as_datetimes": False,
    }
    args_keys = ("column",)

    def validate_configuration(
        self, configuration: Optional[ExpectationConfiguration]
    ) -> None:
        super().validate_configuration(configuration)

    @classmethod
    def _atomic_prescriptive_template(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = (
            False if runtime_configuration.get("include_column_name") is False else True
        )
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "strictly",
                "mostly",
                "parse_strings_as_datetimes",
                "row_condition",
                "condition_parser",
            ],
        )
        params_with_json_schema = {
            "column": {"schema": {"type": "string"}, "value": params.get("column")},
            "strictly": {
                "schema": {"type": "boolean"},
                "value": params.get("strictly"),
            },
            "mostly": {"schema": {"type": "number"}, "value": params.get("mostly")},
            "mostly_pct": {
                "schema": {"type": "string"},
                "value": params.get("mostly_pct"),
            },
            "parse_strings_as_datetimes": {
                "schema": {"type": "boolean"},
                "value": params.get("parse_strings_as_datetimes"),
            },
            "row_condition": {
                "schema": {"type": "string"},
                "value": params.get("row_condition"),
            },
            "condition_parser": {
                "schema": {"type": "string"},
                "value": params.get("condition_parser"),
            },
        }

        if params.get("strictly"):
            template_str = "values must be strictly greater than previous values"
        else:
            template_str = "values must be greater than or equal to previous values"

        if params["mostly"] is not None and params["mostly"] < 1.0:
            params_with_json_schema["mostly_pct"]["value"] = num_to_str(
                params["mostly"] * 100, precision=15, no_scientific=True
            )
            # params["mostly_pct"] = "{:.14f}".format(params["mostly"]*100).rstrip("0").rstrip(".")
            template_str += ", at least $mostly_pct % of the time."
        else:
            template_str += "."

        if params.get("parse_strings_as_datetimes"):
            template_str += " Values should be parsed as datetimes."

        if include_column_name:
            template_str = f"$column {template_str}"

        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(
                params["row_condition"], with_schema=True
            )
            template_str = f"{conditional_template_str}, then {template_str}"
            params_with_json_schema.update(conditional_params)

        return template_str, params_with_json_schema, None, styling

    @classmethod
    @renderer(renderer_type=LegacyRendererType.PRESCRIPTIVE)
    @render_evaluation_parameter_string
    def _prescriptive_renderer(
        cls,
        configuration: Optional[ExpectationConfiguration] = None,
        result: Optional[ExpectationValidationResult] = None,
        runtime_configuration: Optional[dict] = None,
        **kwargs,
    ):
        runtime_configuration = runtime_configuration or {}
        include_column_name = (
            False if runtime_configuration.get("include_column_name") is False else True
        )
        styling = runtime_configuration.get("styling")
        params = substitute_none_for_missing(
            configuration.kwargs,
            [
                "column",
                "strictly",
                "mostly",
                "parse_strings_as_datetimes",
                "row_condition",
                "condition_parser",
            ],
        )

        if params.get("strictly"):
            template_str = "values must be strictly greater than previous values"
        else:
            template_str = "values must be greater than or equal to previous values"

        if params["mostly"] is not None and params["mostly"] < 1.0:
            params["mostly_pct"] = num_to_str(
                params["mostly"] * 100, precision=15, no_scientific=True
            )
            # params["mostly_pct"] = "{:.14f}".format(params["mostly"]*100).rstrip("0").rstrip(".")
            template_str += ", at least $mostly_pct % of the time."
        else:
            template_str += "."

        if params.get("parse_strings_as_datetimes"):
            template_str += " Values should be parsed as datetimes."

        if include_column_name:
            template_str = f"$column {template_str}"

        if params["row_condition"] is not None:
            (
                conditional_template_str,
                conditional_params,
            ) = parse_row_condition_string_pandas_engine(params["row_condition"])
            template_str = f"{conditional_template_str}, then {template_str}"
            params.update(conditional_params)

        return [
            RenderedStringTemplateContent(
                **{
                    "content_block_type": "string_template",
                    "string_template": {
                        "template": template_str,
                        "params": params,
                        "styling": styling,
                    },
                }
            )
        ]
