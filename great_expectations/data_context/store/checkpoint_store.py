from __future__ import annotations

import itertools
import logging
import os
import random
import uuid
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

from marshmallow import ValidationError

import great_expectations.exceptions as gx_exceptions
from great_expectations.core.data_context_key import DataContextKey  # noqa: TCH001
from great_expectations.data_context.cloud_constants import GXCloudRESTResource
from great_expectations.data_context.store import ConfigurationStore
from great_expectations.data_context.types.base import (
    CheckpointConfig,
    DataContextConfigDefaults,
)
from great_expectations.data_context.types.refs import (
    GXCloudIDAwareRef,
    GXCloudResourceRef,
)
from great_expectations.data_context.types.resource_identifiers import (
    ConfigurationIdentifier,  # noqa: TCH001
    GXCloudIdentifier,  # noqa: TCH001
)

if TYPE_CHECKING:
    from great_expectations.checkpoint import Checkpoint

logger = logging.getLogger(__name__)


class CheckpointStore(ConfigurationStore):
    """
    A CheckpointStore manages Checkpoints for the DataContext.
    """

    _configuration_class = CheckpointConfig

    def ge_cloud_response_json_to_object_dict(self, response_json: Dict) -> Dict:
        """
        This method takes full json response from GX cloud and outputs a dict appropriate for
        deserialization into a GX object
        """
        cp_data: Dict
        if isinstance(response_json["data"], list):
            cp_data = response_json["data"][0]
        else:
            cp_data = response_json["data"]
        ge_cloud_checkpoint_id: str = cp_data["id"]
        checkpoint_config_dict: Dict = cp_data["attributes"]["checkpoint_config"]
        checkpoint_config_dict["ge_cloud_id"] = ge_cloud_checkpoint_id

        # Checkpoints accept a `ge_cloud_id` but not an `id`
        checkpoint_config_dict.pop("id", None)

        return checkpoint_config_dict

    def serialization_self_check(self, pretty_print: bool) -> None:
        test_checkpoint_name: str = "test-name-" + "".join(
            [random.choice(list("0123456789ABCDEF")) for i in range(20)]
        )
        test_checkpoint_configuration = CheckpointConfig(
            **{"name": test_checkpoint_name}  # type: ignore[arg-type]
        )
        if self.cloud_mode:
            test_key: GXCloudIdentifier = self.key_class(  # type: ignore[call-arg,assignment]
                resource_type=GXCloudRESTResource.CHECKPOINT,
                ge_cloud_id=str(uuid.uuid4()),
            )
        else:
            test_key = self.key_class(configuration_key=test_checkpoint_name)  # type: ignore[call-arg,assignment]

        if pretty_print:
            print(f"Attempting to add a new test key {test_key} to Checkpoint store...")
        self.set(key=test_key, value=test_checkpoint_configuration)
        if pretty_print:
            print(f"\tTest key {test_key} successfully added to Checkpoint store.\n")

        if pretty_print:
            print(
                f"Attempting to retrieve the test value associated with key {test_key} from Checkpoint store..."
            )

        self.get(key=test_key)
        if pretty_print:
            print("\tTest value successfully retrieved from Checkpoint store.")
            print()

        if pretty_print:
            print(f"Cleaning up test key {test_key} and value from Checkpoint store...")

        self.remove_key(key=test_key)
        if pretty_print:
            print("\tTest key and value successfully removed from Checkpoint store.")
            print()

    @staticmethod
    def default_checkpoints_exist(directory_path: str) -> bool:
        if not directory_path:
            return False

        checkpoints_directory_path: str = os.path.join(
            directory_path,
            DataContextConfigDefaults.DEFAULT_CHECKPOINT_STORE_BASE_DIRECTORY_RELATIVE_NAME.value,
        )
        return os.path.isdir(checkpoints_directory_path)

    def list_checkpoints(
        self, ge_cloud_mode: bool = False
    ) -> Union[List[str], List[ConfigurationIdentifier]]:
        keys: Union[List[str], List[ConfigurationIdentifier]] = self.list_keys()  # type: ignore[assignment]
        if ge_cloud_mode:
            return keys
        return [k.configuration_key for k in keys]  # type: ignore[union-attr]

    def delete_checkpoint(
        self,
        name: str | None = None,
        id: str | None = None,
    ) -> None:
        key: Union[GXCloudIdentifier, ConfigurationIdentifier] = self.determine_key(
            name=name, ge_cloud_id=id
        )
        try:
            self.remove_key(key=key)
        except gx_exceptions.InvalidKeyError as exc_ik:
            raise gx_exceptions.CheckpointNotFoundError(
                message=f'Non-existent Checkpoint configuration named "{key.configuration_key}".\n\nDetails: {exc_ik}'  # type: ignore[union-attr]
            )

    def get_checkpoint(
        self, name: Optional[ConfigurationIdentifier | str], id: Optional[str]
    ) -> CheckpointConfig:
        key: GXCloudIdentifier | ConfigurationIdentifier
        if not isinstance(name, ConfigurationIdentifier):
            key = self.determine_key(name=name, ge_cloud_id=id)
        else:
            key = name

        try:
            checkpoint_config: Optional[Any] = self.get(key=key)
            assert isinstance(
                checkpoint_config, CheckpointConfig
            ), "checkpoint_config retrieved was not of type CheckpointConfig"
        except gx_exceptions.InvalidKeyError as exc_ik:
            raise gx_exceptions.CheckpointNotFoundError(
                message=f'Non-existent Checkpoint configuration named "{key.configuration_key}".\n\nDetails: {exc_ik}'  # type: ignore[union-attr]
            )
        except ValidationError as exc_ve:
            raise gx_exceptions.InvalidCheckpointConfigError(
                message="Invalid Checkpoint configuration", validation_error=exc_ve
            )

        if checkpoint_config.config_version is None:
            config_dict: dict = checkpoint_config.to_json_dict()
            batches: Optional[dict] = config_dict.get("batches")
            if not (
                batches is not None
                and (
                    len(batches) == 0
                    or {"batch_kwargs", "expectation_suite_names"}.issubset(
                        set(
                            itertools.chain.from_iterable(
                                item.keys() for item in batches
                            )
                        )
                    )
                )
            ):
                raise gx_exceptions.CheckpointError(
                    message="Attempt to instantiate LegacyCheckpoint with insufficient and/or incorrect arguments."
                )

        return checkpoint_config

    def add_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        key = self._construct_key_from_checkpoint(checkpoint)
        return self._add_checkpoint(key=key, checkpoint=checkpoint)

    def update_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        key = self._construct_key_from_checkpoint(checkpoint)
        if not self.has_key(key):
            raise gx_exceptions.CheckpointNotFoundError(
                f"Could not find a Checkpoint named {checkpoint.name}"
            )
        return self._add_checkpoint(key=key, checkpoint=checkpoint)

    def add_or_update_checkpoint(self, checkpoint: Checkpoint) -> Checkpoint:
        key = self._construct_key_from_checkpoint(checkpoint)
        if self.has_key(key):
            return self.update_checkpoint(checkpoint)
        return self._add_checkpoint(key=key, checkpoint=checkpoint)

    def _construct_key_from_checkpoint(
        self, checkpoint: Checkpoint
    ) -> Union[GXCloudIdentifier, ConfigurationIdentifier]:
        name = checkpoint.name
        id = checkpoint.ge_cloud_id
        if id:
            return self.determine_key(ge_cloud_id=str(id))
        return self.determine_key(name=name)

    def _add_checkpoint(
        self,
        key: GXCloudIdentifier | ConfigurationIdentifier,
        checkpoint: Checkpoint,
    ) -> Checkpoint:
        checkpoint_config = checkpoint.get_config()
        checkpoint_ref = self.set(key=key, value=checkpoint_config)  # type: ignore[func-returns-value]
        if isinstance(checkpoint_ref, GXCloudIDAwareRef):
            cloud_id = checkpoint_ref.cloud_id
            checkpoint.ge_cloud_id = uuid.UUID(cloud_id)  # type: ignore[misc]
        return checkpoint

    def create(self, checkpoint_config: CheckpointConfig) -> Optional[DataContextKey]:
        """Create a checkpoint config in the store using a store_backend-specific key.

        Args:
            checkpoint_config: Config containing the checkpoint name.

        Returns:
            None unless using GXCloudStoreBackend and if so the GeCloudResourceRef which contains the id
            which was used to create the config in the backend.
        """
        # CheckpointConfig not an AbstractConfig??
        # mypy error: incompatible type "CheckpointConfig"; expected "AbstractConfig"
        key: DataContextKey = self._build_key_from_config(checkpoint_config)  # type: ignore[arg-type]

        # Make two separate requests to set and get in order to obtain any additional
        # values that may have been added to the config by the StoreBackend (i.e. object ids)
        ref: Optional[Union[bool, GXCloudResourceRef]] = self.set(key, checkpoint_config)  # type: ignore[func-returns-value]
        if ref and isinstance(ref, GXCloudResourceRef):
            key.cloud_id = ref.cloud_id  # type: ignore[attr-defined]

        config = self.get(key=key)

        return config
