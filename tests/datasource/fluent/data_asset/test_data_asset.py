import pytest

from great_expectations.core.batch_config import BatchConfig
from great_expectations.core.data_context_key import DataContextVariableKey
from great_expectations.data_context.data_context.abstract_data_context import (
    AbstractDataContext,
)
from great_expectations.data_context.store.datasource_store import DatasourceStore
from great_expectations.datasource.fluent.interfaces import DataAsset, Datasource


@pytest.fixture
def datasource_name() -> str:
    return "my datasource for batch configs"


@pytest.fixture
def empty_data_asset_name() -> str:
    return "my data asset for batch configs"


@pytest.fixture
def data_asset_with_batch_config_name() -> str:
    return "I have batch configs"


@pytest.fixture
def batch_config_name() -> str:
    return "my batch config"


@pytest.fixture
def context(empty_data_context: AbstractDataContext) -> AbstractDataContext:
    return empty_data_context


@pytest.fixture
def store(
    context: AbstractDataContext,
    datasource_name: str,
    empty_data_asset_name: str,
    data_asset_with_batch_config_name: str,
    batch_config_name: str,
) -> DatasourceStore:
    """Datasource store on datasource that has 2 assets. one of the assets has a batch config."""
    store = context._datasource_store
    datasource = context.sources.add_pandas(datasource_name)
    datasource.add_csv_asset(empty_data_asset_name, "taxi.csv")  # type: ignore [arg-type]
    datasource.add_csv_asset(
        data_asset_with_batch_config_name,
        "taxi.csv",  # type: ignore [arg-type]
    ).add_batch_config(batch_config_name)

    key = DataContextVariableKey(resource_name=datasource_name)
    store.set(key=key, value=datasource)
    return store


@pytest.fixture
def empty_data_asset(
    store: DatasourceStore,
    datasource_name: str,
    empty_data_asset_name: str,
) -> DataAsset:
    key = DataContextVariableKey(resource_name=datasource_name)
    datasource = store.get(key)

    assert isinstance(datasource, Datasource)
    return datasource.get_asset(empty_data_asset_name)


@pytest.fixture
def data_asset_with_batch_config(
    store: DatasourceStore,
    datasource_name: str,
    data_asset_with_batch_config_name: str,
) -> DataAsset:
    key = DataContextVariableKey(resource_name=datasource_name)
    datasource = store.get(key)

    assert isinstance(datasource, Datasource)
    return datasource.get_asset(data_asset_with_batch_config_name)


@pytest.fixture
def persisted_batch_config(
    data_asset_with_batch_config: DataAsset,
) -> BatchConfig:
    return data_asset_with_batch_config.batch_configs[0]


@pytest.mark.unit
def test_add_batch_config__success(empty_data_asset: DataAsset):
    name = "my batch config"
    batch_config = empty_data_asset.add_batch_config(name)

    assert batch_config.name == name
    assert batch_config.data_asset == empty_data_asset
    assert empty_data_asset.batch_configs == [batch_config]


@pytest.mark.unit
def test_add_batch_config__persists_when_context_present(
    context: AbstractDataContext,
    store: DatasourceStore,
    empty_data_asset: DataAsset,
    datasource_name: str,
    empty_data_asset_name: str,
):
    key = DataContextVariableKey(resource_name=datasource_name)
    name = "my batch config"

    # depending on how a datasource is created, it may or may not have a context
    empty_data_asset._datasource._data_context = context

    batch_config = empty_data_asset.add_batch_config(name)

    loaded_datasource = store.get(key)
    assert isinstance(loaded_datasource, Datasource)
    loaded_asset = loaded_datasource.get_asset(empty_data_asset_name)

    assert loaded_asset.batch_configs == [batch_config]


@pytest.mark.unit
def test_add_batch_config__multiple(empty_data_asset: DataAsset):
    empty_data_asset.add_batch_config("foo")
    empty_data_asset.add_batch_config("bar")

    assert len(empty_data_asset.batch_configs) == 2


@pytest.mark.unit
def test_add_batch_config__duplicate_key(empty_data_asset: DataAsset):
    name = "my batch config"
    empty_data_asset.add_batch_config(name)

    with pytest.raises(ValueError, match="already exists"):
        empty_data_asset.add_batch_config(name)


@pytest.mark.unit
def test_delete_batch_config__success(
    data_asset_with_batch_config: DataAsset,
    persisted_batch_config: BatchConfig,
):
    assert persisted_batch_config in data_asset_with_batch_config.batch_configs

    data_asset_with_batch_config.delete_batch_config(persisted_batch_config)

    assert data_asset_with_batch_config.batch_configs == []


@pytest.mark.unit
def test_delete_batch_config__persists(
    store: DatasourceStore,
    context: AbstractDataContext,
    datasource_name: str,
    empty_data_asset_name: str,
    data_asset_with_batch_config: DataAsset,
    persisted_batch_config: BatchConfig,
):
    key = DataContextVariableKey(resource_name=datasource_name)

    # depending on how a datasource is created, it may or may not have a context
    data_asset_with_batch_config._datasource._data_context = context
    data_asset_with_batch_config.delete_batch_config(persisted_batch_config)

    loaded_datasource = store.get(key)
    assert isinstance(loaded_datasource, Datasource)
    loaded_asset = loaded_datasource.get_asset(empty_data_asset_name)

    assert loaded_asset.batch_configs == []


@pytest.mark.unit
def test_delete_batch_config__unsaved_batch_config(empty_data_asset: DataAsset):
    batch_config = BatchConfig(name="uh oh")

    with pytest.raises(ValueError, match="does not exist"):
        empty_data_asset.delete_batch_config(batch_config)


@pytest.mark.unit
def test_fields_set(empty_data_asset: DataAsset):
    """We mess with pydantic's internal __fields_set__ to determine
    if certain fields (batch_configs in this case) should get serialized.

    This test is essentially a proxy for whether we serialize that field
    """
    asset = empty_data_asset

    # when we don't have batch configs, it shouldn't be in the set
    assert "batch_configs" not in asset.__fields_set__

    # add some batch configs and ensure we have it in the set
    batch_config_a = asset.add_batch_config("a")
    batch_config_b = asset.add_batch_config("b")
    assert "batch_configs" in asset.__fields_set__

    # delete one of the batch configs and ensure we still have it in the set
    asset.delete_batch_config(batch_config_a)
    assert "batch_configs" in asset.__fields_set__

    # delete the remaining batch config and ensure we don't have it in the set
    asset.delete_batch_config(batch_config_b)
    assert "batch_configs" not in asset.__fields_set__
