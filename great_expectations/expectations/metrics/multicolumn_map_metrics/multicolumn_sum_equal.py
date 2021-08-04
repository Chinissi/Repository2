from great_expectations.execution_engine import PandasExecutionEngine
from great_expectations.expectations.metrics.map_metric_provider import (
    MulticolumnMapMetricProvider,
    multicolumn_condition_partial,
)


class MulticolumnSumEqual(MulticolumnMapMetricProvider):
    condition_metric_name = "multicolumn_sum.equal"
    condition_domain_keys = (
        "batch_id",
        "table",
        "column_list",
        "row_condition",
        "condition_parser",
        "ignore_row_if",
    )
    condition_value_keys = ("sum_total",)

    # TODO: <Alex>ALEX -- temporarily only a Pandas implementation is provided (others to follow).</Alex>
    @multicolumn_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column_list, **kwargs):
        sum_total = kwargs.get("sum_total")
        row_wise_cond = column_list.sum(axis=1, skipna=False) == sum_total
        return row_wise_cond
