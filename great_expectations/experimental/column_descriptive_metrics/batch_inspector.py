from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from great_expectations.experimental.column_descriptive_metrics.metrics import (
    Metric,
    Metrics,
    Value,
)
from great_expectations.validator.metric_configuration import MetricConfiguration

if TYPE_CHECKING:
    from great_expectations.datasource.fluent.interfaces import Batch
    from great_expectations.validator.validator import Validator


class BatchInspector:
    def __init__(self):
        pass

    def _generate_run_id(self) -> uuid.UUID:
        return uuid.uuid4()

    def get_column_descriptive_metrics(self, validator: Validator) -> Metrics:
        run_id = self._generate_run_id()
        table_row_count = self._get_table_row_count_metric(
            run_id=run_id, validator=validator
        )
        column_names = self._get_column_names_metric(run_id=run_id, validator=validator)
        metrics = Metrics(metrics=[table_row_count, column_names])
        return metrics

    def _get_metric(
        self, metric_name: str, run_id: uuid.UUID, validator: Validator
    ) -> Metric:
        # TODO: Thu - do we need the MetricConfiguration or can we just pass in the metric name?
        #  E.g. metrics_calculator.get_table_metric(metric_name)
        metric_config = MetricConfiguration(
            metric_name=metric_name,
            metric_domain_kwargs={},
            metric_value_kwargs={},
        )

        raw_metric = validator.get_metric(metric_config)

        metric = self._convert_raw_metric_to_metric_object(
            raw_metric=raw_metric,
            metric_config=metric_config,
            run_id=run_id,
            batch=validator.active_batch,
        )

        return metric

    def _get_table_row_count_metric(self, run_id: uuid.UUID, validator) -> Metric:
        return self._get_metric(
            metric_name="table.row_count",
            run_id=run_id,
            validator=validator,
        )

    def _get_column_names_metric(self, run_id: uuid.UUID, validator) -> Metric:
        return self._get_metric(
            metric_name="table.columns", run_id=run_id, validator=validator
        )

    def _generate_metric_id(self) -> uuid.UUID:
        return uuid.uuid4()

    def _convert_raw_metric_to_metric_object(
        self,
        batch: Batch,
        run_id: uuid.UUID,  # TODO: Should run_id be a separate type?
        raw_metric: int | list,  # TODO: What are the possible types of raw_metric?
        metric_config: MetricConfiguration,
    ) -> Metric:
        """Convert a dict of a single metric to a Metric object.
        Args:
            raw_metric: Dict of a single metric, where keys are metric names and values are metrics.
                Generated by the MetricsCalculator.
            metric_config: MetricConfiguration object for this metric.
        Returns:
            Metric object.
        """
        # TODO: Add the rest of the metric fields, convert value to Value object:

        print("converting metric dict to metric object")

        # TODO: Consider just having Batch as a parameter and serializing the parts we want
        #  (e.g. datasource_name, data_asset_name, batch_id).
        metric = Metric(
            id=self._generate_metric_id(),
            # TODO: Consider removing organization id and only adding when serializing in the store
            # organization_id=self._organization_id,
            run_id=run_id,
            # TODO: reimplement batch param
            # batch=batch,
            metric_name=metric_config.metric_name,
            metric_domain_kwargs=metric_config.metric_domain_kwargs,
            metric_value_kwargs=metric_config.metric_value_kwargs,
            column=metric_config.metric_domain_kwargs.get("column"),
            value=Value(value=raw_metric),
            details={},  # TODO: Pass details through
        )

        return metric
