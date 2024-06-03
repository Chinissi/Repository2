from __future__ import annotations

from pprint import pformat as pf
from sys import version_info as python_version
from typing import TYPE_CHECKING, Final, Sequence

import pytest
import sqlalchemy as sa
from pytest import param

from great_expectations.compatibility import pydantic
from great_expectations.compatibility.snowflake import snowflake
from great_expectations.data_context import AbstractDataContext
from great_expectations.datasource.fluent import GxContextWarning
from great_expectations.datasource.fluent.config_str import ConfigStr
from great_expectations.datasource.fluent.snowflake_datasource import (
    SnowflakeDatasource,
    SnowflakeDsn,
)
from great_expectations.execution_engine import SqlAlchemyExecutionEngine

if TYPE_CHECKING:
    from pytest.mark.structures import ParameterSet

VALID_DS_CONFIG_PARAMS: Final[Sequence[ParameterSet]] = [
    param(
        {
            "connection_string": "snowflake://my_user:password@my_account/d_public/s_public?numpy=True"
        },
        id="connection_string str",
    ),
    param(
        {"connection_string": "${MY_CONN_STR_PARTIAL}@${MY_PATH}?${MY_QUERY_PARAMS}"},
        id="connection_string ConfigStr with required query params",
    ),
    param(
        {"connection_string": "${MY_CONN_STR_FULL}"},
        id="connection_string ConfigStr - required params part of sub",
    ),
    param(
        {"connection_string": "${MY_CONN_STR_MIN}?${MY_QUERY_PARAMS}"},
        id="connection_string ConfigStr - dedicated query params sub",
    ),
    param(
        {
            "connection_string": {
                "user": "my_user",
                "password": "password",
                "account": "my_account",
                "schema": "s_public",
                "database": "d_public",
            }
        },
        id="connection_string dict",
    ),
    param(
        {
            "connection_string": {
                "user": "my_user",
                "password": "${MY_PASSWORD}",
                "account": "my_account",
                "schema": "s_public",
                "database": "d_public",
            }
        },
        id="connection_string dict with password ConfigStr",
    ),
]


@pytest.fixture
def seed_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MY_CONN_STR_PARTIAL", "snowflake://my_user:password")
    monkeypatch.setenv(
        "MY_CONN_STR_MIN", "snowflake://my_user:password@my_account/my_db/my_schema"
    )
    monkeypatch.setenv(
        "MY_CONN_STR_FULL",
        "snowflake://my_user:password@my_account/my_db/my_schema?warehouse=my_wh&role=my_role",
    )
    monkeypatch.setenv("MY_PATH", "my_account/my_db/my_schema")
    monkeypatch.setenv("MY_QUERY_PARAMS", "warehouse=my_wh&role=my_role")
    monkeypatch.setenv("MY_PASSWORD", "my_password")


@pytest.mark.unit
def test_snowflake_dsn():
    dsn = pydantic.parse_obj_as(
        SnowflakeDsn,
        "snowflake://my_user:password@my_account/my_db/my_schema?role=my_role&warehouse=my_wh",
    )
    assert dsn.user == "my_user"
    assert dsn.password == "password"
    assert dsn.account_identifier == "my_account"
    assert dsn.database == "my_db"
    assert dsn.schema == "my_schema"
    assert dsn.role == "my_role"
    assert dsn.warehouse == "my_wh"


@pytest.mark.snowflake  # TODO: make this a unit test
@pytest.mark.parametrize(
    "config_kwargs",
    [
        *VALID_DS_CONFIG_PARAMS,
        param(
            {
                "user": "my_user",
                "password": "password",
                "account": "my_account",
                "schema": "s_public",
                "database": "d_public",
            },
            id="old config format - top level keys",
        ),
        param(
            {"connection_string": "${MY_CONN_STR_MIN}"},
            id="connection_string ConfigStr missing query params",
        ),
    ],
)
def test_valid_config(
    empty_file_context: AbstractDataContext, seed_env_vars: None, config_kwargs: dict
):
    my_sf_ds_1 = SnowflakeDatasource(name="my_sf_ds_1", **config_kwargs)
    assert my_sf_ds_1

    my_sf_ds_1._data_context = (
        empty_file_context  # attach to enable config substitution
    )
    sql_engine = my_sf_ds_1.get_engine()
    assert isinstance(sql_engine, sa.engine.Engine)

    exec_engine = my_sf_ds_1.get_execution_engine()
    assert isinstance(exec_engine, SqlAlchemyExecutionEngine)


