import datetime
import json
import logging
from copy import deepcopy
from typing import Dict, Optional, Union

try:
    from typing import TypedDict
except ImportError:
    # Fallback for python < 3.8
    from typing_extensions import TypedDict

from uuid import UUID

import great_expectations.exceptions as ge_exceptions
from great_expectations import __version__ as ge_version
from great_expectations.core.batch import BatchDefinition, BatchMarkers
from great_expectations.core.expectation_configuration import (
    ExpectationConfigurationSchema,
)
from great_expectations.core.id_dict import BatchSpec
from great_expectations.core.run_identifier import RunIdentifier
from great_expectations.core.util import (
    convert_to_json_serializable,
    ensure_json_serializable,
    in_jupyter_notebook,
)
from great_expectations.data_context.util import instantiate_class_from_config
from great_expectations.exceptions import ClassInstantiationError
from great_expectations.marshmallow__shade import (
    Schema,
    fields,
    post_dump,
    post_load,
    pre_dump,
)
from great_expectations.render.types import (
    RenderedAtomicContent,
    RenderedAtomicContentSchema,
)
from great_expectations.types import SerializableDictDot

logger = logging.getLogger(__name__)


def get_metric_kwargs_id(metric_name, metric_kwargs):
    ###
    #
    # WARNING
    # WARNING
    # THIS IS A PLACEHOLDER UNTIL WE HAVE REFACTORED EXPECTATIONS TO HANDLE THIS LOGIC THEMSELVES
    # WE ARE NO WORSE OFF THAN THE PREVIOUS SYSTEM, BUT NOT FULLY CUSTOMIZABLE
    # WARNING
    # WARNING
    #
    ###
    if "metric_kwargs_id" in metric_kwargs:
        return metric_kwargs["metric_kwargs_id"]
    if "column" in metric_kwargs:
        return f"column={metric_kwargs.get('column')}"
    return None


