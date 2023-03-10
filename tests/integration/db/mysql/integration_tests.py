# from tests.integration.test_script_runner import (
#     BackendDependencies,
#     IntegrationTestFixture,
# )
import enum
from dataclasses import dataclass
from typing import Optional, Tuple


class BackendDependencies(enum.Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    BIGQUERY = "BIGQUERY"
    GCS = "GCS"
    MYSQL = "MYSQL"
    MSSQL = "MSSQL"
    PANDAS = "PANDAS"
    POSTGRESQL = "POSTGRESQL"
    REDSHIFT = "REDSHIFT"
    SPARK = "SPARK"
    SQLALCHEMY = "SQLALCHEMY"
    SNOWFLAKE = "SNOWFLAKE"
    TRINO = "TRINO"


@dataclass
class IntegrationTestFixture:
    """IntegrationTestFixture

    Configurations for integration tests are defined as IntegrationTestFixture dataclass objects.

    Individual tests can also be run by setting the '-k' flag and referencing the name of test, like the following example:
    pytest -v --docs-tests -m integration -k "test_docs[migration_guide_spark_v2_api]" tests/integration/test_script_runner.py

    Args:
        name: Name for integration test. Individual tests can be run by using the -k option and specifying the name of the test.
        user_flow_script: Required script for integration test.
        data_context_dir: Path of great_expectations/ that is used in the test.
        data_dir: Folder that contains data used in the test.
        extra_backend_dependencies: Optional flag allows you to tie an individual test with a BackendDependency. Allows for tests to be run / disabled using cli flags (like --aws which enables AWS integration tests).
        other_files: other files (like credential information) to copy into the test environment. These are presented as Tuple(path_to_source_file, path_to_target_file), where path_to_target_file is relative to the test_script.py file in our test environment
        util_script: Path of optional util script that is used in test script (for loading test_specific methods like load_data_into_test_database())
    """

    name: str
    user_flow_script: str
    data_context_dir: Optional[str] = None
    data_dir: Optional[str] = None
    extra_backend_dependencies: Optional[BackendDependencies] = None
    other_files: Optional[Tuple[Tuple[str, str]]] = None
    util_script: Optional[str] = None

mysql_integration_tests = [
    IntegrationTestFixture(
        name="mysql_yaml_example",
        user_flow_script="tests/integration/docusaurus/connecting_to_your_data/database/mysql_yaml_example.py",
        data_context_dir="tests/integration/fixtures/no_datasources/great_expectations",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/first_3_files",
        util_script="tests/test_utils.py",
        extra_backend_dependencies=BackendDependencies.MYSQL,
    ),
    IntegrationTestFixture(
        name="mysql_python_example",
        user_flow_script="tests/integration/docusaurus/connecting_to_your_data/database/mysql_python_example.py",
        data_context_dir="tests/integration/fixtures/no_datasources/great_expectations",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/first_3_files",
        util_script="tests/test_utils.py",
        extra_backend_dependencies=BackendDependencies.MYSQL,
    ),
]
