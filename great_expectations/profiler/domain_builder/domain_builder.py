from abc import ABC, abstractmethod
from typing import List, Optional

from great_expectations.core.batch import Batch
from great_expectations.execution_engine.execution_engine import MetricDomainTypes
from great_expectations.validator.validator import Validator


class DomainBuilder(ABC):
    """A DomainBuilder provides methods to get domains based on one or more batches of data.

    It may additionally accept other configuration.
    """

    # TODO: <Alex>ALEX -- We should be careful with **kwargs -- if there is no immediate use case for them, then we should only keep explicit arguments.</Alex>
    def get_domains(
        self,
        *,
        validator: Optional[Validator] = None,
        batch_ids: Optional[List[str]] = None,
        include_batch_id: Optional[bool] = False,
        domain_type: Optional[MetricDomainTypes] = None,
        **kwargs
    ):
        """get_domains may be overridden by children who wish to check parameters prior to passing
        work to the implementation of _get_domains in the particular domain_builder.
        """
        return self._get_domains(
            validator=validator,
            batch_ids=batch_ids,
            include_batch_id=include_batch_id,
            domain_type=domain_type,
            **kwargs
        )

    @abstractmethod
    def _get_domains(
        self,
        *,
        validator: Optional[Validator] = None,
        batch_ids: Optional[List[str]] = None,
        include_batch_id: Optional[bool] = False,
        # TODO: <Alex>ALEX -- We must make sure that the definitions of this method, _get_domains(), in all subclasses adhere to the same signature; currently, the signature for this method is used inconsistently compared to the present (base class) signature.</Alex>
        # TODO: <Alex>ALEX -- Do we want to specify only the "domain_type", or also provide optional "domain_type_filters", or only the latter?</Alex>
        domain_type: Optional[MetricDomainTypes] = None,
        # TODO: <Alex>ALEX -- the following inconsistent signature was found in a subclass.</Alex>
        # type_filters: Optional[List[str]] = None,
        **kwargs
    ):
        """_get_domains is the primary workhorse for the DomainBuilder"""
        pass
