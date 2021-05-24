from typing import Any, Dict, Optional

from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.rule_based_profiler.domain_builder.domain import Domain
from great_expectations.rule_based_profiler.expectation_configuration_builder.expectation_configuration_builder import (
    ExpectationConfigurationBuilder,
)
from great_expectations.rule_based_profiler.parameter_builder.parameter_container import (
    ParameterContainer,
    get_parameter_value,
)


class DefaultExpectationConfigurationBuilder(ExpectationConfigurationBuilder):
    """
    Class which creates ExpectationConfiguration out of a given Expectation type and
    parameter_name-to-parameter_fully_qualified_parameter_name map (name-value pairs supplied in the kwargs dictionary).
    """

    def __init__(
        self,
        expectation_type: str,
        meta: Optional[Dict[str, Any]] = None,
        success_on_last_run: Optional[bool] = None,
        **kwargs,
    ):
        self._expectation_type = expectation_type
        self._expectation_kwargs = kwargs
        if meta is None:
            meta = {}
        self._meta = meta
        self._success_on_last_run = success_on_last_run

    def _build_expectation_configuration(
        self,
        domain: Domain,
        variables: Optional[ParameterContainer] = None,
        parameters: Optional[Dict[str, ParameterContainer]] = None,
    ) -> ExpectationConfiguration:
        parameter_name: str
        fully_qualified_parameter_name: str
        expectation_kwargs: Dict[str, Any] = {
            parameter_name: get_parameter_value(
                fully_qualified_parameter_name=fully_qualified_parameter_name,
                domain=domain,
                variables=variables,
                parameters=parameters,
            )
            for parameter_name, fully_qualified_parameter_name in self._expectation_kwargs.items()
        }
        return ExpectationConfiguration(
            expectation_type=self._expectation_type,
            kwargs=expectation_kwargs,
            meta=self._meta,
            success_on_last_run=self._success_on_last_run,
        )