class ExpectationValidationResult(SerializableDictDot):
    def __init__(
        self,
        success: Optional[bool] = None,
        expectation_config: Optional["ExpectationConfiguration"] = None,  # noqa: F821
        result: Optional[dict] = None,
        meta: Optional[dict] = None,
        exception_info: Optional[dict] = None,
        rendered_content: Optional[RenderedAtomicContent] = None,
        **kwargs: dict,
    ) -> None:
        if result and not self.validate_result_dict(result):
            raise ge_exceptions.InvalidCacheValueError(result)
        self.success = success
        self.expectation_config = expectation_config
        # TODO: re-add
        # assert_json_serializable(result, "result")
        if result is None:
            result = {}
        self.result = result
        if meta is None:
            meta = {}
        # We require meta information to be serializable, but do not convert until necessary
        ensure_json_serializable(meta)
        self.meta = meta
        self.exception_info = exception_info or {
            "raised_exception": False,
            "exception_traceback": None,
            "exception_message": None,
        }
        self.rendered_content = rendered_content

    def __eq__(self, other):
        """ExpectationValidationResult equality ignores instance identity, relying only on properties."""
        # NOTE: JPC - 20200213 - need to spend some time thinking about whether we want to
        # consistently allow dict as a comparison alternative in situations like these...
        # if isinstance(other, dict):
        #     try:
        #         other = ExpectationValidationResult(**other)
        #     except ValueError:
        #         return NotImplemented
        if not isinstance(other, self.__class__):
            # Delegate comparison to the other instance's __eq__.
            return NotImplemented
        try:
            if self.result and other.result:
                common_keys = set(self.result.keys()) & other.result.keys()
                result_dict = self.to_json_dict()["result"]
                other_result_dict = other.to_json_dict()["result"]
                contents_equal = all(
                    [result_dict[k] == other_result_dict[k] for k in common_keys]
                )
            else:
                contents_equal = False

            return all(
                (
                    self.success == other.success,
                    (
                        self.expectation_config is None
                        and other.expectation_config is None
                    )
                    or (
                        self.expectation_config is not None
                        and self.expectation_config.isEquivalentTo(
                            other=other.expectation_config, match_type="success"
                        )
                    ),
                    # Result is a dictionary allowed to have nested dictionaries that are still of complex types (e.g.
                    # numpy) consequently, series' comparison can persist. Wrapping in all() ensures comparison is
                    # handled appropriately.
                    not (self.result or other.result) or contents_equal,
                    self.meta == other.meta,
                    self.exception_info == other.exception_info,
                )
            )
        except (ValueError, TypeError):
            # if invalid comparisons are attempted, the objects are not equal.
            return False

    def __ne__(self, other):
        # Negated implementation of '__eq__'. TODO the method should be deleted when it will coincide with __eq__.
        # return not self == other
        if not isinstance(other, self.__class__):
            # Delegate comparison to the other instance's __ne__.
            return NotImplemented
        try:
            return any(
                (
                    self.success != other.success,
                    (
                        self.expectation_config is None
                        and other.expectation_config is not None
                    )
                    or (
                        self.expectation_config is not None
                        and not self.expectation_config.isEquivalentTo(
                            other.expectation_config
                        )
                    ),
                    # TODO should it be wrapped in all()/any()? Since it is the only difference to __eq__:
                    (self.result is None and other.result is not None)
                    or (self.result != other.result),
                    self.meta != other.meta,
                    self.exception_info != other.exception_info,
                )
            )
        except (ValueError, TypeError):
            # if invalid comparisons are attempted, the objects are not equal.
            return True

    def __repr__(self) -> str:
        """
        # TODO: <Alex>5/9/2022</Alex>
        This implementation is non-ideal (it was agreed to employ it for development expediency).  A better approach
        would consist of "__str__()" calling "__repr__()", while all output options are handled through state variables.
        """
        json_dict: dict = self.to_json_dict()
        if in_jupyter_notebook():
            if (
                "expectation_config" in json_dict
                and "kwargs" in json_dict["expectation_config"]
                and "auto" in json_dict["expectation_config"]["kwargs"]
                and json_dict["expectation_config"]["kwargs"]["auto"]
            ):
                json_dict["expectation_config"]["meta"] = {
                    "auto_generated_at": datetime.datetime.now(
                        datetime.timezone.utc
                    ).strftime("%Y%m%dT%H%M%S.%fZ"),
                    "great_expectations_version": ge_version,
                }
                json_dict["expectation_config"]["kwargs"].pop("auto")
                json_dict["expectation_config"]["kwargs"].pop("batch_id", None)
            else:
                json_dict.pop("expectation_config", None)

        return json.dumps(json_dict, indent=2)

    def __str__(self) -> str:
        """
        # TODO: <Alex>5/9/2022</Alex>
        This implementation is non-ideal (it was agreed to employ it for development expediency).  A better approach
        would consist of "__str__()" calling "__repr__()", while all output options are handled through state variables.
        """
        return json.dumps(self.to_json_dict(), indent=2)

    def render(self) -> None:
        """Renders content using the:
        - atomic prescriptive renderer for the expectation configuration associated with this
          ExpectationValidationResult to self.expectation_config.rendered_content
        - atomic diagnostic renderer for the expectation configuration associated with this
          ExpectationValidationResult to self.rendered_content.
        """
        inline_renderer_config: Dict[str, Union[str, ExpectationValidationResult]] = {
            "class_name": "InlineRenderer",
            "render_object": self,
        }
        module_name: str = "great_expectations.render.renderer.inline_renderer"
        inline_renderer = instantiate_class_from_config(
            config=inline_renderer_config,
            runtime_environment={},
            config_defaults={"module_name": module_name},
        )
        if not inline_renderer:
            raise ClassInstantiationError(
                module_name=module_name,
                package_name=None,
                class_name=inline_renderer_config["class_name"],
            )

        (
            self.expectation_config.rendered_content,
            self.rendered_content,
        ) = inline_renderer.render()

    @staticmethod
    def validate_result_dict(result):
        if result.get("unexpected_count") and result["unexpected_count"] < 0:
            return False
        if result.get("unexpected_percent") and (
            result["unexpected_percent"] < 0 or result["unexpected_percent"] > 100
        ):
            return False
        if result.get("missing_percent") and (
            result["missing_percent"] < 0 or result["missing_percent"] > 100
        ):
            return False
        if result.get("unexpected_percent_nonmissing") and (
            result["unexpected_percent_nonmissing"] < 0
            or result["unexpected_percent_nonmissing"] > 100
        ):
            return False
        if result.get("missing_count") and result["missing_count"] < 0:
            return False
        return True

    def to_json_dict(self):
        myself = expectationValidationResultSchema.dump(self)
        # NOTE - JPC - 20191031: migrate to expectation-specific schemas that subclass result with properly-typed
        # schemas to get serialization all-the-way down via dump
        if "expectation_config" in myself:
            myself["expectation_config"] = convert_to_json_serializable(
                myself["expectation_config"]
            )
        if "result" in myself:
            myself["result"] = convert_to_json_serializable(myself["result"])
        if "meta" in myself:
            myself["meta"] = convert_to_json_serializable(myself["meta"])
        if "exception_info" in myself:
            myself["exception_info"] = convert_to_json_serializable(
                myself["exception_info"]
            )
        if "rendered_content" in myself:
            myself["rendered_content"] = convert_to_json_serializable(
                myself["rendered_content"]
            )
        return myself

    def get_metric(self, metric_name, **kwargs):
        if not self.expectation_config:
            raise ge_exceptions.UnavailableMetricError(
                "No ExpectationConfig found in this ExpectationValidationResult. Unable to "
                "return a metric."
            )

        metric_name_parts = metric_name.split(".")
        metric_kwargs_id = get_metric_kwargs_id(metric_name, kwargs)

        if metric_name_parts[0] == self.expectation_config.expectation_type:
            curr_metric_kwargs = get_metric_kwargs_id(
                metric_name, self.expectation_config.kwargs
            )
            if metric_kwargs_id != curr_metric_kwargs:
                raise ge_exceptions.UnavailableMetricError(
                    "Requested metric_kwargs_id (%s) does not match the configuration of this "
                    "ExpectationValidationResult (%s)."
                    % (metric_kwargs_id or "None", curr_metric_kwargs or "None")
                )
            if len(metric_name_parts) < 2:
                raise ge_exceptions.UnavailableMetricError(
                    "Expectation-defined metrics must include a requested metric."
                )
            elif len(metric_name_parts) == 2:
                if metric_name_parts[1] == "success":
                    return self.success
                else:
                    raise ge_exceptions.UnavailableMetricError(
                        "Metric name must have more than two parts for keys other than "
                        "success."
                    )
            elif metric_name_parts[1] == "result":
                try:
                    if len(metric_name_parts) == 3:
                        return self.result.get(metric_name_parts[2])
                    elif metric_name_parts[2] == "details":
                        return self.result["details"].get(metric_name_parts[3])
                except KeyError:
                    raise ge_exceptions.UnavailableMetricError(
                        "Unable to get metric {} -- KeyError in "
                        "ExpectationValidationResult.".format(metric_name)
                    )
        raise ge_exceptions.UnavailableMetricError(
            f"Unrecognized metric name {metric_name}"
        )


