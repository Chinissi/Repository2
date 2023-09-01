from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, TypeVar, Union

import pydantic
from pydantic import BaseModel

from great_expectations.compatibility.typing_extensions import override
from great_expectations.core.http import create_session
from great_expectations.experimental.metric_repository.data_store import DataStore
from great_expectations.experimental.metric_repository.metrics import MetricRun

if TYPE_CHECKING:
    from typing_extensions import TypeAlias

    from great_expectations.data_context import CloudDataContext

StorableTypes: TypeAlias = Union[MetricRun,]

T = TypeVar("T", bound=StorableTypes)


class PayloadData(BaseModel):
    type: str
    attributes: Dict[str, Any]

    class Config:
        extra = pydantic.Extra.forbid


class Payload(BaseModel):
    data: PayloadData

    class Config:
        extra = pydantic.Extra.forbid


class CloudDataStore(DataStore[StorableTypes]):
    """DataStore implementation for GX Cloud.

    Uses JSON:API https://jsonapi.org/
    """

    @override
    def __init__(self, context: CloudDataContext):
        super().__init__(context=context)
        assert context.ge_cloud_config is not None
        assert self._context.ge_cloud_config is not None
        self._session = create_session(
            access_token=context.ge_cloud_config.access_token
        )

    def _map_to_url(self, value: StorableTypes) -> str:
        if isinstance(value, MetricRun):
            return "/metric-runs"

    def _map_to_resource_type(self, value: StorableTypes) -> str:
        if isinstance(value, MetricRun):
            return "metric-run"

    def _build_payload(self, value: StorableTypes) -> dict:
        payload = Payload(
            data=PayloadData(
                type=self._map_to_resource_type(value),
                attributes=value.dict(
                    exclude={"metrics": {"__all__": {"__orig_class__"}}}
                ),
            )
        )
        return payload.dict()

    def _build_url(self, value: StorableTypes) -> str:
        assert self._context.ge_cloud_config is not None
        config = self._context.ge_cloud_config
        return f"{config.base_url}/organizations/{config.organization_id}{self._map_to_url(value)}"

    @override
    def add(self, value: T) -> T:
        """Add a value to the DataStore. Currently, returns the input value not the value from the DataStore."""
        url = self._build_url(value)
        payload = self._build_payload(value)
        self._session.post(url=url, data=payload)
        return value
