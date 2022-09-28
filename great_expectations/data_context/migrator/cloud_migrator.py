"""TODO: Add docstring"""
import logging
from typing import Dict, List, NamedTuple, Optional, cast

import requests

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.configuration import AbstractConfig
from great_expectations.core.http import create_session
from great_expectations.core.usage_statistics.events import UsageStatsEvents
from great_expectations.core.usage_statistics.usage_statistics import send_usage_message
from great_expectations.data_context.data_context.base_data_context import (
    BaseDataContext,
)
from great_expectations.data_context.data_context.cloud_data_context import (
    CloudDataContext,
)
from great_expectations.data_context.migrator.configuration_bundle import (
    ConfigurationBundle,
    ConfigurationBundleJsonSerializer,
    ConfigurationBundleSchema,
)
from great_expectations.data_context.store.ge_cloud_store_backend import (
    ErrorPayload,
    GeCloudRESTResource,
    GeCloudStoreBackend,
    construct_json_payload,
    construct_url,
)

logger = logging.getLogger(__name__)


class MigrationResponse(NamedTuple):
    message: str
    status_code: int
    success: bool


class CloudMigrator:
    def __init__(
        self,
        context: BaseDataContext,
        ge_cloud_base_url: Optional[str] = None,
        ge_cloud_access_token: Optional[str] = None,
        ge_cloud_organization_id: Optional[str] = None,
    ) -> None:
        self._context = context

        cloud_config = CloudDataContext.get_ge_cloud_config(
            ge_cloud_base_url=ge_cloud_base_url,
            ge_cloud_access_token=ge_cloud_access_token,
            ge_cloud_organization_id=ge_cloud_organization_id,
        )

        ge_cloud_base_url = cloud_config.base_url
        ge_cloud_access_token = cloud_config.access_token
        ge_cloud_organization_id = cloud_config.organization_id

        # Invariant due to `get_ge_cloud_config` raising an error if any config values are missing
        if not ge_cloud_organization_id:
            raise ValueError(
                "An organization id must be present when performing a migration"
            )

        self._ge_cloud_base_url = ge_cloud_base_url
        self._ge_cloud_access_token = ge_cloud_access_token
        self._ge_cloud_organization_id = ge_cloud_organization_id

        self._session = create_session(access_token=ge_cloud_access_token)

        self._unsuccessful_validations = {}

    @classmethod
    def migrate(
        cls,
        context: BaseDataContext,
        test_migrate: bool,
        ge_cloud_base_url: Optional[str] = None,
        ge_cloud_access_token: Optional[str] = None,
        ge_cloud_organization_id: Optional[str] = None,
    ) -> "CloudMigrator":
        """Migrate your Data Context to GX Cloud.

        Args:
            context: The Data Context you wish to migrate.
            test_migrate: True if this is a test, False if you want to perform
                the migration.
            ge_cloud_base_url: Optional, you may provide this alternatively via
                environment variable GE_CLOUD_BASE_URL
            ge_cloud_access_token: Optional, you may provide this alternatively
                via environment variable GE_CLOUD_ACCESS_TOKEN
            ge_cloud_organization_id: Optional, you may provide this alternatively
                via environment variable GE_CLOUD_ORGANIZATION_ID

        Returns:
            CloudMigrator instance
        """
        event = UsageStatsEvents.CLOUD_MIGRATE.value
        event_payload = {"organization_id": ge_cloud_organization_id}
        try:
            cloud_migrator: CloudMigrator = cls(
                context=context,
                ge_cloud_base_url=ge_cloud_base_url,
                ge_cloud_access_token=ge_cloud_access_token,
                ge_cloud_organization_id=ge_cloud_organization_id,
            )
            cloud_migrator._migrate_to_cloud(test_migrate)
            if not test_migrate:  # Only send an event if this is not a test run.
                send_usage_message(
                    data_context=context,
                    event=event,
                    event_payload=event_payload,
                    success=True,
                )
            return cloud_migrator
        except Exception as e:
            # Note we send an event on any exception here
            if not test_migrate:
                send_usage_message(
                    data_context=context,
                    event=event,
                    event_payload=event_payload,
                    success=False,
                )
            raise ge_exceptions.MigrationError(
                "Migration failed. Please check the error message for more details."
            ) from e

    def retry_unsuccessful_validations(self) -> None:
        validations = self._unsuccessful_validations
        if not validations:
            print("No unsuccessful validations found!")
            return

        self._process_validation_results(serialized_validation_results=validations)
        if validations:
            self._print_unsuccessful_validation_message()

    def _migrate_to_cloud(self, test_migrate: bool) -> None:
        self._print_migration_introduction_message()

        configuration_bundle: ConfigurationBundle = ConfigurationBundle(
            context=self._context
        )
        self._emit_warnings(
            configuration_bundle=configuration_bundle, test_migrate=test_migrate
        )
        self._print_configuration_bundle_summary(
            configuration_bundle=configuration_bundle
        )

        serialized_bundle = self._serialize_configuration_bundle(
            configuration_bundle=configuration_bundle
        )
        serialized_validation_results = self._prepare_validation_results(
            serialized_bundle=serialized_bundle
        )

        if not self._send_configuration_bundle(
            serialized_bundle=serialized_bundle, test_migrate=test_migrate
        ):
            return  # Exit early as validation results cannot be sent if the main payload fails

        self._send_validation_results(
            serialized_validation_results=serialized_validation_results,
            test_migrate=test_migrate,
        )

        self._print_migration_conclusion_message()

    def _emit_warnings(
        self, configuration_bundle: ConfigurationBundle, test_migrate: bool
    ) -> None:
        if test_migrate:
            self._warn_about_test_migrate()
        if not configuration_bundle.is_usage_stats_enabled():
            self._warn_about_usage_stats_disabled()
        if configuration_bundle.datasources:
            self._warn_about_bundle_contains_datasources()

    def _warn_about_test_migrate(self) -> None:
        logger.warning(
            "This is a test run! Please pass `test_migrate=False` to begin the "
            "actual migration (e.g. `CloudMigrator.migrate(context=context, test_migrate=False)`).\n"
        )

    def _warn_about_usage_stats_disabled(self) -> None:
        logger.warning(
            "We noticed that you had disabled usage statistics tracking. "
            "Please note that by migrating your context to GX Cloud your new Cloud Data Context "
            "will emit usage statistics. These statistics help us understand how we can improve "
            "the product and we hope you don't mind!\n"
        )

    def _warn_about_bundle_contains_datasources(self) -> None:
        logger.warning(
            "Since your existing context includes one or more datasources, "
            "please note that if your credentials are included in the datasource config "
            "they will be sent to the GX Cloud backend. We recommend storing your credentials "
            "locally in config_variables.yml or in environment variables referenced "
            "from your configuration rather than directly in your configuration. Please see "
            "our documentation for more details.\n"
        )

    def _print_configuration_bundle_summary(
        self, configuration_bundle: ConfigurationBundle
    ) -> None:
        to_print = (
            (
                "Datasource",
                configuration_bundle.datasources,
            ),  # This needs to print the whole config, not just the summary
            ("Checkpoint", configuration_bundle.checkpoints),
            ("Expectation Suite", configuration_bundle.expectation_suites),
            ("Profiler", configuration_bundle.profilers),
        )

        print("[Step 1/4: Bundling context configuration]")
        for name, collection in to_print:
            self._print_object_summary(obj_name=name, obj_collection=collection)

    def _print_object_summary(
        self, obj_name: str, obj_collection: List[AbstractConfig]
    ) -> None:
        length = len(obj_collection)

        summary = f"  Bundled {length} {obj_name}(s)"
        if length:
            summary += ":"
        print(summary)

        for obj in obj_collection[:10]:
            print(f"    {obj.name}")

        if length > 10:
            extra = length - 10
            print(f"    ({extra} other {obj_name.lower()}(s) not displayed)")

    def _serialize_configuration_bundle(
        self, configuration_bundle: ConfigurationBundle
    ) -> dict:
        serializer = ConfigurationBundleJsonSerializer(
            schema=ConfigurationBundleSchema()
        )
        serialized_bundle = serializer.serialize(configuration_bundle)
        return serialized_bundle

    def _prepare_validation_results(self, serialized_bundle: dict) -> Dict[str, dict]:
        print("[Step 2/4: Preparing validation results]")
        return serialized_bundle.pop("validation_results")

    def _send_configuration_bundle(
        self, serialized_bundle: dict, test_migrate: bool
    ) -> bool:
        print("[Step 3/4: Sending context configuration]")
        if test_migrate:
            return True

        response = self._post_to_cloud_backend(
            resource_name="migration",
            resource_type="migration",
            attributes_key="bundle",
            attributes_value=serialized_bundle,
        )

        if not response.success:
            print(
                "\nThere was an error sending your configuration to GX Cloud!\n"
                "We have reverted your GX Cloud configuration to the state before the migration. "
                "Please check your configuration before re-attempting the migration.\n\n"
                "The server returned the following error:\n"
                f"  Code : {response.status_code}\n  Error: {response.message}"
            )

        return response.success

    def _send_validation_results(
        self,
        serialized_validation_results: Dict[str, dict],
        test_migrate: bool,
    ) -> None:
        print("[Step 4/4: Sending validation results]")
        if test_migrate:
            return

        self._process_validation_results(
            serialized_validation_results=serialized_validation_results
        )

    def _process_validation_results(
        self, serialized_validation_results: Dict[str, dict]
    ) -> None:
        # 20220928 - Chetan - We want to use the static lookup tables in GeCloudStoreBackend
        # to ensure the appropriate URL and payload shape. This logic should be moved to
        # a more central location.
        resource_type = GeCloudRESTResource.EXPECTATION_VALIDATION_RESULT
        resource_name = GeCloudStoreBackend.RESOURCE_PLURALITY_LOOKUP_DICT[
            resource_type
        ]
        attributes_key = GeCloudStoreBackend.PAYLOAD_ATTRIBUTES_KEYS[resource_type]

        unsuccessful_validations = {}

        for i, (key, validation_result) in enumerate(
            serialized_validation_results.items()
        ):
            response = self._post_to_cloud_backend(
                resource_name=resource_name,
                resource_type=resource_type,
                attributes_key=attributes_key,
                attributes_value=validation_result,
            )

            progress = f"({i+1}/{len(serialized_validation_results)})"

            if response.success:
                print(f"  Sent validation result {progress}")
            else:
                print(f"  Error sending validation result '{key}' {progress}")
                unsuccessful_validations[key] = validation_result

        self._unsuccessful_validations = unsuccessful_validations

    def _post_to_cloud_backend(
        self,
        resource_name: str,
        resource_type: str,
        attributes_key: str,
        attributes_value: dict,
    ) -> MigrationResponse:
        url = construct_url(
            base_url=self._ge_cloud_base_url,
            organization_id=self._ge_cloud_organization_id,
            resource_name=resource_name,
        )
        data = construct_json_payload(
            resource_type=resource_type,
            organization_id=self._ge_cloud_organization_id,
            attributes_key=attributes_key,
            attributes_value=attributes_value,
        )
        response = self._session.post(url, json=data)
        return self._parse_cloud_response(response=response)

    def _parse_cloud_response(self, response: requests.Response) -> MigrationResponse:
        success = response.ok
        status_code = response.status_code

        # TODO: Handle success/failure cases and parse errors from Cloud responses

        # Use `get_user_friendly_error_message` instead of custom error parsing
        message = ""
        if not success:
            try:
                response_json = cast(ErrorPayload, response.json())
                errors = response_json.get("errors", [])
                for error in errors:
                    detail = error.get("detail")
                    if detail:
                        message += f"{detail}\n"
            except requests.exceptions.JSONDecodeError:
                message = "Something went wrong!"

        return MigrationResponse(
            message=message, status_code=status_code, success=success
        )

    def _print_unsuccessful_validation_message(self) -> None:
        length = len(self._unsuccessful_validations)
        summary = f"\nPlease note that there were {length} validation result(s) that were not successfully migrated:"
        print(summary)
        for key in self._unsuccessful_validations:
            print(f"  {key}")

        print(
            "\nTo retry uploading these validation results, you can use the following "
            "code snippet:\n"
            "  `migrator.retry_unsuccessful_validations()`"
        )

    def _print_migration_introduction_message(self) -> None:
        print(
            "Thank you for using Great Expectations!\n\n"
            "We will now begin the migration process to GX Cloud. First we will bundle "
            "your existing context configuration and send it to the cloud backend. Then "
            "we will send each of your validation results.\n"
        )

    def _print_migration_conclusion_message(self) -> None:
        if self._unsuccessful_validations:
            print("\nPartial Success!")
        else:
            print("\nSuccess!")

        print(
            "Now that you have migrated your Data Context to GX Cloud, you should use your "
            "Cloud Data Context from now on to interact with Great Expectations. "
            "If you continue to use your existing Data Context your configurations could "
            "become out of sync. "
        )

        if self._unsuccessful_validations:
            self._print_unsuccessful_validation_message()
