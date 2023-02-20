"""
This is a template for creating custom TableExpectations.
For detailed instructions on how to use it, please see:
    https://docs.greatexpectations.io/docs/guides/expectations/creating_custom_expectations/how_to_create_custom_table_expectations
"""


import logging
from typing import Dict, Optional

import pandas as pd

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.execution_engine import (
    ExecutionEngine,
)
from great_expectations.expectations.expectation import TableExpectation

from time_series_expectations.expectations.util import get_prophet_model_from_json

with open("./example_prophet_date_model.json") as f_:
    example_prophet_date_model = f_.read()


class ExpectBatchVolumeToMathProphetDateModel(TableExpectation):
    """This Expectation checks to see if the volume of a Batch matches the predictions of a prophet model for a given date."""

    examples = [
        {
            "data": {"foo": [1, 2, 3, 4]},
            "tests": [
                {
                    "title": "positive_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "date": "2022-01-11",
                        "model": example_prophet_date_model,
                    },
                    "out": {
                        "success": True,
                        "observed_value": 4,
                    },
                }
            ],
            "test_backends": [
                {
                    "backend": "pandas",
                    "dialects": None,
                },
            ],
        },
        {
            "data": {"foo": range(100)},
            "tests": [
                {
                    "title": "negative_test",
                    "exact_match_out": False,
                    "include_in_gallery": True,
                    "in": {
                        "date": "2022-01-01",
                        "model": example_prophet_date_model,
                    },
                    "out": {
                        "success": False,
                        "observed_value": 100,
                    },
                }
            ],
            "test_backends": [
                {
                    "backend": "pandas",
                    "dialects": None,
                },
            ],
        },
    ]

    metric_dependencies = ("table.row_count",)

    # This a tuple of parameter names that can affect whether the Expectation evaluates to True or False.
    success_keys = ()

    # This dictionary contains default values for any parameters that should have default values.
    default_kwarg_values = {}

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

        super().validate_configuration(configuration)
        configuration = configuration or self.configuration

        # # Check other things in configuration.kwargs and raise Exceptions if needed
        # try:
        #     assert (
        #         ...
        #     ), "message"
        #     assert (
        #         ...
        #     ), "message"
        # except AssertionError as e:
        #     raise InvalidExpectationConfigurationError(str(e))

    def _validate(
        self,
        configuration: ExpectationConfiguration,
        metrics: Dict,
        runtime_configuration: dict = None,
        execution_engine: ExecutionEngine = None,
    ):
        batch_volume = metrics["table.row_count"]
        model_json = configuration.kwargs["model"]
        date = configuration.kwargs["date"]

        model = get_prophet_model_from_json(model_json)
        forecast = model.predict(pd.DataFrame({"ds": [date]}))

        forecast_value = forecast.yhat[0]
        forecast_lower_bound = forecast.yhat_lower[0]
        forecast_upper_bound = forecast.yhat_upper[0]

        in_bounds = (forecast_lower_bound < batch_volume) & (
            batch_volume < forecast_upper_bound
        )

        return {
            "success": in_bounds,
            "result": {
                "observed_value": batch_volume,
                "forecast_value": forecast_value,
                "forecast_lower_bound": forecast_lower_bound,
                "forecast_upper_bound": forecast_upper_bound,
            },
        }

    # This object contains metadata for display in the public Gallery
    library_metadata = {
        "tags": [],  # Tags for this Expectation in the Gallery
        "contributors": [  # Github handles for all contributors to this Expectation.
            "@your_name_here",  # Don't forget to add your github handle here!
        ],
    }


if __name__ == "__main__":
    ExpectBatchVolumeToMathProphetDateModel().print_diagnostic_checklist()
