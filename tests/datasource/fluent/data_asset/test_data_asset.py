import pytest

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
def data_asset_name() -> str:
    return "my data asset for batch configs"


@pytest.fixture
def context(empty_data_context: AbstractDataContext) -> AbstractDataContext:
    return empty_data_context


@pytest.fixture
def store(
    context: AbstractDataContext,
    datasource_name: str,
    data_asset_name: str,
) -> DatasourceStore:
    """Datasource store on datasource that has 2 assets. one of the assets has a batch config."""
    store = context._datasource_store
    datasource = context.sources.add_pandas(datasource_name)
    datasource.add_csv_asset(data_asset_name, "taxi.csv")  # type: ignore [arg-type]

    key = DataContextVariableKey(resource_name=datasource_name)
    store.set(key=key, value=datasource)
    return store


@pytest.fixture
def empty_data_asset(
    store: DatasourceStore,
    datasource_name: str,
    data_asset_name: str,
) -> DataAsset:
    key = DataContextVariableKey(resource_name=datasource_name)
    datasource = store.get(key)

    assert isinstance(datasource, Datasource)
    return datasource.get_asset(data_asset_name)


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
    data_asset_name: str,
):
    key = DataContextVariableKey(resource_name=datasource_name)
    name = "my batch config"

    # depending on how a datasource is created, it may or may not have a context
    empty_data_asset._datasource._data_context = context

    batch_config = empty_data_asset.add_batch_config(name)

    loaded_datasource = store.get(key)
    assert isinstance(loaded_datasource, Datasource)
    loaded_asset = loaded_datasource.get_asset(data_asset_name)

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
