import copy
from typing import Any, List, Optional, Set, Union

from great_expectations.core.batch import (
    BATCH_REQUEST_INSTANTIATION_KEYS,
    BatchRequest,
    RuntimeBatchRequest,
    get_batch_request_from_acceptable_arguments,
)
from great_expectations.core.usage_statistics.anonymizers.anonymizer import Anonymizer


class BatchRequestAnonymizer(Anonymizer):
    def __init__(self, salt=None):
        super().__init__(salt=salt)

    def anonymize_batch_request(self, *args, **kwargs) -> List[Union[str, dict]]:
        batch_request: Union[
            BatchRequest, RuntimeBatchRequest
        ] = get_batch_request_from_acceptable_arguments(*args, **kwargs)
        batch_request_dict: dict = batch_request.to_json_dict()
        anonymized_batch_request_dict: Optional[
            Union[Any, dict]
        ] = self._anonymize_batch_request_properties(source=batch_request_dict)
        anonymized_batch_request: List[Union[str, dict]] = []
        self._build_anonymized_batch_request(
            destination=anonymized_batch_request, source=anonymized_batch_request_dict
        )
        return anonymized_batch_request

    def _anonymize_batch_request_properties(
        self, source: Optional[Any] = None
    ) -> Optional[Union[Any, dict]]:
        if source is None:
            return None

        if isinstance(source, str) and source in BATCH_REQUEST_INSTANTIATION_KEYS:
            return source

        if isinstance(source, dict):
            source_copy: dict = copy.deepcopy(source)
            anonymized_keys: Set[str] = set()

            key: str
            value: Any
            for key, value in source.items():
                if key in BATCH_REQUEST_INSTANTIATION_KEYS:
                    source_copy[key] = self._anonymize_batch_request_properties(
                        source=value
                    )
                else:
                    anonymized_key: str = self.anonymize(key)
                    source_copy[
                        anonymized_key
                    ] = self._anonymize_batch_request_properties(source=value)
                    anonymized_keys.add(key)

            for key in anonymized_keys:
                source_copy.pop(key)

            return source_copy

        return self.anonymize(str(source))

    def _build_anonymized_batch_request(
        self, destination: List[Union[str, dict]], source: Optional[Any] = None
    ):
        if isinstance(source, dict):
            key: str
            value: Any
            for key, value in source.items():
                if key in BATCH_REQUEST_INSTANTIATION_KEYS:
                    if isinstance(value, dict):
                        anonymized_keys: List[Union[str, dict]] = []
                        destination.append({key: anonymized_keys})
                        self._build_anonymized_batch_request(
                            destination=anonymized_keys, source=value
                        )
                    else:
                        destination.append(key)
