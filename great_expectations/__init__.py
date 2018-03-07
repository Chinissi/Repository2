import json
import pandas as pd

from .util import *
from great_expectations import dataset

from .connections import GreatExpectationsConnection, SqlAlchemyConnection, FilepathConnection, SparkSqlConnection

from .version import __version__

def get_connection(connection_type, *args, **kwargs):
    if connection_type == "SqlAlchemy":
        #FIXME: provide an additional API that allows connection strings to be generated from arguments.
        return SqlAlchemyConnection(kwargs['connection_string'])

    if connection_type == "Filepath":
        #FIXME: provide an additional API that allows connection strings to be generated from arguments.
        return FilepathConnection(**kwargs)

    # elif connection_type == "pandas_directory":
    #     PandasDataContext(args, kwargs)
    # elif ...

    else:
        raise ValueError("Unknown connection_type: %s" % (connection_type,))

def _convert_to_dataset_class(df, dataset_class, expectations_config=None):
    """
    Convert a (pandas) dataframe to a great_expectations dataset, with (optional) expectations_config
    """
    if expectations_config is not None:
        # Cast the dataframe into the new class, and manually initialize expectations according to the provided configuration
        df.__class__ = dataset_class
        df.initialize_expectations(expectations_config)
    else:
        # Instantiate the new DataSet with default expectations
        try:
            df = dataset_class(df)
        except:
            #FIXME: This error message says the wrong thing. It references read_csv, but we're in a different function.
            raise NotImplementedError("read_csv requires a DataSet class that can be instantiated from a Pandas DataFrame")

    return df

def read_csv(
    filename,
    dataset_class=dataset.pandas_dataset.PandasDataSet,
    expectations_config=None,
    *args, **kwargs
):
    df = pd.read_csv(filename, *args, **kwargs)
    df = _convert_to_dataset_class(df, dataset_class, expectations_config)
    return df

def read_json(
    filename,
    dataset_class=dataset.pandas_dataset.PandasDataSet,
    expectations_config=None,
    accessor_func=None,
    *args, **kwargs
):
    if accessor_func != None:
        json_obj = json.load(open(filename, 'rb'))
        json_obj = accessor_func(json_obj)
        df = pd.read_json(json.dumps(json_obj), *args, **kwargs)

    else:
        df = pd.read_json(filename, *args, **kwargs)

    df = _convert_to_dataset_class(df, dataset_class, expectations_config)
    return df

def validate(df, expectations_config, *args, **kwargs):
    #FIXME: I'm not sure that this should always default to PandasDataSet
    dataset_ = _convert_to_dataset_class(df,
        dataset.pandas_dataset.PandasDataSet,
        expectations_config
    )
    return dataset_.validate(*args, **kwargs)

def expect(data_source_str, expectation):
    raise NotImplementedError
