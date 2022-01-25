import uuid
from typing import Any, Dict, List, Optional

import great_expectations.exceptions as ge_exceptions
from great_expectations import DataContext
from great_expectations.core.expectation_configuration import ExpectationConfiguration
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.data_context.util import instantiate_class_from_config
from great_expectations.rule_based_profiler.config.base import (
    DomainBuilderConfig,
    ExpectationConfigurationBuilderConfig,
    ParameterBuilderConfig,
    RuleConfig,
)
from great_expectations.rule_based_profiler.domain_builder.domain_builder import (
    DomainBuilder,
)
from great_expectations.rule_based_profiler.expectation_configuration_builder.expectation_configuration_builder import (
    ExpectationConfigurationBuilder,
)
from great_expectations.rule_based_profiler.parameter_builder.parameter_builder import (
    ParameterBuilder,
)
from great_expectations.rule_based_profiler.parameter_builder.parameter_container import (
    build_parameter_container_for_variables,
)
from great_expectations.rule_based_profiler.rule.rule import Rule


class RuleBasedProfiler:
    """
    RuleBasedProfiler object serves to profile, or automatically evaluate a set of rules, upon a given
    batch / multiple batches of data.

    --ge-feature-maturity-info--

        id: rule_based_profiler_overall
        title: Rule-Based Profiler
        icon:
        short_description: Configuration Driven Profiler
        description: Use YAML to configure a flexible Profiler engine, which will then generate an ExpectationSuite for a data set
        how_to_guide_url:
        maturity: Experimental
        maturity_details:
            api_stability: Low (instantiation of Profiler and the signature of the profile() method will change)
            implementation_completeness: Moderate (some augmentation and/or growth in capabilities is to be expected)
            unit_test_coverage: High (but not complete -- additional unit tests will be added, commensurate with the upcoming new functionality)
            integration_infrastructure_test_coverage: N/A -> TBD
            documentation_completeness: Moderate
            bug_risk: Low/Moderate
            expectation_completeness: Moderate

        id: domain_builders
        title: Domain Builders
        icon:
        short_description: Configurable Domain builders for generating lists of ExpectationConfiguration objects
        description: Use YAML to build domains for ExpectationConfiguration generator (table, column, semantic types, etc.)
        how_to_guide_url:
        maturity: Experimental
        maturity_details:
            api_stability: Moderate
            implementation_completeness: Moderate (additional DomainBuilder classes will be developed)
            unit_test_coverage: High (but not complete -- additional unit tests will be added, commensurate with the upcoming new functionality)
            integration_infrastructure_test_coverage: N/A -> TBD
            documentation_completeness: Moderate
            bug_risk: Low/Moderate
            expectation_completeness: Moderate

        id: parameter_builders
        title: Parameter Builders
        icon:
        short_description: Configurable Parameter builders for generating parameters to be used by ExpectationConfigurationBuilder classes for generating lists of ExpectationConfiguration objects (e.g., as kwargs and meta arguments), corresponding to the Domain built by a DomainBuilder class
        description: Use YAML to configure single and multi batch based parameter computation modules for the use by ExpectationConfigurationBuilder classes
        how_to_guide_url:
        maturity: Experimental
        maturity_details:
            api_stability: Moderate
            implementation_completeness: Moderate (additional ParameterBuilder classes will be developed)
            unit_test_coverage: High (but not complete -- additional unit tests will be added, commensurate with the upcoming new functionality)
            integration_infrastructure_test_coverage: N/A -> TBD
            documentation_completeness: Moderate
            bug_risk: Low/Moderate
            expectation_completeness: Moderate

        id: expectation_configuration_builders
        title: ExpectationConfiguration Builders
        icon:
        short_description: Configurable ExpectationConfigurationBuilder classes for generating lists of ExpectationConfiguration objects (e.g., as kwargs and meta arguments), corresponding to the Domain built by a DomainBuilder class and using parameters, computed by ParameterBuilder classes
        description: Use YAML to configure ExpectationConfigurationBuilder classes, which emit lists of ExpectationConfiguration objects (e.g., as kwargs and meta arguments)
        how_to_guide_url:
        maturity: Experimental
        maturity_details:
            api_stability: Moderate
            implementation_completeness: Moderate (additional ExpectationConfigurationBuilder classes might be developed)
            unit_test_coverage: High (but not complete -- additional unit tests will be added, commensurate with the upcoming new functionality)
            integration_infrastructure_test_coverage: N/A -> TBD
            documentation_completeness: Moderate
            bug_risk: Low/Moderate
            expectation_completeness: Moderate

    --ge-feature-maturity-info--
    """

    def __init__(
        self,
        *,
        name: str,
        config_version: float,
        rules: Dict[str, RuleConfig],
        variables: Optional[Dict[str, Any]] = None,
        data_context: Optional[DataContext] = None,
    ):
        """
        Create a new Profiler using configured rules.
        For a rule or an item in a rule configuration, instantiates the following if
        available: a domain builder, a parameter builder, and a configuration builder.
        These will be used to define profiler computation patterns.

        Args:
            profiler_config: Variables and Rules configuration as a dictionary
            data_context: DataContext object that defines a full runtime environment (data access, etc.)
        """
        self._name = name
        self._config_version = config_version
        self._data_context = data_context
        self._variables = variables or {}
        self._rules = []

        for rule_name, rule_config in rules.items():
            # Config is validated through schema but do a sanity check
            for attr in (
                "domain_builder",
                "parameter_builders",
                "expectation_configuration_builders",
            ):
                if attr not in rule_config:
                    raise ge_exceptions.ProfilerConfigurationError(
                        message=f'Invalid rule "{rule_name}": missing mandatory {attr}.'
                    )

            # Instantiate DomainBuilder
            domain_builder_config: DomainBuilderConfig = rule_config["domain_builder"]

            domain_builder: DomainBuilder = instantiate_class_from_config(
                config=domain_builder_config,
                runtime_environment={"data_context": data_context},
                config_defaults={
                    "module_name": "great_expectations.rule_based_profiler.domain_builder"
                },
            )

            # Instantiate ParameterBuilders
            parameter_builder_configs: List[ParameterBuilderConfig] = rule_config[
                "parameter_builders"
            ]

            parameter_builders: List[ParameterBuilder] = []
            for parameter_builder_config in parameter_builder_configs:
                parameter_builders.append(
                    instantiate_class_from_config(
                        config=parameter_builder_config,
                        runtime_environment={"data_context": data_context},
                        config_defaults={
                            "module_name": "great_expectations.rule_based_profiler.parameter_builder"
                        },
                    )
                )

            # Instantiate ExpectationConfigurationBuilders
            expectation_configuration_builder_configs: List[
                ExpectationConfigurationBuilderConfig
            ] = rule_config["expectation_configuration_builders"]

            expectation_configuration_builders: List[
                ExpectationConfigurationBuilder
            ] = []
            for (
                expectation_configuration_builder_config
            ) in expectation_configuration_builder_configs:
                expectation_configuration_builders.append(
                    instantiate_class_from_config(
                        config=expectation_configuration_builder_config,
                        runtime_environment={},
                        config_defaults={
                            "class_name": "DefaultExpectationConfigurationBuilder",
                            "module_name": "great_expectations.rule_based_profiler.expectation_configuration_builder",
                        },
                    )
                )

            # Convert variables to ParameterContainer
            _variables = build_parameter_container_for_variables(
                variables_configs=variables
            )

            # Compile previous steps and package into a Rule object
            self._rules.append(
                Rule(
                    name=rule_name,
                    domain_builder=domain_builder,
                    parameter_builders=parameter_builders,
                    expectation_configuration_builders=expectation_configuration_builders,
                    variables=_variables,
                )
            )

    def profile(
        self,
        *,
        expectation_suite_name: Optional[str] = None,
        include_citation: bool = True,
    ) -> ExpectationSuite:
        """
        Args:
            :param expectation_suite_name: A name for returned Expectation suite.
            :param include_citation: Whether or not to include the Profiler config in the metadata for the ExpectationSuite produced by the Profiler
        :return: Set of rule evaluation results in the form of an ExpectationSuite
        """
        if expectation_suite_name is None:
            expectation_suite_name = (
                f"tmp.profiler_{self.__class__.__name__}_suite_{str(uuid.uuid4())[:8]}"
            )

        expectation_suite: ExpectationSuite = ExpectationSuite(
            expectation_suite_name=expectation_suite_name,
            data_context=self._data_context,
        )

        if include_citation:
            expectation_suite.add_citation(
                comment="Suite created by Rule-Based Profiler with the configuration included.",
                profiler_config=self._profiler_config,
            )

        rule: Rule
        for rule in self._rules:
            expectation_configurations: List[ExpectationConfiguration] = rule.generate()
            expectation_configuration: ExpectationConfiguration
            for expectation_configuration in expectation_configurations:
                expectation_suite._add_expectation(
                    expectation_configuration=expectation_configuration,
                    send_usage_event=False,
                )

        return expectation_suite
