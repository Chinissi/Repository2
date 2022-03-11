import logging
from hashlib import md5
from typing import Optional, Tuple

from great_expectations.util import load_class

logger = logging.getLogger(__name__)


class Anonymizer:
    """Anonymize string names in an optionally-consistent way."""

    def __init__(self, salt: Optional[str] = None) -> None:
        if salt is not None and not isinstance(salt, str):
            logger.error("invalid salt: must provide a string. Setting a random salt.")
            salt = None
        if salt is None:
            import secrets

            self._salt = secrets.token_hex(8)
        else:
            self._salt = salt

    @property
    def salt(self) -> str:
        return self._salt

    def anonymize(self, string_: Optional[str]) -> Optional[str]:
        if string_ is None:
            return None

        if not isinstance(string_, str):
            raise TypeError(
                f"""The type of the "string_" argument must be a string (Python "str").  The type given is
"{str(type(string_))}", which is illegal.
            """
            )

        salted = self._salt + string_
        return md5(salted.encode("utf-8")).hexdigest()

    def anonymize_object_info(
        self,
        anonymized_info_dict: dict,
        ge_classes,
        object_: Optional[object] = None,
        object_class: Optional[type] = None,
        object_config: Optional[dict] = None,
        runtime_environment: Optional[dict] = None,
    ) -> dict:
        assert (
            object_ or object_class or object_config
        ), "Must pass either object_ or object_class or object_config."

        if runtime_environment is None:
            runtime_environment = {}

        object_class_name: Optional[str] = None
        object_module_name: Optional[str] = None
        try:
            if object_class is None and object_ is not None:
                object_class = object_.__class__
            elif object_class is None and object_config is not None:
                object_class_name = object_config.get("class_name")
                object_module_name = object_config.get(
                    "module_name"
                ) or runtime_environment.get("module_name")
                object_class = load_class(object_class_name, object_module_name)

            object_class_name = object_class.__name__
            object_module_name = object_class.__module__
            bases: Tuple[type, ...] = object_class.__bases__

            if object_module_name.startswith("great_expectations"):
                anonymized_info_dict["parent_class"] = object_class_name
            elif len(bases) == 0:
                logger.warning("Could not find parent class when anonymizing payload")
                self._anonymize_class_with_unrecognized_parent(
                    anonymized_info_dict=anonymized_info_dict,
                    class_name=object_class_name,
                )
            elif len(bases) > 1:
                logger.warning(
                    "Due to the ambiguity brought on by multiple inheritance, short-circuiting anonymization of payload"
                )
                self._anonymize_class_with_unrecognized_parent(
                    anonymized_info_dict=anonymized_info_dict,
                    class_name=object_class_name,
                )
            else:
                parent_class: type = bases[0]
                parent_module_name: str = parent_class.__module__
                if parent_module_name.startswith("great_expectations"):
                    anonymized_info_dict["parent_class"] = parent_class.__name__
                    anonymized_info_dict["anonymized_class"] = self.anonymize(
                        object_class_name
                    )
                else:
                    self._anonymize_class_with_unrecognized_parent(
                        anonymized_info_dict=anonymized_info_dict,
                        class_name=object_class_name,
                    )

            if not anonymized_info_dict.get("parent_class"):
                self._anonymize_class_with_unrecognized_parent(
                    anonymized_info_dict=anonymized_info_dict,
                    class_name=object_class_name,
                )

        except AttributeError:
            self._anonymize_class_with_unrecognized_parent(
                anonymized_info_dict=anonymized_info_dict, class_name=object_class_name
            )

        return anonymized_info_dict

    def _anonymize_class_with_unrecognized_parent(
        self, anonymized_info_dict: dict, class_name: Optional[str]
    ) -> None:
        anonymized_info_dict["parent_class"] = "__not_recognized__"
        anonymized_info_dict["anonymized_class"] = self.anonymize(class_name)

    @staticmethod
    def _is_parent_class_recognized(
        classes_to_check,
        object_=None,
        object_class=None,
        object_config=None,
    ) -> Optional[str]:
        """
        Check if the parent class is a subclass of any core GE class.
        This private method is intended to be used by anonymizers in a public `is_parent_class_recognized()` method. These anonymizers define and provide the core GE classes_to_check.
        Returns:
            The name of the parent class found, or None if no parent class was found
        """
        assert (
            object_ or object_class or object_config
        ), "Must pass either object_ or object_class or object_config."
        try:
            if object_class is None and object_ is not None:
                object_class = object_.__class__
            elif object_class is None and object_config is not None:
                object_class_name = object_config.get("class_name")
                object_module_name = object_config.get("module_name")
                object_class = load_class(object_class_name, object_module_name)

            for class_to_check in classes_to_check:
                if issubclass(object_class, class_to_check):
                    return class_to_check.__name__

            return None

        except AttributeError:
            return None
