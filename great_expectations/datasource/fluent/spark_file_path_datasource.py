from __future__ import annotations

import logging
from typing import TYPE_CHECKING, ClassVar, Dict, List, Type

import pydantic
from typing_extensions import Literal

from great_expectations.datasource.fluent import _SparkDatasource
from great_expectations.datasource.fluent.file_path_data_asset import (
    _FilePathDataAsset,
)

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import DataAsset


logger = logging.getLogger(__name__)


class CSVAsset(_FilePathDataAsset):
    # Overridden inherited instance fields
    type: Literal["csv"] = "csv"
    header: bool = False
    infer_schema: bool = False

    class Config:
        extra = pydantic.Extra.forbid

    def _get_reader_method(self) -> str:
        return self.type

    def _get_reader_options_include(self) -> set[str] | None:
        return {"header", "infer_schema"}


class _SparkFilePathDatasource(_SparkDatasource):
    # class attributes
    asset_types: ClassVar[List[Type[DataAsset]]] = [CSVAsset]

    # instance attributes
    assets: Dict[str, _FilePathDataAsset] = {}  # type: ignore[assignment]
