from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple, Type

import numpy as np

from great_expectations.core import ExpectationConfiguration
from great_expectations.exceptions.metric_exceptions import MetricError
from great_expectations.execution_engine import ExecutionEngine, PandasExecutionEngine
from great_expectations.execution_engine.sparkdf_execution_engine import (
    F,
    SparkDFExecutionEngine,
)
from great_expectations.execution_engine.sqlalchemy_execution_engine import (
    SqlAlchemyExecutionEngine,
    sa,
)
from great_expectations.expectations.metrics.metric_provider import MetricProvider
from great_expectations.expectations.registry import register_metric
from great_expectations.validator.validation_graph import MetricConfiguration


def column_map_function(engine: Type[ExecutionEngine], **kwargs):
    """Provides engine-specific support for authing a metric_fn with a simplified signature.

    A metric function that is decorated as a column_map_function will be called with the engine-specific column type
    and any value_kwargs associated with the Metric for which the provider function is being declared.

    Args:
        engine:
        **kwargs:

    Returns:
        An annotated metric_function which will be called with a simplified signature.

    """
    if issubclass(engine, PandasExecutionEngine):

        def wrapper(metric_fn: Callable):
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "PandasExecutionEngine",
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: Dict,
            ):
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
                )

                df, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs,
                )
                if filter_column_isnull:
                    df = df[df[accessor_domain_kwargs["column"]].notnull()]
                values = metric_fn(
                    cls,
                    df[accessor_domain_kwargs["column"]],
                    **metric_value_kwargs,
                    _metrics=metrics,
                )
                return values

            inner_func.map_function_metric_engine = engine
            inner_func.map_function_metric_kwargs = kwargs
            inner_func.metric_fn_type = "map_fn"
            inner_func.column_domain = True
            return inner_func

        return wrapper

    elif issubclass(engine, SqlAlchemyExecutionEngine):

        def wrapper(metric_fn: Callable):
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "SqlAlchemyExecutionEngine",
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: Dict,
            ):
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
                )
                if filter_column_isnull:
                    compute_domain_kwargs = execution_engine.add_column_null_filter_row_condition(
                        metric_domain_kwargs
                    )
                else:
                    # We do not copy here because if compute domain is different, it will be copied by get_compute_domain
                    compute_domain_kwargs = metric_domain_kwargs
                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(compute_domain_kwargs)
                column_name = accessor_domain_kwargs["column"]
                dialect = execution_engine.dialect
                column_function = metric_fn(
                    cls,
                    sa.column(column_name),
                    **metric_value_kwargs,
                    _dialect=dialect,
                    _table=selectable,
                    _metrics=metrics,
                )
                return column_function, compute_domain_kwargs

            inner_func.map_function_metric_engine = engine
            inner_func.map_function_metric_kwargs = kwargs
            inner_func.metric_fn_type = "map_fn"
            inner_func.column_domain = True
            return inner_func

        return wrapper

    elif issubclass(engine, SparkDFExecutionEngine):

        def wrapper(metric_fn: Callable):
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "SparkDFExecutionEngine",
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: Dict,
            ):
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
                )

                if filter_column_isnull:
                    compute_domain_kwargs = execution_engine.add_column_null_filter_row_condition(
                        metric_domain_kwargs
                    )
                else:
                    # We do not copy here because if compute domain is different, it will be copied by get_compute_domain
                    compute_domain_kwargs = metric_domain_kwargs

                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=compute_domain_kwargs
                )
                column_name = accessor_domain_kwargs["column"]
                column_function = metric_fn(
                    cls,
                    column=data[column_name],
                    **metric_value_kwargs,
                    _metrics=metrics,
                    _compute_domain_kwargs=compute_domain_kwargs,
                )
                return column_function, compute_domain_kwargs

            inner_func.map_function_metric_engine = engine
            inner_func.map_function_metric_kwargs = kwargs
            inner_func.metric_fn_type = "map_fn"
            inner_func.column_domain = True
            return inner_func

        return wrapper

    else:
        raise ValueError("Unsupported engine for column_aggregate_metric")


