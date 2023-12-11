import enum
from typing import List, Optional

from great_expectations.compatibility import pydantic


class ResultFormat(str, enum.Enum):
    BOOLEAN_ONLY = "BOOLEAN_ONLY"
    BASIC = "BASIC"
    COMPLETE = "COMPLETE"
    SUMMARY = "SUMMARY"


class ResultFormatConfig(pydantic.BaseModel):
    result_format: ResultFormat
    unexpected_index_column_names: Optional[List[str]] = None
    return_unexpected_index_query: Optional[bool] = None
    partial_unexpected_count: Optional[int] = None
    include_unexpected_rows: Optional[bool] = None
    exclude_unexpected_values: Optional[bool] = None
