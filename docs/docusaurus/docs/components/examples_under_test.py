docs_tests = []

connecting_to_a_datasource = [
    # # Create a Data Source
    # IntegrationTestFixture(
    #     name="create_a_datasource_postgres",
    #     user_flow_script="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py",
    #     data_context_dir="docs/docusaurus/docs/components/_testing/create_datasource/great_expectations/",
    #     data_dir="tests/test_sets/taxi_yellow_tripdata_samples/",
    #     util_script="tests/test_utils.py",
    #     other_files=(
    #         (
    #             "tests/integration/fixtures/partition_and_sample_data/postgres_connection_string.yml",
    #             "connection_string.yml",
    #         ),
    #     ),
    #     backend_dependencies=[BackendDependencies.POSTGRESQL],
    # ),
    # # Create a Data Asset
    # IntegrationTestFixture(
    #     name="create_a_data_asset_postgres",
    #     user_flow_script="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_asset/create_a_data_asset.py",
    #     data_context_dir="docs/docusaurus/docs/components/_testing/create_datasource/great_expectations/",
    #     data_dir="tests/test_sets/taxi_yellow_tripdata_samples/",
    #     util_script="tests/test_utils.py",
    #     other_files=(
    #         (
    #             "tests/integration/fixtures/partition_and_sample_data/postgres_connection_string.yml",
    #             "connection_string.yml",
    #         ),
    #     ),
    #     backend_dependencies=[BackendDependencies.POSTGRESQL],
    # ),
    # # Create a Batch Definition
    # IntegrationTestFixture(
    #     name="create_a_batch_definition_postgres",
    #     user_flow_script="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_batch_definition/create_a_batch_definition.py",
    #     data_context_dir="docs/docusaurus/docs/components/_testing/create_datasource/great_expectations/",
    #     data_dir="tests/test_sets/taxi_yellow_tripdata_samples/samples_2020",
    #     util_script="tests/test_utils.py",
    #     other_files=(
    #         (
    #             "tests/integration/fixtures/partition_and_sample_data/postgres_connection_string.yml",
    #             "connection_string.yml",
    #         ),
    #     ),
    #     backend_dependencies=[BackendDependencies.POSTGRESQL],
    # ),
]


docs_tests.extend(connecting_to_a_datasource)
