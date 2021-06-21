from typing import List, Optional

from ruamel.yaml import YAML

from great_expectations import DataContext
from great_expectations.rule_based_profiler.domain_builder import (
    ColumnDomainBuilder,
    DomainBuilder,
    SimpleSemanticTypeColumnDomainBuilder,
    TableDomainBuilder,
)
from great_expectations.rule_based_profiler.domain_builder.domain import Domain
from great_expectations.rule_based_profiler.parameter_builder.parameter_container import (
    ParameterContainer,
    build_parameter_container_for_variables,
)

yaml = YAML()


# noinspection PyPep8Naming
def test_table_domain_builder(
    alice_columnar_table_single_batch_context,
    table_Users_domain,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    domain_builder: DomainBuilder = TableDomainBuilder(
        data_context=data_context,
        batch_request=None,
    )
    domains: List[Domain] = domain_builder.get_domains()

    assert len(domains) == 1
    assert domains == [
        {
            "domain_type": "table",
        }
    ]

    domain: Domain = domains[0]
    # Assert Domain object equivalence.
    assert domain == table_Users_domain
    # Also test that the dot notation is supported properly throughout the dictionary fields of the Domain object.
    assert domain.domain_kwargs.batch_id is None


# noinspection PyPep8Naming
def test_column_domain_builder(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
    column_Age_domain,
    column_Date_domain,
    column_Description_domain,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)
    variables_configs: dict = full_profiler_config_dict.get("variables")
    variables: Optional[ParameterContainer] = None
    if variables_configs:
        variables = build_parameter_container_for_variables(
            variables_configs=variables_configs
        )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    domain_builder: DomainBuilder = ColumnDomainBuilder(
        data_context=data_context,
        batch_request=batch_request,
    )
    domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert len(domains) == 7
    assert domains == [
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "id",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "event_type",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "user_id",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "event_ts",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "server_ts",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "device_ts",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "user_agent",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {},
        },
    ]


# noinspection PyPep8Naming
def test_simple_semantic_type_column_domain_builder(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
    column_Age_domain,
    column_Description_domain,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)
    variables_configs: dict = full_profiler_config_dict.get("variables")
    variables: Optional[ParameterContainer] = None
    if variables_configs:
        variables = build_parameter_container_for_variables(
            variables_configs=variables_configs
        )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }
    domain_builder: DomainBuilder = SimpleSemanticTypeColumnDomainBuilder(
        data_context=data_context,
        batch_request=batch_request,
        semantic_types=[
            "numeric",
        ],
    )
    domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert len(domains) == 2
    assert domains == [
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "event_type",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {"inferred_semantic_domain_type": "numeric"},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "user_id",
                "batch_id": "cf28d8229c247275c8cc0f41b4ceb62d",
            },
            "details": {"inferred_semantic_domain_type": "numeric"},
        },
    ]
