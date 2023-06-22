import sys

# setup.py should restrict installing gx to Python >= 3.8
PYTHON3_SUPPORTED_MINOR_VERSIONS = [8, 9, 10]
if sys.version_info.minor not in PYTHON3_SUPPORTED_MINOR_VERSIONS:
    raise ImportError(
        "Great Expectations is only supported on Python 3.8 through 3.10. "
        f"You are using: {sys.version}"
    )


# Set up version information immediately
from ._version import get_versions  # isort:skip

__version__ = get_versions()["version"]  # isort:skip

from great_expectations.data_context.migrator.cloud_migrator import CloudMigrator
from great_expectations.expectations.registry import register_core_expectations

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

# By placing this registry function in our top-level __init__,  we ensure that all
# GX workflows have populated expectation registries before they are used.
#
# Both of the following import paths will trigger this file, causing the registration to occur:
#   import great_expectations as gx
#   from great_expectations.core import ExpectationSuite, ExpectationConfiguration
register_core_expectations()

# from great_expectations.expectations.core import *
# from great_expectations.expectations.metrics import *


rtd_url_ge_version = __version__.replace(".", "_")
