import pandas as pd
import json

import great_expectations.dataset as dataset


def _convert_to_dataset_class(df, dataset_class, expectations_config=None, autoinspect_func=None):
    """
    Convert a (pandas) dataframe to a great_expectations dataset, with (optional) expectations_config
    """
    if expectations_config is not None:
        # Cast the dataframe into the new class, and manually initialize expectations according to the provided configuration
        new_df = dataset_class(df)
        new_df._initialize_expectations(expectations_config)
    else:
        # Instantiate the new Dataset with default expectations
        try:
            new_df = dataset_class(df, autoinspect_func=autoinspect_func)
        except:
            raise NotImplementedError(
                "read_csv requires a Dataset class that can be instantiated from a Pandas DataFrame")

    return new_df


def read_csv(
    filename,
    dataset_class=dataset.pandas_dataset.PandasDataset,
    expectations_config=None,
    autoinspect_func=None,
    *args, **kwargs
):
    df = pd.read_csv(filename, *args, **kwargs)
    df = _convert_to_dataset_class(
        df, dataset_class, expectations_config, autoinspect_func)
    return df


def read_json(
    filename,
    dataset_class=dataset.pandas_dataset.PandasDataset,
    expectations_config=None,
    accessor_func=None,
    autoinspect_func=None,
    *args, **kwargs
):
    if accessor_func != None:
        json_obj = json.load(open(filename, 'rb'))
        json_obj = accessor_func(json_obj)
        df = pd.read_json(json.dumps(json_obj), *args, **kwargs)

    else:
        df = pd.read_json(filename, *args, **kwargs)

    df = _convert_to_dataset_class(
        df, dataset_class, expectations_config, autoinspect_func)
    return df


def read_excel(
    filename,
    dataset_class=dataset.pandas_dataset.PandasDataset,
    expectations_config=None,
    autoinspect_func=None,
    *args, **kwargs
):
    """Read a file using Pandas read_excel and return a great_expectations dataset.

    Args:
        filename (string): path to file to read
        dataset_class (Dataset class): class to which to convert resulting Pandas df
        expectations_config (string): path to great_expectations config file

    Returns:
        great_expectations dataset or ordered dict of great_expectations datasets,
        if multiple worksheets are imported
    """
    df = pd.read_excel(filename, *args, **kwargs)
    if isinstance(df, dict):
        for key in df:
            df[key] = _convert_to_dataset_class(
                df[key], dataset_class, expectations_config, autoinspect_func)
    else:
        df = _convert_to_dataset_class(
            df, dataset_class, expectations_config, autoinspect_func)
    return df


def read_table(
    filename,
    dataset_class=dataset.pandas_dataset.PandasDataset,
    expectations_config=None,
    autoinspect_func=None,
    *args, **kwargs
):
    """Read a file using Pandas read_table and return a great_expectations dataset.

    Args:
        filename (string): path to file to read
        dataset_class (Dataset class): class to which to convert resulting Pandas df
        expectations_config (string): path to great_expectations config file

    Returns:
        great_expectations dataset
    """
    df = pd.read_table(filename, *args, **kwargs)
    df = _convert_to_dataset_class(
        df, dataset_class, expectations_config, autoinspect_func)
    return df


def read_parquet(
    filename,
    dataset_class=dataset.pandas_dataset.PandasDataset,
    expectations_config=None,
    autoinspect_func=None,
    *args, **kwargs
):
    """Read a file using Pandas read_parquet and return a great_expectations dataset.

    Args:
        filename (string): path to file to read
        dataset_class (Dataset class): class to which to convert resulting Pandas df
        expectations_config (string): path to great_expectations config file

    Returns:
        great_expectations dataset
    """
    df = pd.read_parquet(filename, *args, **kwargs)
    df = _convert_to_dataset_class(
        df, dataset_class, expectations_config, autoinspect_func)
    return df


def from_pandas(pandas_df, 
                dataset_class=dataset.pandas_dataset.PandasDataset,
                expectations_config=None, 
                autoinspect_func=None
):
    """Read a Pandas data frame and return a great_expectations dataset.

    Args:
        pandas_df (Pandas df): Pandas data frame
        dataset_class (Dataset class) = dataset.pandas_dataset.PandasDataset:
            class to which to convert resulting Pandas df
        expectations_config (string) = None: path to great_expectations config file
        autoinspect_func (function) = None: The autoinspection function that should 
            be run on the dataset to establish baseline expectations.

    Returns:
        great_expectations dataset
    """
    return _convert_to_dataset_class(
        pandas_df,
        dataset_class,
        expectations_config,
        autoinspect_func
    )


def validate(data_asset, expectations_config, data_asset_type=None, *args, **kwargs):
    """Validate the provided data asset using the provided config"""

    # If the object is already a Dataset type, then this is purely a convenience method
    # and no conversion is needed
    if isinstance(data_asset, dataset.Dataset) and data_asset_type is None:
        return data_asset.validate(*args, **kwargs)
    elif data_asset_type is None:
        # Guess the GE data_asset_type based on the type of the data_asset
        if isinstance(data_asset, pd.DataFrame):
            data_asset_type = dataset.PandasDataset
        # Add other data_asset_type conditions here as needed
    elif type(data_asset) is data_asset_type:
        # Finally, if data_asset_type happens to have been unnecessarily provided
        return data_asset.validate(*args, **kwargs)

    # Otherwise, we will convert for the user to a subclass of the
    # existing class to enable new expectations, but only for datasets
    if not isinstance(data_asset, (dataset.Dataset, pd.DataFrame)):
        raise ValueError("The validate util method only supports type conversion for dataset validations, including custom subclasses. For other data asset types, use the object's own validate method or specify the exact type.")

    if not issubclass(type(data_asset), data_asset_type):
        if isinstance(data_asset, pd.DataFrame) and issubclass(data_asset_type, dataset.PandasDataset):
            pass # This is a special type of allowed coercion
        else:
            raise ValueError("The validate util method only supports validation for subtypes of the provided data_asset_type.")

    data_asset_ = _convert_to_dataset_class(data_asset, data_asset_type, expectations_config)
    return data_asset_.validate(*args, **kwargs)


class DotDict(dict):
    """dot.notation access to dictionary attributes"""

    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __dir__(self):
        return self.keys()
