import os
from typing import List

import pytest

from contrib.capitalone_dataprofiler_expectations.capitalone_dataprofiler_expectations.metrics import (
    DataProfilerProfileReport,
)
from contrib.capitalone_dataprofiler_expectations.capitalone_dataprofiler_expectations.rule_based_profiler.domain_builder.data_profiler_column_domain_builder import (
    DataProfilerColumnDomainBuilder,
)
from great_expectations.core.domain import (
    INFERRED_SEMANTIC_TYPE_KEY,
    Domain,
    SemanticDomainTypes,
)
from great_expectations.core.metric_domain_types import MetricDomainTypes
from great_expectations.data_context import FileDataContext
from great_expectations.rule_based_profiler.domain_builder import DomainBuilder
from great_expectations.rule_based_profiler.parameter_container import (
    ParameterContainer,
    build_parameter_container_for_variables,
)

test_root_path: str = os.path.dirname(  # noqa: PTH120
    os.path.dirname(os.path.dirname(os.path.realpath(__file__)))  # noqa: PTH120
)


_ = DataProfilerProfileReport  # registers this metric


@pytest.mark.integration
@pytest.mark.slow  # 1.21s
def test_data_profiler_column_domain_builder(
    bobby_columnar_table_multi_batch_deterministic_data_context: FileDataContext,
):
    data_context: FileDataContext = (
        bobby_columnar_table_multi_batch_deterministic_data_context
    )

    variables_configs: dict = {
        "estimator": "quantiles",
        "false_positive_rate": 1.0e-2,
        "mostly": 1.0,
    }
    variables: ParameterContainer = build_parameter_container_for_variables(
        variables_configs=variables_configs
    )

    batch_request: dict = {
        "datasource_name": "taxi_pandas",
        "data_connector_name": "monthly",
        "data_asset_name": "my_reports",
        "data_connector_query": {"index": -1},
    }

    profile_path = os.path.join(  # noqa: PTH118
        test_root_path,
        "data_profiler_files",
        "profile.pkl",
    )

    domain_builder: DomainBuilder = DataProfilerColumnDomainBuilder(
        profile_path=profile_path,
        data_context=data_context,
    )
    domains: List[Domain] = domain_builder.get_domains(
        rule_name="my_rule",
        variables=variables,
        batch_request=batch_request,
    )

    assert len(domains) == 18
    assert domains == [
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "vendor_id",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "vendor_id": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "pickup_datetime",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "pickup_datetime": SemanticDomainTypes.TEXT.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "dropoff_datetime",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "dropoff_datetime": SemanticDomainTypes.TEXT.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "passenger_count",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "passenger_count": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "trip_distance",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "trip_distance": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "rate_code_id",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "rate_code_id": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "store_and_fwd_flag",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "store_and_fwd_flag": SemanticDomainTypes.TEXT.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "pickup_location_id",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "pickup_location_id": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "dropoff_location_id",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "dropoff_location_id": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "payment_type",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "payment_type": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "fare_amount",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "fare_amount": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "extra",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "extra": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "mta_tax",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "mta_tax": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "tip_amount",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "tip_amount": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "tolls_amount",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "tolls_amount": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "improvement_surcharge",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "improvement_surcharge": SemanticDomainTypes.NUMERIC.value,
                }
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "total_amount",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "total_amount": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
        {
            "rule_name": "my_rule",
            "domain_type": MetricDomainTypes.COLUMN.value,
            "domain_kwargs": {
                "column": "congestion_surcharge",
            },
            "details": {
                INFERRED_SEMANTIC_TYPE_KEY: {
                    "congestion_surcharge": SemanticDomainTypes.NUMERIC.value,
                },
            },
        },
    ]
