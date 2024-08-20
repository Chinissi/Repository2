from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Type
from unittest import mock

import pandas as pd
import pytest

import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations import __version__ as GX_VERSION
from great_expectations.core.batch_definition import BatchDefinition
from great_expectations.core.expectation_suite import ExpectationSuite
from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
    ExpectationValidationResult,
)
from great_expectations.core.result_format import ResultFormat
from great_expectations.core.serdes import _IdentifierBundle
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context.data_context.abstract_data_context import AbstractDataContext
from great_expectations.data_context.data_context.cloud_data_context import (
    CloudDataContext,
)
from great_expectations.data_context.data_context.context_factory import (
    ProjectManager,
    set_context,
)
from great_expectations.data_context.data_context.ephemeral_data_context import (
    EphemeralDataContext,
)
from great_expectations.data_context.store.validation_results_store import ValidationResultsStore
from great_expectations.data_context.types.resource_identifiers import (
    GXCloudIdentifier,
    ValidationResultIdentifier,
)
from great_expectations.datasource.fluent.pandas_datasource import (
    CSVAsset,
    PandasDatasource,
    _PandasDataAsset,
)
from great_expectations.exceptions.exceptions import (
    BatchDefinitionNotAddedError,
    ExpectationSuiteNotAddedError,
    ResourceNotAddedError,
    ValidationDefinitionNotAddedError,
    ValidationDefinitionRelatedResourcesNotAddedError,
)
from great_expectations.execution_engine.execution_engine import ExecutionEngine
from great_expectations.expectations.expectation_configuration import (
    ExpectationConfiguration,
)
from great_expectations.validator.v1_validator import (
    OldValidator,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock  # noqa: TID251

    from pytest_mock import MockerFixture

BATCH_ID = "my_batch_id"
DATA_SOURCE_NAME = "my_datasource"
ASSET_NAME = "csv_asset"
BATCH_DEFINITION_NAME = "my_batch_definition"
ACTIVE_BATCH_SPEC = {
    "type": "table",
    "data_asset_name": ASSET_NAME,
    "table_name": "test_table",
    "schema_name": "test_schema",
    "batch_identifiers": {"date": {"year": 2017, "month": 12, "day": 3}},
    "partitioner_method": "partition_on_year_and_month_and_day",
    "partitioner_kwargs": {"column_name": "date"},
}
ACTIVE_BATCH_DEFINITION = {
    "datasource_name": DATA_SOURCE_NAME,
    "data_connector_name": "fluent",
    "data_asset_name": ASSET_NAME,
    "batch_identifiers": {"date": {"year": 2017, "month": 12, "day": 3}},
}
BATCH_MARKERS = {"ge_load_time": "20240814T172846.050804Z"}


@pytest.fixture
def ephemeral_context():
    return gx.get_context(mode="ephemeral")


@pytest.fixture
def validation_definition(ephemeral_context: EphemeralDataContext) -> ValidationDefinition:
    context = ephemeral_context
    batch_definition = (
        context.data_sources.add_pandas(DATA_SOURCE_NAME)
        .add_csv_asset(ASSET_NAME, "taxi.csv")  # type: ignore
        .add_batch_definition(BATCH_DEFINITION_NAME)
    )
    return context.validation_definitions.add(
        ValidationDefinition(
            name="my_validation",
            data=batch_definition,
            suite=context.suites.add(ExpectationSuite(name="my_suite")),
        )
    )


@pytest.fixture
def dataframe_validation_definition(
    ephemeral_context: EphemeralDataContext,
) -> ValidationDefinition:
    context = ephemeral_context
    batch_definition = (
        context.data_sources.add_pandas(DATA_SOURCE_NAME)
        .add_dataframe_asset("dataframe_asset")
        .add_batch_definition_whole_dataframe("dataframe_batch_def")
    )
    return context.validation_definitions.add(
        ValidationDefinition(
            name="my_dataframe_validation",
            data=batch_definition,
            suite=context.suites.add(ExpectationSuite(name="my_suite")),
        )
    )


@pytest.fixture
def postgres_validation_definition(
    ephemeral_context: EphemeralDataContext,
) -> ValidationDefinition:
    context = ephemeral_context
    batch_definition = (
        ephemeral_context.data_sources.add_postgres(
            name="postgres_datasource",
            connection_string="postgresql+psycopg2://postgres:postgres@localhost:5432/test_ci",
        )
        .add_table_asset(name="my_asset", table_name="postgres_taxi_data")
        .add_batch_definition_monthly(name="my_batch_definition", column="pickup_datetime")
    )
    return context.validation_definitions.add(
        ValidationDefinition(
            name="my_postgres_validation",
            data=batch_definition,
            suite=context.suites.add(ExpectationSuite(name="my_suite")),
        )
    )


@pytest.fixture
def cloud_validation_definition(
    empty_cloud_data_context: CloudDataContext,
) -> ValidationDefinition:
    context = empty_cloud_data_context
    batch_definition = (
        empty_cloud_data_context.data_sources.add_pandas(DATA_SOURCE_NAME)
        .add_csv_asset(ASSET_NAME, "taxi.csv")  # type: ignore
        .add_batch_definition(BATCH_DEFINITION_NAME)
    )
    return context.validation_definitions.add(
        ValidationDefinition(
            name="my_validation",
            data=batch_definition,
            suite=context.suites.add(ExpectationSuite(name="my_suite")),
        )
    )


@pytest.mark.unit
def test_validation_definition_data_properties(validation_definition: ValidationDefinition):
    assert validation_definition.data.name == BATCH_DEFINITION_NAME
    assert validation_definition.batch_definition.name == BATCH_DEFINITION_NAME
    assert validation_definition.asset.name == ASSET_NAME
    assert validation_definition.data_source.name == DATA_SOURCE_NAME


class TestValidationRun:
    @pytest.fixture
    def mock_validator(self, mocker: MockerFixture):
        """Set up our ProjectManager to return a mock Validator"""
        with mock.patch.object(ProjectManager, "get_validator") as mock_get_validator:
            with mock.patch.object(OldValidator, "graph_validate"):
                gx.get_context(mode="ephemeral")
                mock_execution_engine = mocker.MagicMock(
                    spec=ExecutionEngine,
                    batch_manager=mocker.MagicMock(
                        active_batch_id=BATCH_ID,
                        active_batch_spec=ACTIVE_BATCH_SPEC,
                        active_batch_definition=ACTIVE_BATCH_DEFINITION,
                        active_batch_markers=BATCH_MARKERS,
                    ),
                )
                mock_validator = OldValidator(execution_engine=mock_execution_engine)
                mock_get_validator.return_value = mock_validator

                yield mock_validator

    @pytest.mark.unit
    def test_passes_simple_data_to_validator(
        self,
        mock_validator: MagicMock,
        validation_definition: ValidationDefinition,
    ):
        validation_definition.suite.add_expectation(
            gxe.ExpectColumnMaxToBeBetween(column="foo", max_value=1)
        )
        mock_validator.graph_validate.return_value = [ExpectationValidationResult(success=True)]

        validation_definition.run()

        mock_validator.graph_validate.assert_called_with(
            configurations=[
                ExpectationConfiguration(
                    type="expect_column_max_to_be_between",
                    kwargs={"column": "foo", "max_value": 1.0},
                )
            ],
            runtime_configuration={"result_format": "SUMMARY"},
        )

    @mock.patch.object(_PandasDataAsset, "build_batch_request", autospec=True)
    @pytest.mark.unit
    def test_passes_complex_data_to_validator(
        self,
        mock_build_batch_request,
        mock_validator: MagicMock,
        validation_definition: ValidationDefinition,
    ):
        validation_definition.suite.add_expectation(
            gxe.ExpectColumnMaxToBeBetween(column="foo", max_value={"$PARAMETER": "max_value"})
        )
        mock_validator.graph_validate.return_value = [ExpectationValidationResult(success=True)]

        validation_definition.run(
            batch_parameters={"year": 2024},
            expectation_parameters={"max_value": 9000},
            result_format=ResultFormat.COMPLETE,
        )

        mock_validator.graph_validate.assert_called_with(
            configurations=[
                ExpectationConfiguration(
                    type="expect_column_max_to_be_between",
                    kwargs={"column": "foo", "max_value": 9000},
                )
            ],
            runtime_configuration={"result_format": "COMPLETE"},
        )

    @pytest.mark.unit
    def test_returns_expected_data(
        self,
        mock_validator: MagicMock,
        validation_definition: ValidationDefinition,
    ):
        graph_validate_results = [ExpectationValidationResult(success=True)]
        mock_validator.graph_validate.return_value = graph_validate_results

        output = validation_definition.run()

        # Ignore meta for purposes of this test
        output["meta"] = {}
        assert output == ExpectationSuiteValidationResult(
            results=graph_validate_results,
            success=True,
            suite_name="empty_suite",
            statistics={
                "evaluated_expectations": 1,
                "successful_expectations": 1,
                "unsuccessful_expectations": 0,
                "success_percent": 100.0,
            },
            meta={},
        )

    @pytest.mark.parametrize("checkpoint_id", [None, "my_checkpoint_id"])
    @pytest.mark.unit
    def test_adds_requisite_fields(
        self,
        mock_validator: MagicMock,
        validation_definition: ValidationDefinition,
        checkpoint_id: str | None,
    ):
        mock_validator.graph_validate.return_value = []

        output = validation_definition.run(checkpoint_id=checkpoint_id)

        assert output.meta == {
            "validation_id": validation_definition.id,
            "checkpoint_id": checkpoint_id,
            "batch_parameters": None,
            "batch_spec": ACTIVE_BATCH_SPEC,
            "batch_markers": BATCH_MARKERS,
            "active_batch_definition": ACTIVE_BATCH_DEFINITION,
            "great_expectations_version": GX_VERSION,
        }

    @pytest.mark.unit
    def test_adds_correct_batch_parameter_field_for_dataframes(
        self,
        mock_validator: MagicMock,
        dataframe_validation_definition: ValidationDefinition,
    ) -> None:
        mock_validator.graph_validate.return_value = []

        output = dataframe_validation_definition.run(
            checkpoint_id=None,
            batch_parameters={"dataframe": pd.DataFrame({"a": ["1", "2", "3", "4", "5"]})},
        )

        assert output.meta == {
            "validation_id": dataframe_validation_definition.id,
            "checkpoint_id": None,
            "batch_parameters": {"dataframe": "<DATAFRAME>"},
            "batch_spec": ACTIVE_BATCH_SPEC,
            "batch_markers": BATCH_MARKERS,
            "active_batch_definition": ACTIVE_BATCH_DEFINITION,
            "great_expectations_version": GX_VERSION,
        }

    @pytest.mark.parametrize(
        "batch_parameters",
        [
            pytest.param(None),
            pytest.param({"year": 2024}),
            pytest.param({"year": 2024, "month": 10}),
        ],
    )
    @pytest.mark.postgresql
    def test_adds_correct_batch_parameter_fields_for_postgres(
        self,
        mock_validator: MagicMock,
        postgres_validation_definition: ValidationDefinition,
        batch_parameters: dict | None,
    ) -> None:
        mock_validator.graph_validate.return_value = []

        output = postgres_validation_definition.run(
            checkpoint_id=None,
            batch_parameters=batch_parameters,
        )

        assert output.meta == {
            "validation_id": postgres_validation_definition.id,
            "checkpoint_id": None,
            "batch_parameters": batch_parameters,
            "batch_spec": ACTIVE_BATCH_SPEC,
            "batch_markers": BATCH_MARKERS,
            "active_batch_definition": ACTIVE_BATCH_DEFINITION,
            "great_expectations_version": GX_VERSION,
        }

    @mock.patch.object(ValidationResultsStore, "set")
    @pytest.mark.unit
    def test_persists_validation_results_for_non_cloud(
        self,
        mock_validation_results_store_set: MagicMock,
        mock_validator: MagicMock,
        validation_definition: ValidationDefinition,
    ):
        validation_definition.suite.add_expectation(
            gxe.ExpectColumnMaxToBeBetween(column="foo", max_value=1)
        )
        mock_validator.graph_validate.return_value = [ExpectationValidationResult(success=True)]

        validation_definition.run()

        mock_validator.graph_validate.assert_called_with(
            configurations=[
                ExpectationConfiguration(
                    type="expect_column_max_to_be_between",
                    kwargs={"column": "foo", "max_value": 1.0},
                )
            ],
            runtime_configuration={"result_format": "SUMMARY"},
        )

        # validate we are calling set on the store with data that's roughly the right shape
        [(_, kwargs)] = mock_validation_results_store_set.call_args_list
        key = kwargs["key"]
        value = kwargs["value"]
        assert isinstance(key, ValidationResultIdentifier)
        assert key.batch_identifier == BATCH_ID
        assert value.success is True

    @mock.patch.object(ValidationResultsStore, "set")
    @pytest.mark.unit
    def test_persists_validation_results_for_cloud(
        self,
        mock_validation_results_store_set: MagicMock,
        mock_validator: MagicMock,
        cloud_validation_definition: ValidationDefinition,
    ):
        expectation = gxe.ExpectColumnMaxToBeBetween(column="foo", max_value=1)
        cloud_validation_definition.suite.add_expectation(expectation=expectation)
        mock_validator.graph_validate.return_value = [
            ExpectationValidationResult(success=True, expectation_config=expectation.configuration)
        ]

        cloud_validation_definition.run()

        # validate we are calling set on the store with data that's roughly the right shape
        [(_, kwargs)] = mock_validation_results_store_set.call_args_list
        key = kwargs["key"]
        value = kwargs["value"]
        assert isinstance(key, GXCloudIdentifier)
        assert value.success is True

    @mock.patch.object(ValidationResultsStore, "set")
    @pytest.mark.unit
    def test_cloud_validation_def_creates_rendered_content(
        self,
        mock_validation_results_store_set: MagicMock,
        mock_validator: MagicMock,
        cloud_validation_definition: ValidationDefinition,
    ):
        expectation = gxe.ExpectColumnMaxToBeBetween(column="foo", max_value=1)
        cloud_validation_definition.suite.add_expectation(expectation=expectation)
        mock_validator.graph_validate.return_value = [
            ExpectationValidationResult(success=True, expectation_config=expectation.configuration)
        ]

        result = cloud_validation_definition.run()

        assert len(result.results) == 1
        assert result.results[0].expectation_config is not None
        assert result.results[0].expectation_config.rendered_content is not None
        assert result.results[0].rendered_content is not None

    @pytest.mark.unit
    def test_dependencies_not_added_raises_error(self, validation_definition: ValidationDefinition):
        validation_definition.suite.id = None
        validation_definition.data.id = None

        with pytest.raises(ValidationDefinitionRelatedResourcesNotAddedError) as e:
            validation_definition.run()

        assert [type(err) for err in e.value.errors] == [
            BatchDefinitionNotAddedError,
            ExpectationSuiteNotAddedError,
        ]


class TestValidationDefinitionSerialization:
    ds_name = "my_ds"
    asset_name = "my_asset"
    batch_definition_name = "my_batch_definition"
    suite_name = "my_suite"
    validation_definition_name = "my_validation"

    @pytest.fixture
    def context(self, in_memory_runtime_context: EphemeralDataContext) -> EphemeralDataContext:
        return in_memory_runtime_context

    @pytest.fixture
    def validation_definition_data(
        self,
        context: EphemeralDataContext,
    ) -> tuple[PandasDatasource, CSVAsset, BatchDefinition]:
        ds = context.data_sources.add_pandas(self.ds_name)
        asset = ds.add_csv_asset(self.asset_name, "data.csv")
        batch_definition = asset.add_batch_definition(self.batch_definition_name)

        return ds, asset, batch_definition

    @pytest.fixture
    def validation_definition_suite(self, context: EphemeralDataContext) -> ExpectationSuite:
        return context.suites.add(ExpectationSuite(self.suite_name))

    @pytest.mark.unit
    def test_validation_definition_serialization(
        self,
        in_memory_runtime_context: EphemeralDataContext,
        validation_definition_data: tuple[PandasDatasource, CSVAsset, BatchDefinition],
        validation_definition_suite: ExpectationSuite,
    ):
        context = in_memory_runtime_context
        pandas_ds, csv_asset, batch_definition = validation_definition_data

        ds_id = str(uuid.uuid4())
        pandas_ds.id = ds_id

        asset_id = str(uuid.uuid4())
        csv_asset.id = asset_id

        batch_definition_id = str(uuid.uuid4())
        batch_definition.id = batch_definition_id

        suite_id = str(uuid.uuid4())
        validation_definition_suite.id = suite_id

        validation_definition = context.validation_definitions.add(
            ValidationDefinition(
                name=self.validation_definition_name,
                data=batch_definition,
                suite=validation_definition_suite,
            )
        )

        actual = json.loads(validation_definition.json(models_as_dict=False))
        expected = {
            "name": self.validation_definition_name,
            "data": {
                "datasource": {
                    "name": pandas_ds.name,
                    "id": ds_id,
                },
                "asset": {
                    "name": csv_asset.name,
                    "id": asset_id,
                },
                "batch_definition": {
                    "name": batch_definition.name,
                    "id": batch_definition_id,
                },
            },
            "suite": {
                "name": validation_definition_suite.name,
                "id": suite_id,
            },
            "id": mock.ANY,
        }

        assert actual == expected
        assert actual["id"] is not None

    def _assert_contains_valid_uuid(self, data: dict):
        id = data.pop("id")
        data["id"] = mock.ANY
        try:
            uuid.UUID(id)
        except ValueError:
            pytest.fail(f"Expected {id} to be a valid UUID")

    @pytest.mark.unit
    def test_validation_definition_deserialization_success(
        self,
        context: EphemeralDataContext,
        validation_definition_data: tuple[PandasDatasource, CSVAsset, BatchDefinition],
        validation_definition_suite: ExpectationSuite,
    ):
        _, _, batch_definition = validation_definition_data

        serialized_config = {
            "name": self.validation_definition_name,
            "data": {
                "datasource": {
                    "name": self.ds_name,
                    "id": None,
                },
                "asset": {
                    "name": self.asset_name,
                    "id": None,
                },
                "batch_definition": {
                    "name": self.batch_definition_name,
                    "id": None,
                },
            },
            "suite": {
                "name": validation_definition_suite.name,
                "id": validation_definition_suite.id,
            },
            "id": None,
        }

        validation_definition = ValidationDefinition.parse_obj(serialized_config)
        assert validation_definition.name == self.validation_definition_name
        assert validation_definition.data == batch_definition
        assert validation_definition.suite == validation_definition_suite

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "serialized_config, error_substring",
        [
            pytest.param(
                {
                    "name": validation_definition_name,
                    "data": {
                        "asset": {
                            "name": asset_name,
                            "id": None,
                        },
                        "batch_definition": {
                            "name": batch_definition_name,
                            "id": None,
                        },
                    },
                    "suite": {
                        "name": suite_name,
                        "id": None,
                    },
                    "id": None,
                },
                "data did not contain expected identifiers",
                id="bad_data_format[missing_datasource]",
            ),
            pytest.param(
                {
                    "name": validation_definition_name,
                    "data": {},
                    "suite": {
                        "name": suite_name,
                        "id": None,
                    },
                    "id": None,
                },
                "data did not contain expected identifiers",
                id="bad_data_format[empty_field]",
            ),
            pytest.param(
                {
                    "name": validation_definition_name,
                    "data": {
                        "datasource": {
                            "name": ds_name,
                            "id": None,
                        },
                        "asset": {
                            "name": asset_name,
                            "id": None,
                        },
                        "batch_definition": {
                            "name": batch_definition_name,
                            "id": None,
                        },
                    },
                    "suite": {},
                    "id": None,
                },
                "suite did not contain expected identifiers",
                id="bad_suite_format",
            ),
        ],
    )
    def test_validation_definition_deserialization_bad_format(
        self, serialized_config: dict, error_substring: str
    ):
        with pytest.raises(ValueError, match=f"{error_substring}*."):
            ValidationDefinition.parse_obj(serialized_config)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "serialized_config, error_substring",
        [
            pytest.param(
                {
                    "name": validation_definition_name,
                    "data": {
                        "datasource": {
                            "name": ds_name,
                            "id": None,
                        },
                        "asset": {
                            "name": asset_name,
                            "id": None,
                        },
                        "batch_definition": {
                            "name": batch_definition_name,
                            "id": None,
                        },
                    },
                    "suite": {
                        "name": "i_do_not_exist",
                        "id": None,
                    },
                    "id": None,
                },
                "Could not find suite",
                id="non_existant_suite",
            ),
            pytest.param(
                {
                    "name": validation_definition_name,
                    "data": {
                        "datasource": {
                            "name": "i_do_not_exist",
                            "id": None,
                        },
                        "asset": {
                            "name": asset_name,
                            "id": None,
                        },
                        "batch_definition": {
                            "name": batch_definition_name,
                            "id": None,
                        },
                    },
                    "suite": {
                        "name": suite_name,
                        "id": None,
                    },
                    "id": None,
                },
                "Could not find datasource",
                id="non_existant_datasource",
            ),
            pytest.param(
                {
                    "name": validation_definition_name,
                    "data": {
                        "datasource": {
                            "name": ds_name,
                            "id": None,
                        },
                        "asset": {
                            "name": "i_do_not_exist",
                            "id": None,
                        },
                        "batch_definition": {
                            "name": batch_definition_name,
                            "id": None,
                        },
                    },
                    "suite": {
                        "name": suite_name,
                        "id": None,
                    },
                    "id": None,
                },
                "Could not find asset",
                id="non_existant_asset",
            ),
            pytest.param(
                {
                    "name": validation_definition_name,
                    "data": {
                        "datasource": {
                            "name": ds_name,
                            "id": None,
                        },
                        "asset": {
                            "name": asset_name,
                            "id": None,
                        },
                        "batch_definition": {
                            "name": "i_do_not_exist",
                            "id": None,
                        },
                    },
                    "suite": {
                        "name": suite_name,
                        "id": None,
                    },
                    "id": None,
                },
                "Could not find batch definition",
                id="non_existant_batch_definition",
            ),
        ],
    )
    def test_validation_definition_deserialization_non_existant_resource(
        self,
        validation_definition_data: tuple[PandasDatasource, CSVAsset, BatchDefinition],
        validation_definition_suite: ExpectationSuite,
        serialized_config: dict,
        error_substring: str,
    ):
        with pytest.raises(ValueError, match=f"{error_substring}*."):
            ValidationDefinition.parse_obj(serialized_config)


