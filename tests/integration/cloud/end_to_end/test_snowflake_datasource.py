from __future__ import annotations

import os
import uuid
from typing import TYPE_CHECKING

import pytest

from great_expectations.core import ExpectationConfiguration

if TYPE_CHECKING:
    from great_expectations.checkpoint import Checkpoint
    from great_expectations.core import ExpectationSuite
    from great_expectations.data_context import CloudDataContext
    from great_expectations.datasource.fluent import (
        BatchRequest,
        DataAsset,
        Datasource,
        SnowflakeDatasource,
    )
    from great_expectations.datasource.fluent.sql_datasource import TableAsset
    from tests.integration.cloud.end_to_end.conftest import TableFactory


@pytest.fixture(scope="module")
def connection_string() -> str:
    if os.getenv("SNOWFLAKE_CI_USER_PASSWORD") and os.getenv("SNOWFLAKE_CI_ACCOUNT"):
        return "snowflake://ci:${SNOWFLAKE_CI_USER_PASSWORD}@${SNOWFLAKE_CI_ACCOUNT}/ci/public?warehouse=ci&role=ci"
    elif os.getenv("SNOWFLAKE_USER") and os.getenv("SNOWFLAKE_CI_ACCOUNT"):
        return "snowflake://${SNOWFLAKE_USER}@${SNOWFLAKE_CI_ACCOUNT}/DEMO_DB?warehouse=COMPUTE_WH&role=PUBLIC&authenticator=externalbrowser"
    else:
        pytest.skip("no snowflake credentials")


@pytest.fixture(scope="module")
def snowflake_datasource(
    context: CloudDataContext,
    datasource: Datasource,
    connection_string: str,
) -> SnowflakeDatasource:
    datasource = context.sources.add_snowflake(
        name=datasource.name,
        connection_string=connection_string,
        create_temp_table=False,
    )
    datasource.create_temp_table = True
    datasource = context.sources.add_or_update_snowflake(datasource=datasource)
    assert (
        datasource.create_temp_table is True
    ), "The datasource was not updated in the previous method call."
    datasource.create_temp_table = False
    datasource = context.add_or_update_datasource(datasource=datasource)  # type: ignore[assignment]
    assert (
        datasource.create_temp_table is False
    ), "The datasource was not updated in the previous method call."
    datasource.create_temp_table = True
    datasource_dict = datasource.dict()
    # this is a bug - LATIKU-448
    # call to datasource.dict() results in a ConfigStr that fails pydantic
    # validation on SnowflakeDatasource
    datasource_dict["connection_string"] = str(datasource_dict["connection_string"])
    datasource = context.sources.add_or_update_snowflake(**datasource_dict)
    assert (
        datasource.create_temp_table is True
    ), "The datasource was not updated in the previous method call."
    datasource.create_temp_table = False
    datasource_dict = datasource.dict()
    # this is a bug - LATIKU-448
    # call to datasource.dict() results in a ConfigStr that fails pydantic
    # validation on SnowflakeDatasource
    datasource_dict["connection_string"] = str(datasource_dict["connection_string"])
    datasource = context.add_or_update_datasource(**datasource_dict)
    assert (
        datasource.create_temp_table is False
    ), "The datasource was not updated in the previous method call."
    return datasource


@pytest.fixture(scope="module")
def data_asset(
    snowflake_datasource: SnowflakeDatasource,
    data_asset: DataAsset,
    table_factory: TableFactory,
) -> TableAsset:
    schema_name = f"i{uuid.uuid4().hex}"
    table_name = f"i{uuid.uuid4().hex}"
    table_factory(
        gx_engine=snowflake_datasource.get_execution_engine(),
        table_names={table_name},
        schema_name=schema_name,
    )
    _ = snowflake_datasource.add_table_asset(
        name=data_asset.name, table_name=table_name, schema_name=schema_name
    )
    return snowflake_datasource.get_asset(asset_name=data_asset.name)


@pytest.fixture(scope="module")
def batch_request(data_asset: TableAsset) -> BatchRequest:
    return data_asset.build_batch_request()


@pytest.fixture(scope="module")
def expectation_suite(
    context: CloudDataContext,
    expectation_suite: ExpectationSuite,
) -> ExpectationSuite:
    """Test adding Expectations and updating the Expectation Suite for the Data Asset
    defined in this module. The package-level expectation_suite fixture handles add and delete.
    """
    expectation_suite.add_expectation(
        expectation_configuration=ExpectationConfiguration(
            expectation_type="expect_column_values_to_not_be_null",
            kwargs={
                "column": "name",
                "mostly": 1,
            },
        )
    )
    _ = context.add_or_update_expectation_suite(expectation_suite=expectation_suite)
    expectation_suite = context.get_expectation_suite(
        expectation_suite_name=expectation_suite.name
    )
    assert (
        len(expectation_suite.expectations) == 1
    ), "Expectation Suite was not updated in the previous method call."
    return expectation_suite


@pytest.mark.cloud
def test_interactive_validator(
    context: CloudDataContext,
    batch_request: BatchRequest,
    expectation_suite: ExpectationSuite,
):
    expectation_count = len(expectation_suite.expectations)
    expectation_suite_name = expectation_suite.expectation_suite_name
    validator = context.get_validator(
        batch_request=batch_request,
        expectation_suite_name=expectation_suite_name,
    )
    validator.head()
    validator.expect_column_values_to_not_be_null(
        column="id",
        mostly=1,
    )
    validator.save_expectation_suite()
    expectation_suite = context.get_expectation_suite(
        expectation_suite_name=expectation_suite_name
    )
    assert len(expectation_suite.expectations) == expectation_count + 1


@pytest.mark.cloud
def test_checkpoint_run(checkpoint: Checkpoint):
    checkpoint_result = checkpoint.run()
    assert checkpoint_result.success is True
