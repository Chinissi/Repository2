import pathlib
from unittest import mock

import pytest

from great_expectations.data_context.data_context.base_data_context import (
    BaseDataContext,
)
from great_expectations.data_context.data_context.data_context import DataContext
from great_expectations.data_context.store.ge_cloud_store_backend import (
    GeCloudStoreBackend,
)
from great_expectations.data_context.store.inline_store_backend import (
    InlineStoreBackend,
)
from great_expectations.data_context.types.base import DataContextConfig, GeCloudConfig
from great_expectations.datasource.pandas_datasource import PandasDatasource


@pytest.mark.integration
def test_data_context_instantiates_ge_cloud_store_backend_with_cloud_config(
    tmp_path: pathlib,
    data_context_config_with_datasources: DataContextConfig,
    ge_cloud_config: GeCloudConfig,
) -> None:
    project_path = tmp_path / "my_data_context"
    project_path.mkdir()

    # Clear datasources to improve test performance in DataContext._init_datasources
    data_context_config_with_datasources.datasources = {}

    context = BaseDataContext(
        project_config=data_context_config_with_datasources,
        context_root_dir=str(project_path),
        ge_cloud_mode=True,
        ge_cloud_config=ge_cloud_config,
    )

    assert isinstance(context._datasource_store.store_backend, GeCloudStoreBackend)


@pytest.mark.integration
def test_data_context_instantiates_inline_store_backend_with_filesystem_config(
    tmp_path: pathlib,
    data_context_config_with_datasources: DataContextConfig,
) -> None:
    project_path = tmp_path / "my_data_context"
    project_path.mkdir()

    # Clear datasources to improve test performance in DataContext._init_datasources
    data_context_config_with_datasources.datasources = {}

    context = BaseDataContext(
        project_config=data_context_config_with_datasources,
        context_root_dir=str(project_path),
        ge_cloud_mode=False,
    )

    assert isinstance(context._datasource_store.store_backend, InlineStoreBackend)


@pytest.mark.parametrize(
    "data_context_fixture_name",
    [
        # In order to leverage existing fixtures in parametrization, we provide
        # their string names and dynamically retrieve them using pytest's built-in
        # `request` fixture.
        # Source: https://stackoverflow.com/a/64348247
        pytest.param(
            "in_memory_runtime_context",
            id="BaseDataContext",
        ),
        pytest.param(
            "cloud_data_context_in_cloud_mode_with_datasource_pandas_engine",
            id="DataContext",
        ),
    ],
)
@pytest.mark.unit
def test_get_datasource_retrieves_from_cache(
    data_context_fixture_name: str,
    request,
) -> None:
    """
    What does this test and why?

    For both persistence-enabled and disabled contexts, we should always be looking at the
    cache for object retrieval.
    """
    context = request.getfixturevalue(data_context_fixture_name)

    name = context.list_datasources()[0]["name"]

    # If the value is in the cache, no store methods should be invoked
    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.get"
    ) as mock_get:
        context.get_datasource(name)

    assert not mock_get.called


@pytest.mark.parametrize(
    "data_context_fixture_name",
    [
        # In order to leverage existing fixtures in parametrization, we provide
        # their string names and dynamically retrieve them using pytest's built-in
        # `request` fixture.
        # Source: https://stackoverflow.com/a/64348247
        pytest.param(
            "in_memory_runtime_context",
            id="BaseDataContext",
        ),
        pytest.param(
            "cloud_data_context_in_cloud_mode_with_datasource_pandas_engine",
            id="DataContext",
        ),
    ],
)
@pytest.mark.unit
def test_get_datasource_cache_miss(
    data_context_fixture_name: str,
    request,
) -> None:
    """
    What does this test and why?

    For persistence-enabled contexts, we should leverage the underlying store in the case
    of a cache miss.

    For persistence-disabled contexts, we only look at the cache.
    """
    context = request.getfixturevalue(data_context_fixture_name)

    name = "my_fake_datasource_name"

    # Initial GET will miss the cache, necessitating store retrieval
    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.has_key"
    ), mock.patch(
        "great_expectations.data_context.data_context.BaseDataContext._instantiate_datasource_from_config"
    ), mock.patch(
        "great_expectations.data_context.store.DatasourceStore.get"
    ) as mock_get:
        context.get_datasource(name)

    assert mock_get.called

    # Subsequent GET will retrieve from the cache
    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.get"
    ) as mock_get:
        context.get_datasource(name)

    assert not mock_get.called


@pytest.mark.unit
def test_DataContext_add_datasource_updates_cache_and_store(
    cloud_data_context_in_cloud_mode_with_datasource_pandas_engine: DataContext,
) -> None:
    """
    What does this test and why?

    For persistence-enabled contexts, we should update both the cache and the underlying
    store upon adding a datasource.
    """
    context = cloud_data_context_in_cloud_mode_with_datasource_pandas_engine

    name = "my_new_datasource"

    assert name not in context.datasources

    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.set"
    ) as mock_set:
        context.add_datasource(
            name,
            class_name="PandasDatasource",
            batch_kwargs_generators={
                "subdir_reader": {
                    "class_name": "SubdirReaderBatchKwargsGenerator",
                }
            },
        )

    mock_set.assert_called_once()
    assert name in context.datasources


