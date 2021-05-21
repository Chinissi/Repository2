from ruamel import yaml

import great_expectations as ge
from great_expectations.core.batch import RuntimeBatchRequest

context = ge.get_context()

datasource_yaml = f"""
name: taxi_datasource_with_runtime_data_connector
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
    default_runtime_data_connector_name:
        class_name: RuntimeDataConnector
        batch_identifiers:
            - default_identifier_name
"""

context.add_datasource(**yaml.load(datasource_yaml))

batch_request = RuntimeBatchRequest(
    datasource_name="taxi_datasource_with_runtime_data_connector",
    data_connector_name="default_runtime_data_connector_name",
    data_asset_name="<YOUR_MEANGINFUL_NAME>",  # this can be anything that identifies this data_asset for you
    runtime_parameters={"path": "<PATH_TO_YOUR_DATA_HERE>"},  # Add your path here.
    batch_identifiers={"default_identifier_name": "something_something"},
)

# Please note this override is only to provide good UX for docs and tests.
# In normal usage you'd set your path directly in the BatchRequest above.
batch_request.runtime_parameters[
    "path"
] = "./data/reports/yellow_tripdata_sample_2019-01.csv"

context.create_expectation_suite(
    expectation_suite_name="test_suite", overwrite_existing=True
)
validator = context.get_validator(
    batch_request=batch_request, expectation_suite_name="test_suite"
)
print(validator.head())

# Please note this is only for testing.
assert isinstance(validator, ge.validator.validator.Validator)
