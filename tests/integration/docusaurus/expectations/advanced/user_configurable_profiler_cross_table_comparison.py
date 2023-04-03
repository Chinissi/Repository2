# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py imports">
import great_expectations as gx
from great_expectations.core.batch import BatchRequest
from great_expectations.core.yaml_handler import YAMLHandler
from great_expectations.profile.user_configurable_profiler import (
    UserConfigurableProfiler,
)

yaml = YAMLHandler()
context = gx.get_context()
# </snippet>

# This utility is not for general use. It is only to support testing.
from tests.test_utils import load_data_into_test_database

# The following load & config blocks up until the batch requests are only to support testing.
MY_CONNECTION_STRING = "mysql+pymysql://root@localhost/test_ci"

PG_CONNECTION_STRING = "postgresql+psycopg2://postgres:@localhost/test_ci"

load_data_into_test_database(
    table_name="mysql_taxi_data",
    csv_path="./data/yellow_tripdata_sample_2019-01.csv",
    connection_string=MY_CONNECTION_STRING,
)

load_data_into_test_database(
    table_name="postgres_taxi_data",
    csv_path="./data/yellow_tripdata_sample_2019-01.csv",
    connection_string=PG_CONNECTION_STRING,
)

pg_datasource_config = {
    "name": "my_postgresql_datasource",
    "class_name": "Datasource",
    "execution_engine": {
        "class_name": "SqlAlchemyExecutionEngine",
        "connection_string": f"{PG_CONNECTION_STRING}",
    },
    "data_connectors": {
        "default_inferred_data_connector_name": {
            "class_name": "InferredAssetSqlDataConnector",
            "include_schema_name": True,
        },
    },
}

mysql_datasource_config = {
    "name": "my_mysql_datasource",
    "class_name": "Datasource",
    "execution_engine": {
        "class_name": "SqlAlchemyExecutionEngine",
        "connection_string": f"{MY_CONNECTION_STRING}",
    },
    "data_connectors": {
        "default_inferred_data_connector_name": {
            "class_name": "InferredAssetSqlDataConnector",
            "include_schema_name": True,
        },
    },
}

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml.
pg_datasource_config["execution_engine"]["connection_string"] = PG_CONNECTION_STRING

context.test_yaml_config(yaml.dump(pg_datasource_config))

context.add_datasource(**pg_datasource_config)

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the yaml.
mysql_datasource_config["execution_engine"]["connection_string"] = MY_CONNECTION_STRING

context.test_yaml_config(yaml.dump(mysql_datasource_config))

context.add_datasource(**mysql_datasource_config)

# Tutorial content resumes here.
# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py mysql_batch_request">
mysql_batch_request = BatchRequest(
    datasource_name="my_mysql_datasource",
    data_connector_name="default_inferred_data_connector_name",
    data_asset_name="test_ci.mysql_taxi_data",
)
# </snippet>
# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py pg_batch_request">
pg_batch_request = BatchRequest(
    datasource_name="my_postgresql_datasource",
    data_connector_name="default_inferred_data_connector_name",
    data_asset_name="public.postgres_taxi_data",
)
# </snippet>
# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py get_validator">
validator = context.get_validator(batch_request=mysql_batch_request)
# </snippet>
# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py profiler">
profiler = UserConfigurableProfiler(
    profile_dataset=validator,
    excluded_expectations=[
        "expect_column_quantile_values_to_be_between",
        "expect_column_mean_to_be_between",
    ],
)
# </snippet>
# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py build_suite">
expectation_suite_name = "compare_two_tables"
suite = profiler.build_suite()
suite.expectation_suite_name = expectation_suite_name
context.add_expectation_suite(expectation_suite=suite)
# </snippet>
# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py checkpoint_config">
my_checkpoint_name = "comparison_checkpoint"

yaml_config = f"""
name: {my_checkpoint_name}
config_version: 1.0
class_name: SimpleCheckpoint
run_name_template: "%Y%m%d-%H%M%S-my-run-name-template"
expectation_suite_name: {expectation_suite_name}
"""

context.add_or_update_checkpoint(**yaml.load(yaml_config))
# </snippet>
# <snippet name="tests/integration/docusaurus/expectations/advanced/user_configurable_profiler_cross_table_comparison.py run_checkpoint">
results = context.run_checkpoint(
    checkpoint_name=my_checkpoint_name, batch_request=pg_batch_request
)
# </snippet>

# Note to users: code below this line is only for integration testing -- ignore!

assert results["success"] is True
statistics = results["run_results"][list(results["run_results"].keys())[0]][
    "validation_result"
]["statistics"]
assert statistics["evaluated_expectations"] != 0
assert statistics["evaluated_expectations"] == statistics["successful_expectations"]
assert statistics["unsuccessful_expectations"] == 0
assert statistics["success_percent"] == 100.0