@pytest.mark.unit
@pytest.mark.parametrize(
    ["connection_string", "expected_errors"],
    [
        pytest.param(
            "snowflake://my_user:password@my_account",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format "
                    "'${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "URL path missing database/schema",
                    "type": "value_error.url.path",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, "
                    "user, and password.",
                    "type": "value_error",
                },
            ],
            id="missing path",
        ),
        pytest.param(
            "snowflake://my_user:password@my_account//",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format "
                    "'${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "ctx": {"msg": "missing database"},
                    "loc": ("connection_string",),
                    "msg": "URL path missing database/schema",
                    "type": "value_error.url.path",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, "
                    "user, and password.",
                    "type": "value_error",
                },
            ],
            id="missing database + schema",
        ),
        pytest.param(
            "snowflake://my_user:password@my_account/my_db",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format "
                    "'${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "URL path missing database/schema",
                    "type": "value_error.url.path",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, "
                    "user, and password.",
                    "type": "value_error",
                },
            ],
            id="missing schema",
        ),
        pytest.param(
            "snowflake://my_user:password@my_account/my_db/",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format "
                    "'${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "ctx": {"msg": "missing schema"},
                    "loc": ("connection_string",),
                    "msg": "URL path missing database/schema",
                    "type": "value_error.url.path",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, "
                    "user, and password.",
                    "type": "value_error",
                },
            ],
            id="missing schema 2",
        ),
        pytest.param(
            "snowflake://my_user:password@my_account//my_schema",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format "
                    "'${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "ctx": {"msg": "missing database"},
                    "loc": ("connection_string",),
                    "msg": "URL path missing database/schema",
                    "type": "value_error.url.path",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, "
                    "user, and password.",
                    "type": "value_error",
                },
            ],
            id="missing database",
        ),
    ],
)
def test_missing_required_params(
    connection_string: str,
    expected_errors: list[dict],  # TODO: use pydantic error dict
):
    with pytest.raises(pydantic.ValidationError) as exc_info:
        ds = SnowflakeDatasource(
            name="my_sf_ds",
            connection_string=connection_string,
        )
        print(f"{ds!r}")

    print(f"\n\tErrors:\n{pf(exc_info.value.errors())}")
    assert exc_info.value.errors() == expected_errors


@pytest.mark.unit
@pytest.mark.parametrize(
    "connection_string, connect_args, expected_errors",
    [
        pytest.param(
            "snowflake://my_user:password@my_account/foo/bar?numpy=True",
            {
                "account": "my_account",
                "user": "my_user",
                "password": "123456",
                "schema": "foo",
                "database": "bar",
            },
            [
                {
                    "loc": ("__root__",),
                    "msg": "Cannot provide both a connection string and a combination of account, user, and password.",
                    "type": "value_error",
                }
            ],
            id="both connection_string and connect_args",
        ),
        pytest.param(
            None,
            {},
            [
                {
                    "loc": ("connection_string",),
                    "msg": "none is not an allowed value",
                    "type": "type_error.none.not_allowed",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, user, and password.",
                    "type": "value_error",
                },
            ],
            id="neither connection_string nor connect_args",
        ),
        pytest.param(
            None,
            {
                "account": "my_account",
                "user": "my_user",
                "schema": "foo",
                "database": "bar",
            },
            [
                {
                    "loc": ("connection_string", "password"),
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ("connection_string",),
                    "msg": f"""expected string or bytes-like object{"" if python_version < (3, 11) else ", got 'dict'"}""",
                    "type": "type_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "str type expected",
                    "type": "type_error.str",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, user, and password.",
                    "type": "value_error",
                },
            ],
            id="incomplete connect_args",
        ),
        pytest.param(
            {
                "account": "my_account",
                "user": "my_user",
                "schema": "foo",
                "database": "bar",
            },
            {},
            [
                {
                    "loc": ("connection_string", "password"),
                    "msg": "field required",
                    "type": "value_error.missing",
                },
                {
                    "loc": ("connection_string",),
                    "msg": f"""expected string or bytes-like object{"" if python_version < (3, 11) else ", got 'dict'"}""",
                    "type": "type_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "str type expected",
                    "type": "type_error.str",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, "
                    "user, and password.",
                    "type": "value_error",
                },
            ],
            id="incomplete connection_string dict connect_args",
        ),
    ],
)
def test_conflicting_connection_string_and_args_raises_error(
    connection_string: ConfigStr | SnowflakeDsn | None | dict,
    connect_args: dict,
    expected_errors: list[dict],
):
    with pytest.raises(pydantic.ValidationError) as exc_info:
        _ = SnowflakeDatasource(
            name="my_sf_ds", connection_string=connection_string, **connect_args
        )
    assert exc_info.value.errors() == expected_errors


