import pytest

from ruamel.yaml import YAML
yaml = YAML(typ='safe')
import os
import shutil

import pandas as pd
import sqlalchemy as sa

from great_expectations.data_context import DataContext
from great_expectations.datasource import PandasCSVDatasource
from great_expectations.datasource.sqlalchemy_source import SqlAlchemyDatasource

from great_expectations.dataset import PandasDataset, SqlAlchemyDataset

@pytest.fixture(scope="module")
def test_folder_connection_path(tmp_path_factory):
    df1 = pd.DataFrame(
        {'col_1': [1, 2, 3, 4, 5], 'col_2': ['a', 'b', 'c', 'd', 'e']})
    path = str(tmp_path_factory.mktemp("test_folder_connection_path"))
    df1.to_csv(os.path.join(path, "test.csv"))

    return str(path)

@pytest.fixture(scope="module")
def test_db_connection_string(tmp_path_factory):
    df1 = pd.DataFrame(
        {'col_1': [1, 2, 3, 4, 5], 'col_2': ['a', 'b', 'c', 'd', 'e']})
    df2 = pd.DataFrame(
        {'col_1': [0, 1, 2, 3, 4], 'col_2': ['b', 'c', 'd', 'e', 'f']})

    basepath = str(tmp_path_factory.mktemp("db_context"))
    path = os.path.join(basepath, "test.db")
    engine = sa.create_engine('sqlite:///' + str(path))
    df1.to_sql('table_1', con=engine, index=True)
    df2.to_sql('table_2', con=engine, index=True, schema='main')

    # Return a connection string to this newly-created db
    return 'sqlite:///' + str(path)

def test_create_pandas_datasource(data_context, tmp_path_factory):
    basedir = tmp_path_factory.mktemp('test_create_pandas_datasource')
    name = "test_pandas_datasource"
    type_ = "pandas"

    data_context.add_datasource(name, type_, base_directory=str(basedir))
    data_context_config = data_context.get_config()

    assert name in data_context_config["datasources"] 
    assert data_context_config["datasources"][name]["type"] == type_

    # We should now see updated configs
    # Finally, we should be able to confirm that the folder structure is as expected
    with open(os.path.join(data_context.context_root_directory, "great_expectations/great_expectations.yml"), "r") as data_context_config_file:
        data_context_file_config = yaml.load(data_context_config_file)

    assert data_context_file_config["datasources"][name] == data_context_config["datasources"][name]

def test_standalone_pandas_datasource(test_folder_connection_path):
    datasource = PandasCSVDatasource('PandasCSV', base_directory=test_folder_connection_path)

    assert datasource.list_available_data_asset_names() == [{"generator": "default", "available_data_asset_names": {"test"}}]
    manual_batch_kwargs = datasource.build_batch_kwargs(os.path.join(str(test_folder_connection_path), "test.csv"))

    # Get the default (filesystem) generator
    generator = datasource.get_generator()
    auto_batch_kwargs = generator.yield_batch_kwargs("test")

    assert manual_batch_kwargs["path"] == auto_batch_kwargs["path"]

    # Include some extra kwargs...
    dataset = datasource.get_data_asset("test", batch_kwargs=auto_batch_kwargs, sep=",", header=0, index_col=0)
    assert isinstance(dataset, PandasDataset)
    assert (dataset["col_1"] == [1, 2, 3, 4, 5]).all()

def test_standalone_sqlalchemy_datasource(test_db_connection_string):
    datasource = SqlAlchemyDatasource(
        'SqlAlchemy', connection_string=test_db_connection_string, echo=False)

    assert datasource.list_available_data_asset_names() == [{"generator": "default", "available_data_asset_names": {"table_1", "table_2"}}]
    dataset1 = datasource.get_data_asset("table_1")
    dataset2 = datasource.get_data_asset("table_2", schema='main')
    assert isinstance(dataset1, SqlAlchemyDataset)
    assert isinstance(dataset2, SqlAlchemyDataset)


def test_create_sqlalchemy_datasource(data_context):
    name = "test_sqlalchemy_datasource"
    type_ = "sqlalchemy"
    connection_kwargs = {
        "drivername": "postgresql",
        "username": "user",
        "password": "pass",
        "host": "host",
        "port": 1234,
        "database": "db",
    }

    # It should be possible to create a sqlalchemy source using these params without
    # saving a profile
    data_context.add_datasource(name, type_, **connection_kwargs)
    data_context_config = data_context.get_config()
    assert name in data_context_config["datasources"] 
    assert data_context_config["datasources"][name]["type"] == type_

    # We should be able to get it in this session even without saving the config
    source = data_context.get_datasource(name)
    assert isinstance(source, SqlAlchemyDatasource)

    profile_name = "test_sqlalchemy_datasource"
    data_context.add_profile_credentials(profile_name, **connection_kwargs)

    # But we should be able to add a source using a profile
    name = "second_source"
    data_context.add_datasource(name, type_, profile="test_sqlalchemy_datasource")
    
    data_context_config = data_context.get_config()
    assert name in data_context_config["datasources"] 
    assert data_context_config["datasources"][name]["type"] == type_
    assert data_context_config["datasources"][name]["profile"] == profile_name

    source = data_context.get_datasource(name)
    assert isinstance(source, SqlAlchemyDatasource)

    # Finally, we should be able to confirm that the folder structure is as expected
    with open(os.path.join(data_context.context_root_directory, "great_expectations/uncommitted/credentials/profiles.yml"), "r") as profiles_file:
        profiles = yaml.load(profiles_file)
    
    assert profiles == {
        profile_name: dict(**connection_kwargs)
    }

def test_create_sparkdf_datasource(data_context, tmp_path_factory):
    base_dir = tmp_path_factory.mktemp('test_create_sparkdf_datasource')
    name = "test_sparkdf_datasource"
    type_ = "spark"

    data_context.add_datasource(name, type_, base_directory=str(base_dir))
    data_context_config = data_context.get_config()

    assert name in data_context_config["datasources"] 
    assert data_context_config["datasources"][name]["type"] == type_
    assert data_context_config["datasources"][name]["generators"]["default"]["base_directory"] == str(base_dir)

    base_dir = tmp_path_factory.mktemp('test_create_sparkdf_datasource-2')
    name = "test_sparkdf_datasource"
    type_ = "spark"

    data_context.add_datasource(name, type_, reader_options={"sep": "|", "header": False})
    data_context_config = data_context.get_config()

    assert name in data_context_config["datasources"] 
    assert data_context_config["datasources"][name]["type"] == type_ 
    assert data_context_config["datasources"][name]["reader_options"]["sep"] == "|"

    # Note that pipe is special in yml, so let's also check to see that it was properly serialized
    with open(os.path.join(data_context.get_context_root_directory(), "great_expectations/great_expectations.yml"), "r") as configfile:
        lines = configfile.readlines()
        assert "      sep: '|'\n" in lines
        assert "      header: false\n" in lines


def test_sqlalchemysource_templating(sqlitedb_engine):
    datasource = SqlAlchemyDatasource(engine=sqlitedb_engine)
    generator = datasource.get_generator()
    generator.add_query("test", "select 'cat' as ${col_name};")
    df = datasource.get_data_asset("test", col_name="animal_name")
    res = df.expect_column_to_exist("animal_name")
    assert res["success"] == True