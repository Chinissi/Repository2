import datetime
import os
from typing import List, Optional

import pandas as pd
import pytest
from ruamel.yaml import YAML

from great_expectations import DataContext
from great_expectations.core import ExpectationSuite
from great_expectations.profiler.profiler import Profiler

yaml = YAML()


# TODO: AJB 20210416 Move this fixture, generalize, add to quagga, add more column types
@pytest.fixture
def multibatch_generic_csv_generator():
    """
    Construct a series of csv files with many data types for use in multibatch testing
    """

    def _multibatch_generic_csv_generator(
        data_path: str,
        start_date: Optional[datetime.datetime] = None,
        num_event_batches: Optional[int] = 20,
        num_events_per_batch: Optional[int] = 5,
    ) -> List[str]:

        if start_date is None:
            start_date = datetime.datetime(2000, 1, 1)

        file_list = []
        for batch_num in range(num_event_batches):
            # generate a dataframe with multiple column types
            batch_start_date = start_date + datetime.timedelta(
                days=(batch_num * num_events_per_batch)
            )
            # TODO: AJB 20210416 Add more column types
            df = pd.DataFrame(
                {
                    "event_date": [
                        (batch_start_date + datetime.timedelta(days=i)).strftime(
                            "%Y-%m-%d"
                        )
                        for i in range(num_events_per_batch)
                    ],
                    "batch_num": [batch_num + 1 for _ in range(num_events_per_batch)],
                }
            )
            filename = f"csv_batch_{batch_num + 1:03}_of_{num_event_batches:03}.csv"
            file_list.append(filename)
            df.to_csv(
                os.path.join(data_path, filename),
                index_label="intra_batch_index",
            )

        return file_list

    return _multibatch_generic_csv_generator


@pytest.fixture
def multibatch_generic_csv_generator_context(monkeypatch, empty_data_context):
    context: DataContext = empty_data_context
    monkeypatch.chdir(context.root_directory)
    data_relative_path = "../data"
    data_path = os.path.join(context.root_directory, data_relative_path)
    os.makedirs(data_path, exist_ok=True)

    data_connector_base_directory = "./"
    monkeypatch.setenv("base_directory", data_connector_base_directory)
    monkeypatch.setenv("data_fixtures_root", data_relative_path)

    datasource_name = "generic_csv_generator"
    data_connector_name = "daily_data_connector"
    asset_name = "daily_data_asset"
    datasource_config = fr"""
class_name: Datasource
module_name: great_expectations.datasource
execution_engine:
  module_name: great_expectations.execution_engine
  class_name: PandasExecutionEngine
data_connectors:
  {data_connector_name}:
    class_name: ConfiguredAssetFilesystemDataConnector
    assets:
      {asset_name}:
        module_name: great_expectations.datasource.data_connector.asset
        group_names:
          - batch
          - total_batches
        pattern: csv_batch_(\d.+)_of_(\d.+)\.csv
        reader_options:
          delimiter: ","
        class_name: Asset
        base_directory: $data_fixtures_root
        glob_directive: "*.csv"
    base_directory: $base_directory
    module_name: great_expectations.datasource.data_connector
        """

    context.add_datasource(name=datasource_name, **yaml.load(datasource_config))

    assert context.list_datasources() == [
        {
            "class_name": "Datasource",
            "data_connectors": {
                data_connector_name: {
                    "assets": {
                        asset_name: {
                            "base_directory": data_relative_path,
                            "class_name": "Asset",
                            "glob_directive": "*.csv",
                            "group_names": ["batch", "total_batches"],
                            "module_name": "great_expectations.datasource.data_connector.asset",
                            "pattern": "csv_batch_(\\d.+)_of_(\\d.+)\\.csv",
                        }
                    },
                    "base_directory": data_connector_base_directory,
                    "class_name": "ConfiguredAssetFilesystemDataConnector",
                    "module_name": "great_expectations.datasource.data_connector",
                }
            },
            "execution_engine": {
                "class_name": "PandasExecutionEngine",
                "module_name": "great_expectations.execution_engine",
            },
            "module_name": "great_expectations.datasource",
            "name": "generic_csv_generator",
        }
    ]
    return context


def test_batches_are_accessible(
    monkeypatch,
    multibatch_generic_csv_generator,
    multibatch_generic_csv_generator_context,
):
    """
    What does this test and why?
    Batches created in the multibatch_generic_csv_generator fixture should be available using the
    multibatch_generic_csv_generator_context
    This test most likely duplicates tests elsewhere, but it is more of a test of the configurable fixture.
    """

    context: DataContext = multibatch_generic_csv_generator_context
    data_relative_path = "../data"
    data_path = os.path.join(context.root_directory, data_relative_path)
    datasource_name = "generic_csv_generator"
    data_connector_name = "daily_data_connector"
    asset_name = "daily_data_asset"

    datasource = context.datasources[datasource_name]

    data_connector = datasource.data_connectors[data_connector_name]

    file_list = multibatch_generic_csv_generator(data_path=data_path)

    assert (
        data_connector._get_data_reference_list_from_cache_by_data_asset_name(
            data_asset_name=asset_name
        )
        == file_list
    )


