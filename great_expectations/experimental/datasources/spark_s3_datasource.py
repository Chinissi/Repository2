from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

import pydantic
from typing_extensions import Literal

from great_expectations.core.util import S3Url
from great_expectations.experimental.datasources import _SparkFilePathDatasource
from great_expectations.experimental.datasources.data_asset.data_connector import (
    DataConnector,
    S3DataConnector,
)
from great_expectations.experimental.datasources.interfaces import TestConnectionError
from great_expectations.experimental.datasources.spark_file_path_datasource import (
    CSVAsset,
)

if TYPE_CHECKING:
    from botocore.client import BaseClient

    from great_expectations.experimental.datasources.interfaces import (
        BatchSorter,
        BatchSortersDefinition,
    )


logger = logging.getLogger(__name__)


try:
    import boto3
except ImportError:
    logger.debug("Unable to load boto3; install optional boto3 dependency for support.")
    boto3 = None


class SparkS3Datasource(_SparkFilePathDatasource):
    # instance attributes
    type: Literal["spark_s3"] = "spark_s3"

    # S3 specific attributes
    bucket: str
    boto3_options: Dict[str, Any] = {}

    _s3_client: Optional[BaseClient] = pydantic.PrivateAttr()

    def __init__(self, **data):
        super().__init__(**data)

        try:
            self._s3_client = boto3.client("s3", **self.boto3_options)
        except (TypeError, AttributeError):
            self._s3_client = None

    def test_connection(self, test_assets: bool = True) -> None:
        """Test the connection for the SparkS3Datasource.

        Args:
            test_assets: If assets have been passed to the SparkS3Datasource, whether to test them as well.

        Raises:
            TestConnectionError: If the connection test fails.
        """
        if self._s3_client is None:
            raise TestConnectionError(
                "Unable to load boto3 (it is required for SparkS3Datasource)."
            )

        if self.assets and test_assets:
            for asset in self.assets.values():
                asset.test_connection()

    def add_csv_asset(
        self,
        name: str,
        batching_regex: Union[re.Pattern, str],
        header: bool = False,
        infer_schema: bool = False,
        prefix: str = "",
        delimiter: str = "/",
        max_keys: int = 1000,
        order_by: Optional[BatchSortersDefinition] = None,
        **kwargs,  # TODO: update signature to have specific keys & types
    ) -> CSVAsset:  # type: ignore[valid-type]
        """Adds a CSV DataAsst to the present "SparkS3Datasource" object.

        Args:
            name: The name of the csv asset
            batching_regex: regex pattern that matches csv filenames that is used to label the batches
            header: boolean (default False) indicating whether or not first line of CSV file is header line
            infer_schema: boolean (default False) instructing Spark to attempt to infer schema of CSV file heuristically
            prefix (str): S3 prefix
            delimiter (str): S3 delimiter
            max_keys (int): S3 max_keys (default is 1000)
            order_by: sorting directive via either list[BatchSorter] or "{+|-}key" syntax: +/- (a/de)scending; + default
            kwargs: Extra keyword arguments should correspond to ``pandas.read_csv`` keyword args
        """
        batching_regex_pattern: re.Pattern = self.parse_batching_regex_string(
            batching_regex=batching_regex
        )
        order_by_sorters: list[BatchSorter] = self.parse_order_by_sorters(
            order_by=order_by
        )

        asset = CSVAsset(
            name=name,
            batching_regex=batching_regex_pattern,
            header=header,
            inferSchema=infer_schema,
            order_by=order_by_sorters,
            **kwargs,
        )

        data_connector: DataConnector = S3DataConnector(
            datasource_name=self.name,
            data_asset_name=name,
            batching_regex=batching_regex_pattern,
            s3_client=self._s3_client,
            bucket=self.bucket,
            prefix=prefix,
            delimiter=delimiter,
            max_keys=max_keys,
            file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
        )
        test_connection_error_message: str = f"""No file in bucket "{self.bucket}" with prefix "{prefix}" matched regular expressions pattern "{batching_regex_pattern.pattern}" using deliiter "{delimiter}" for DataAsset "{name}"."""
        return self.add_asset(
            asset=asset,
            data_connector=data_connector,
            test_connection_error_message=test_connection_error_message,
        )
