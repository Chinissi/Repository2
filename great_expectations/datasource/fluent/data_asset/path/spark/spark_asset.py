from __future__ import annotations

from typing import Union

from great_expectations.datasource.fluent.data_asset.path.spark.csv_asset import (
    CSVAsset,
    DirectoryCSVAsset,
)
from great_expectations.datasource.fluent.data_asset.path.spark.delta_asset import (
    DeltaAsset,
    DirectoryDeltaAsset,
)
from great_expectations.datasource.fluent.data_asset.path.spark.json_asset import (
    DirectoryJSONAsset,
    JSONAsset,
)
from great_expectations.datasource.fluent.data_asset.path.spark.orc_asset import (
    DirectoryORCAsset,
    ORCAsset,
)
from great_expectations.datasource.fluent.data_asset.path.spark.parquet_asset import (
    DirectoryParquetAsset,
    ParquetAsset,
)
from great_expectations.datasource.fluent.data_asset.path.spark.text_asset import (
    DirectoryTextAsset,
    TextAsset,
)

# New asset types should be added to the SPARK_FILE_PATH_ASSET_TYPES tuple,
# and to SPARK_FILE_PATH_ASSET_TYPES_UNION
# so that the schemas are generated and the assets are registered.


SPARK_FILE_PATH_ASSET_TYPES = (
    CSVAsset,
    DirectoryCSVAsset,
    ParquetAsset,
    DirectoryParquetAsset,
    ORCAsset,
    DirectoryORCAsset,
    JSONAsset,
    DirectoryJSONAsset,
    TextAsset,
    DirectoryTextAsset,
    DeltaAsset,
    DirectoryDeltaAsset,
)
SPARK_FILE_PATH_ASSET_TYPES_UNION = Union[
    CSVAsset,
    DirectoryCSVAsset,
    ParquetAsset,
    DirectoryParquetAsset,
    ORCAsset,
    DirectoryORCAsset,
    JSONAsset,
    DirectoryJSONAsset,
    TextAsset,
    DirectoryTextAsset,
    DeltaAsset,
    DirectoryDeltaAsset,
]