@pytest.fixture(scope="module")
def simple_multibatch_profiler_configuration_yaml():
    config = """
name: BasicSuiteBuilderProfiler
variables:
  alert_threshold: 0.01
rules:
  datetime:
    domain_builder:
      class_name: SimpleSemanticTypeColumnDomainBuilder
      module_name: great_expectations.profiler.domain_builder.simple_semantic_type_domain_builder
      type_filters: datetime
    parameter_builders:
      - parameter_id: my_dateformat
        class_name: SimpleDateFormatStringParameterBuilder
        module_name: great_expectations.profiler.parameter_builder.simple_dateformat_string_parameter_builder
        domain_kwargs: $domain.domain_kwargs
    configuration_builders:
        - expectation: expect_column_values_to_match_strftime_format
          column: $domain.domain_kwargs.column
          date_fmt: $my_dateformat.parameter.date_string
  numeric:
    class_name: SemanticTypeColumnDomainBuilder
    type: numeric
    parameter_builders:
      - id: quantile_ranges
        class_name: MultiBatchBootstrappedMetricDistributionParameterBuilder
        batch_request:
          partition_request:
            partition_index: "-10:"
        metric_configuration:
          metric_name: column.quantile_values
          metric_domain_kwargs: $domain.domain_kwargs
          metric_value_kwargs:
            quantiles:
              - 0.05
              - 0.25
              - 0.50
              - 0.75
              - 0.95
        p_values:
          min_value: ($alert_threshold / 2)
          max_value: 1 - ($alert_threshold / 2)
    configuration_builders:
      - expectation: expect_column_quantile_values_to_be_between
        value_ranges: $quantile_ranges
"""
    return config


@pytest.fixture(scope="module")
def very_simple_multibatch_profiler_configuration_yaml():
    config = """
name: BasicSuiteBuilderProfiler
rules:
  numeric:
    domain_builder:
      class_name: SimpleSemanticTypeColumnDomainBuilder
      module_name: great_expectations.profiler.domain_builder.simple_semantic_type_domain_builder
      type_filters: datetime
    parameter_builders:
      - parameter_id: min
        class_name: MetricParameterBuilder
        module_name: great_expectations.profiler.parameter_builder.metric_parameter_builder
        metric_name: column.min
        metric_domain_kwargs: $domain.domain_kwargs
      - parameter_id: max
        class_name: MetricParameterBuilder
        module_name: great_expectations.profiler.parameter_builder.metric_parameter_builder
        metric_name: column.max
        metric_domain_kwargs: $domain.domain_kwargs
    configuration_builders:
      - expectation: expect_column_values_to_be_between
        module_name: great_expectations.profiler.configuration_builder.parameter_id_configuration_builder
        min_value: $min
        max_value: $max
"""
    return config


# TODO: 20210416 AJB - Parametrize these tests, pull fixtures from ?? (public repo e.g. here or quagga?)


def test_profiler_init_manual_very_simple_multibatch_profiler_configuration_yaml(
    multibatch_generic_csv_generator_context,
    very_simple_multibatch_profiler_configuration_yaml,
    multibatch_generic_csv_generator,
):

    # TODO: 20210416 AJB - THIS IS A HACK - use/create a ProfilerConfig & ProfilerConfigSchema with validation etc
    full_profiler_config_dict = yaml.load(
        very_simple_multibatch_profiler_configuration_yaml
    )
    rule_configs = full_profiler_config_dict["rules"]

    profiler = Profiler(
        rule_configs=rule_configs,
        data_context=multibatch_generic_csv_generator_context,
    )
    suite = profiler.profile()

    # TODO: 20210416 AJB Make these assertions against the expected ExpectationSuite for the config / data
    assert suite == ExpectationSuite()
    assert False


def test_profiler_init_manual_simple_multibatch_profiler_configuration_yaml(
    multibatch_generic_csv_generator_context,
    simple_multibatch_profiler_configuration_yaml,
    multibatch_generic_csv_generator,
):

    # TODO: 20210416 AJB - THIS IS A HACK - use/create a ProfilerConfig & ProfilerConfigSchema with validation etc
    full_profiler_config_dict = yaml.load(simple_multibatch_profiler_configuration_yaml)
    rule_configs = full_profiler_config_dict["rules"]

    profiler = Profiler(
        rule_configs=rule_configs,
        data_context=multibatch_generic_csv_generator_context,
    )
    suite = profiler.profile()

    # TODO: 20210416 AJB Make these assertions against the expected ExpectationSuite for the config / data
    assert suite == ExpectationSuite()
    assert False


def test_profiler_rule_init_helper(
    taxicab_context, simple_multibatch_profiler_configuration_yaml
):
    assert False