class ExpectationValidationResultSchema(Schema):
    success = fields.Bool(required=False, allow_none=True)
    expectation_config = fields.Nested(
        lambda: ExpectationConfigurationSchema, required=False, allow_none=True
    )
    result = fields.Dict(required=False, allow_none=True)
    meta = fields.Dict(required=False, allow_none=True)
    exception_info = fields.Dict(required=False, allow_none=True)
    rendered_content = fields.List(
        fields.Nested(
            lambda: RenderedAtomicContentSchema, required=False, allow_none=True
        )
    )

    # noinspection PyUnusedLocal
    @pre_dump
    def convert_result_to_serializable(self, data, **kwargs):
        data = deepcopy(data)
        if isinstance(data, ExpectationValidationResult):
            data.result = convert_to_json_serializable(data.result)
        elif isinstance(data, dict):
            data["result"] = convert_to_json_serializable(data.get("result"))
        return data

    REMOVE_KEYS_IF_NONE = ["rendered_content"]

    @post_dump
    def clean_null_attrs(self, data: dict, **kwargs: dict) -> dict:
        """Removes the attributes in ExpectationValidationResultSchema.REMOVE_KEYS_IF_NONE during serialization if
        their values are None."""
        data = deepcopy(data)
        for key in ExpectationConfigurationSchema.REMOVE_KEYS_IF_NONE:
            if key in data and data[key] is None:
                data.pop(key)
        return data

    # noinspection PyUnusedLocal
    @post_load
    def make_expectation_validation_result(self, data, **kwargs):
        return ExpectationValidationResult(**data)


class ExpectationSuiteValidationResultMeta(TypedDict):
    active_batch_definition: BatchDefinition
    batch_markers: BatchMarkers
    batch_spec: BatchSpec
    checkpoint_id: Optional[str]
    checkpoint_name: str
    expectation_suite_name: str
    great_expectations_version: str
    run_id: RunIdentifier
    validation_time: str


