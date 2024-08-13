"""
This file contains the integration test fixtures for documentation example scripts that are
under CI test.
"""

from tests.integration.backend_dependencies import BackendDependencies
from tests.integration.integration_test_fixture import IntegrationTestFixture

docs_tests = []

connecting_to_a_datasource = [
    # # Create a Data Source
    IntegrationTestFixture(
        # To test, run:
        # pytest --docs-tests --postgresql -k "create_a_datasource_postgres" tests/integration/test_script_runner.py
        name="create_a_datasource_postgres",
        user_flow_script="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_source/postgres.py",
        data_context_dir="docs/docusaurus/docs/components/_testing/test_data_contexts/postgres_datasource_credentials_in_file/great_expectations/",
        backend_dependencies=[BackendDependencies.POSTGRESQL],
    ),
    # Create a Data Asset
    IntegrationTestFixture(
        # To test, run:
        # pytest --docs-tests --postgresql -k "create_a_data_asset_postgres" tests/integration/test_script_runner.py
        name="create_a_data_asset_postgres",
        user_flow_script="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_data_asset/create_a_data_asset.py",
        data_context_dir="docs/docusaurus/docs/components/_testing/test_data_contexts/postgres_datasource_credentials_in_file/great_expectations/",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/",
        util_script="docs/docusaurus/docs/components/_testing/utility_scripts/postgres_data_setup.py",
        backend_dependencies=[BackendDependencies.POSTGRESQL],
    ),
    # Create a Batch Definition
    IntegrationTestFixture(
        # To test, run:
        # pytest --docs-tests --postgresql -k "create_a_batch_definition_postgres" tests/integration/test_script_runner.py
        name="create_a_batch_definition_postgres",
        user_flow_script="docs/docusaurus/docs/core/connect_to_data/sql_data/_create_a_batch_definition/create_a_batch_definition.py",
        data_context_dir="docs/docusaurus/docs/components/_testing/test_data_contexts/postgres_datasource_credentials_in_file/great_expectations/",
        data_dir="tests/test_sets/taxi_yellow_tripdata_samples/samples_2020",
        util_script="docs/docusaurus/docs/components/_testing/utility_scripts/postgres_preconfigured_data_asset.py",
        backend_dependencies=[BackendDependencies.POSTGRESQL],
    ),
]

# TODO: As we get these example tests working, uncomment/update to add them to CI.
expectation_tests = [
    # # Expectation example scripts
    # IntegrationTestFixture(
    #     name="create_an_expectation.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectations/_examples/create_an_expectation.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="edit_an_expectation.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectations/_examples/edit_an_expectation.py",
    #     backend_dependencies=[],
    # ),
    # # Expectation Suite example scripts
    # IntegrationTestFixture(
    #     name="add_expectations_to_an_expectation_suite.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/add_expectations_to_an_expectation_suite.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="create_an_expectation_suite.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/create_an_expectation_suite.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="delete_an_expectation_in_an_expectation_suite.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/delete_an_expectation_in_an_expectation_suite.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="delete_an_expectation_suite",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/delete_an_expectation_suite.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="edit_a_single_expectation.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/edit_a_single_expectation.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="edit_all_expectations_in_an_expectation_suite.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/edit_all_expectations_in_an_expectation_suite.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="get_a_specific_expectation_from_an_expectation_suite.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/get_a_specific_expectation_from_an_expectation_suite.py",
    #     backend_dependencies=[],
    # ),
    # IntegrationTestFixture(
    #     name="get_an_existing_expectation_suite.py",
    #     user_flow_script="docs/docusaurus/docs/core/_create_expectations/expectation_suites/_examples/get_an_existing_expectation_suite.py",
    #     backend_dependencies=[],
    # ),
]


learn_data_quality_use_cases = [
    # Schema.
    IntegrationTestFixture(
        name="data_quality_use_case_schema_expectations",
        user_flow_script="docs/docusaurus/docs/reference/learn/data_quality_use_cases/schema_resources/schema_expectations.py",
        data_dir="tests/test_sets/learn_data_quality_use_cases/",
        util_script="tests/test_utils.py",
        backend_dependencies=[BackendDependencies.POSTGRESQL],
    ),
    IntegrationTestFixture(
        name="data_quality_use_case_schema_validation_over_time",
        user_flow_script="docs/docusaurus/docs/reference/learn/data_quality_use_cases/schema_resources/schema_validation_over_time.py",
        data_dir="tests/test_sets/learn_data_quality_use_cases/",
        util_script="tests/test_utils.py",
        backend_dependencies=[BackendDependencies.POSTGRESQL],
    ),
    IntegrationTestFixture(
        name="data_quality_use_case_schema_strict_and_relaxed_validation",
        user_flow_script="docs/docusaurus/docs/reference/learn/data_quality_use_cases/schema_resources/schema_strict_and_relaxed.py",
        data_dir="tests/test_sets/learn_data_quality_use_cases/",
        util_script="tests/test_utils.py",
        backend_dependencies=[BackendDependencies.POSTGRESQL],
    ),
]

# Extend the docs_tests list with the above sublists (only the docs_tests list is imported
# into `test_script_runner.py` and actually used in CI checks).
docs_tests.extend(connecting_to_a_datasource)
docs_tests.extend(learn_data_quality_use_cases)
docs_tests.extend(expectation_tests)
