from __future__ import annotations

"""
This file contains demo code for the column_descriptive_metrics module.
Unit, integration and end-to-end tests should be written to replace this code.
"""
import uuid
from unittest import mock

import pytest

from great_expectations.agent.models import RunColumnDescriptiveMetricsEvent
from great_expectations.data_context import CloudDataContext
from great_expectations.experimental.metric_repository.batch_inspector import (
    BatchInspector,
)
from great_expectations.agent.actions.run_column_descriptive_metrics_action import (
    ColumnDescriptiveMetricsAction,
)
from great_expectations.experimental.metric_repository.metric_repository import (
    MetricRepository,
)
from great_expectations.datasource.fluent.batch_request import BatchRequest

import pandas as pd
from great_expectations.experimental.metric_repository.metrics import (
    Metric,
    Metrics,
    NumericTableMetric,
    MetricException,
)


@pytest.fixture
def metric_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def run_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def cloud_context_and_batch_request_with_simple_dataframe(
    empty_cloud_context_fluent: CloudDataContext,
):
    context = empty_cloud_context_fluent
    datasource = context.sources.add_pandas(name="my_pandas_datasource")

    d = {"col1": [1, 2], "col2": [3, 4]}
    df = pd.DataFrame(data=d)

    name = "dataframe"
    data_asset = datasource.add_dataframe_asset(name=name)
    batch_request = data_asset.build_batch_request(dataframe=df)
    return context, batch_request


def test_demo_batch_inspector(
    metric_id: uuid.UUID,
    run_id: uuid.UUID,
    cloud_context_and_batch_request_with_simple_dataframe: tuple[
        CloudDataContext, BatchRequest
    ],
):
    """This is a demo of how to get column descriptive metrics,
    this should be replaced with proper tests."""

    context, batch_request = cloud_context_and_batch_request_with_simple_dataframe

    event = RunColumnDescriptiveMetricsEvent(
        datasource_name=batch_request.datasource_name,
        data_asset_name=batch_request.data_asset_name,
    )
    action = ColumnDescriptiveMetricsAction(context)

    with mock.patch(
        f"{BatchInspector.__module__}.{BatchInspector.__name__}._generate_run_id",
        return_value=run_id,
    ), mock.patch(
        f"{BatchInspector.__module__}.{BatchInspector.__name__}._generate_metric_id",
        return_value=metric_id,
    ), mock.patch(
        f"{MetricRepository.__module__}.{MetricRepository.__name__}.add",
    ) as mock_add:
        action.run(event, "some_event_id")

    metrics_stored = mock_add.call_args[0][0]

    assert metrics_stored == Metrics(
        id=run_id,
        metrics=[
            NumericTableMetric(
                id=metric_id,
                run_id=run_id,
                # TODO: reimplement batch param
                # batch=batch_from_action,
                metric_name="table.row_count",
                value=2,
                exception=MetricException(),
            ),
            # TableMetric(
            #     id=metric_id,
            #     run_id=run_id,
            #     # TODO: reimplement batch param
            #     # batch=batch_from_action,
            #     metric_name="table.columns",
            #     value=Value(value=["col1", "col2"]),
            #     details={},
            # ),
        ],
    )


# def test_cant_init_abstract_metric(
#     metric_id: uuid.UUID,
#     run_id: uuid.UUID,
# ):
#     # TODO: Which exception?
#     with pytest.raises():
#         _ = (
#             Metric(
#                 id=metric_id,
#                 run_id=run_id,
#                 # TODO: reimplement batch param
#                 # batch=batch_from_action,
#                 metric_name="table.columns",
#                 value=Value(value=["col1", "col2"]),
#                 details={},
#             ),
#         )
