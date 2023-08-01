from typing import Generator
import pytest

from pytest import param as p
from great_expectations.datasource.fluent import SQLDatasource
from great_expectations import get_context
from great_expectations.expectations.expectation import (
    ExpectationConfiguration,
)
from great_expectations.data_context import EphemeralDataContext


@pytest.fixture
def context() -> EphemeralDataContext:
    ctx = get_context(cloud_mode=False)
    assert isinstance(ctx, EphemeralDataContext)
    return ctx


@pytest.fixture(
    scope="function",
    params=[
        p(
            {
                "name": "my_postgres",
                "type": "postgres",
                "connection_string": "postgresql+psycopg2://postgres:postgres@localhost:5432/mercury",
            },
            id="postgres",
        )
    ],
)
def datasources(context, request) -> Generator[SQLDatasource, None, None]:
    ds_type = request.param["type"]
    factory_method = getattr(context.sources, f"add_{ds_type}")
    ds = factory_method(**request.param)
    yield ds


@pytest.mark.parametrize(
    ["asset_config"],
    [
        p(
            {"name": "unquoted_lower", "table_name": "checkpoints"},
            id="unquoted_lower",
        ),
        p(
            {"name": "quoted_lower", "table_name": "'checkpoints'"},
            id="quoted_lower",
        ),
        p(
            {"name": "unqouted_upper", "table_name": "CHECKPOINTS"},
            id="unqouted_upper",
        ),
        p(
            {"name": "qouted_upper", "table_name": "'CHECKPOINTS'"},
            id="qouted_upper",
        ),
    ],
)
class TestIndentifiers:
    def test_add_table_asset(self, datasources: SQLDatasource, asset_config: dict):
        print(datasources)
        print(asset_config)

        asset = datasources.add_table_asset(**asset_config)
        print(asset)

    def test_run_checkpoint(
        self,
        context: EphemeralDataContext,
        datasources: SQLDatasource,
        asset_config: dict,
    ):
        asset = datasources.add_table_asset(**asset_config)
        suite = context.add_expectation_suite(
            expectation_suite_name=f"{datasources.name}-{asset.name}"
        )
        suite.add_expectation(
            expectation_configuration=ExpectationConfiguration(
                expectation_type="expect_column_values_to_not_be_null",
                kwargs={
                    "column": "val",
                    "mostly": 1,
                },
            )
        )

        checkpoint_name = f"{datasources.name}-{asset_config['name']}"
        print(f"WTF: {asset.name}")

        checkpoint_config = {
            "name": checkpoint_name,
            "validations": [
                {
                    "expectation_suite_name": suite.expectation_suite_name,
                    "expectation_suite_ge_cloud_id": suite.ge_cloud_id,
                    "batch_request": {
                        "datasource_name": datasources.name,
                        "data_asset_name": asset.name,
                    },
                }
            ],
        }
        checkpoint = context.add_checkpoint(**checkpoint_config)
        result = checkpoint.run()
        assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-vv", "-rxpEf"])
