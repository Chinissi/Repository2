from typing import List

import pytest
from ruamel.yaml import YAML

import great_expectations.exceptions as ge_exceptions
from great_expectations import DataContext
from great_expectations.rule_based_profiler.domain_builder import (
    ColumnDomainBuilder,
    ColumnPairDomainBuilder,
    DomainBuilder,
    MultiColumnDomainBuilder,
    TableDomainBuilder,
)
from great_expectations.rule_based_profiler.types import (
    Domain,
    ParameterContainer,
    build_parameter_container_for_variables,
)

yaml = YAML(typ="safe")


# noinspection PyPep8Naming
def test_table_domain_builder(
    alice_columnar_table_single_batch_context,
    table_Users_domain,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    domain_builder: DomainBuilder = TableDomainBuilder(
        batch_request=None,
        data_context=data_context,
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
    assert domain.domain_type.value == "table"
    assert domain.kwargs is None


def test_column_domain_builder(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)

    variables_configs: dict = full_profiler_config_dict.get("variables")
    if variables_configs is None:
        variables_configs = {}

    variables: ParameterContainer = build_parameter_container_for_variables(
        variables_configs=variables_configs
    )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    domain_builder: DomainBuilder = ColumnDomainBuilder(
        batch_request=batch_request,
        data_context=data_context,
    )
    domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert len(domains) == 7
    assert domains == [
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "id",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "event_type",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "user_id",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "event_ts",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "server_ts",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "device_ts",
            },
            "details": {},
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "user_agent",
            },
            "details": {},
        },
    ]


def test_column_domain_builder_with_simple_semantic_type_included(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)

    variables_configs: dict = full_profiler_config_dict.get("variables")
    if variables_configs is None:
        variables_configs = {}

    variables: ParameterContainer = build_parameter_container_for_variables(
        variables_configs=variables_configs
    )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    domain_builder: DomainBuilder = ColumnDomainBuilder(
        include_semantic_types=[
            "numeric",
        ],
        batch_request=batch_request,
        data_context=data_context,
    )
    domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert len(domains) == 2
    # Assert Domain object equivalence.
    assert domains == [
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "event_type",
            },
            "details": {
                "inferred_semantic_domain_type": "numeric",
            },
        },
        {
            "domain_type": "column",
            "domain_kwargs": {
                "column": "user_id",
            },
            "details": {
                "inferred_semantic_domain_type": "numeric",
            },
        },
    ]


def test_column_pair_domain_builder_wrong_column_names(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)

    variables_configs: dict = full_profiler_config_dict.get("variables")
    if variables_configs is None:
        variables_configs = {}

    variables: ParameterContainer = build_parameter_container_for_variables(
        variables_configs=variables_configs
    )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    domain_builder: DomainBuilder = ColumnPairDomainBuilder(
        include_column_names=[
            "user_id",
            "event_type",
            "user_agent",
        ],
        batch_request=batch_request,
        data_context=data_context,
    )

    with pytest.raises(ge_exceptions.ProfilerExecutionError) as excinfo:
        # noinspection PyArgumentList
        domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert (
        'Error: Columns specified for ColumnPairDomainBuilder in sorted order must correspond to "column_A" and "column_B" (in this exact order).'
        in str(excinfo.value)
    )


def test_column_pair_domain_builder_correct_sorted_column_names(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)

    variables_configs: dict = full_profiler_config_dict.get("variables")
    if variables_configs is None:
        variables_configs = {}

    variables: ParameterContainer = build_parameter_container_for_variables(
        variables_configs=variables_configs
    )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    domain_builder: DomainBuilder = ColumnPairDomainBuilder(
        include_column_names=[
            "user_id",
            "event_type",
        ],
        batch_request=batch_request,
        data_context=data_context,
    )
    domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert len(domains) == 1
    # Assert Domain object equivalence.
    assert domains == [
        {
            "domain_type": "column_pair",
            "domain_kwargs": {
                "column_A": "event_type",
                "column_B": "user_id",
            },
            "details": {},
        }
    ]

    domain: Domain = domains[0]

    # Also test that the dot notation is supported properly throughout the dictionary fields of the Domain object.
    assert domain.domain_type.value == "column_pair"
    assert domain.domain_kwargs.column_A == "event_type"
    assert domain.domain_kwargs.column_B == "user_id"


def test_multi_column_domain_builder_wrong_column_list(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)

    variables_configs: dict = full_profiler_config_dict.get("variables")
    if variables_configs is None:
        variables_configs = {}

    variables: ParameterContainer = build_parameter_container_for_variables(
        variables_configs=variables_configs
    )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    domain_builder: DomainBuilder = MultiColumnDomainBuilder(
        include_column_names=None,
        batch_request=batch_request,
        data_context=data_context,
    )

    with pytest.raises(ge_exceptions.ProfilerExecutionError) as excinfo:
        # noinspection PyArgumentList
        domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert 'Error: "column_list" in MultiColumnDomainBuilder must not be empty.' in str(
        excinfo.value
    )

    with pytest.raises(ge_exceptions.ProfilerExecutionError) as excinfo:
        # noinspection PyArgumentList
        domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert 'Error: "column_list" in MultiColumnDomainBuilder must not be empty.' in str(
        excinfo.value
    )


def test_multi_column_domain_builder_correct_column_list(
    alice_columnar_table_single_batch_context,
    alice_columnar_table_single_batch,
):
    data_context: DataContext = alice_columnar_table_single_batch_context

    profiler_config: str = alice_columnar_table_single_batch["profiler_config"]

    full_profiler_config_dict: dict = yaml.load(profiler_config)

    variables_configs: dict = full_profiler_config_dict.get("variables")
    if variables_configs is None:
        variables_configs = {}

    variables: ParameterContainer = build_parameter_container_for_variables(
        variables_configs=variables_configs
    )

    batch_request: dict = {
        "datasource_name": "alice_columnar_table_single_batch_datasource",
        "data_connector_name": "alice_columnar_table_single_batch_data_connector",
        "data_asset_name": "alice_columnar_table_single_batch_data_asset",
    }

    domain_builder: DomainBuilder = MultiColumnDomainBuilder(
        include_column_names=[
            "event_type",
            "user_id",
            "user_agent",
        ],
        batch_request=batch_request,
        data_context=data_context,
    )
    domains: List[Domain] = domain_builder.get_domains(variables=variables)

    assert len(domains) == 1
    # Assert Domain object equivalence.
    assert domains == [
        {
            "domain_type": "multicolumn",
            "domain_kwargs": {
                "column_list": [
                    "event_type",
                    "user_id",
                    "user_agent",
                ],
            },
            "details": {},
        }
    ]

    domain: Domain = domains[0]

    # Also test that the dot notation is supported properly throughout the dictionary fields of the Domain object.
    assert domain.domain_type.value == "multicolumn"
    assert domain.domain_kwargs.column_list == [
        "event_type",
        "user_id",
        "user_agent",
    ]
