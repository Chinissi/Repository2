from __future__ import annotations

import copy
import logging
import pathlib
import re
from dataclasses import dataclass
from typing import List

import pytest

import great_expectations.exceptions as ge_exceptions
from great_expectations.alias_types import PathStr
from great_expectations.datasource.fluent.data_asset.data_connector import (
    FilesystemDataConnector,
)
from great_expectations.datasource.fluent.interfaces import (
    SortersDefinition,
    TestConnectionError,
)
from great_expectations.datasource.fluent.spark_file_path_datasource import (
    CSVAsset,
)
from great_expectations.datasource.fluent.spark_filesystem_datasource import (
    SparkFilesystemDatasource,
)

logger = logging.getLogger(__name__)


@pytest.fixture
def spark_filesystem_datasource(
    empty_data_context, test_backends
) -> SparkFilesystemDatasource:
    if "SparkDFDataset" not in test_backends:
        pytest.skip("No spark backend selected.")

    base_directory_rel_path = pathlib.Path(
        "..", "..", "test_sets", "taxi_yellow_tripdata_samples"
    )
    base_directory_abs_path = (
        pathlib.Path(__file__)
        .parent.joinpath(base_directory_rel_path)
        .resolve(strict=True)
    )
    spark_filesystem_datasource = SparkFilesystemDatasource(
        name="spark_filesystem_datasource",
        base_directory=base_directory_abs_path,
    )
    spark_filesystem_datasource._data_context = empty_data_context
    return spark_filesystem_datasource


@pytest.fixture
def csv_path() -> pathlib.Path:
    relative_path = pathlib.Path(
        "..", "..", "test_sets", "taxi_yellow_tripdata_samples"
    )
    abs_csv_path = (
        pathlib.Path(__file__).parent.joinpath(relative_path).resolve(strict=True)
    )
    return abs_csv_path


