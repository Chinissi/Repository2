import pathlib

import pytest


@pytest.fixture
def sample_docs_example_python_file_string() -> str:
    return """from scripts.sample_with_definitions import ExampleClass, example_module_level_function

ec = ExampleClass()

ec.example_method()

a = ec.example_method_with_args(some_arg=1, other_arg=2)

b = ec.example_staticmethod()

c = ec.example_classmethod()

example_module_level_function()

d = example_module_level_function()

assert d
"""


@pytest.fixture
def sample_with_definitions_python_file_string() -> str:
    return """
class ExampleClass:

    def __init__(self):
        pass

    def example_method(self):
        pass

    def example_method_with_args(self, some_arg, other_arg):
        pass

    @staticmethod
    def example_staticmethod():
        pass

    @classmethod
    def example_classmethod(cls):
        pass


def example_module_level_function():
    pass
"""

@pytest.fixture
def sample_docs_example_python_file_string_filepath() -> pathlib.Path:
    return pathlib.Path("/great_expectations/sample_docs_example_python_file_string.py")

@pytest.fixture
def sample_with_definitions_python_file_string_filepath() -> pathlib.Path:
    return pathlib.Path("/great_expectations/sample_with_definitions_python_file_string.py")

@pytest.fixture
def filesystem_with_samples(fs, sample_docs_example_python_file_string: str, sample_docs_example_python_file_string_filepath: pathlib.Path, sample_with_definitions_python_file_string: str, sample_with_definitions_python_file_string_filepath: pathlib.Path) -> None:
    fs.create_file(sample_docs_example_python_file_string_filepath, contents=sample_docs_example_python_file_string)
    fs.create_file(sample_with_definitions_python_file_string_filepath, contents=sample_with_definitions_python_file_string)


def test_fixtures_are_accessible(filesystem_with_samples, sample_docs_example_python_file_string: str, sample_docs_example_python_file_string_filepath: pathlib.Path, sample_with_definitions_python_file_string: str, sample_with_definitions_python_file_string_filepath: pathlib.Path):
    with open(sample_docs_example_python_file_string_filepath) as f:
        file_contents = f.read()
        assert file_contents == sample_docs_example_python_file_string
        assert len(file_contents) > 200

    with open(sample_with_definitions_python_file_string_filepath) as f:
        file_contents = f.read()
        assert file_contents == sample_with_definitions_python_file_string
        assert len(file_contents) > 200



# class TestDocExampleParser:
#
#     def test_retrieve_all_usages_in_files(self):
#         doc_example_parser = DocExampleParser()



#
# def test_parse_method_names(sample_docs_example_python_file_string):
#     """Ensure method names are retrieved from test file."""
#     print(sample_docs_example_python_file_string)
