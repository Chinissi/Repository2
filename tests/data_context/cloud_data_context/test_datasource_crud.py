"""This file is meant for integration tests related to datasource CRUD."""
import copy
from unittest.mock import patch

import pytest

# TODO: Tests
# Test add_datasource
# Test get_datasource
# Test update_datasource
# Test delete_datasource
from great_expectations.data_context import BaseDataContext
from great_expectations.data_context.store import GeCloudStoreBackend
from great_expectations.data_context.types.base import (
    DatasourceConfig,
    datasourceConfigSchema,
)

# TODO: Fixtures
# empty_cloud_data_context for a BaseDataContext in cloud mode
# ?? new fixture for a CloudDataContext data context
# ?? for DataContext in cloud mode
from great_expectations.data_context.types.refs import GeCloudResourceRef
from great_expectations.datasource import BaseDatasource


@pytest.mark.integration
def test_cloud_mode_data_context_add_datasource_save_changes_true():
    """A BaseDataContext in cloud mode should save to the Datasource store when calling add_datasource
    with save_changes=True."""
    # 1. setup context
    # 2. call add_datasource with mocked `requests.set`
    # 3. assert the right call was made to the store backend
    raise NotImplementedError


@pytest.mark.integration
def test_cloud_mode_data_context_add_datasource_save_changes_false():
    """A BaseDataContext in cloud mode should not save to the Datasource store when calling add_datasource
    with save_changes=False."""

    # Assert no call was made to the store backend
    raise NotImplementedError


@pytest.mark.integration
@pytest.mark.parametrize(
    "config_includes_name",
    [
        pytest.param("name_supplied_separately", id="name supplied separately"),
        pytest.param("config_includes_name", id="config includes name"),
        pytest.param(
            "name_supplied_separately_and_included_in_config",
            id="name supplied separately and config includes name",
            marks=pytest.mark.xfail(strict=True, raises=TypeError),
        ),
    ],
)
def test_cloud_mode_base_data_context_add_datasource_save_changes_true(
    config_includes_name: str,
    empty_cloud_data_context: BaseDataContext,
    datasource_config: DatasourceConfig,
    datasource_name: str,
    ge_cloud_base_url: str,
    ge_cloud_organization_id: str,
    request_headers: dict,
):
    """A BaseDataContext in cloud mode should save to the cloud backed Datasource store when calling add_datasource
    with save_changes=True."""

    # Make sure we are using the right fixtures
    assert empty_cloud_data_context.ge_cloud_mode
    assert isinstance(empty_cloud_data_context, BaseDataContext)
    assert isinstance(
        empty_cloud_data_context._data_context._datasource_store._store_backend,
        GeCloudStoreBackend,
    )
    assert len(empty_cloud_data_context.list_datasources()) == 0

    # Setup
    datasource_id: str = "some_uuid"
    datasource_config_with_name: DatasourceConfig = copy.deepcopy(datasource_config)
    datasource_config_with_name.name = datasource_name

    def mocked_post_response(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data: dict, status_code: int) -> None:
                self._json_data = json_data
                self._status_code = status_code

            def json(self):
                return self._json_data

        return MockResponse({"data": {"id": datasource_id}}, 201)

    with patch(
        "requests.post", autospec=True, side_effect=mocked_post_response
    ) as mock_post:

        # Call add_datasource with and without the name field included in the datasource config
        if config_includes_name == "name_supplied_separately":
            stored_datasource: BaseDatasource = empty_cloud_data_context.add_datasource(
                name=datasource_name, **datasource_config.to_dict(), save_changes=True
            )
        elif config_includes_name == "config_includes_name":
            stored_datasource: BaseDatasource = empty_cloud_data_context.add_datasource(
                **datasource_config_with_name.to_dict(), save_changes=True
            )
        elif config_includes_name == "name_supplied_separately_and_included_in_config":
            stored_datasource: BaseDatasource = empty_cloud_data_context.add_datasource(
                name=datasource_name,
                **datasource_config_with_name.to_dict(),
                save_changes=True,
            )

        # Make sure we have stored our datasource in the context
        assert len(empty_cloud_data_context.list_datasources()) == 1

        retrieved_datasource: BaseDatasource = empty_cloud_data_context.get_datasource(
            datasource_name
        )

        # This post should have been called without the id (which is retrieved from the response).
        # It should have been called with the datasource name in the config.
        mock_post.assert_called_with(
            f"{ge_cloud_base_url}/organizations/{ge_cloud_organization_id}/datasources",
            json={
                "data": {
                    "type": "datasource",
                    "attributes": {
                        "datasource_config": datasource_config_with_name.to_json_dict(),
                        "organization_id": ge_cloud_organization_id,
                    },
                }
            },
            headers=request_headers,
        )

        # Make sure the id was populated correctly into the created datasource object and config
        assert stored_datasource.id_ == datasource_id
        assert retrieved_datasource.id_ == datasource_id
        assert retrieved_datasource.config["id_"] == datasource_id

        # Make sure the name is populated correctly into the created datasource
        assert retrieved_datasource.name == datasource_name
        assert retrieved_datasource.config["name"] == datasource_name


@pytest.mark.integration
def test_cloud_mode_base_data_context_add_datasource_save_changes_false():
    """A BaseDataContext in cloud mode should not save to the Datasource store when calling add_datasource
    with save_changes=False."""
    raise NotImplementedError


@pytest.mark.integration
def test_cloud_data_context_add_datasources_save_changes_true():
    raise NotImplementedError


@pytest.mark.integration
def test_cloud_data_context_add_datasources_save_changes_false():
    raise NotImplementedError