@pytest.mark.unit
def test_DataContext_update_datasource_updates_existing_value_in_cache_and_store(
    cloud_data_context_in_cloud_mode_with_datasource_pandas_engine: DataContext,
) -> None:
    """
    What does this test and why?

    For persistence-enabled contexts, we should update both the cache and the underlying
    store upon updating an existing datasource.
    """
    context = cloud_data_context_in_cloud_mode_with_datasource_pandas_engine

    name = context.list_datasources()[0]["name"]
    boto3_options = {"my": "option"}
    datasource = PandasDatasource(name=name, boto3_options=boto3_options)

    assert name in context.datasources

    # Ensure that our cache value is updated to reflect changes
    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.has_key"
    ), mock.patch(
        "great_expectations.data_context.store.DatasourceStore.set"
    ) as mock_set:
        context.update_datasource(datasource)

    mock_set.assert_called_once()
    assert name in context.datasources

    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.get"
    ) as mock_get:
        retrieved_datasource = context.get_datasource(datasource_name=name)

    assert not mock_get.called
    assert retrieved_datasource.boto3_options == boto3_options


@pytest.mark.unit
def test_DataContext_update_datasource_creates_new_value_in_cache_and_store(
    cloud_data_context_in_cloud_mode_with_datasource_pandas_engine: DataContext,
) -> None:
    """
    What does this test and why?

    For persistence-enabled contexts, we should update both the cache and the underlying
    store upon using update to create a new datasource.
    """
    context = cloud_data_context_in_cloud_mode_with_datasource_pandas_engine

    name = "my_new_datasource"
    boto3_options = {"my": "option"}
    datasource = PandasDatasource(name=name, boto3_options=boto3_options)

    assert name not in context.datasources

    # Ensure that a brand new cache value is added to reflect changes
    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.has_key"
    ), mock.patch(
        "great_expectations.data_context.store.DatasourceStore.set"
    ) as mock_set:
        context.update_datasource(datasource)

    mock_set.assert_called_once()
    assert name in context.datasources


@pytest.mark.unit
def test_DataContext_delete_datasource_updates_cache(
    cloud_data_context_in_cloud_mode_with_datasource_pandas_engine: DataContext,
) -> None:
    """
    What does this test and why?

    For persistence-enabled contexts, we should delete values in both the cache and the
    underlying store.
    """
    context = cloud_data_context_in_cloud_mode_with_datasource_pandas_engine

    name = context.list_datasources()[0]["name"]

    # If the value is in the cache, no store methods should be invoked
    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.remove_key"
    ) as mock_delete:
        context.delete_datasource(name)

    mock_delete.assert_called_once()
    assert name not in context.datasources


@pytest.mark.unit
def test_BaseDataContext_add_datasource_updates_cache(
    in_memory_runtime_context: BaseDataContext,
) -> None:
    """
    What does this test and why?

    For persistence-disabled contexts, we should only update the cache upon adding a
    datasource.
    """
    context = in_memory_runtime_context

    name = "my_new_datasource"

    assert name not in context.datasources

    context.add_datasource(
        name,
        class_name="PandasDatasource",
        batch_kwargs_generators={
            "subdir_reader": {
                "class_name": "SubdirReaderBatchKwargsGenerator",
            }
        },
    )

    assert name in context.datasources


@pytest.mark.unit
def test_BaseDataContext_update_datasource_updates_existing_value_in_cache(
    in_memory_runtime_context: BaseDataContext,
) -> None:
    """
    What does this test and why?

    For persistence-disabled contexts, we should only update the cache upon
    updating an existing datasource.
    """
    context = in_memory_runtime_context

    name = context.list_datasources()[0]["name"]
    boto3_options = {"my": "option"}
    datasource = PandasDatasource(name=name, boto3_options=boto3_options)

    assert name in context.datasources

    # Ensure that our cache value is updated to reflect changes
    context.update_datasource(datasource)

    assert name in context.datasources

    retrieved_datasource = context.get_datasource(datasource_name=name)
    assert retrieved_datasource.boto3_options == boto3_options


@pytest.mark.unit
def test_BaseDataContext_update_datasource_creates_new_value_in_cache(
    in_memory_runtime_context: BaseDataContext,
) -> None:
    """
    What does this test and why?

    For persistence-disabled contexts, we should only update the cache upon
    using update to create a new datasource.
    """
    context = in_memory_runtime_context

    name = "my_new_datasource"
    boto3_options = {"my": "option"}
    datasource = PandasDatasource(name=name, boto3_options=boto3_options)

    assert name not in context.datasources

    # Ensure that a brand new cache value is added to reflect changes
    context.update_datasource(datasource)

    assert name in context.datasources


@pytest.mark.unit
def test_BaseDataContext_delete_datasource_updates_cache(
    in_memory_runtime_context: BaseDataContext,
) -> None:
    """
    What does this test and why?

    For persistence-disabled contexts, we should only delete the value from
    the cache.
    """
    context = in_memory_runtime_context

    name = context.list_datasources()[0]["name"]

    # If the value is in the cache, no store methods should be invoked
    with mock.patch(
        "great_expectations.data_context.store.DatasourceStore.remove_key"
    ) as mock_delete:
        context.delete_datasource(name)

    assert not mock_delete.called
    assert name not in context.datasources
