.. _warning_and_failure_expectation_suites_validation_operator:

================================================================================
How to configure a WarningAndFailureExpectationSuitesValidationOperator
================================================================================

WarningAndFailureExpectationSuitesValidationOperator implements a business logic pattern that many data practitioners consider useful - grouping the expectations about a data asset into two expectation suites.

The "failure" expectation suite contains expectations that are considered important enough to stop the pipeline when they are violated. The rest of the expectations go into the "warning" expectation suite.


WarningAndFailureExpectationSuitesValidationOperator retrieves the two expectation suites ("failure" and "warning") for every data asset in the `assets_to_validate` argument of its `run` method. It does not require both suites to be present.

The operator invokes a list of actions on every validation result. The list is configured for the operator.
Each action in the list must be an instance of ValidationAction
class (or its descendants). Read more about actions here: :ref:`actions`.

After completing all the validations, it sends a Slack notification with the success status.


Configuration
--------------

Below is an example of this operator's configuration:

.. code-block:: yaml

    run_warning_and_failure_expectation_suites:
        class_name: WarningAndFailureExpectationSuitesValidationOperator

        # the following two properties are optional - by default the operator looks for
        # expectation suites named "failure" and "warning".
        # You can use these two properties to override these names.
        # e.g., with expectation_suite_name_prefix=boo_ and
        # expectation_suite_name_suffixes = ["red", "green"], the operator
        # will look for expectation suites named "boo_red" and "boo_green"
        expectation_suite_name_prefix="",
        expectation_suite_name_suffixes=["failure", "warning"],

        # optional - if true, the operator will stop and exit after first failed validation. false by default.
        stop_on_first_error=False,

        # put the actual webhook URL in the uncommitted/config_variables.yml file
        slack_webhook: ${validation_notification_slack_webhook}
        # optional - if "all" - notify always, "success" - notify only on success, "failure" - notify only on failure
        notify_on="all"

        # the operator will call the following actions on each validation result
        # you can remove or add actions to this list. See the details in the actions
        # reference
        action_list:
          - name: store_validation_result
            action:
              class_name: StoreValidationResultAction
              target_store_name: validations_store
          - name: store_evaluation_params
            action:
              class_name: StoreEvaluationParametersAction
              target_store_name: evaluation_parameter_store


Invocation
-----------

This is an example of invoking an instance of a Validation Operator from Python:

.. code-block:: python

    results = context.run_validation_operator(
        assets_to_validate=[batch0, batch1, ...],
        run_id=RunIdentifier(**{
          "run_name": "some_string_that_uniquely_identifies_this_run",
          "run_time": "2020-04-29T10:46:03.197008"  # optional run timestamp, defaults to current UTC datetime
        }),  # you may also pass in a dictionary with run_name and run_time keys
        validation_operator_name="operator_instance_name",
    )

* `assets_to_validate` - an iterable that specifies the data assets that the operator will validate. The members of the list can be either batches or triples that will allow the operator to fetch the batch: (data_asset_name, expectation_suite_name, batch_kwargs) using this method: :py:meth:`~great_expectations.data_context.BaseDataContext.get_batch`
* run_id - pipeline run id of type RunIdentifier, consisting of a run_time (always assumed to be UTC time) and run_name string that is meaningful to you and will help you refer to the result of this operation later
* validation_operator_name you can instances of a class that implements a Validation Operator

The `run` method returns a ValidationOperatorResult object.

The value of "success" is True if no critical expectation suites ("failure") failed to validate (non-critical warning") expectation suites are allowed to fail without affecting the success status of the run.

.. code-block:: json

    {
        "run_id": {"run_time": "20200527T041833.074212Z", "run_name": "my_run_name"},
        "success": True,
        "evaluation_parameters": None,
        "validation_operator_config": {
            "class_name": "WarningAndFailureExpectationSuitesValidationOperator",
            "module_name": "great_expectations.validation_operators",
            "name": "warning_and_failure_operator",
            "kwargs": {
                "action_list": [
                    {
                        "name": "store_validation_result",
                        "action": {"class_name": "StoreValidationResultAction"},
                    },
                    {
                        "name": "store_evaluation_params",
                        "action": {"class_name": "StoreEvaluationParametersAction"},
                    },
                    {
                        "name": "update_data_docs",
                        "action": {"class_name": "UpdateDataDocsAction"},
                    },
                ],
                "base_expectation_suite_name": ...,
                "expectation_suite_name_suffixes": ...,
                "stop_on_first_error": ...,
                "slack_webhook": ...,
                "notify_on": ...,
            },
        },
        "run_results": {
            ValidationResultIdentifier: {
                "validation_result": ExpectationSuiteValidationResult object,
                "expectation_suite_severity_level": "warning",
                "actions_results": {
                    "store_validation_result": {},
                    "store_evaluation_params": {},
                    "update_data_docs": {},
                },
            }
        }
    }