@pytest.mark.unit
def test_identifier_bundle_with_existing_id(validation_definition: ValidationDefinition):
    validation_definition.id = "fa34fbb7-124d-42ff-9760-e410ee4584a0"

    assert validation_definition.identifier_bundle() == _IdentifierBundle(
        name="my_validation", id="fa34fbb7-124d-42ff-9760-e410ee4584a0"
    )


@pytest.mark.unit
def test_identifier_bundle_no_id(validation_definition: ValidationDefinition):
    validation_definition.id = None

    with pytest.raises(ValidationDefinitionNotAddedError):
        validation_definition.identifier_bundle()


@pytest.mark.unit
def test_save_success(mocker: MockerFixture, validation_definition: ValidationDefinition):
    context = mocker.Mock(spec=AbstractDataContext)
    set_context(project=context)

    store_key = context.validation_definition_store.get_key.return_value
    validation_definition.save()

    context.validation_definition_store.update.assert_called_once_with(
        key=store_key, value=validation_definition
    )


@pytest.mark.parametrize(
    "id,suite_id,batch_def_id,is_added,error_list",
    [
        pytest.param(
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            True,
            [],
            id="validation_id|suite_id|batch_def_id",
        ),
        pytest.param(
            str(uuid.uuid4()),
            None,
            str(uuid.uuid4()),
            False,
            [ExpectationSuiteNotAddedError],
            id="validation_id|no_suite_id|batch_def_id",
        ),
        pytest.param(
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            None,
            False,
            [BatchDefinitionNotAddedError],
            id="validation_id|suite_id|no_batch_def_id",
        ),
        pytest.param(
            str(uuid.uuid4()),
            None,
            None,
            False,
            [BatchDefinitionNotAddedError, ExpectationSuiteNotAddedError],
            id="validation_id|no_suite_id|no_batch_def_id",
        ),
        pytest.param(
            None,
            str(uuid.uuid4()),
            str(uuid.uuid4()),
            False,
            [ValidationDefinitionNotAddedError],
            id="no_validation_id|suite_id|batch_def_id",
        ),
        pytest.param(
            None,
            None,
            str(uuid.uuid4()),
            False,
            [ExpectationSuiteNotAddedError, ValidationDefinitionNotAddedError],
            id="no_validation_id|no_suite_id|batch_def_id",
        ),
        pytest.param(
            None,
            str(uuid.uuid4()),
            None,
            False,
            [BatchDefinitionNotAddedError, ValidationDefinitionNotAddedError],
            id="no_validation_id|suite_id|no_batch_def_id",
        ),
        pytest.param(
            None,
            None,
            None,
            False,
            [
                BatchDefinitionNotAddedError,
                ExpectationSuiteNotAddedError,
                ValidationDefinitionNotAddedError,
            ],
            id="no_validation_id|no_suite_id|no_batch_def_id",
        ),
    ],
)
@pytest.mark.unit
def test_is_added(
    id: str | None,
    suite_id: str | None,
    batch_def_id: str | None,
    is_added: bool,
    error_list: list[Type[ResourceNotAddedError]],
):
    validation_definition = ValidationDefinition(
        name="my_validation_definition",
        id=id,
        suite=ExpectationSuite(name="my_suite", id=suite_id),
        data=BatchDefinition(name="my_batch_def", id=batch_def_id),
    )
    validation_definition_added, errors = validation_definition.is_added()

    assert validation_definition_added == is_added
    assert [type(err) for err in errors] == error_list
