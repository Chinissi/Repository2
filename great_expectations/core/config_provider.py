import errno
import os
from abc import ABC, abstractmethod
from typing import Dict, Optional

from great_expectations.core.yaml_handler import YAMLHandler

yaml = YAMLHandler()


class AbstractConfigurationProvider(ABC):
    @abstractmethod
    def get_values(self) -> Dict[str, str]:
        """
        TODO
        """
        pass


class ConfigurationProvider(AbstractConfigurationProvider):
    def __init__(self) -> None:
        self._providers = {}

    def register_provider(self, provider: AbstractConfigurationProvider):
        type_ = type(provider)
        if type_ in self._providers:
            raise ValueError(f"Provider of type {type_} has already been registered!")
        self._providers[type_] = provider

    def get_values(self) -> Dict[str, str]:
        values = {}
        for provider in self._providers.values():
            values.update(provider.get_values())
        return values


class RuntimeEnvironmentConfigurationProvider(AbstractConfigurationProvider):
    def __init__(self, runtime_environment: Dict[str, str]) -> None:
        self._runtime_environment = runtime_environment

    def get_values(self) -> Dict[str, str]:
        return self._runtime_environment


class EnvironmentConfigurationProvider(AbstractConfigurationProvider):
    def get_values(self) -> Dict[str, str]:
        return dict(os.environ)


class ConfigurationVariablesConfigurationProvider(AbstractConfigurationProvider):
    def __init__(
        self, config_variables_file_path: str, root_directory: Optional[str] = None
    ) -> None:
        self._config_variables_file_path = config_variables_file_path
        self._root_directory = root_directory

    def get_values(self) -> Dict[str, str]:
        try:
            # If the user specifies the config variable path with an environment variable, we want to substitute it
            defined_path: str = substitute_config_variable(  # type: ignore[assignment]
                self._config_variables_file_path, dict(os.environ)
            )
            if not os.path.isabs(defined_path) and hasattr(self, "root_directory"):
                # A BaseDataContext will not have a root directory; in that case use the current directory
                # for any non-absolute path
                root_directory: str = self._root_directory or os.curdir
            else:
                root_directory = ""
            var_path = os.path.join(root_directory, defined_path)
            with open(var_path) as config_variables_file:
                contents = config_variables_file.read()

            variables = yaml.load(contents) or {}
            return dict(variables)

        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
            return {}
