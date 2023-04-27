# Set up version information immediately
from ._version import get_versions  # isort:skip

__version__ = get_versions()["version"]  # isort:skip

from great_expectations.data_context.migrator.cloud_migrator import CloudMigrator

from .expectations.registry import register_core_expectations

del get_versions  # isort:skip

from great_expectations.data_context import DataContext

from .util import (
    from_pandas,
    get_context,
    read_csv,
    read_excel,
    read_feather,
    read_json,
    read_parquet,
    read_pickle,
    read_sas,
    read_table,
    validate,
)

register_core_expectations()

# from great_expectations.expectations.core import *
# from great_expectations.expectations.metrics import *


rtd_url_ge_version = __version__.replace(".", "_")
