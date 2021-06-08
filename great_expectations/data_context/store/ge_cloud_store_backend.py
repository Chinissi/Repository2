import logging
import os
import random
import re
import shutil
import uuid
from abc import ABCMeta
from urllib.parse import urljoin

import requests

from great_expectations.data_context.store.store_backend import StoreBackend
from great_expectations.exceptions import InvalidKeyError, StoreBackendError
from great_expectations.util import filter_properties_dict, pluralize, singularize

logger = logging.getLogger(__name__)


class GeCloudStoreBackend(StoreBackend, metaclass=ABCMeta):
    def __init__(
        self,
        ge_cloud_base_url,
        ge_cloud_credentials,
        ge_cloud_resource_type=None,
        ge_cloud_resource_name=None,
        suppress_store_backend_id=False,
        manually_initialize_store_backend_id: str = "",
        store_name=None,
    ):
        super().__init__(
            fixed_length_key=True,
            suppress_store_backend_id=suppress_store_backend_id,
            manually_initialize_store_backend_id=manually_initialize_store_backend_id,
            store_name=store_name,
        )
        assert ge_cloud_resource_type or ge_cloud_resource_name, "Must provide either ge_cloud_resource_type or " \
                                                                 "ge_cloud_resource_name"
        self._ge_cloud_base_url = ge_cloud_base_url
        self._ge_cloud_resource_name = ge_cloud_resource_name or pluralize(ge_cloud_resource_type)
        self._ge_cloud_resource_type = ge_cloud_resource_type or singularize(ge_cloud_resource_name)
        self._ge_cloud_credentials = ge_cloud_credentials

        # Initialize with store_backend_id if not part of an HTMLSiteStore
        if not self._suppress_store_backend_id:
            _ = self.store_backend_id

        # Gather the call arguments of the present function (include the "module_name" and add the "class_name"), filter
        # out the Falsy values, and set the instance "_config" variable equal to the resulting dictionary.
        self._config = {
            "ge_cloud_base_url": ge_cloud_base_url,
            "ge_cloud_resource_name": ge_cloud_resource_name,
            "ge_cloud_resource_type": ge_cloud_resource_type,
            "fixed_length_key": True,
            "suppress_store_backend_id": suppress_store_backend_id,
            "manually_initialize_store_backend_id": manually_initialize_store_backend_id,
            "store_name": store_name,
            "module_name": self.__class__.__module__,
            "class_name": self.__class__.__name__,
        }
        filter_properties_dict(properties=self._config, inplace=True)

    def _get(self, key):
        ge_cloud_url = self.get_url_for_key(key=key)
        headers = {
            "Content-Type": "application/vnd.api+json",
            "GE-Cloud-API-Token": self.ge_cloud_credentials['access_token'],
        }
        response = requests.get(ge_cloud_url, headers=headers)
        return response.json()

    def _move(self):
        pass

    def _set(self, key, value, **kwargs):
        data = {
            "data": {
                "type": self.ge_cloud_resource_type,
                "attributes": {
                    "account_id": self.ge_cloud_credentials["account_id"],
                    "checkpoint_config": value.to_json_dict(),
                },
            }
        }

        headers = {
            "Content-Type": "application/vnd.api+json",
            "GE-Cloud-API-Token": self.ge_cloud_credentials['access_token'],
        }
        url = urljoin(
            self.ge_cloud_base_url,
            f"accounts/"
            f"{self.ge_cloud_credentials['account_id']}/"
            f"{self.ge_cloud_resource_name}",
        )
        try:
            response = requests.post(url, json=data, headers=headers)
            response_json = response.json()

            object_id = response_json["data"]["id"]
            return self.get_url_for_key((object_id,))
        except Exception as e:
            logger.debug(str(e))
            raise StoreBackendError("Unable to set object in GE Cloud Store Backend.")

    @property
    def ge_cloud_base_url(self):
        return self._ge_cloud_base_url

    @property
    def ge_cloud_resource_name(self):
        return self._ge_cloud_resource_name

    @property
    def ge_cloud_resource_type(self):
        return self._ge_cloud_resource_type

    @property
    def ge_cloud_credentials(self):
        return self._ge_cloud_credentials

    def list_keys(self):
        headers = {
            "Content-Type": "application/vnd.api+json",
            "GE-Cloud-API-Token": self.ge_cloud_credentials['access_token'],
        }
        url = urljoin(
            self.ge_cloud_base_url,
            f"accounts/"
            f"{self.ge_cloud_credentials['account_id']}/"
            f"{self.ge_cloud_resource_name}",
        )
        try:
            response = requests.get(url, headers=headers)
            response_json = response.json()
            keys = [
                (resource["id"], ) for resource in
                response_json.get("data")
            ]
            return keys
        except Exception as e:
            logger.debug(str(e))
            raise StoreBackendError("Unable to list keys in GE Cloud Store Backend.")

    def get_url_for_key(self, key, protocol=None):
        ge_cloud_id = key[0]
        url = urljoin(
            self.ge_cloud_base_url,
            f"accounts/{self.ge_cloud_credentials['account_id']}/{self.ge_cloud_resource_name}/{ge_cloud_id}",
        )
        return url

    def remove_key(self, key):
        if not isinstance(key, tuple):
            key = key.to_tuple()

        ge_cloud_id = key[0]

        headers = {
            "Content-Type": "application/vnd.api+json",
            "GE-Cloud-API-Token": self.ge_cloud_credentials['access_token'],
        }

        data = {
            "data": {
                "type": self.ge_cloud_resource_type,
                "id": ge_cloud_id,
                "attributes": {
                    "deleted": True,
                },
            }
        }

        url = urljoin(
            self.ge_cloud_base_url,
            f"accounts/"
            f"{self.ge_cloud_credentials['account_id']}/"
            f"{self.ge_cloud_resource_name}/"
            f"{ge_cloud_id}",
        )
        try:
            response = requests.patch(url, json=data, headers=headers)
            response_status_code = response.status_code

            if response_status_code < 300:
                return True
            return False
        except Exception as e:
            logger.debug(str(e))
            raise StoreBackendError("Unable to delete object in GE Cloud Store Backend.")

    def _has_key(self, key):
        all_keys = self.list_keys()
        return key in all_keys

    @property
    def config(self) -> dict:
        return self._config
