import atexit
import datetime
import json
import logging
import platform
import signal
import sys
import threading
import time
from functools import wraps
from queue import Queue
from typing import Optional

import jsonschema
import requests

from great_expectations import __version__ as ge_version
from great_expectations.core import ExpectationSuite
from great_expectations.core.usage_statistics.anonymizers.anonymizer import Anonymizer
from great_expectations.core.usage_statistics.anonymizers.batch_anonymizer import (
    BatchAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.batch_request_anonymizer import (
    BatchRequestAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.checkpoint_run_anonymizer import (
    CheckpointRunAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.data_docs_site_anonymizer import (
    DataDocsSiteAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.datasource_anonymizer import (
    DatasourceAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.execution_engine_anonymizer import (
    ExecutionEngineAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.expectation_suite_anonymizer import (
    ExpectationSuiteAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.store_anonymizer import (
    StoreAnonymizer,
)
from great_expectations.core.usage_statistics.anonymizers.validation_operator_anonymizer import (
    ValidationOperatorAnonymizer,
)
from great_expectations.core.usage_statistics.schemas import (
    anonymized_usage_statistics_record_schema,
)
from great_expectations.core.util import nested_update, get_datetime_string_from_strftime_format
from great_expectations.data_context.types.base import CheckpointConfig

STOP_SIGNAL = object()

logger = logging.getLogger(__name__)

_anonymizers = {}


class UsageStatisticsHandler:
    def __init__(self, data_context, data_context_id, usage_statistics_url):
        self._url = usage_statistics_url

        self._data_context_id = data_context_id
        self._data_context_instance_id = data_context.instance_id
        self._data_context = data_context
        self._ge_version = ge_version

        self._message_queue = Queue()
        self._worker = threading.Thread(target=self._requests_worker, daemon=True)
        self._worker.start()
        self._datasource_anonymizer = DatasourceAnonymizer(data_context_id)
        self._execution_engine_anonymizer = ExecutionEngineAnonymizer(data_context_id)
        self._store_anonymizer = StoreAnonymizer(data_context_id)
        self._validation_operator_anonymizer = ValidationOperatorAnonymizer(
            data_context_id
        )
        self._data_docs_sites_anonymizer = DataDocsSiteAnonymizer(data_context_id)
        self._batch_request_anonymizer = BatchRequestAnonymizer(data_context_id)
        self._batch_anonymizer = BatchAnonymizer(data_context_id)
        self._expectation_suite_anonymizer = ExpectationSuiteAnonymizer(data_context_id)
        self._checkpoint_run_anonymizer = CheckpointRunAnonymizer(data_context_id)
        try:
            self._sigterm_handler = signal.signal(signal.SIGTERM, self._teardown)
        except ValueError:
            # if we are not the main thread, we don't get to ask for signal handling.
            self._sigterm_handler = None
        try:
            self._sigint_handler = signal.signal(signal.SIGINT, self._teardown)
        except ValueError:
            # if we are not the main thread, we don't get to ask for signal handling.
            self._sigint_handler = None

        atexit.register(self._close_worker)

    def _teardown(self, signum: int, frame):
        self._close_worker()
        if signum == signal.SIGTERM and self._sigterm_handler:
            self._sigterm_handler(signum, frame)
        if signum == signal.SIGINT and self._sigint_handler:
            self._sigint_handler(signum, frame)

    def _close_worker(self):
        self._message_queue.put(STOP_SIGNAL)
        self._worker.join()

    def _requests_worker(self):
        session = requests.Session()
        while True:
            message = self._message_queue.get()
            if message == STOP_SIGNAL:
                self._message_queue.task_done()
                return
            try:
                res = session.post(self._url, json=message, timeout=2)
                logger.debug(
                    "Posted usage stats: message status " + str(res.status_code)
                )
                if res.status_code != 201:
                    logger.debug(
                        "Server rejected message: ", json.dumps(message, indent=2)
                    )
            except requests.exceptions.Timeout:
                logger.debug("Timeout while sending usage stats message.")
            except Exception as e:
                logger.debug("Unexpected error posting message: " + str(e))
            finally:
                self._message_queue.task_done()

    def build_init_payload(self):
        """Adds information that may be available only after full data context construction, but is useful to
        calculate only one time (for example, anonymization)."""
        expectation_suites = [
            self._data_context.get_expectation_suite(expectation_suite_name)
            for expectation_suite_name in self._data_context.list_expectation_suite_names()
        ]
        return {
            "platform.system": platform.system(),
            "platform.release": platform.release(),
            "version_info": str(sys.version_info),
            "anonymized_datasources": [
                self._datasource_anonymizer.anonymize_datasource_info(
                    datasource_name, datasource_config
                )
                for datasource_name, datasource_config in self._data_context.project_config_with_variables_substituted.datasources.items()
            ],
            "anonymized_stores": [
                self._store_anonymizer.anonymize_store_info(store_name, store_obj)
                for store_name, store_obj in self._data_context.stores.items()
            ],
            "anonymized_validation_operators": [
                self._validation_operator_anonymizer.anonymize_validation_operator_info(
                    validation_operator_name=validation_operator_name,
                    validation_operator_obj=validation_operator_obj,
                )
                for validation_operator_name, validation_operator_obj in self._data_context.validation_operators.items()
            ],
            "anonymized_data_docs_sites": [
                self._data_docs_sites_anonymizer.anonymize_data_docs_site_info(
                    site_name=site_name, site_config=site_config
                )
                for site_name, site_config in self._data_context.project_config_with_variables_substituted.data_docs_sites.items()
            ],
            "anonymized_expectation_suites": [
                self._expectation_suite_anonymizer.anonymize_expectation_suite_info(
                    expectation_suite
                )
                for expectation_suite in expectation_suites
            ],
        }

    def build_envelope(self, message):
        message["version"] = "1.0.0"
        message["ge_version"] = self._ge_version

        message["data_context_id"] = self._data_context_id
        message["data_context_instance_id"] = self._data_context_instance_id

        message["event_time"] = (
            datetime.datetime.now(datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%S.%f"
            )[:-3]
            + "Z"
        )

        event_duration_property_name: str = f'{message["event_name"]}.duration'.replace(
            ".", "_"
        )
        if hasattr(self, event_duration_property_name):
            delta_t: int = getattr(self, event_duration_property_name)
            message["event_duration"] = delta_t

        return message

    @staticmethod
    def validate_message(message, schema):
        try:
            jsonschema.validate(message, schema=schema)
            return True
        except jsonschema.ValidationError as e:
            logger.debug("invalid message: " + str(e))
            return False

    def send_usage_message(
        self,
        event: str,
        event_payload: Optional[dict] = None,
        success: Optional[bool] = None,
    ):
        """send a usage statistics message."""
        # noinspection PyBroadException
        try:
            message: dict = {
                "event": event,
                "event_payload": event_payload or {},
                "success": success,
            }
            self.emit(message)
        except Exception:
            pass

    def emit(self, message):
        """
        Emit a message.
        """
        try:
            if message["event"] == "data_context.__init__":
                message["event_payload"] = self.build_init_payload()
            message = self.build_envelope(message=message)
            if not self.validate_message(
                message, schema=anonymized_usage_statistics_record_schema
            ):
                return
            self._message_queue.put(message)
        # noinspection PyBroadException
        except Exception as e:
            # We *always* tolerate *any* error in usage statistics
            logger.debug(e)


def get_usage_statistics_handler(args_array):
    try:
        # If the object is usage_statistics-capable, then it will have a usage_statistics_handler
        handler = getattr(args_array[0], "_usage_statistics_handler", None)
        if handler is not None and not isinstance(handler, UsageStatisticsHandler):
            logger.debug("Invalid UsageStatisticsHandler found on object.")
            handler = None
    except IndexError:
        # A wrapped method that is not an object; this would be erroneous usage
        logger.debug(
            "usage_statistics enabled decorator should only be used on data context methods"
        )
        handler = None
    except AttributeError:
        # A wrapped method that is not usage_statistics capable
        handler = None
    except Exception as e:
        # An unknown error -- but we still fail silently
        logger.debug(
            "Unrecognized error when trying to find usage_statistics_handler: " + str(e)
        )
        handler = None
    return handler


def usage_statistics_enabled_method(
    func=None, event_name=None, args_payload_fn=None, result_payload_fn=None
):
    """
    A decorator for usage statistics which defaults to the less detailed payload schema.
    """
    if callable(func):
        if event_name is None:
            event_name = func.__name__

        @wraps(func)
        def usage_statistics_wrapped_method(*args, **kwargs):
            # if a function like `build_data_docs()` is being called as a `dry_run`
            # then we dont want to emit usage_statistics. We just return the function without sending a usage_stats message
            if "dry_run" in kwargs and kwargs["dry_run"]:
                return func(*args, **kwargs)
            # Set event_payload now so it can be updated below
            event_payload = {}
            message = {"event_payload": event_payload, "event": event_name}
            result = None
            time_begin: int = int(round(time.time() * 1000))
            try:
                if args_payload_fn is not None:
                    nested_update(event_payload, args_payload_fn(*args, **kwargs))

                result = func(*args, **kwargs)
                message["success"] = True
            except Exception:
                message["success"] = False
                raise
            finally:
                if not ((result is None) or (result_payload_fn is None)):
                    nested_update(event_payload, result_payload_fn(result))

                time_end: int = int(round(time.time() * 1000))
                delta_t: int = time_end - time_begin

                handler = get_usage_statistics_handler(args)
                if handler:
                    event_duration_property_name: str = (
                        f"{event_name}.duration".replace(".", "_")
                    )
                    setattr(handler, event_duration_property_name, delta_t)
                    handler.emit(message)
                    delattr(handler, event_duration_property_name)

            return result

        return usage_statistics_wrapped_method
    else:

        # noinspection PyShadowingNames
        def usage_statistics_wrapped_method_partial(func):
            return usage_statistics_enabled_method(
                func,
                event_name=event_name,
                args_payload_fn=args_payload_fn,
                result_payload_fn=result_payload_fn,
            )

        return usage_statistics_wrapped_method_partial


# noinspection PyUnusedLocal
def run_validation_operator_usage_statistics(
    data_context,
    validation_operator_name,
    assets_to_validate,
    **kwargs,
):
    try:
        data_context_id = data_context.data_context_id
    except AttributeError:
        data_context_id = None
    anonymizer = _anonymizers.get(data_context_id, None)
    if anonymizer is None:
        anonymizer = Anonymizer(data_context_id)
        _anonymizers[data_context_id] = anonymizer
    payload = {}
    try:
        payload["anonymized_operator_name"] = anonymizer.anonymize(
            validation_operator_name
        )
    except TypeError:
        logger.debug(
            "run_validation_operator_usage_statistics: Unable to create validation_operator_name hash"
        )
    if data_context._usage_statistics_handler:
        # noinspection PyBroadException
        try:
            batch_anonymizer = data_context._usage_statistics_handler._batch_anonymizer
            payload["anonymized_batches"] = [
                batch_anonymizer.anonymize_batch_info(batch)
                for batch in assets_to_validate
            ]
        except Exception:
            logger.debug(
                "run_validation_operator_usage_statistics: Unable to create anonymized_batches payload field"
            )

    return payload


# noinspection SpellCheckingInspection
# noinspection PyUnusedLocal
def save_expectation_suite_usage_statistics(
    data_context,
    expectation_suite,
    expectation_suite_name=None,
    **kwargs,
):
    try:
        data_context_id = data_context.data_context_id
    except AttributeError:
        data_context_id = None
    anonymizer = _anonymizers.get(data_context_id, None)
    if anonymizer is None:
        anonymizer = Anonymizer(data_context_id)
        _anonymizers[data_context_id] = anonymizer
    payload = {}

    if expectation_suite_name is None:
        if isinstance(expectation_suite, ExpectationSuite):
            expectation_suite_name = expectation_suite.expectation_suite_name
        elif isinstance(expectation_suite, dict):
            expectation_suite_name = expectation_suite.get("expectation_suite_name")

    # noinspection PyBroadException
    try:
        payload["anonymized_expectation_suite_name"] = anonymizer.anonymize(
            expectation_suite_name
        )
    except Exception:
        logger.debug(
            "save_expectation_suite_usage_statistics: Unable to create anonymized_expectation_suite_name payload field"
        )

    return payload


def edit_expectation_suite_usage_statistics(data_context, expectation_suite_name):
    try:
        data_context_id = data_context.data_context_id
    except AttributeError:
        data_context_id = None
    anonymizer = _anonymizers.get(data_context_id, None)
    if anonymizer is None:
        anonymizer = Anonymizer(data_context_id)
        _anonymizers[data_context_id] = anonymizer
    payload = {}

    # noinspection PyBroadException
    try:
        payload["anonymized_expectation_suite_name"] = anonymizer.anonymize(
            expectation_suite_name
        )
    except Exception:
        logger.debug(
            "edit_expectation_suite_usage_statistics: Unable to create anonymized_expectation_suite_name payload field"
        )

    return payload


def add_datasource_usage_statistics(data_context, name, **kwargs):
    if not data_context._usage_statistics_handler:
        return {}
    try:
        data_context_id = data_context.data_context_id
    except AttributeError:
        data_context_id = None

    # noinspection PyBroadException
    try:
        datasource_anonymizer = (
            data_context._usage_statistics_handler._datasource_anonymizer
        )
    except Exception:
        datasource_anonymizer = DatasourceAnonymizer(data_context_id)

    payload = {}
    # noinspection PyBroadException
    try:
        payload = datasource_anonymizer.anonymize_datasource_info(name, kwargs)
    except Exception:
        logger.debug(
            "add_datasource_usage_statistics: Unable to create add_datasource_usage_statistics payload field"
        )

    return payload


# noinspection SpellCheckingInspection
def get_batch_list_usage_statistics(data_context, *args, **kwargs):
    try:
        data_context_id = data_context.data_context_id
    except AttributeError:
        data_context_id = None
    anonymizer = _anonymizers.get(data_context_id, None)
    if anonymizer is None:
        anonymizer = Anonymizer(data_context_id)
        _anonymizers[data_context_id] = anonymizer
    payload = {}

    if data_context._usage_statistics_handler:
        # noinspection PyBroadException
        try:
            batch_request_anonymizer: BatchRequestAnonymizer = (
                data_context._usage_statistics_handler._batch_request_anonymizer
            )
            payload = batch_request_anonymizer.anonymize_batch_request(*args, **kwargs)
        except Exception:
            logger.debug(
                "get_batch_list_usage_statistics: Unable to create anonymized_batch_request payload field"
            )

    return payload


def get_checkpoint_run_usage_statistics(checkpoint, *args, **kwargs):
    print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT_OBJ-0: {checkpoint} ; TYPE: {str(type(checkpoint))}')
    # TODO: <Alex>ALEX</Alex>
    a = hasattr(checkpoint, "_substituted_config")
    # TODO: <Alex>ALEX</Alex>
    print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT.SUBSTITUTED_CONFIG_EXISTS-0: {a} ; TYPE: {str(type(a))}')
    try:
        data_context_id = checkpoint.data_context.data_context_id
    except AttributeError:
        data_context_id = None
    anonymizer = _anonymizers.get(data_context_id, None)
    if anonymizer is None:
        anonymizer = Anonymizer(data_context_id)
        _anonymizers[data_context_id] = anonymizer
    payload = {}

    if checkpoint._usage_statistics_handler:
        # noinspection PyBroadException
        try:
            checkpoint_run_anonymizer: CheckpointRunAnonymizer = (
                checkpoint._usage_statistics_handler._checkpoint_run_anonymizer
            )
            # TODO: <Alex>ALEX</Alex>
            # args = args + (checkpoint,)
            # TODO: <Alex>ALEX</Alex>
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] ARGS-BEFORE-BEFORE-BEFORE-BEFORE-BEFORE: {args} ; TYPE: {str(type(args))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] KWARGS-BEFORE-BEFORE-BEFORE-BEFORE-BEFORE: {kwargs} ; TYPE: {str(type(kwargs))}')
            # TODO: <Alex>ALEX</Alex>
            # pos_args: tuple = copy.deepcopy(args)
            # kw_args: dict = copy.deepcopy(kwargs)
            # resolved_runtime_kwargs: dict = (
            #     checkpoint.resolve_config_using_acceptable_arguments(*pos_args, **kw_args)
            # )
            # TODO: <Alex>ALEX</Alex>
            # resolved_runtime_kwargs: dict
            # TODO: <Alex>ALEX</Alex>
            # TODO: <Alex>ALEX</Alex>
            # substituted_runtime_config: CheckpointConfig
            # TODO: <Alex>ALEX</Alex>
            # TODO: <Alex>ALEX</Alex>
            # resolved_runtime_kwargs, substituted_runtime_config = checkpoint.resolve_config_using_acceptable_arguments(*args, **kwargs)
            # TODO: <Alex>ALEX</Alex>
            substituted_runtime_config: CheckpointConfig = checkpoint.resolve_config_using_acceptable_arguments(*args, **kwargs)
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG-COMPUTED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!****************')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG: ; TYPE: {str(type(substituted_runtime_config))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG.TO_JSON_DICT():\n{substituted_runtime_config.to_json_dict()}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG:\n{substituted_runtime_config} ; TYPE: {str(type(substituted_runtime_config))}')
            resolved_runtime_kwargs: dict = substituted_runtime_config.to_json_dict()
            # TODO: <Alex>ALEX</Alex>
            # print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_CONFIG: {substituted_runtime_config} ; TYPE: {str(type(substituted_runtime_config))}')
            # TODO: <Alex>ALEX</Alex>
            # resolved_runtime_kwargs, substituted_runtime_config = resolve_checkpoint_config(*args, **kwargs)
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] RESOLVED_RUNTIME_KWARGS-COMPUTED!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!****************')
            print( f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT_OBJ-1: {checkpoint} ; TYPE: {str(type(checkpoint))}')
            # TODO: <Alex>ALEX</Alex>
            # resolved_runtime_kwargs: dict = {}
            # TODO: <Alex>ALEX</Alex>
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] RESOLVED_RUNTIME_KWARGS: {resolved_runtime_kwargs} ; TYPE: {str(type(resolved_runtime_kwargs))}')
            # print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG: {substituted_runtime_config} ; TYPE: {str(type(substituted_runtime_config))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT.SUBSTITUTED_CONFIG: {checkpoint._substituted_config} ; TYPE: {str(type(checkpoint._substituted_config))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT_OBJ-2: {checkpoint} ; TYPE: {str(type(checkpoint))}')
            # TODO: <Alex>ALEX</Alex>
            # TODO: <Alex>ALEX</Alex>
            a = hasattr(checkpoint, "_substituted_config")
            # TODO: <Alex>ALEX</Alex>
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT.SUBSTITUTED_CONFIG_EXISTS-1: {a} ; TYPE: {str(type(a))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG: ; TYPE: {str(type(substituted_runtime_config))}')
            # print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG.TO_JSON_DICT: {substituted_runtime_config.to_json_dict()} ; TYPE: {str(type(substituted_runtime_config.to_json_dict()))}')
            # print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] SUBSTITUTED_RUNTIME_CONFIG: {substituted_runtime_config} ; TYPE: {str(type(substituted_runtime_config))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT.SUBSTITUTED_CONFIG: ; TYPE: {str(type(checkpoint._substituted_config))}')
            print( f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT_OBJ-3: {checkpoint} ; TYPE: {str(type(checkpoint))}')
            # print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] CHECKPOINT.SUBSTITUTED_CONFIG: {checkpoint._substituted_config} ; TYPE: {str(type(checkpoint._substituted_config))}')
            # TODO: <Alex>ALEX</Alex>
            # checkpoint._substituted_config.update(other_config=substituted_runtime_config)
            # TODO: <Alex>ALEX</Alex>
            # TODO: <Alex>ALEX</Alex>
            payload = checkpoint_run_anonymizer.anonymize_checkpoint_run(
                *(checkpoint,), **resolved_runtime_kwargs
            )
            # TODO: <Alex>ALEX</Alex>
            # payload = checkpoint_run_anonymizer.anonymize_checkpoint_run(
            #     *args, **kwargs
            # )
            # TODO: <Alex>ALEX</Alex>
            # kwargs.update(resolved_runtime_kwargs)
            # TODO: <Alex>ALEX</Alex>
            # checkpoint._substituted_config = substituted_runtime_config
            # TODO: <Alex>ALEX</Alex>
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] PAYLOAD-COMPUTED!!!-AFTER-AFTER-AFTER-AFTER:\n{payload} ; TYPE: {str(type(payload))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] ARGS-AFTER-AFTER-AFTER-AFTER-AFTER: {args} ; TYPE: {str(type(args))}')
            print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] KWARGS-AFTER-AFTER-AFTER-AFTER: {kwargs} ; TYPE: {str(type(kwargs))}')
            # TODO: <Alex>ALEX</Alex>
        except Exception:
            logger.debug(
                "get_batch_list_usage_statistics: Unable to create anonymized_checkpoint_run payload field"
            )

    print(f'\n[ALEX_TEST] [GET_CHECKPOINT_RUN_USAGE_STATISTICS] PAYLOAD-RETURNING!!!-AFTER-AFTER-AFTER-AFTER:\n{payload} ; TYPE: {str(type(payload))}')
    return payload


# # TODO: <Alex>ALEX</Alex>
# def resolve_checkpoint_config(
#     checkpoint: Checkpoint,
#     template_name: Optional[str] = None,
#     run_name_template: Optional[str] = None,
#     expectation_suite_name: Optional[str] = None,
#     batch_request: Optional[Union[dict, BatchRequest]] = None,
#     action_list: Optional[List[dict]] = None,
#     evaluation_parameters: Optional[dict] = None,
#     runtime_configuration: Optional[dict] = None,
#     validations: Optional[List[dict]] = None,
#     profilers: Optional[List[dict]] = None,
#     run_id: Optional[Union[str, RunIdentifier]] = None,
#     run_name: Optional[str] = None,
#     run_time: Optional[Union[str, datetime.datetime]] = None,
#     result_format: Optional[Union[str, dict]] = None,
#     expectation_suite_ge_cloud_id: Optional[str] = None,
# ) -> Tuple[dict, CheckpointConfig]:
#     print(f'\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] BATCH_REQUEST:\n{batch_request} ; TYPE: {str(type(batch_request))}')
#     assert not (run_id and run_name) and not (
#         run_id and run_time
#     ), "Please provide either a run_id or run_name and/or run_time."
#
#     run_time = run_time or datetime.datetime.now()
#     runtime_configuration = runtime_configuration or {}
#     result_format = result_format or runtime_configuration.get("result_format")
#
#     batch_request, validations = get_batch_request_dict(
#         batch_request=batch_request, validations=validations
#     )
#     print(f'\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] BATCH_REQUEST-UPDATED:\n{batch_request} ; TYPE: {str(type(batch_request))}')
#
#     runtime_kwargs: dict = {
#         "template_name": template_name,
#         "run_name_template": run_name_template,
#         "expectation_suite_name": expectation_suite_name,
#         "batch_request": batch_request,
#         "action_list": action_list,
#         "evaluation_parameters": evaluation_parameters,
#         "runtime_configuration": runtime_configuration,
#         "validations": validations,
#         "profilers": profilers,
#         "expectation_suite_ge_cloud_id": expectation_suite_ge_cloud_id,
#     }
#     # TODO: <Alex>ALEX</Alex>
#     substituted_runtime_config: CheckpointConfig = checkpoint.get_substituted_config(
#         runtime_kwargs=runtime_kwargs
#     )
#     # TODO: <Alex>ALEX</Alex>
#     run_name_template = substituted_runtime_config.run_name_template
#     validations = substituted_runtime_config.validations
#     batch_request = substituted_runtime_config.batch_request
#     print(f'\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] BATCH_REQUEST-SUBSTITUTED:\n{batch_request} ; TYPE: {str(type(batch_request))}')
#     if len(validations) == 0 and not batch_request:
#         raise ge_exceptions.CheckpointError(
#             f'Checkpoint "{checkpoint.name}" must contain either a batch_request or validations.'
#         )
#
#     if run_name is None and run_name_template is not None:
#         run_name = get_datetime_string_from_strftime_format(
#             format_str=run_name_template, datetime_obj=run_time
#         )
#
#     run_id = run_id or RunIdentifier(run_name=run_name, run_time=run_time)
#
#     validation_dict: dict
#
#     for validation_dict in validations:
#         substituted_validation_dict: dict = get_substituted_validation_dict(
#             substituted_runtime_config=substituted_runtime_config,
#             validation_dict=validation_dict,
#         )
#         validation_batch_request: BatchRequest = substituted_validation_dict.get(
#             "batch_request"
#         )
#         validation_dict["batch_request"] = validation_batch_request
#         validation_expectation_suite_name: str = substituted_validation_dict.get(
#             "expectation_suite_name"
#         )
#         validation_dict["expectation_suite_name"] = validation_expectation_suite_name
#         validation_expectation_suite_ge_cloud_id: str = substituted_validation_dict.get(
#             "expectation_suite_ge_cloud_id"
#         )
#         validation_dict["expectation_suite_ge_cloud_id"] = validation_expectation_suite_ge_cloud_id
#         validation_action_list: list = substituted_validation_dict.get("action_list")
#         validation_dict["action_list"] = validation_action_list
#
#     runtime_kwargs.update(
#         {
#             "run_name_template": run_name_template,
#             "batch_request": batch_request,
#             "validations": validations,
#             "run_id": run_id,
#             # TODO: <Alex>ALEX</Alex>
#             # "run_name": run_name,
#             # "run_time": run_time,
#             # TODO: <Alex>ALEX</Alex>
#             "result_format": result_format,
#         }
#     )
#     print(f"\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] RUN_ID: {run_id} ; TYPE: {str(type(run_id))}")
#     print(f"\n[ALX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] RUN_NAME: {run_name} ; TYPE: {str(type(run_name))}")
#     print(f"\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] RUN_TIME: {run_time} ; TYPE: {str(type(run_time))}")
#
#     print(f"\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] RUNTIME_KWARGS:\n{runtime_kwargs} ; TYPE: {str(type(runtime_kwargs))}")
#     # deep_filter_properties_iterable(
#     #     properties=runtime_kwargs,
#     #     clean_falsy=True,
#     #     inplace=True,
#     # )
#     # print(f"\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] RUNTIME_KWARGS-DEEP_CLEANED:\n{runtime_kwargs} ; TYPE: {str(type(runtime_kwargs))}")
#
#     # TODO: <Alex>ALEX</Alex>
#     # runtime_kwargs["substituted_runtime_config"] = substituted_runtime_config
#     # TODO: <Alex>ALEX</Alex>
#     print(f'\n[ALEX_TEST] [CHECKPOINT.RESOLVE_CONFIG_USING_ACCEPTABLE_ARGUMENTS] BATCH_REQUEST-AT_RETURN:\n{runtime_kwargs["batch_request"]} ; TYPE: {str(type(runtime_kwargs["batch_request"]))}')
#
#     return runtime_kwargs, substituted_runtime_config


def send_usage_message(
    data_context,
    event: str,
    event_payload: Optional[dict] = None,
    success: Optional[bool] = None,
):
    """send a usage statistics message."""
    # noinspection PyBroadException
    try:
        handler: UsageStatisticsHandler = getattr(
            data_context, "_usage_statistics_handler", None
        )
        message: dict = {
            "event": event,
            "event_payload": event_payload,
            "success": success,
        }
        if handler is not None:
            handler.emit(message)
    except Exception:
        pass
