from tests.integration.backend_dependencies import BackendDependencies
from tests.integration.integration_test_fixture import IntegrationTestFixture

snowflake_integration_tests = []

connecting_to_your_data = [
    IntegrationTestFixture(
        name="snowflake_python_example",
        user_flow_script="tests/integration/docusaurus/connecting_to_your_data/database/snowflake_python_example.py",
        data_context_dir="tests/integration/fixtures/no_datasources/great_expectations",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/first_3_files",
        backend_dependencies=[BackendDependencies.SNOWFLAKE],
        util_script="tests/test_utils.py",
    ),
]

partition_data = [
    IntegrationTestFixture(
        name="partition_data_on_whole_table_snowflake",
        user_flow_script="tests/integration/db/test_sql_data_partitioned_on_whole_table.py",
        data_context_dir="tests/integration/fixtures/no_datasources/great_expectations",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/",
        util_script="tests/test_utils.py",
        other_files=(
            (
                "tests/integration/fixtures/partition_and_sample_data/snowflake_connection_string.yml",
                "connection_string.yml",
            ),
        ),
        backend_dependencies=[BackendDependencies.SNOWFLAKE],
    ),
    IntegrationTestFixture(
        name="partition_data_on_datetime_snowflake",
        user_flow_script="tests/integration/db/test_sql_data_partitioned_on_datetime_and_day_part.py",
        data_context_dir="tests/integration/fixtures/no_datasources/great_expectations",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/",
        util_script="tests/test_utils.py",
        other_files=(
            (
                "tests/integration/fixtures/partition_and_sample_data/snowflake_connection_string.yml",
                "connection_string.yml",
            ),
        ),
        backend_dependencies=[BackendDependencies.SNOWFLAKE],
    ),
]

sample_data = [
    IntegrationTestFixture(
        name="sample_data_using_limit_snowflake",
        user_flow_script="tests/integration/db/test_sql_data_sampling.py",
        data_context_dir="tests/integration/fixtures/no_datasources/great_expectations",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/",
        util_script="tests/test_utils.py",
        other_files=(
            (
                "tests/integration/fixtures/partition_and_sample_data/snowflake_connection_string.yml",
                "connection_string.yml",
            ),
        ),
        backend_dependencies=[BackendDependencies.SNOWFLAKE],
    ),
]

snowflake_integration_tests += connecting_to_your_data
snowflake_integration_tests += partition_data
snowflake_integration_tests += sample_data
