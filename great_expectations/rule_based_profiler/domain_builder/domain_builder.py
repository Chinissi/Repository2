from abc import ABC, abstractmethod
from typing import List, Optional, Union

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.batch import Batch, BatchRequest, RuntimeBatchRequest
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.rule_based_profiler.helpers.util import (
    get_batch_ids as get_batch_ids_from_batch_list_or_batch_request,
)
from great_expectations.rule_based_profiler.helpers.util import (
    get_validator as get_validator_using_batch_list_or_batch_request,
)
from great_expectations.rule_based_profiler.types import (
    Builder,
    Domain,
    ParameterContainer,
)


class DomainBuilder(Builder, ABC):
    """
    A DomainBuilder provides methods to get domains based on one or more batches of data.
    """

    def __init__(
        self,
        batch_list: Optional[List[Batch]] = None,
        batch_request: Optional[Union[BatchRequest, RuntimeBatchRequest, dict]] = None,
        data_context: Optional["DataContext"] = None,  # noqa: F821
    ):
        """
        Args:
            batch_list: explicitly specified Batch objects for use in DomainBuilder
            batch_request: specified in DomainBuilder configuration to get Batch objects for domain computation.
            data_context: DataContext
        """
        super().__init__(
            batch_list=batch_list,
            batch_request=batch_request,
            data_context=data_context,
        )

    def get_domains(
        self,
        variables: Optional[ParameterContainer] = None,
    ) -> List[Domain]:
        """
        Note: Please do not overwrite the public "get_domains()" method.  If a child class needs to check parameters,
        then please do so in its implementation of the (private) "_get_domains()" method, or in a utility method.
        """
        return self._get_domains(variables=variables)

    @property
    @abstractmethod
    def domain_type(self) -> Union[str, MetricDomainTypes]:
        pass

    """
    Full getter/setter accessors for "batch_request" and "batch_list" are for configuring DomainBuilder dynamically.
    """

    @property
    def batch_request(self) -> Optional[Union[BatchRequest, RuntimeBatchRequest, dict]]:
        return self._batch_request

    @batch_request.setter
    def batch_request(
        self, value: Union[BatchRequest, RuntimeBatchRequest, dict]
    ) -> None:
        self._batch_request = value

    @property
    def batch_list(self) -> Optional[List[Batch]]:
        return self._batch_list

    @batch_list.setter
    def batch_list(self, value: List[Batch]) -> None:
        self._batch_list = value

    @property
    def data_context(self) -> "DataContext":  # noqa: F821
        return self._data_context

    @abstractmethod
    def _get_domains(
        self,
        variables: Optional[ParameterContainer] = None,
    ) -> List[Domain]:
        """
        _get_domains is the primary workhorse for the DomainBuilder
        """

        pass

    def get_validator(
        self,
        variables: Optional[ParameterContainer] = None,
    ) -> Optional["Validator"]:  # noqa: F821
        return get_validator_using_batch_list_or_batch_request(
            purpose="domain_builder",
            data_context=self.data_context,
            batch_list=self.batch_list,
            batch_request=self.batch_request,
            domain=None,
            variables=variables,
            parameters=None,
        )

    def get_batch_ids(
        self,
        variables: Optional[ParameterContainer] = None,
    ) -> Optional[List[str]]:
        return get_batch_ids_from_batch_list_or_batch_request(
            data_context=self.data_context,
            batch_list=self.batch_list,
            batch_request=self.batch_request,
            domain=None,
            variables=variables,
            parameters=None,
        )

    def get_batch_id(
        self,
        variables: Optional[ParameterContainer] = None,
    ) -> str:
        batch_ids: Optional[List[str]] = self.get_batch_ids(
            variables=variables,
        )
        num_batch_ids: int = len(batch_ids)
        if num_batch_ids != 1:
            raise ge_exceptions.ProfilerExecutionError(
                message=f"""{self.__class__.__name__}.get_batch_id() must return exactly one batch_id ({num_batch_ids} \
were retrieved).
"""
            )

        return batch_ids[0]


def build_simple_domains_from_column_names(
    column_names: List[str],
    domain_type: MetricDomainTypes = MetricDomainTypes.COLUMN,
) -> List[Domain]:
    """
    This utility method builds "simple" Domain objects (i.e., required fields only, no "details" metadata accepted).

    :param column_names: list of column names to serve as values for "column" keys in "domain_kwargs" dictionary
    :param domain_type: type of Domain objects (same "domain_type" must be applicable to all Domain objects returned)
    :return: list of resulting Domain objects
    """
    column_name: str
    domains: List[Domain] = [
        Domain(
            domain_type=domain_type,
            domain_kwargs={
                "column": column_name,
            },
        )
        for column_name in column_names
    ]

    return domains
