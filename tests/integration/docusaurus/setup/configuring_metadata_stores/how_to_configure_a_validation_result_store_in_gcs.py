import os
import subprocess

from ruamel import yaml

import great_expectations as ge

context = ge.get_context()

# parse great_expectations.yml for comparison
great_expectations_yaml_file_path = os.path.join(
    context.root_directory, "great_expectations.yml"
)
with open(great_expectations_yaml_file_path, "r") as f:
    great_expectations_yaml = yaml.safe_load(f)

stores = great_expectations_yaml["stores"]
pop_stores = ["checkpoint_store", "evaluation_parameter_store", "expectations_store"]
for store in pop_stores:
    stores.pop(store)

actual_existing_validations_store = dict()
actual_existing_validations_store["stores"] = stores
actual_existing_validations_store["validations_store_name"] = great_expectations_yaml[
    "validations_store_name"
]

expected_existing_validations_store_yaml = """
stores:
  validations_store:
    class_name: ValidationsStore
    store_backend:
      class_name: TupleFilesystemStoreBackend
      base_directory: uncommitted/validations/

validations_store_name: validations_store
"""

assert actual_existing_validations_store == yaml.safe_load(
    expected_existing_validations_store_yaml
)

configured_validations_store_yaml = """
stores:
  validations_GCS_store:
    class_name: ValidationsStore
    store_backend:
      class_name: TupleGCSStoreBackend
      project: <YOUR GCP PROJECT NAME>
      bucket: <YOUR GCS BUCKET NAME>
      prefix: <YOUR GCS PREFIX NAME>

validations_store_name: validations_GCS_store
"""

# replace example code with integration test configuration
configured_validations_store = yaml.safe_load(configured_validations_store_yaml)
configured_validations_store["stores"]["validations_GCS_store"]["store_backend"][
    "project"
] = "superconductive-internal"
configured_validations_store["stores"]["validations_GCS_store"]["store_backend"][
    "bucket"
] = "superconductive-integration-tests"
configured_validations_store["stores"]["validations_GCS_store"]["store_backend"][
    "prefix"
] = "validations"

# add and set the new validation store
context.add_store(
    store_name=configured_validations_store["validations_store_name"],
    store_config=configured_validations_store["stores"]["validations_GCS_store"],
)
with open(great_expectations_yaml_file_path, "r") as f:
    great_expectations_yaml = yaml.safe_load(f)
great_expectations_yaml["validations_store_name"] = "validations_GCS_store"
great_expectations_yaml["stores"]["validations_GCS_store"]["store_backend"].pop(
    "suppress_store_backend_id"
)
with open(great_expectations_yaml_file_path, "w") as f:
    yaml.dump(great_expectations_yaml, f, default_flow_style=False)

expectation_suite_name = "my_expectation_suite"
context.create_expectation_suite(expectation_suite_name=expectation_suite_name)

# try gsutil cp command
copy_validation_command = """
gsutil cp uncommitted/validations/validation_1.json gs://<YOUR GCS BUCKET NAME>/<YOUR GCS PREFIX NAME>/validation_1.json
gsutil cp uncommitted/validations/validation_2.json gs://<YOUR GCS BUCKET NAME>/<YOUR GCS PREFIX NAME>/validation_2.json
"""

local_validation_1_file_path = os.path.join(
    context.root_directory, "validations", "validation_1.json"
)
local_validation_2_file_path = os.path.join(
    context.root_directory, "validations", "validation_1.json"
)
copy_validation_command = copy_validation_command.replace(
    "uncommitted/validations/validation_1.json", local_validation_1_file_path
)
copy_validation_command = copy_validation_command.replace(
    "uncommitted/validations/validation_2.json", local_validation_1_file_path
)
copy_validation_command = copy_validation_command.replace(
    "<YOUR GCS BUCKET NAME>",
    configured_validations_store["stores"]["validations_GCS_store"]["store_backend"][
        "bucket"
    ],
)
copy_validation_command = copy_validation_command.replace(
    "<YOUR GCS PREFIX NAME>/validation_1.json",
    configured_validations_store["stores"]["validations_GCS_store"]["store_backend"][
        "prefix"
    ]
    + "validation_1.json",
)
copy_validation_command = copy_validation_command.replace(
    "<YOUR GCS PREFIX NAME>/validation_2.json",
    configured_validations_store["stores"]["validations_GCS_store"]["store_backend"][
        "prefix"
    ]
    + "validation_1.json",
)

result = subprocess.run(
    copy_validation_command.strip().split(),
    check=True,
    stderr=subprocess.PIPE,
)
stderr = result.stderr.decode("utf-8")

copy_validation_output = """
Operation completed over 2 objects
"""

assert copy_validation_output.strip() in stderr

# list validation stores
list_validation_stores_command = """
great_expectations --v3-api store list
"""

try:
    result = subprocess.run(
        list_validation_stores_command.strip().split(),
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
except subprocess.CalledProcessError as e:
    exitcode, err = e.returncode, e.stderr
    print("exitcode:", exitcode, "stderr:", err)
stdout = result.stdout.decode("utf-8")

list_validation_stores_output = """
  - name: validations_GCS_store
    class_name: ValidationsStore
    store_backend:
      class_name: TupleGCSStoreBackend
      project: <YOUR GCP PROJECT NAME>
      bucket: <YOUR GCS BUCKET NAME>
      prefix: <YOUR GCS PREFIX NAME>
"""

assert "validations_GCS_store" in list_validation_stores_output
assert "validations_GCS_store" in stdout
assert "TupleGCSStoreBackend" in list_validation_stores_output
assert "TupleGCSStoreBackend" in stdout