@pytest.mark.unit
@pytest.mark.parametrize(
    "connection_string, expected_errors",
    [
        pytest.param(
            "user_login_name:password@account_identifier",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "invalid or missing URL scheme",
                    "type": "value_error.url.scheme",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, user, and password.",
                    "type": "value_error",
                },
            ],
            id="missing scheme",
        ),
        pytest.param(
            "snowflake://user_login_name@account_identifier",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "URL password invalid",
                    "type": "value_error.url.password",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, user, and password.",
                    "type": "value_error",
                },
            ],
            id="bad password",
        ),
        pytest.param(
            "snowflake://user_login_name:password@",
            [
                {
                    "loc": ("connection_string",),
                    "msg": "value is not a valid dict",
                    "type": "type_error.dict",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "ConfigStr - contains no config template strings in the format '${MY_CONFIG_VAR}' or '$MY_CONFIG_VAR'",
                    "type": "value_error",
                },
                {
                    "loc": ("connection_string",),
                    "msg": "URL domain invalid",
                    "type": "value_error.url.domain",
                },
                {
                    "loc": ("__root__",),
                    "msg": "Must provide either a connection string or a combination of account, user, and password.",
                    "type": "value_error",
                },
            ],
            id="bad domain",
        ),
    ],
)
def test_invalid_connection_string_raises_dsn_error(
    connection_string: str, expected_errors: list[dict]
):
    with pytest.raises(pydantic.ValidationError) as exc_info:
        _ = SnowflakeDatasource(
            name="my_snowflake", connection_string=connection_string
        )

    assert expected_errors == exc_info.value.errors()


# TODO: Cleanup how we install test dependencies and remove this skipif
@pytest.mark.skipif(
    True if not snowflake else False, reason="snowflake is not installed"
)
@pytest.mark.unit
def test_get_execution_engine_succeeds():
    connection_string = "snowflake://my_user:password@my_account/my_db/my_schema"
    datasource = SnowflakeDatasource(
        name="my_snowflake", connection_string=connection_string
    )
    # testing that this doesn't raise an exception
    datasource.get_execution_engine()


@pytest.mark.snowflake
@pytest.mark.parametrize(
    "connection_string",
    [
        param(
            "snowflake://my_user:password@my_account/my_db/my_schema?numpy=True",
            id="connection_string str",
        ),
        param(
            {
                "user": "my_user",
                "password": "password",
                "account": "my_account",
                "database": "foo",
                "schema": "bar",
            },
            id="connection_string dict",
        ),
    ],
)
@pytest.mark.parametrize(
    "context_fixture_name,expected_query_param",
    [
        param(
            "empty_file_context",
            "great_expectations_core",
            id="file context",
        ),
        param(
            "empty_cloud_context_fluent",
            "great_expectations_platform",
            id="cloud context",
        ),
    ],
)
def test_get_engine_correctly_sets_application_query_param(
    request,
    context_fixture_name: str,
    expected_query_param: str,
    connection_string: str | dict,
):
    context = request.getfixturevalue(  # TODO: fix this and make it a fixture in the root conftest
        context_fixture_name
    )
    my_sf_ds = SnowflakeDatasource(name="my_sf_ds", connection_string=connection_string)
    my_sf_ds._data_context = context

    sql_engine = my_sf_ds.get_engine()
    application_query_param = sql_engine.url.query.get("application")
    assert application_query_param == expected_query_param


@pytest.mark.parametrize("ds_config", VALID_DS_CONFIG_PARAMS)
class TestConvenienceProperties:
    def test_schema(
        self,
        ds_config: dict,
        seed_env_vars: None,
        request: pytest.FixtureRequest,
        ephemeral_context_with_defaults: AbstractDataContext,
    ):
        param_id = request.node.name
        datasource = SnowflakeDatasource(name=param_id, **ds_config)
        if isinstance(datasource.connection_string, ConfigStr):
            # expect a warning if connection string is a ConfigStr
            with pytest.warns(GxContextWarning):
                assert (
                    not datasource.schema_
                ), "Don't expect schema to be available without config_provider"
            # attach context to enable config substitution
            datasource._data_context = ephemeral_context_with_defaults

        assert datasource.schema_

    def test_database(
        self,
        ds_config: dict,
        seed_env_vars: None,
        request: pytest.FixtureRequest,
        ephemeral_context_with_defaults: AbstractDataContext,
    ):
        param_id = request.node.name
        datasource = SnowflakeDatasource(name=param_id, **ds_config)
        if isinstance(datasource.connection_string, ConfigStr):
            # expect a warning if connection string is a ConfigStr
            with pytest.warns(GxContextWarning):
                assert (
                    not datasource.database
                ), "Don't expect schema to be available without config_provider"
            # attach context to enable config substitution
            datasource._data_context = ephemeral_context_with_defaults

        assert datasource.database


if __name__ == "__main__":
    pytest.main([__file__, "-vv"])
