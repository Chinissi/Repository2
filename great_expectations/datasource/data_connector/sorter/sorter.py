import json
import logging
from typing import Any, List

import great_expectations.exceptions as ge_exceptions
from great_expectations.core.batch import BatchDefinition

logger = logging.getLogger(__name__)


class Sorter:
    def __init__(self, name: str, orderby: str = "asc") -> None:
        self._name = name
        if orderby is None or orderby == "asc":
            reverse: bool = False
        elif orderby == "desc":
            reverse: bool = True
        else:
            raise ge_exceptions.SorterError(
                f'Illegal sort order "{orderby}" for attribute "{name}".'
            )
        self._reverse = reverse

    def get_sorted_batch_definitions(
        self, batch_definitions: List[BatchDefinition]
    ) -> List[BatchDefinition]:
        none_batches: List[int] = []
        value_batches: List[int] = []
        for idx, batch_definition in enumerate(batch_definitions):
            for value in batch_definition.batch_identifiers.values():
                if value is None:
                    none_batches.append(idx)
                else:
                    value_batches.append(idx)

        none_batch_definitions: List[BatchDefinition] = [
            batch_definitions[idx] for idx in none_batches
        ]
        value_batch_definitiions: List[BatchDefinition] = sorted(
            [batch_definitions[idx] for idx in value_batches],
            key=self.get_batch_key,
            reverse=self.reverse,
        )

        # the convention for ORDER BY in SQL is for NULL values to be first in the sort order for ascending
        # and last in the sort order for descending
        if self.reverse:
            return value_batch_definitiions + none_batch_definitions
        return none_batch_definitions + value_batch_definitiions

    def get_batch_key(self, batch_definition: BatchDefinition) -> Any:
        raise NotImplementedError

    @property
    def name(self) -> str:
        return self._name

    @property
    def reverse(self) -> bool:
        return self._reverse

    def __repr__(self) -> str:
        doc_fields_dict: dict = {"name": self.name, "reverse": self.reverse}
        return json.dumps(doc_fields_dict, indent=2)