def map_condition(
    engine: Type[ExecutionEngine], metric_fn_type: str = "map_condition", **kwargs
):
    """Annotates a metric provider with the "map" metric_fn_type and associated engine.

    The MapMetricProvider class provides engine-specific support for authoring metrics that operate on rows/records
    of a dataset, where intermediate values may not be returned.

    Args:
        engine:
        **kwargs:

    Returns:
        An annotated metric_function which will be used to construct map-related metrics, such as unexpected_count.

    """

    def wrapper(metric_fn: Callable):
        def inner_func(*args, **kwargs):
            return metric_fn(*args, **kwargs)

        inner_func.map_condition_metric_engine = engine
        inner_func.map_condition_metric_kwargs = kwargs
        inner_func.metric_fn_type = metric_fn_type

        return inner_func

    return wrapper


def column_map_condition(
    engine: Type[ExecutionEngine], metric_fn_type: str = "map_condition", **kwargs
):
    """Provides engine-specific support for authing a metric_fn with a simplified signature. A column_map_condition
    must provide a map function that evalues to a boolean value; it will be used to provide supplemental metrics, such
    as the unexpected_value count, unexpected_values, and unexpected_rows.

    A metric function that is decorated as a column_map_condition will be called with the engine-specific column type
    and any value_kwargs associated with the Metric for which the provider function is being declared.



    Args:
        engine:
        **kwargs:

    Returns:
        An annotated metric_function which will be called with a simplified signature.

    """
    if issubclass(engine, PandasExecutionEngine):

        def wrapper(metric_fn: Callable):
            @map_condition(engine, metric_fn_type, **kwargs)
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "PandasExecutionEngine",
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: Dict,
            ):
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", True)
                )

                df, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs,
                )
                if filter_column_isnull:
                    df = df[df[accessor_domain_kwargs["column"]].notnull()]

                meets_expectation_series = metric_fn(
                    cls,
                    df[accessor_domain_kwargs["column"]],
                    **metric_value_kwargs,
                    _metrics=metrics,
                )
                return ~meets_expectation_series

            inner_func.column_domain = True
            return inner_func

        return wrapper

    elif issubclass(engine, SqlAlchemyExecutionEngine):

        def wrapper(metric_fn: Callable):
            @map_condition(engine, metric_fn_type, **kwargs)
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "SqlAlchemyExecutionEngine",
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: Dict,
            ):
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", True)
                )

                (
                    selectable,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(metric_domain_kwargs)
                column_name = accessor_domain_kwargs["column"]
                dialect = execution_engine.dialect
                sqlalchemy_engine = execution_engine.engine

                expected_condition = metric_fn(
                    cls,
                    sa.column(column_name),
                    **metric_value_kwargs,
                    _dialect=dialect,
                    _table=selectable,
                    _sqlalchemy_engine=sqlalchemy_engine,
                    _metrics=metrics,
                )
                if filter_column_isnull:
                    # If we "filter" (ignore) nulls then we allow null as part of our new expected condition
                    unexpected_condition = sa.and_(
                        sa.not_(sa.column(column_name).is_(None)),
                        sa.not_(expected_condition),
                    )
                else:
                    unexpected_condition = sa.not_(expected_condition)
                return unexpected_condition, compute_domain_kwargs

            inner_func.column_domain = True
            return inner_func

        return wrapper

    elif issubclass(engine, SparkDFExecutionEngine):

        def wrapper(metric_fn: Callable):
            @map_condition(engine, metric_fn_type, **kwargs)
            @wraps(metric_fn)
            def inner_func(
                cls,
                execution_engine: "SparkDFExecutionEngine",
                metric_domain_kwargs: Dict,
                metric_value_kwargs: Dict,
                metrics: Dict[Tuple, Any],
                runtime_configuration: Dict,
            ):
                filter_column_isnull = kwargs.get(
                    "filter_column_isnull", getattr(cls, "filter_column_isnull", True)
                )
                (
                    data,
                    compute_domain_kwargs,
                    accessor_domain_kwargs,
                ) = execution_engine.get_compute_domain(
                    domain_kwargs=metric_domain_kwargs
                )
                column_name = accessor_domain_kwargs["column"]
                column = data[column_name]
                expected_condition = metric_fn(
                    cls,
                    column,
                    **metric_value_kwargs,
                    _table=data,
                    _metrics=metrics,
                    _compute_domain_kwargs=compute_domain_kwargs,
                    _accessor_domain_kwargs=accessor_domain_kwargs,
                )
                if metric_fn_type == "window_condition_fn":
                    if filter_column_isnull:
                        compute_domain_kwargs = execution_engine.add_column_null_filter_row_condition(
                            metric_domain_kwargs
                        )
                    unexpected_condition = ~expected_condition
                else:
                    if filter_column_isnull:
                        unexpected_condition = column.isNotNull() & ~expected_condition
                    else:
                        unexpected_condition = ~expected_condition
                return unexpected_condition, compute_domain_kwargs

            inner_func.column_domain = True
            return inner_func

        return wrapper
    else:
        raise ValueError("Unsupported engine for column_map_condition")


def _pandas_map_unexpected_count(
    cls,
    execution_engine: "PandasExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """Returns unexpected count for MapExpectations"""
    return np.count_nonzero(metrics.get("unexpected_condition"))


def _pandas_column_map_values(
    cls,
    execution_engine: "PandasExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """Return values from the specified domain that match the map-style metric in the metrics dictionary."""
    df, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
        domain_kwargs=metric_domain_kwargs,
    )
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if filter_column_isnull:
        df = df[df[accessor_domain_kwargs["column"]].notnull()]

    data = df[accessor_domain_kwargs["column"]]

    result_format = metric_value_kwargs["result_format"]
    boolean_map_unexpected_values = metrics.get("unexpected_condition")
    if result_format["result_format"] == "COMPLETE":
        return list(
            data[
                # boolean_map_unexpected_values[
                #     metric_name[: -len(".unexpected_values")]
                # ]
                boolean_map_unexpected_values
                == True
            ]
        )
    else:
        return list(
            data[
                # boolean_map_unexpected_values[
                #     metric_name[: -len(".unexpected_values")]
                # ]
                boolean_map_unexpected_values
                == True
            ][: result_format["partial_unexpected_count"]]
        )


def _pandas_column_map_index(
    cls,
    execution_engine: "PandasExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """Maps metric values and kwargs to results of success kwargs"""
    df, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
        domain_kwargs=metric_domain_kwargs,
    )
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if filter_column_isnull:
        df = df[df[accessor_domain_kwargs["column"]].notnull()]
    data = df[accessor_domain_kwargs["column"]]
    result_format = metric_value_kwargs["result_format"]
    boolean_mapped_unexpected_values = metrics.get("unexpected_condition")
    if result_format["result_format"] == "COMPLETE":
        return list(data[boolean_mapped_unexpected_values == True].index)
    else:
        return list(
            data[boolean_mapped_unexpected_values == True].index[
                : result_format["partial_unexpected_count"]
            ]
        )


def _pandas_column_map_value_counts(
    cls,
    execution_engine: "PandasExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """Returns respective value counts for distinct column values"""
    df, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
        domain_kwargs=metric_domain_kwargs,
    )
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if filter_column_isnull:
        df = df[df[accessor_domain_kwargs["column"]].notnull()]
    data = df[accessor_domain_kwargs["column"]]
    result_format = metric_value_kwargs["result_format"]
    boolean_mapped_unexpected_values = metrics.get("unexpected_condition")
    value_counts = None
    try:
        value_counts = data[boolean_mapped_unexpected_values == True].value_counts()
    except ValueError:
        try:
            value_counts = (
                data[boolean_mapped_unexpected_values == True]
                .apply(tuple)
                .value_counts()
            )
        except ValueError:
            pass

    if not value_counts:
        raise MetricError("Unable to compute value counts")

    if result_format["result_format"] == "COMPLETE":
        return value_counts
    else:
        return value_counts[result_format["partial_unexpected_count"]]


def _pandas_column_map_rows(
    cls,
    execution_engine: "PandasExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """Return values from the specified domain (ignoring the column constraint) that match the map-style metric in the metrics dictionary."""
    df, _, accessor_domain_kwargs = execution_engine.get_compute_domain(
        domain_kwargs=metric_domain_kwargs,
    )
    filter_column_isnull = kwargs.get(
        "filter_column_isnull", getattr(cls, "filter_column_isnull", False)
    )
    if filter_column_isnull:
        df = df[df[accessor_domain_kwargs["column"]].notnull()]
    result_format = metric_value_kwargs["result_format"]
    boolean_mapped_unexpected_values = metrics.get("unexpected_condition")
    if result_format["result_format"] == "COMPLETE":
        return df[boolean_mapped_unexpected_values == True]
    else:
        return df[boolean_mapped_unexpected_values == True][
            result_format["partial_unexpected_count"]
        ]


def _sqlalchemy_map_unexpected_count(
    cls,
    execution_engine: "SqlAlchemyExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """Returns unexpected count for MapExpectations"""
    unexpected_condition, fn_domain_kwargs = metrics.get("unexpected_condition")
    return (
        sa.func.sum(sa.case([(unexpected_condition, 1)], else_=0,)),
        fn_domain_kwargs,
    )


def _sqlalchemy_column_map_values(
    cls,
    execution_engine: "SqlAlchemyExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """
    Particularly for the purpose of finding unexpected values, returns all the metric values which do not meet an
    expected Expectation condition for ColumnMapExpectation Expectations.
    """
    (
        selectable,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = execution_engine.get_compute_domain(metric_domain_kwargs)

    result_format = metric_value_kwargs["result_format"]
    unexpected_condition, fn_domain_kwargs = metrics.get("unexpected_condition")
    assert (
        fn_domain_kwargs == compute_domain_kwargs
    ), "compute domain should be equivalent to the function domain"
    query = (
        sa.select(
            [sa.column(accessor_domain_kwargs.get("column")).label("unexpected_values")]
        )
        .select_from(selectable)
        .where(unexpected_condition)
    )
    if result_format["result_format"] != "COMPLETE":
        query = query.limit(result_format["partial_unexpected_count"])
    return [
        val.unexpected_values
        for val in execution_engine.engine.execute(query).fetchall()
    ]


def _sqlalchemy_column_map_value_counts(
    cls,
    execution_engine: "SqlAlchemyExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """
    Returns value counts for all the metric values which do not meet an expected Expectation condition for instances
    of ColumnMapExpectation.
    """
    (
        selectable,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = execution_engine.get_compute_domain(metric_domain_kwargs)

    unexpected_condition, fn_domain_kwargs = metrics.get("unexpected_condition")
    assert (
        fn_domain_kwargs == compute_domain_kwargs
    ), "compute domain should be equivalent to the function domain"
    column = sa.column(accessor_domain_kwargs["column"])
    return execution_engine.engine.execute(
        sa.select([column, sa.func.count(column)])
        .select_from(selectable)
        .where(unexpected_condition)
        .group_by(column)
    ).fetchall()


def _sqlalchemy_column_map_rows(
    cls,
    execution_engine: "SqlAlchemyExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    """
    Returns all rows of the metric values which do not meet an expected Expectation condition for instances
    of ColumnMapExpectation.
    """
    (
        selectable,
        compute_domain_kwargs,
        accessor_domain_kwargs,
    ) = execution_engine.get_compute_domain(metric_domain_kwargs)

    result_format = metric_value_kwargs["result_format"]
    unexpected_condition, fn_domain_kwargs = metrics.get("unexpected_condition")
    assert (
        fn_domain_kwargs == compute_domain_kwargs
    ), "compute domain should be equivalent to the function domain"
    query = (
        sa.select([sa.text("*")]).select_from(selectable).where(unexpected_condition)
    )
    if result_format["result_format"] != "COMPLETE":
        query = query.limit(result_format["partial_unexpected_count"])
    return execution_engine.engine.execute(query).fetchall()


def _spark_map_unexpected_count(
    cls,
    execution_engine: "SparkDFExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    unexpected_condition, compute_domain_kwargs = metrics.get("unexpected_condition")
    return F.sum(F.when(unexpected_condition, 1).otherwise(0)), compute_domain_kwargs


def _spark_map_unexpected_count_data(
    cls,
    execution_engine: "SparkDFExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    # fn_domain_kwargs maybe updated to reflect null filtering
    condition, fn_domain_kwargs = metrics.get("unexpected_condition")
    (data, _, accessor_domain_kwargs,) = execution_engine.get_compute_domain(
        fn_domain_kwargs
    )
    data = data.withColumn("__unexpected", condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    return filtered.count()


def _spark_column_map_values(
    cls,
    execution_engine: "SparkDFExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    condition, fn_domain_kwargs = metrics.get("unexpected_condition")
    (data, _, _,) = execution_engine.get_compute_domain(fn_domain_kwargs)

    """Return values from the specified domain that match the map-style metric in the metrics dictionary."""
    result_format = metric_value_kwargs["result_format"]
    column_name = metric_domain_kwargs["column"]
    data = data.withColumn("__unexpected", condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    if result_format["result_format"] == "COMPLETE":
        rows = filtered.select(F.col(column_name)).collect()
    else:
        rows = (
            filtered.select(F.col(column_name))
            .limit(result_format["partial_unexpected_count"])
            .collect()
        )
    return [row[column_name] for row in rows]


def _spark_column_map_value_counts(
    cls,
    execution_engine: "SparkDFExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    condition, fn_domain_kwargs = metrics.get("unexpected_condition")
    (data, _, accessor_domain_kwargs,) = execution_engine.get_compute_domain(
        fn_domain_kwargs
    )
    """Returns all unique values in the column and their corresponding counts"""
    result_format = metric_value_kwargs["result_format"]
    column_name = accessor_domain_kwargs["column"]
    data = data.withColumn("__unexpected", condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    value_counts = filtered.groupBy(F.col(column_name)).count()
    if result_format["result_format"] == "COMPLETE":
        rows = value_counts.collect()
    else:
        rows = value_counts.collect()[: result_format["partial_unexpected_count"]]
    return rows


def _spark_column_map_rows(
    cls,
    execution_engine: "PandasExecutionEngine",
    metric_domain_kwargs: Dict,
    metric_value_kwargs: Dict,
    metrics: Dict[Tuple, Any],
    **kwargs,
):
    condition, fn_domain_kwargs = metrics.get("unexpected_condition")

    (data, _, accessor_domain_kwargs,) = execution_engine.get_compute_domain(
        fn_domain_kwargs
    )
    result_format = metric_value_kwargs["result_format"]
    data = data.withColumn("__unexpected", condition)
    filtered = data.filter(F.col("__unexpected") == True).drop(F.col("__unexpected"))
    if result_format["result_format"] == "COMPLETE":
        return filtered.collect()
    else:
        return filtered.limit(result_format["partial_unexpected_count"]).collect()


class MapMetricProvider(MetricProvider):
    condition_domain_keys = (
        "batch_id",
        "table",
        "row_condition",
        "condition_parser",
    )
    function_domain_keys = (
        "batch_id",
        "table",
        "row_condition",
        "condition_parser",
    )
    condition_value_keys = tuple()
    function_value_keys = tuple()
    filter_column_isnull = True

    @classmethod
    def _register_metric_functions(cls):
        if not hasattr(cls, "function_metric_name") and not hasattr(
            cls, "condition_metric_name"
        ):
            return

        for attr, candidate_metric_fn in cls.__dict__.items():
            if not hasattr(
                candidate_metric_fn, "map_condition_metric_engine"
            ) and not hasattr(candidate_metric_fn, "map_function_metric_engine"):
                # This is not a metric
                continue
            if hasattr(candidate_metric_fn, "map_condition_metric_engine"):
                engine = candidate_metric_fn.map_condition_metric_engine
                if not issubclass(engine, ExecutionEngine):
                    raise ValueError(
                        "metric functions must be defined with an Execution Engine"
                    )
                if not hasattr(cls, "condition_metric_name"):
                    raise ValueError(
                        "A MapMetricProvider must have a metric_condition_name to have a decorated column_map_condition method."
                    )

                condition_provider = candidate_metric_fn
                metric_name = cls.condition_metric_name
                metric_domain_keys = cls.condition_domain_keys
                metric_value_keys = cls.condition_value_keys
                map_condition_metric_kwargs = getattr(
                    condition_provider, "map_condition_metric_kwags", dict()
                )
                is_column_domain = getattr(condition_provider, "column_domain", False)
                if issubclass(engine, PandasExecutionEngine):
                    register_metric(
                        metric_name=metric_name,
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=condition_provider,
                        metric_fn_type="map_condition",
                    )
                    register_metric(
                        metric_name=metric_name + ".unexpected_count",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=_pandas_map_unexpected_count,
                        metric_fn_type="data",
                    )
                    if is_column_domain:
                        register_metric(
                            metric_name=metric_name + ".unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_map_values,
                            metric_fn_type="data",
                        )
                        register_metric(
                            metric_name=metric_name + ".unexpected_index_list",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_map_index,
                            metric_fn_type="data",
                        )
                        register_metric(
                            metric_name=metric_name + ".unexpected_value_counts",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_map_value_counts,
                            metric_fn_type="data",
                        )
                        register_metric(
                            metric_name=metric_name + ".unexpected_rows",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_pandas_column_map_rows,
                            metric_fn_type="data",
                        )

                if issubclass(engine, SqlAlchemyExecutionEngine):
                    register_metric(
                        metric_name=metric_name,
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=condition_provider,
                        metric_fn_type="map_condition",
                    )
                    register_metric(
                        metric_name=metric_name + ".unexpected_count",
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=_sqlalchemy_map_unexpected_count,
                        metric_fn_type="aggregate_fn",
                    )
                    if is_column_domain:
                        register_metric(
                            metric_name=metric_name + ".unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_column_map_values,
                            metric_fn_type="data",
                        )
                        register_metric(
                            metric_name=metric_name + ".unexpected_value_counts",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_column_map_value_counts,
                            metric_fn_type="data",
                        )
                        register_metric(
                            metric_name=metric_name + ".unexpected_rows",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_sqlalchemy_column_map_rows,
                            metric_fn_type="data",
                        )
                elif issubclass(engine, SparkDFExecutionEngine):
                    metric_fn_type = getattr(
                        condition_provider, "metric_fn_type", "map_condition"
                    )
                    register_metric(
                        metric_name=metric_name,
                        metric_domain_keys=metric_domain_keys,
                        metric_value_keys=metric_value_keys,
                        execution_engine=engine,
                        metric_class=cls,
                        metric_provider=condition_provider,
                        metric_fn_type=metric_fn_type,
                    )
                    if metric_fn_type == "map_condition":
                        register_metric(
                            metric_name=metric_name + ".unexpected_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=metric_value_keys,
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_map_unexpected_count,
                            metric_fn_type="aggregate_fn",
                        )
                    elif metric_fn_type == "window_condition_fn":
                        register_metric(
                            metric_name=metric_name + ".unexpected_count",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=metric_value_keys,
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_map_unexpected_count_data,
                            metric_fn_type="data",
                        )
                    if is_column_domain:
                        register_metric(
                            metric_name=metric_name + ".unexpected_values",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_column_map_values,
                            metric_fn_type="data",
                        )
                        register_metric(
                            metric_name=metric_name + ".unexpected_value_counts",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_column_map_value_counts,
                            metric_fn_type="data",
                        )
                        register_metric(
                            metric_name=metric_name + ".unexpected_rows",
                            metric_domain_keys=metric_domain_keys,
                            metric_value_keys=(*metric_value_keys, "result_format"),
                            execution_engine=engine,
                            metric_class=cls,
                            metric_provider=_spark_column_map_rows,
                            metric_fn_type="data",
                        )
            if hasattr(candidate_metric_fn, "map_function_metric_engine"):
                engine = candidate_metric_fn.map_function_metric_engine
                if not issubclass(engine, ExecutionEngine):
                    raise ValueError(
                        "metric functions must be defined with an Execution Engine"
                    )
                if not hasattr(cls, "function_metric_name"):
                    raise ValueError(
                        "A MapMetricProvider must have a function_metric_name to have a decorated column_map_function method."
                    )
                map_function_provider = candidate_metric_fn
                metric_name = cls.function_metric_name
                metric_domain_keys = cls.function_domain_keys
                metric_value_keys = cls.function_value_keys
                metric_map_function_kwargs = getattr(
                    map_function_provider, "metric_map_function_kwargs", dict()
                )
                register_metric(
                    metric_name=metric_name,
                    metric_domain_keys=metric_domain_keys,
                    metric_value_keys=metric_value_keys,
                    execution_engine=engine,
                    metric_class=cls,
                    metric_provider=map_function_provider,
                    metric_fn_type="map_fn",
                )

    @classmethod
    def get_evaluation_dependencies(
        cls,
        metric: MetricConfiguration,
        configuration: Optional[ExpectationConfiguration] = None,
        execution_engine: Optional[ExecutionEngine] = None,
        runtime_configuration: Optional[dict] = None,
    ):
        """This should return a dictionary:

        {
          "dependency_name": MetricConfiguration,
          ...
        }
        """
        metric_name = metric.metric_name
        base_metric_value_kwargs = {
            k: v for k, v in metric.metric_value_kwargs.items() if k != "result_format"
        }

        if metric_name.endswith(".unexpected_count"):
            return {
                "unexpected_condition": MetricConfiguration(
                    metric_name[: -len(".unexpected_count")],
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
            }

        if metric_name.endswith(".unexpected_values"):
            return {
                "unexpected_condition": MetricConfiguration(
                    metric_name[: -len(".unexpected_values")],
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
            }

        if metric_name.endswith(".unexpected_index_list"):
            return {
                "unexpected_condition": MetricConfiguration(
                    metric_name[: -len(".unexpected_index_list")],
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
            }

        if metric_name.endswith(".unexpected_value_counts"):
            return {
                "unexpected_condition": MetricConfiguration(
                    metric_name[: -len(".unexpected_value_counts")],
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
            }

        if metric_name.endswith(".unexpected_rows"):
            return {
                "unexpected_condition": MetricConfiguration(
                    metric_name[: -len(".unexpected_rows")],
                    metric.metric_domain_kwargs,
                    base_metric_value_kwargs,
                )
            }

        return dict()


class ColumnMapMetricProvider(MapMetricProvider):
    condition_domain_keys = (
        "batch_id",
        "table",
        "column",
        "row_condition",
        "condition_parser",
    )
    function_domain_keys = (
        "batch_id",
        "table",
        "column",
        "row_condition",
        "condition_parser",
    )
    condition_value_keys = tuple()
    function_value_keys = tuple()
