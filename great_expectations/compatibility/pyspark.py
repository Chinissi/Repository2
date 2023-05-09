from __future__ import annotations

from collections import UserDict
from typing import Any, MutableMapping

from pydantic.fields import ModelField

from great_expectations.compatibility.not_imported import NotImported

SPARK_NOT_IMPORTED = NotImported(
    "pyspark is not installed, please 'pip install pyspark'"
)

try:
    import pyspark
except ImportError:
    pyspark = SPARK_NOT_IMPORTED  # type: ignore[assignment]

try:
    from pyspark.sql import functions
except (ImportError, AttributeError):
    functions = SPARK_NOT_IMPORTED  # type: ignore[assignment]

try:
    from pyspark.sql import types
except (ImportError, AttributeError):
    types = SPARK_NOT_IMPORTED  # type: ignore[assignment]

try:
    from pyspark import SparkContext
except ImportError:
    SparkContext = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.ml.feature import Bucketizer
except (ImportError, AttributeError):
    Bucketizer = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql import Column
except (ImportError, AttributeError):
    Column = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql import DataFrame
except (ImportError, AttributeError):
    DataFrame = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql import Row
except (ImportError, AttributeError):
    Row = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql import SparkSession
except (ImportError, AttributeError):
    SparkSession = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql import SQLContext
except (ImportError, AttributeError):
    SQLContext = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql import Window
except (ImportError, AttributeError):
    Window = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql.readwriter import DataFrameReader
except (ImportError, AttributeError):
    DataFrameReader = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]

try:
    from pyspark.sql.utils import AnalysisException
except (ImportError, AttributeError):
    AnalysisException = SPARK_NOT_IMPORTED  # type: ignore[assignment,misc]


# TODO: move this into fluent/serializable_types
class SerializableStructType(dict):
    """Custom type implementing pydantic validation."""

    struct_type: pyspark.sql.types.StructType

    def __init__(
        self,
        fields_or_struct_type: pyspark.sql.types.StructType
        | list[pyspark.sql.types.StructField]
        | None,
    ):
        if isinstance(fields_or_struct_type, pyspark.sql.types.StructType):
            self.struct_type = fields_or_struct_type
        else:
            self.struct_type = pyspark.sql.types.StructType(
                fields=fields_or_struct_type
            )

        json_value = self.struct_type.jsonValue()
        super().__init__(**json_value)

    @classmethod
    def validate(cls, v):
        """If already StructType then return otherwise try to create a StructType."""
        if isinstance(v, pyspark.sql.types.StructType):
            return v
        else:
            return cls(v)

    @classmethod
    def __get_validators__(cls):
        # one or more validators may be yielded which will be called in the
        # order to validate the input, each validator will receive as an input
        # the value returned from the previous validator
        yield cls.validate
