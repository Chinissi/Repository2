import datetime
import great_expectations as ge
import great_expectations.jupyter_ux
from great_expectations.data_context.types.resource_identifiers import ValidationResultIdentifier

context = ge.data_context.DataContext()

# Feel free to change the name of your suite here. Renaming this will not
# remove the other one.
expectation_suite_name = "{{ suite_name }}"
suite = context.get_expectation_suite(expectation_suite_name)
suite.expectations = []

batch_kwargs = {{ batch_kwargs }}
batch = context.get_batch(batch_kwargs, suite)
batch.head()