class ExpectationSuiteValidationResult(SerializableDictDot):
    def __init__(
        self,
        success: Optional[bool] = None,
        results: Optional[list] = None,
        evaluation_parameters: Optional[dict] = None,
        statistics: Optional[dict] = None,
        meta: Optional[ExpectationSuiteValidationResultMeta] = None,
        ge_cloud_id: Optional[UUID] = None,
    ) -> None:
        self.success = success
        if results is None:
            results = []
        self.results = results
        if evaluation_parameters is None:
            evaluation_parameters = {}
        self.evaluation_parameters = evaluation_parameters
        if statistics is None:
            statistics = {}
        self.statistics = statistics
        if meta is None:
            meta = {}
        ensure_json_serializable(
            meta
        )  # We require meta information to be serializable.
        self.meta = meta
        self._metrics = {}

    def __eq__(self, other):
        """ExpectationSuiteValidationResult equality ignores instance identity, relying only on properties."""
        if not isinstance(other, self.__class__):
            # Delegate comparison to the other instance's __eq__.
            return NotImplemented
        return all(
            (
                self.success == other.success,
                self.results == other.results,
                self.evaluation_parameters == other.evaluation_parameters,
                self.statistics == other.statistics,
                self.meta == other.meta,
            )
        )

    def __repr__(self):
        return json.dumps(self.to_json_dict(), indent=2)

    def __str__(self):
        return json.dumps(self.to_json_dict(), indent=2)

    def to_json_dict(self):
        myself = deepcopy(self)
        # NOTE - JPC - 20191031: migrate to expectation-specific schemas that subclass result with properly-typed
        # schemas to get serialization all-the-way down via dump
        myself["evaluation_parameters"] = convert_to_json_serializable(
            myself["evaluation_parameters"]
        )
        myself["statistics"] = convert_to_json_serializable(myself["statistics"])
        myself["meta"] = convert_to_json_serializable(myself["meta"])
        myself = expectationSuiteValidationResultSchema.dump(myself)
        return myself

    def get_metric(self, metric_name, **kwargs):
        metric_name_parts = metric_name.split(".")
        metric_kwargs_id = get_metric_kwargs_id(metric_name, kwargs)

        metric_value = None
        # Expose overall statistics
        if metric_name_parts[0] == "statistics":
            if len(metric_name_parts) == 2:
                return self.statistics.get(metric_name_parts[1])
            else:
                raise ge_exceptions.UnavailableMetricError(
                    f"Unrecognized metric {metric_name}"
                )

        # Expose expectation-defined metrics
        elif metric_name_parts[0].lower().startswith("expect_"):
            # Check our cache first
            if (metric_name, metric_kwargs_id) in self._metrics:
                return self._metrics[(metric_name, metric_kwargs_id)]
            else:
                for result in self.results:
                    try:
                        if (
                            metric_name_parts[0]
                            == result.expectation_config.expectation_type
                        ):
                            metric_value = result.get_metric(metric_name, **kwargs)
                            break
                    except ge_exceptions.UnavailableMetricError:
                        pass
                if metric_value is not None:
                    self._metrics[(metric_name, metric_kwargs_id)] = metric_value
                    return metric_value

        raise ge_exceptions.UnavailableMetricError(
            "Metric {} with metric_kwargs_id {} is not available.".format(
                metric_name, metric_kwargs_id
            )
        )

    def get_failed_validation_results(
        self,
    ) -> "ExpectationSuiteValidationResult":  # noqa: F821
        validation_results = [result for result in self.results if not result.success]

        successful_expectations = sum(exp.success for exp in validation_results)
        evaluated_expectations = len(validation_results)
        unsuccessful_expectations = evaluated_expectations - successful_expectations
        success = successful_expectations == evaluated_expectations
        try:
            success_percent = successful_expectations / evaluated_expectations * 100
        except ZeroDivisionError:
            success_percent = None
        statistics = {
            "successful_expectations": successful_expectations,
            "evaluated_expectations": evaluated_expectations,
            "unsuccessful_expectations": unsuccessful_expectations,
            "success_percent": success_percent,
            "success": success,
        }

        return ExpectationSuiteValidationResult(
            success=success,
            results=validation_results,
            evaluation_parameters=self.evaluation_parameters,
            statistics=statistics,
            meta=self.meta,
        )


class ExpectationSuiteValidationResultSchema(Schema):
    success = fields.Bool()
    results = fields.List(fields.Nested(ExpectationValidationResultSchema))
    evaluation_parameters = fields.Dict()
    statistics = fields.Dict()
    meta = fields.Dict(allow_none=True)
    ge_cloud_id = fields.UUID(required=False, allow_none=True)
    checkpoint_name = fields.String(required=False, allow_none=True)

    # noinspection PyUnusedLocal
    @pre_dump
    def prepare_dump(self, data, **kwargs):
        data = deepcopy(data)
        if isinstance(data, ExpectationSuiteValidationResult):
            data.meta = convert_to_json_serializable(data=data.meta)
            data.statistics = convert_to_json_serializable(data=data.statistics)
        elif isinstance(data, dict):
            data["meta"] = convert_to_json_serializable(data=data.get("meta"))
            data["statistics"] = convert_to_json_serializable(
                data=data.get("statistics")
            )
        return data

    # noinspection PyUnusedLocal
    @post_load
    def make_expectation_suite_validation_result(self, data, **kwargs):
        return ExpectationSuiteValidationResult(**data)


expectationSuiteValidationResultSchema = ExpectationSuiteValidationResultSchema()
expectationValidationResultSchema = ExpectationValidationResultSchema()
