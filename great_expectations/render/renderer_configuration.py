from __future__ import annotations

from enum import Enum
from numbers import Number
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generic,
    Iterable,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from pydantic import BaseModel, Field, create_model, root_validator
from pydantic.generics import GenericModel

from great_expectations.core import (
    ExpectationConfiguration,
    ExpectationValidationResult,
)
from great_expectations.render.exceptions import RendererConfigurationError

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, DictStrAny, MappingIntStrAny


class RendererSchemaType(str, Enum):
    """Type used in renderer json schema dictionary."""

    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"


class _RendererParamsBase(BaseModel):
    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True

    def dict(
        self,
        include: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
        exclude: Optional[Union[AbstractSetIntStr, MappingIntStrAny]] = None,
        by_alias: bool = True,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = True,
    ) -> DictStrAny:
        """
        Override BaseModel dict to make the defaults:
            - by_alias=True because we have an existing attribute named schema, and schema is already a Pydantic
              BaseModel attribute.
            - exclude_none=True to ensure that None values aren't included in the json dict.

        In practice this means the renderer implementer doesn't need to use .dict(by_alias=True, exclude_none=True)
        everywhere.
        """
        return super().dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )


RendererParams = TypeVar("RendererParams", bound=_RendererParamsBase)


class RendererConfiguration(GenericModel, Generic[RendererParams]):
    """Configuration object built for each renderer."""

    configuration: Union[ExpectationConfiguration, None] = Field(
        None, allow_mutation=False
    )
    result: Optional[ExpectationValidationResult] = Field(None, allow_mutation=False)
    runtime_configuration: Optional[dict] = Field({}, allow_mutation=False)
    expectation_type: str = Field("", allow_mutation=False)
    kwargs: dict = Field({}, allow_mutation=False)
    include_column_name: bool = Field(True, allow_mutation=False)
    params: RendererParams = Field(..., allow_mutation=True)
    template_str: str = Field("", allow_mutation=True)
    header_row: List[Dict[str, Optional[Any]]] = Field([], allow_mutation=True)
    table: List[List[Dict[str, Optional[Any]]]] = Field([], allow_mutation=True)
    graph: dict = Field({}, allow_mutation=True)

    class Config:
        validate_assignment = True
        arbitrary_types_allowed = True

    @root_validator(pre=True)
    def _validate_configuration_or_result(cls, values: dict) -> dict:
        if ("configuration" not in values or values["configuration"] is None) and (
            "result" not in values or values["result"] is None
        ):
            raise RendererConfigurationError(
                "RendererConfiguration must be passed either configuration or result."
            )
        return values

    @root_validator()
    def _validate_for_expectation_type_and_kwargs(cls, values: dict) -> dict:
        if (
            "result" in values
            and values["result"] is not None
            and values["result"].expectation_config is not None
        ):
            values["expectation_type"] = values[
                "result"
            ].expectation_config.expectation_type
            values["kwargs"] = values["result"].expectation_config.kwargs
        else:
            values["expectation_type"] = values["configuration"].expectation_type
            values["kwargs"] = values["configuration"].kwargs
        return values

    @root_validator()
    def _validate_for_include_column_name(cls, values: dict) -> dict:
        if "runtime_configuration" in values and values["runtime_configuration"]:
            values["include_column_name"] = (
                False
                if values["runtime_configuration"].get("include_column_name") is False
                else True
            )
        return values

    def __init__(self, **values) -> None:
        values["params"] = _RendererParamsBase()
        super().__init__(**values)

    class _RendererParamBase(BaseModel):
        renderer_schema: RendererSchemaType = Field(..., allow_mutation=False)
        value: Any = Field(..., allow_mutation=False)

        class Config:
            validate_assignment = True
            arbitrary_types_allowed = True

        @root_validator()
        def _validate_schema_matches_value(cls, values: dict) -> dict:
            schema_type: RendererSchemaType = values["renderer_schema"]["type"]
            value: Any = values["value"]
            if schema_type is RendererSchemaType.STRING:
                try:
                    str(value)
                except Exception as e:
                    raise RendererConfigurationError(
                        f"Value was unable to be represented as a string: {str(e)}"
                    )
            else:
                renderer_configuration_error = RendererConfigurationError(
                    f"Param schema_type: <{schema_type}> does "
                    f"not match value: <{value}>."
                )
                if schema_type is RendererSchemaType.NUMBER:
                    if not isinstance(value, Number):
                        raise renderer_configuration_error
                elif schema_type is RendererSchemaType.BOOLEAN:
                    if value is not True and value is not False:
                        raise renderer_configuration_error
                else:
                    if not isinstance(value, Iterable):
                        raise renderer_configuration_error
            return values

        def __eq__(self, other: Any) -> bool:
            if isinstance(other, BaseModel):
                return self.dict() == other.dict()
            elif isinstance(other, dict):
                return self.dict() == other
            else:
                return self == other

    def add_param(
        self,
        name: str,
        schema_type: Union[RendererSchemaType, str],
        value: Optional[Any] = None,
    ) -> None:
        """Adds a param that can be substituted into a template string during rendering.

        Attributes:
            name (str): A name for the attribute to be added to this RendererConfiguration instance.
            schema_type (RendererSchemaType or string): The type of value being substituted. One of:
                - string
                - number
                - boolean
                - array
            value (Optional[Any]): The value to be substituted into the template string. If no value is
                provided, a value lookup will be attempted in RendererConfiguration.kwargs using the
                provided name.

        Returns:
            None
        """
        renderer_param: Type[BaseModel] = create_model(
            name,
            renderer_schema=(
                Dict[str, Optional[RendererSchemaType]],
                Field(..., alias="schema"),
            ),
            value=(Union[Any, None], ...),
            __base__=RendererConfiguration._RendererParamBase,
        )
        renderer_param_definition: Dict[str, Any] = {
            name: (Optional[renderer_param], ...)
        }

        # As of Nov 30, 2022 there is a bug in autocompletion for pydantic dynamic models
        # See: https://github.com/pydantic/pydantic/issues/3930
        renderer_params: Type[BaseModel] = create_model(
            "RendererParams",
            **renderer_param_definition,
            __base__=self.params.__class__,
        )

        if value is None:
            value = self.kwargs.get(name)

        renderer_params_definition: Dict[str, Optional[Any]]
        if value is None:
            renderer_params_definition = {
                **self.params.dict(exclude_none=False),
                name: None,
            }
        else:
            renderer_params_definition = {
                **self.params.dict(exclude_none=False),
                name: renderer_param(schema={"type": schema_type}, value=value),
            }

        self.params = cast(
            RendererParams, renderer_params(**renderer_params_definition)
        )
