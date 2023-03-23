from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Type, Union

import pydantic
from typing_extensions import Literal

from great_expectations.core.util import S3Url
from great_expectations.datasource.fluent import _PandasFilePathDatasource
from great_expectations.datasource.fluent.config_str import (
    ConfigStr,  # noqa: TCH001 # needed at runtime
)
from great_expectations.datasource.fluent.data_asset.data_connector import (
    S3DataConnector,
)
from great_expectations.datasource.fluent.interfaces import TestConnectionError
from great_expectations.datasource.fluent.pandas_datasource import (
    PandasDatasourceError,
)

if TYPE_CHECKING:
    from botocore.client import BaseClient

    from great_expectations.datasource.fluent.file_path_data_asset import (
        _FilePathDataAsset,
    )


logger = logging.getLogger(__name__)


BOTO3_IMPORTED = False
try:
    import boto3  # noqa: disable=E0602

    BOTO3_IMPORTED = True
except ImportError:
    pass


class PandasS3DatasourceError(PandasDatasourceError):
    pass


class PandasS3Datasource(_PandasFilePathDatasource):
    # class attributes
    data_connector_type: ClassVar[Type[S3DataConnector]] = S3DataConnector

    # instance attributes
    type: Literal["pandas_s3"] = "pandas_s3"

    # S3 specific attributes
    bucket: str
    boto3_options: Dict[str, Union[ConfigStr, Any]] = {}

    _s3_client: Union[BaseClient, None] = pydantic.PrivateAttr(default=None)

    def _get_s3_client(self) -> BaseClient:
        s3_client: Union[BaseClient, None] = self._s3_client
        if not s3_client:
            # Validate that "boto3" libarary was successfully imported and attempt to create "s3_client" handle.
            if BOTO3_IMPORTED:
                try:
                    s3_client = boto3.client("s3", **self.boto3_options)
                except Exception as e:
                    # Failure to create "s3_client" is most likely due invalid "boto3_options" dictionary.
                    raise PandasS3DatasourceError(
                        f'Due to exception: "{str(e)}", "s3_client" could not be created.'
                    ) from e
            else:
                raise PandasS3DatasourceError(
                    'Unable to create "PandasS3Datasource" due to missing boto3 dependency.'
                )

            self._s3_client = s3_client

        return s3_client

    def test_connection(self, test_assets: bool = True) -> None:
        """Test the connection for the PandasS3Datasource.

        Args:
            test_assets: If assets have been passed to the PandasS3Datasource, whether to test them as well.

        Raises:
            TestConnectionError: If the connection test fails.
        """
        try:
            _ = self._get_s3_client()
        except Exception as e:
            raise TestConnectionError(
                "Attempt to connect to datasource failed with the following error message: "
                f"{str(e)}"
            ) from e

        if self.assets and test_assets:
            for asset in self.assets.values():
                asset.test_connection()

    def _build_data_connector(
        self,
        data_asset: _FilePathDataAsset,
        prefix: str = "",
        delimiter: str = "/",  # TODO: delimiter conflicts with csv asset args
        max_keys: int = 1000,
        **kwargs,
    ) -> None:
        """Builds and attaches the `FilesystemDataConnector` to the asset."""
        if kwargs:
            raise TypeError(
                f"_build_data_connector() got unexpected keyword arguments {list(kwargs.keys())}"
            )
        
        data_asset._data_connector = self.data_connector_type.build_data_connector(
            datasource_name=self.name,
            data_asset_name=data_asset.name,
            s3_client=self._get_s3_client(),
            batching_regex=data_asset.batching_regex,
            bucket=self.bucket,
            prefix=prefix,
            delimiter=delimiter,
            max_keys=max_keys,
            file_path_template_map_fn=S3Url.OBJECT_URL_TEMPLATE.format,
        )

        # build a more specific `_test_connection_error_message`
        data_asset._test_connection_error_message = (
            self.data_connector_type.build_test_connection_error_message(
                data_asset_name=data_asset.name,
                batching_regex=data_asset.batching_regex,
                bucket=self.bucket,
                prefix=prefix,
                delimiter=delimiter,
            )
        )