@pytest.mark.unit
def test_construct_spark_filesystem_datasource(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    assert spark_filesystem_datasource.name == "spark_filesystem_datasource"


@pytest.mark.unit
def test_add_csv_asset_to_datasource(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        header=True,
        infer_schema=True,
    )
    assert asset.name == "csv_asset"
    m1 = asset.batching_regex.match("this_can_be_named_anything.csv")
    assert m1 is not None


# TODO: Parametrize with all asset types
@pytest.mark.unit
def test_add_parquet_asset_to_datasource(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_parquet_asset(
        name="parquet_asset",
        datetime_rebase_mode="EXCEPTION",
        int_96_rebase_mode="CORRECTED",
        merge_schema=False,
    )
    assert asset.name == "parquet_asset"
    m1 = asset.batching_regex.match("this_can_be_named_anything.parquet")
    assert m1 is not None
    assert asset.datetime_rebase_mode == "EXCEPTION"
    assert asset.int_96_rebase_mode == "CORRECTED"
    assert asset.merge_schema is False


@pytest.mark.unit
def test_add_csv_asset_with_batching_regex_to_datasource(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(\d{4})-(\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    assert asset.name == "csv_asset"
    assert asset.batching_regex.match("random string") is None
    assert asset.batching_regex.match("yellow_tripdata_sample_11D1-22.csv") is None
    m1 = asset.batching_regex.match("yellow_tripdata_sample_1111-22.csv")
    assert m1 is not None


@pytest.mark.unit
def test_construct_csv_asset_directly():
    # noinspection PyTypeChecker
    asset = CSVAsset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(\d{4})-(\d{2})\.csv",  # Ignoring IDE warning (type declarations are consistent).
    )
    assert asset.name == "csv_asset"
    assert asset.batching_regex.match("random string") is None
    assert asset.batching_regex.match("yellow_tripdata_sample_11D1-22.csv") is None
    m1 = asset.batching_regex.match("yellow_tripdata_sample_1111-22.csv")
    assert m1 is not None


@pytest.mark.unit
def test_csv_asset_with_batching_regex_unnamed_parameters(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(\d{4})-(\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    options = asset.batch_request_options
    assert options == (
        "batch_request_param_1",
        "batch_request_param_2",
        "path",
    )


@pytest.mark.unit
def test_csv_asset_with_batching_regex_named_parameters(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    options = asset.batch_request_options
    assert options == ("year", "month", "path")


@pytest.mark.unit
def test_csv_asset_with_some_batching_regex_named_parameters(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    options = asset.batch_request_options
    assert options == ("batch_request_param_1", "month", "path")


@pytest.mark.unit
def test_csv_asset_with_non_string_batching_regex_named_parameters(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    with pytest.raises(ge_exceptions.InvalidBatchRequestError):
        # year is an int which will raise an error
        asset.build_batch_request({"year": 2018, "month": "04"})


@pytest.mark.unit
@pytest.mark.parametrize(
    "path",
    [
        pytest.param("samples_2020", id="str"),
        pytest.param(pathlib.Path("samples_2020"), id="pathlib.Path"),
    ],
)
def test_get_batch_list_from_directory_one_batch(
    path: PathStr,
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    """What does this test and why?

    A "directory" asset should only have a single batch."""
    asset = spark_filesystem_datasource.add_directory_csv_asset(
        name="csv_asset",
        data_directory=path,
        header=True,
        infer_schema=True,
    )
    request = asset.build_batch_request()
    batches = asset.get_batch_list_from_batch_request(request)
    assert len(batches) == 1


@pytest.mark.integration
@pytest.mark.parametrize(
    "path",
    [
        pytest.param("samples_2020", id="str"),
        pytest.param(pathlib.Path("samples_2020"), id="pathlib.Path"),
    ],
)
def test_get_batch_list_from_directory_merges_files(
    path: PathStr,
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    """What does this test and why?

    Adding a "directory" asset should only add a single batch merging all files into one dataframe.

    Marked as an integration test since this uses the execution engine to actually load the files.
    """
    asset = spark_filesystem_datasource.add_directory_csv_asset(
        name="csv_asset",
        data_directory=path,
        header=True,
        infer_schema=True,
    )
    request = asset.build_batch_request()
    batches = asset.get_batch_list_from_batch_request(request)
    batch_data = batches[0].data
    # The directory contains 12 files with 10,000 records each so the batch data
    # (spark dataframe) should contain 120,000 records:
    assert batch_data.dataframe.count() == 12 * 10000  # type: ignore[attr-defined]


@pytest.mark.unit
def test_get_batch_list_from_fully_specified_batch_request(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    request = asset.build_batch_request({"year": "2018", "month": "04"})
    batches = asset.get_batch_list_from_batch_request(request)
    assert len(batches) == 1
    batch = batches[0]
    assert batch.batch_request.datasource_name == spark_filesystem_datasource.name
    assert batch.batch_request.data_asset_name == asset.name

    path = "yellow_tripdata_sample_2018-04.csv"
    assert batch.batch_request.options == {"path": path, "year": "2018", "month": "04"}
    assert batch.metadata == {"path": path, "year": "2018", "month": "04"}

    assert batch.id == "spark_filesystem_datasource-csv_asset-year_2018-month_04"


@pytest.mark.unit
def test_get_batch_list_from_partially_specified_batch_request(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    # Verify test directory has files that don't match what we will query for
    file_name: PathStr
    all_files: List[str] = [
        file_name.stem
        for file_name in list(
            pathlib.Path(spark_filesystem_datasource.base_directory).iterdir()
        )
    ]
    # assert there are files that are not csv files
    assert any(not file_name.endswith("csv") for file_name in all_files)
    # assert there are 12 files from 2018
    files_for_2018 = [
        file_name for file_name in all_files if file_name.find("2018") >= 0
    ]
    assert len(files_for_2018) == 12

    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    request = asset.build_batch_request({"year": "2018"})
    batches = asset.get_batch_list_from_batch_request(request)
    assert (len(batches)) == 12
    batch_filenames = [pathlib.Path(batch.metadata["path"]).stem for batch in batches]
    assert set(files_for_2018) == set(batch_filenames)

    @dataclass(frozen=True)
    class YearMonth:
        year: str
        month: str

    expected_year_month = {
        YearMonth(year="2018", month=format(m, "02d")) for m in range(1, 13)
    }
    batch_year_month = {
        YearMonth(year=batch.metadata["year"], month=batch.metadata["month"])
        for batch in batches
    }
    assert expected_year_month == batch_year_month


@pytest.mark.unit
@pytest.mark.parametrize(
    "order_by",
    [
        ["+year", "month"],
        ["+year", "+month"],
        ["+year", "-month"],
        ["year", "month"],
        ["year", "+month"],
        ["year", "-month"],
        ["-year", "month"],
        ["-year", "+month"],
        ["-year", "-month"],
        ["month", "+year"],
        ["+month", "+year"],
        ["-month", "+year"],
        ["month", "year"],
        ["+month", "year"],
        ["-month", "year"],
        ["month", "-year"],
        ["+month", "-year"],
        ["-month", "-year"],
    ],
)
def test_spark_sorter(
    spark_filesystem_datasource: SparkFilesystemDatasource,
    order_by: SortersDefinition,
):
    # Verify test directory has files we expect
    years = ["2018", "2019", "2020"]
    months = [format(m, "02d") for m in range(1, 13)]
    file_name: PathStr
    all_files: List[str] = [
        file_name.stem
        for file_name in list(
            pathlib.Path(spark_filesystem_datasource.base_directory).iterdir()
        )
    ]
    # assert there are 12 files for each year
    for year in years:
        files_for_year = [
            file_name
            for file_name in all_files
            if file_name.find(f"yellow_tripdata_sample_{year}") == 0
        ]
        assert len(files_for_year) == 12

    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
        order_by=order_by,
    )
    batches = asset.get_batch_list_from_batch_request(asset.build_batch_request())
    assert (len(batches)) == 36

    @dataclass(frozen=True)
    class TimeRange:
        key: str
        range: List[str]

    ordered_years = reversed(years) if "-year" in order_by else years
    ordered_months = reversed(months) if "-month" in order_by else months
    if "year" in order_by[0]:  # type: ignore[operator]
        ordered = [
            TimeRange(key="year", range=ordered_years),  # type: ignore[arg-type]
            TimeRange(key="month", range=ordered_months),  # type: ignore[arg-type]
        ]
    else:
        ordered = [
            TimeRange(key="month", range=ordered_months),  # type: ignore[arg-type]
            TimeRange(key="year", range=ordered_years),  # type: ignore[arg-type]
        ]

    batch_index = -1
    for range1 in ordered[0].range:
        key1 = ordered[0].key
        for range2 in ordered[1].range:
            key2 = ordered[1].key
            batch_index += 1
            metadata = batches[batch_index].metadata
            assert metadata[key1] == range1
            assert metadata[key2] == range2


def bad_batching_regex_config(
    csv_path: pathlib.Path,
) -> tuple[re.Pattern, TestConnectionError]:
    batching_regex = re.compile(
        r"green_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv"
    )
    test_connection_error = TestConnectionError(
        f"""No file at base_directory path "{csv_path.resolve()}" matched regular expressions pattern "{batching_regex.pattern}" and/or glob_directive "**/*" for DataAsset "csv_asset"."""
    )
    return batching_regex, test_connection_error


@pytest.fixture(params=[bad_batching_regex_config])
def datasource_test_connection_error_messages(
    csv_path: pathlib.Path,
    spark_filesystem_datasource: SparkFilesystemDatasource,
    request,
) -> tuple[SparkFilesystemDatasource, TestConnectionError]:
    batching_regex, test_connection_error = request.param(csv_path=csv_path)
    csv_asset = CSVAsset(
        name="csv_asset",
        batching_regex=batching_regex,
    )
    csv_asset._datasource = spark_filesystem_datasource
    spark_filesystem_datasource.assets = [
        csv_asset,
    ]
    csv_asset._data_connector = FilesystemDataConnector(
        datasource_name=spark_filesystem_datasource.name,
        data_asset_name=csv_asset.name,
        batching_regex=batching_regex,
        base_directory=spark_filesystem_datasource.base_directory,
        data_context_root_directory=spark_filesystem_datasource.data_context_root_directory,
    )
    csv_asset._test_connection_error_message = test_connection_error
    return spark_filesystem_datasource, test_connection_error


@pytest.mark.unit
def test_test_connection_failures(
    datasource_test_connection_error_messages: tuple[
        SparkFilesystemDatasource, TestConnectionError
    ]
):
    (
        spark_filesystem_datasource,
        test_connection_error,
    ) = datasource_test_connection_error_messages

    with pytest.raises(type(test_connection_error)) as e:
        spark_filesystem_datasource.test_connection()

    assert str(e.value) == str(test_connection_error)


@pytest.mark.unit
def test_get_batch_list_from_batch_request_does_not_modify_input_batch_request(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    request = asset.build_batch_request({"year": "2018"})
    request_before_call = copy.deepcopy(request)
    batches = asset.get_batch_list_from_batch_request(request)
    # We assert the request before the call to get_batch_list_from_batch_request is equal to the request after the
    # call. This test exists because this call was modifying the request.
    assert request == request_before_call
    # We get all 12 batches, one for each month of 2018.
    assert len(batches) == 12


@pytest.mark.unit
def test_add_csv_asset_with_batch_metadata(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    asset_specified_metadata = {"asset_level_metadata": "my_metadata"}
    asset = spark_filesystem_datasource.add_csv_asset(
        name="csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
        batch_metadata=asset_specified_metadata,
    )
    batch_options = {"year": "2018", "month": "05"}
    request = asset.build_batch_request(batch_options)
    batches = asset.get_batch_list_from_batch_request(request)
    assert len(batches) == 1
    assert batches[0].metadata == {
        "path": "yellow_tripdata_sample_2018-05.csv",
        **batch_options,
        **asset_specified_metadata,
    }


@pytest.mark.integration
def test_add_directory_csv_asset_with_splitter(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    source = spark_filesystem_datasource

    # TODO: Starting with integration test for PoC, but the filesystem should be mocked

    ############# First get one large batch using directory_csv_asset
    # 1. source.add_directory_csv_asset()
    asset = source.add_directory_csv_asset(
        name="directory_csv_asset",
        data_directory="samples_2020",
        header=True,
        infer_schema=True,
    )
    assert len(source.assets) == 1
    assert asset == source.assets[0]

    # Before applying the splitter, there should be one batch
    pre_splitter_batch_request = asset.build_batch_request()
    pre_splitter_batches = asset.get_batch_list_from_batch_request(
        pre_splitter_batch_request
    )
    pre_splitter_expected_num_batches = 1
    assert len(pre_splitter_batches) == pre_splitter_expected_num_batches

    # 3. Assert asset
    assert asset.name == "directory_csv_asset"
    assert asset.data_directory == pathlib.Path("samples_2020")
    assert asset.datasource == source
    assert asset.batch_request_options == ("path",)
    # 4. Assert batch request
    assert pre_splitter_batch_request.datasource_name == source.name
    assert pre_splitter_batch_request.data_asset_name == asset.name
    assert pre_splitter_batch_request.options == {}

    pre_splitter_batch_data = pre_splitter_batches[0].data
    # The directory contains 12 files with 10,000 records each so the batch data
    # (spark dataframe) should contain 120,000 records:
    assert pre_splitter_batch_data.dataframe.count() == 12 * 10000  # type: ignore[attr-defined]

    ############# Now add a splitter to the asset and get one batch (that should be only one month after the split)

    # TODO: For now I think we need to split on something other than year and month just to
    #  be certain that this is working as expected and that we aren't just getting the data from one month file
    #  This whole test is a PoC and should be cleaned up / parametrized.

    # Make sure our data is as expected
    passenger_counts = sorted(
        [
            pc.passenger_count
            for pc in pre_splitter_batch_data.dataframe.select("passenger_count")
            .dropna(subset=["passenger_count"])
            .distinct()
            .collect()
        ]
    )
    assert passenger_counts == [0, 1, 2, 3, 4, 5, 6]

    asset_with_passenger_count_splitter = asset.add_splitter_column_value(
        column_name="passenger_count"
    )
    assert asset_with_passenger_count_splitter.batch_request_options == (
        "path",
        "passenger_count",
    )
    post_passenger_count_splitter_batch_request = (
        asset_with_passenger_count_splitter.build_batch_request({"passenger_count": 2})
    )
    post_passenger_count_splitter_batch_list = (
        asset_with_passenger_count_splitter.get_batch_list_from_batch_request(
            post_passenger_count_splitter_batch_request
        )
    )
    post_splitter_expected_num_batches = 1
    # TODO: For some reason we are not getting a batch from post_splitter_batch_request
    # breakpoint()
    assert (
        len(post_passenger_count_splitter_batch_list)
        == post_splitter_expected_num_batches
    )

    ###################### TODO: replace the below with passenger_count

    # 2. asset.add_splitter_year_and_month()
    asset_with_splitter = asset.add_splitter_year_and_month(
        column_name="pickup_datetime"
    )
    # post_splitter_batch_request = asset.build_batch_request()
    # post_splitter_batch_request = asset.build_batch_request({"year": 2020})
    post_splitter_batch_request = asset_with_splitter.build_batch_request(
        {"year": 2020, "month": 10}
    )
    # TODO: How do I get all batches after applying splitter?
    #  Looks like we dont get all batches for spark / file based https://docs.greatexpectations.io/docs/0.15.50/guides/connecting_to_your_data/advanced/how_to_configure_a_dataconnector_for_splitting_and_sampling_a_file_system_or_blob_store/

    # 3. Assert asset
    assert asset_with_splitter.name == "directory_csv_asset"
    assert asset_with_splitter.data_directory == pathlib.Path("samples_2020")
    assert asset_with_splitter.datasource == source
    assert asset_with_splitter.batch_request_options == ("path", "year", "month")
    # 4. Assert batch request
    assert post_splitter_batch_request.datasource_name == source.name
    assert post_splitter_batch_request.data_asset_name == asset_with_splitter.name
    assert post_splitter_batch_request.options == {"year": 2020, "month": 10}

    # 5. Assert num batches
    post_splitter_batches = asset_with_splitter.get_batch_list_from_batch_request(
        post_splitter_batch_request
    )
    post_splitter_expected_num_batches = 1
    # TODO: For some reason we are not getting a batch from post_splitter_batch_request
    # breakpoint()
    assert len(post_splitter_batches) == post_splitter_expected_num_batches

    # Make sure amount of data in batches is as expected
    post_splitter_batch_data = post_splitter_batches[0].data
    # The directory contains 12 files with 10,000 records each so the batch data
    # (spark dataframe) should contain 10,000 records after splitting by month:
    from great_expectations.compatibility.pyspark import (
        functions as F,
    )

    num_records_should_be = (
        pre_splitter_batch_data.dataframe.filter(
            F.year(F.col("pickup_datetime")) == 2020
        )
        .filter(F.month(F.col("pickup_datetime")) == 10)
        .count()
    )
    assert num_records_should_be == 10001

    assert post_splitter_batch_data.dataframe.count() == num_records_should_be  # type: ignore[attr-defined]


@pytest.mark.integration
def test_add_file_csv_asset_with_splitter(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    source = spark_filesystem_datasource

    # TODO: Starting with integration test for PoC, but the filesystem should be mocked

    ############# First get one large batch using directory_csv_asset
    # 1. source.add_directory_csv_asset()
    asset = source.add_csv_asset(
        name="file_csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    assert len(source.assets) == 1
    assert asset == source.assets[0]

    # Before applying the splitter, there should be one batch
    # pre_splitter_batch_request = asset.build_batch_request()
    # pre_splitter_batches = asset.get_batch_list_from_batch_request(
    #     pre_splitter_batch_request
    # )
    # pre_splitter_expected_num_batches = 36
    # assert len(pre_splitter_batches) == pre_splitter_expected_num_batches

    # 3. Assert asset
    assert asset.name == "file_csv_asset"
    assert asset.datasource == source
    assert asset.batch_request_options == (
        "year",
        "month",
        "path",
    )
    # 4. Assert batch request
    # assert pre_splitter_batch_request.datasource_name == source.name
    # assert pre_splitter_batch_request.data_asset_name == asset.name
    # assert pre_splitter_batch_request.options == {}

    # pre_splitter_batch_data = pre_splitter_batches[0].data
    # # The directory contains 12 files with 10,000 records each so the batch data
    # # (spark dataframe) should contain 120,000 records:
    # assert pre_splitter_batch_data.dataframe.count() == 10000  # type: ignore[attr-defined]

    # breakpoint()
    single_batch_batch_request = asset.build_batch_request(
        {"year": "2020", "month": "10"}
    )
    single_batch_list = asset.get_batch_list_from_batch_request(
        single_batch_batch_request
    )
    assert len(single_batch_list) == 1

    pre_splitter_batch_data = single_batch_list[0].data

    ############# Now add a splitter to the asset and get one batch (that should be only one month after the split)

    # TODO: For now I think we need to split on something other than year and month just to
    #  be certain that this is working as expected and that we aren't just getting the data from one month file
    #  This whole test is a PoC and should be cleaned up / parametrized.

    # Make sure our data is as expected
    passenger_counts = sorted(
        [
            pc.passenger_count
            for pc in pre_splitter_batch_data.dataframe.select("passenger_count")
            .dropna(subset=["passenger_count"])
            .distinct()
            .collect()
        ]
    )
    assert passenger_counts == [0, 1, 2, 3, 4, 5, 6]

    asset_with_passenger_count_splitter = asset.add_splitter_column_value(
        column_name="passenger_count"
    )
    assert asset_with_passenger_count_splitter.batch_request_options == (
        "year",
        "month",
        "path",
        "passenger_count",
    )

    post_passenger_count_splitter_batch_request = (
        asset_with_passenger_count_splitter.build_batch_request(
            {"year": "2020", "month": "10", "passenger_count": 2}
        )
    )
    post_passenger_count_splitter_batch_list = (
        asset_with_passenger_count_splitter.get_batch_list_from_batch_request(
            post_passenger_count_splitter_batch_request
        )
    )
    post_splitter_expected_num_batches = 1
    # TODO: For some reason we are not getting a batch from post_splitter_batch_request
    assert (
        len(post_passenger_count_splitter_batch_list)
        == post_splitter_expected_num_batches
    )

    # Make sure we only have passenger_count == 2 in our batch data
    post_splitter_batch_data = post_passenger_count_splitter_batch_list[0].data
    from great_expectations.compatibility.pyspark import functions as F

    assert (
        post_splitter_batch_data.dataframe.filter(F.col("passenger_count") == 2).count()
        == 1258
    )
    assert (
        post_splitter_batch_data.dataframe.filter(F.col("passenger_count") != 2).count()
        == 0
    )

    ###################### TODO: does this work with conflicting splitter kwargs and regex (year and month)
    ###################### TODO: does this work with conflicting splitter kwargs and regex change to splitter on month only with a different month

    # breakpoint()
    # 2. asset.add_splitter_year_and_month()
    asset_with_splitter = asset.add_splitter_year_and_month(
        column_name="pickup_datetime"
    )
    # post_splitter_batch_request = asset.build_batch_request()
    # post_splitter_batch_request = asset.build_batch_request({"year": 2020})
    post_splitter_batch_request = asset_with_splitter.build_batch_request(
        {"year": "2020", "month": "10"}
    )
    # TODO: How do I get all batches after applying splitter?
    #  Looks like we dont get all batches for spark / file based https://docs.greatexpectations.io/docs/0.15.50/guides/connecting_to_your_data/advanced/how_to_configure_a_dataconnector_for_splitting_and_sampling_a_file_system_or_blob_store/

    # 3. Assert asset
    assert asset_with_splitter.name == "file_csv_asset"
    assert asset_with_splitter.datasource == source
    assert asset_with_splitter.batch_request_options == (
        "year",
        "month",
        "path",
        "year",
        "month",
    )
    # 4. Assert batch request
    assert post_splitter_batch_request.datasource_name == source.name
    assert post_splitter_batch_request.data_asset_name == asset_with_splitter.name
    assert post_splitter_batch_request.options == {"year": "2020", "month": "10"}

    # 5. Assert num batches
    post_splitter_batches = asset_with_splitter.get_batch_list_from_batch_request(
        post_splitter_batch_request
    )
    post_splitter_expected_num_batches = 1
    # TODO: For some reason we are not getting a batch from post_splitter_batch_request
    # breakpoint()
    assert len(post_splitter_batches) == post_splitter_expected_num_batches

    # Make sure amount of data in batches is as expected
    post_splitter_batch_data = post_splitter_batches[0].data
    # The directory contains 12 files with 10,000 records each so the batch data
    # (spark dataframe) should contain 10,000 records after splitting by month:
    from great_expectations.compatibility.pyspark import (
        functions as F,
    )

    num_records_should_be = (
        pre_splitter_batch_data.dataframe.filter(
            F.year(F.col("pickup_datetime")) == 2020
        )
        .filter(F.month(F.col("pickup_datetime")) == 10)
        .count()
    )
    assert num_records_should_be == 10000

    assert post_splitter_batch_data.dataframe.count() == num_records_should_be  # type: ignore[attr-defined]


@pytest.mark.integration
def test_add_file_csv_asset_with_splitter_conflicting_identifier(
    spark_filesystem_datasource: SparkFilesystemDatasource,
):
    source = spark_filesystem_datasource

    # TODO: Starting with integration test for PoC, but the filesystem should be mocked

    ############# First get one large batch using directory_csv_asset
    # 1. source.add_directory_csv_asset()
    asset = source.add_csv_asset(
        name="file_csv_asset",
        batching_regex=r"yellow_tripdata_sample_(?P<year>\d{4})-(?P<month>\d{2})\.csv",
        header=True,
        infer_schema=True,
    )
    assert len(source.assets) == 1
    assert asset == source.assets[0]

    single_batch_batch_request = asset.build_batch_request(
        {"year": "2020", "month": "10"}
    )
    single_batch_list = asset.get_batch_list_from_batch_request(
        single_batch_batch_request
    )
    assert len(single_batch_list) == 1

    pre_splitter_batch_data = single_batch_list[0].data

    ###################### TODO: does this work with conflicting splitter kwargs and regex (year and month)
    ###################### TODO: does this work with conflicting splitter kwargs and regex change to splitter on month only with a different month

    # breakpoint()
    # 2. asset.add_splitter_year_and_month()
    asset_with_splitter = asset.add_splitter_year_and_month(
        column_name="pickup_datetime"
    )
    # post_splitter_batch_request = asset.build_batch_request()
    # post_splitter_batch_request = asset.build_batch_request({"year": 2020})
    post_splitter_batch_request = asset_with_splitter.build_batch_request(
        {"year": "2020", "month": "10"}
    )
    # TODO: How do I get all batches after applying splitter?
    #  Looks like we dont get all batches for spark / file based https://docs.greatexpectations.io/docs/0.15.50/guides/connecting_to_your_data/advanced/how_to_configure_a_dataconnector_for_splitting_and_sampling_a_file_system_or_blob_store/

    # 3. Assert asset
    assert asset_with_splitter.name == "file_csv_asset"
    assert asset_with_splitter.datasource == source
    assert asset_with_splitter.batch_request_options == (
        "year",
        "month",
        "path",
        "year",
        "month",
    )
    # 4. Assert batch request
    assert post_splitter_batch_request.datasource_name == source.name
    assert post_splitter_batch_request.data_asset_name == asset_with_splitter.name
    assert post_splitter_batch_request.options == {"year": "2020", "month": "10"}

    # 5. Assert num batches
    post_splitter_batches = asset_with_splitter.get_batch_list_from_batch_request(
        post_splitter_batch_request
    )
    post_splitter_expected_num_batches = 1
    # TODO: For some reason we are not getting a batch from post_splitter_batch_request
    # breakpoint()
    assert len(post_splitter_batches) == post_splitter_expected_num_batches

    # Make sure amount of data in batches is as expected
    post_splitter_batch_data = post_splitter_batches[0].data
    # The directory contains 12 files with 10,000 records each so the batch data
    # (spark dataframe) should contain 10,000 records after splitting by month:
    from great_expectations.compatibility.pyspark import (
        functions as F,
    )

    num_records_should_be = (
        pre_splitter_batch_data.dataframe.filter(
            F.year(F.col("pickup_datetime")) == 2020
        )
        .filter(F.month(F.col("pickup_datetime")) == 10)
        .count()
    )
    assert num_records_should_be == 10000

    assert post_splitter_batch_data.dataframe.count() == num_records_should_be  # type: ignore[attr-defined]
