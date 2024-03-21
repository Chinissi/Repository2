from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Union

import great_expectations.exceptions as gx_exceptions
from great_expectations.compatibility.sqlalchemy import (
    sqlalchemy as sa,
)
from great_expectations.core.id_dict import BatchSpec  # noqa: TCH001
from great_expectations.execution_engine.partition_and_sample.data_sampler import (
    DataSampler,
)
from great_expectations.execution_engine.sqlalchemy_dialect import GXSqlDialect

if TYPE_CHECKING:
    from great_expectations.compatibility import sqlalchemy
    from great_expectations.execution_engine import SqlAlchemyExecutionEngine


class SqlAlchemyDataSampler(DataSampler):
    """Sampling methods for data stores with SQL interfaces."""

    def sample_using_limit(
        self,
        execution_engine: SqlAlchemyExecutionEngine,
        batch_spec: BatchSpec,
        where_clause: Optional[sqlalchemy.Selectable] = None,
    ) -> Union[str, sqlalchemy.BinaryExpression, sqlalchemy.BooleanClauseList]:
        """Sample using a limit with configuration provided via the batch_spec.

        Note: where_clause needs to be included at this stage since SqlAlchemy's semantics
        for LIMIT are different than normal WHERE clauses.

        Also this requires an engine to find the dialect since certain databases require
        different handling.

        Args:
            execution_engine: Engine used to connect to the database.
            batch_spec: Batch specification describing the batch of interest.
            where_clause: Optional clause used in WHERE clause. Typically generated by a partitioner.

        Returns:
            A query as a string or sqlalchemy object.
        """  # noqa: E501

        # Partition clause should be permissive of all values if not supplied.
        if where_clause is None:
            if execution_engine.dialect_name == GXSqlDialect.SQLITE:
                where_clause = sa.text("1 = 1")
            else:
                where_clause = sa.true()

        table_name: str = batch_spec["table_name"]

        # SQLalchemy's semantics for LIMIT are different than normal WHERE clauses,
        # so the business logic for building the query needs to be different.
        dialect_name: str = execution_engine.dialect_name
        if dialect_name == GXSqlDialect.ORACLE:
            # TODO: AJB 20220429 WARNING THIS oracle dialect METHOD IS NOT COVERED BY TESTS
            # limit doesn't compile properly for oracle so we will append rownum to query string later  # noqa: E501
            raw_query: sqlalchemy.Selectable = (
                sa.select("*")
                .select_from(sa.table(table_name, schema=batch_spec.get("schema_name", None)))
                .where(where_clause)
            )
            query: str = str(
                raw_query.compile(
                    dialect=execution_engine.dialect,
                    compile_kwargs={"literal_binds": True},
                )
            )
            query += "\nAND ROWNUM <= %d" % batch_spec["sampling_kwargs"]["n"]
            return query
        elif dialect_name == GXSqlDialect.MSSQL:
            # Note that this code path exists because the limit parameter is not getting rendered
            # successfully in the resulting mssql query.
            selectable_query: sqlalchemy.Selectable = (
                sa.select("*")
                .select_from(sa.table(table_name, schema=batch_spec.get("schema_name", None)))
                .where(where_clause)
                .limit(batch_spec["sampling_kwargs"]["n"])
            )
            string_of_query: str = str(
                selectable_query.compile(
                    dialect=execution_engine.dialect,
                    compile_kwargs={"literal_binds": True},
                )
            )
            n: Union[str, int] = batch_spec["sampling_kwargs"]["n"]
            self._validate_mssql_limit_param(n)
            # This string replacement is here because the limit parameter is not substituted during query.compile()  # noqa: E501
            string_of_query = string_of_query.replace("?", str(n))
            return string_of_query
        else:
            return (
                sa.select("*")
                .select_from(sa.table(table_name, schema=batch_spec.get("schema_name", None)))
                .where(where_clause)
                .limit(batch_spec["sampling_kwargs"]["n"])
            )

    @staticmethod
    def _validate_mssql_limit_param(n: Union[str, int]) -> None:
        """Validate that the mssql limit param is passed as an int or a string representation of an int.

        Args:
            n: mssql limit parameter.

        Returns:
            None
        """  # noqa: E501
        if not isinstance(n, (str, int)):
            raise gx_exceptions.InvalidConfigError(
                "Please specify your sampling kwargs 'n' parameter as a string or int."
            )
        if isinstance(n, str) and not n.isdigit():
            raise gx_exceptions.InvalidConfigError(
                "If specifying your sampling kwargs 'n' parameter as a string please ensure it is "
                "parseable as an integer."
            )

    @staticmethod
    def sample_using_random(
        execution_engine: SqlAlchemyExecutionEngine,
        batch_spec: BatchSpec,
        where_clause: Optional[sqlalchemy.Selectable] = None,
    ) -> sqlalchemy.Selectable:
        """Sample using random data with configuration provided via the batch_spec.

        Note: where_clause needs to be included at this stage since we use the where clause
        to determine the total number of rows to use in determining the rows returned in the
        sample fraction.

        Args:
            execution_engine: Engine used to connect to the database.
            batch_spec: Batch specification describing the batch of interest.
            where_clause: Optional clause used in WHERE clause. Typically generated by a partitioner.

        Returns:
            Sqlalchemy selectable.
        """  # noqa: E501
        try:
            table_name: str = batch_spec["table_name"]
        except KeyError as e:
            raise ValueError(
                "A table name must be specified when using sample_using_random. "
                "Please update your configuration"
            ) from e
        try:
            p: float = batch_spec["sampling_kwargs"]["p"] or 1.0
        except (KeyError, TypeError) as e:
            raise ValueError(
                "To use sample_using_random you must specify the parameter 'p' in "
                "the 'sampling_kwargs' configuration."
            ) from e

        num_rows: int = execution_engine.execute_query(
            sa.select(sa.func.count())
            .select_from(sa.table(table_name, schema=batch_spec.get("schema_name", None)))
            .where(where_clause)
        ).scalar()
        sample_size: int = round(p * num_rows)
        return (
            sa.select("*")
            .select_from(sa.table(table_name, schema=batch_spec.get("schema_name", None)))
            .where(where_clause)
            .order_by(sa.func.random())
            .limit(sample_size)
        )

    def sample_using_mod(
        self,
        batch_spec: BatchSpec,
    ) -> sqlalchemy.Selectable:
        """Take the mod of named column, and only keep rows that match the given value.

        Args:
            batch_spec: should contain keys `column_name`, `mod` and `value`

        Returns:
            Sampled selectable

        Raises:
            SamplerError
        """
        self.verify_batch_spec_sampling_kwargs_exists(batch_spec)
        self.verify_batch_spec_sampling_kwargs_key_exists("column_name", batch_spec)
        self.verify_batch_spec_sampling_kwargs_key_exists("mod", batch_spec)
        self.verify_batch_spec_sampling_kwargs_key_exists("value", batch_spec)
        column_name: str = self.get_sampling_kwargs_value_or_default(batch_spec, "column_name")
        mod: int = self.get_sampling_kwargs_value_or_default(batch_spec, "mod")
        value: int = self.get_sampling_kwargs_value_or_default(batch_spec, "value")

        return sa.column(column_name) % mod == value

    def sample_using_a_list(
        self,
        batch_spec: BatchSpec,
    ) -> sqlalchemy.Selectable:
        """Match the values in the named column against value_list, and only keep the matches.

        Args:
            batch_spec: should contain keys `column_name` and `value_list`

        Returns:
            Sampled selectable

        Raises:
            SamplerError
        """
        self.verify_batch_spec_sampling_kwargs_exists(batch_spec)
        self.verify_batch_spec_sampling_kwargs_key_exists("column_name", batch_spec)
        self.verify_batch_spec_sampling_kwargs_key_exists("value_list", batch_spec)
        column_name: str = self.get_sampling_kwargs_value_or_default(batch_spec, "column_name")
        value_list: list = self.get_sampling_kwargs_value_or_default(batch_spec, "value_list")
        return sa.column(column_name).in_(value_list)

    def sample_using_md5(
        self,
        batch_spec: BatchSpec,
    ) -> sqlalchemy.Selectable:
        """Hash the values in the named column using md5, and only keep rows that match the given hash_value.

        Args:
            batch_spec: should contain keys `column_name` and optionally `hash_digits`
                (default is 1 if not provided), `hash_value` (default is "f" if not provided)

        Returns:
            Sampled selectable

        Raises:
            SamplerError
        """  # noqa: E501
        self.verify_batch_spec_sampling_kwargs_exists(batch_spec)
        self.verify_batch_spec_sampling_kwargs_key_exists("column_name", batch_spec)
        column_name: str = self.get_sampling_kwargs_value_or_default(batch_spec, "column_name")
        hash_digits: int = self.get_sampling_kwargs_value_or_default(
            batch_spec=batch_spec, sampling_kwargs_key="hash_digits", default_value=1
        )
        hash_value: str = self.get_sampling_kwargs_value_or_default(
            batch_spec=batch_spec, sampling_kwargs_key="hash_value", default_value="f"
        )

        return (
            sa.func.right(sa.func.md5(sa.cast(sa.column(column_name), sa.Text)), hash_digits)
            == hash_value
        )
