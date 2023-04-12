from great_expectations.core.metric_function_types import MetricPartialFunctionTypes
from great_expectations.execution_engine import (
    PandasExecutionEngine,
    SparkDFExecutionEngine,
    SqlAlchemyExecutionEngine,
)
from great_expectations.expectations.metrics.map_metric_provider import (
    ColumnMapMetricProvider,
    column_condition_partial,
)
from great_expectations.optional_imports import (
    SQLALCHEMY_NOT_IMPORTED,
    F,
    sqlalchemy_engine_Engine,
)
from great_expectations.optional_imports import (
    pyspark_sql_Window as Window,
)
from great_expectations.optional_imports import (
    sqlalchemy as sa,
)
from great_expectations.util import generate_temporary_table_name


class ColumnValuesUnique(ColumnMapMetricProvider):
    condition_metric_name = "column_values.unique"

    @column_condition_partial(engine=PandasExecutionEngine)
    def _pandas(cls, column, **kwargs):
        return ~column.duplicated(keep=False)

    # NOTE: 20201119 - JPC - We cannot split per-dialect into window and non-window functions
    # @column_condition_partial(
    #     engine=SqlAlchemyExecutionEngine,
    # )
    # def _sqlalchemy(cls, column, _table, **kwargs):
    #     dup_query = (
    #         sa.select(column)
    #         .select_from(_table)
    #         .group_by(column)
    #         .having(sa.func.count(column) > 1)
    #     )
    #
    #     return column.notin_(dup_query)

    @column_condition_partial(
        engine=SqlAlchemyExecutionEngine,
        partial_fn_type=MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
    )
    def _sqlalchemy_window(cls, column, _table, **kwargs):
        # Will - 20210126
        # This is a special case that needs to be handled for mysql, where you cannot refer to a temp_table
        # more than once in the same query. So instead of passing dup_query as-is, a second temp_table is created with
        # the column we will be performing the expectation on, and the query is performed against it.
        dialect = kwargs.get("_dialect", None)
        sql_engine = kwargs.get("_sqlalchemy_engine", None)
        try:
            dialect_name = dialect.dialect.name
        except AttributeError:
            try:
                dialect_name = dialect.name
            except AttributeError:
                dialect_name = ""
        if sql_engine and dialect and dialect_name == "mysql":
            temp_table_name = generate_temporary_table_name()
            temp_table_stmt = "CREATE TEMPORARY TABLE {new_temp_table} AS SELECT tmp.{column_name} FROM {source_table} tmp".format(
                new_temp_table=temp_table_name,
                source_table=_table,
                column_name=column.name,
            )
            if sqlalchemy_engine_Engine != SQLALCHEMY_NOT_IMPORTED and isinstance(
                sql_engine, sqlalchemy_engine_Engine
            ):
                with sql_engine.connect() as connection:
                    with connection.begin():
                        connection.execute(sa.text(temp_table_stmt))
            else:
                # sql_engine is a connection
                with sql_engine.begin():
                    sql_engine.execute(sa.text(temp_table_stmt))
            dup_query = (
                sa.select(column)
                .select_from(sa.text(temp_table_name))
                .group_by(column)
                .having(sa.func.count(column) > 1)
            )
        else:
            dup_query = (
                sa.select(column)
                .select_from(_table)
                .group_by(column)
                .having(sa.func.count(column) > 1)
            )
        return column.notin_(dup_query)

    @column_condition_partial(
        engine=SparkDFExecutionEngine,
        partial_fn_type=MetricPartialFunctionTypes.WINDOW_CONDITION_FN,
    )
    def _spark(cls, column, **kwargs):
        return F.count(F.lit(1)).over(Window.partitionBy(column)) <= 1
