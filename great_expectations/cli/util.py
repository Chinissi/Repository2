import importlib
import re
import sys
from types import ModuleType
from typing import Dict, Union

import pkg_resources

from great_expectations.cli.python_subprocess import (
    execute_shell_command_with_progress_polling,
)
from great_expectations.util import import_library_module

try:
    from termcolor import colored
except ImportError:
    colored = None


def cli_message(string):
    # the DOTALL flag means that `.` includes newlines for multiline comments inside these tags
    flags = re.DOTALL
    mod_string = re.sub(
        "<blue>(.*?)</blue>", colored("\g<1>", "blue"), string, flags=flags
    )
    mod_string = re.sub(
        "<cyan>(.*?)</cyan>", colored("\g<1>", "cyan"), mod_string, flags=flags
    )
    mod_string = re.sub(
        "<green>(.*?)</green>", colored("\g<1>", "green"), mod_string, flags=flags
    )
    mod_string = re.sub(
        "<yellow>(.*?)</yellow>", colored("\g<1>", "yellow"), mod_string, flags=flags
    )
    mod_string = re.sub(
        "<red>(.*?)</red>", colored("\g<1>", "red"), mod_string, flags=flags
    )

    print(colored(mod_string))


def cli_message_list(string_list, list_intro_string=None):
    """Simple util function for displaying simple lists in cli"""
    if list_intro_string:
        cli_message(list_intro_string)
    for string in string_list:
        cli_message(string)


def action_list_to_string(action_list):
    """Util function for turning an action list into pretty string"""
    action_list_string = ""
    for idx, action in enumerate(action_list):
        action_list_string += "{} ({})".format(
            action["name"], action["action"]["class_name"]
        )
        if idx == len(action_list) - 1:
            continue
        action_list_string += " => "
    return action_list_string


def cli_message_dict(
    dict_, indent=3, bullet_char="-", message_list=None, recursion_flag=False
):
    """Util function for displaying nested dicts representing ge objects in cli"""
    if message_list is None:
        message_list = []
    if dict_.get("name"):
        name = dict_.pop("name")
        message = "{}<cyan>name:</cyan> {}".format(" " * indent, name)
        message_list.append(message)
    if dict_.get("module_name"):
        module_name = dict_.pop("module_name")
        message = "{}<cyan>module_name:</cyan> {}".format(" " * indent, module_name)
        message_list.append(message)
    if dict_.get("class_name"):
        class_name = dict_.pop("class_name")
        message = "{}<cyan>class_name:</cyan> {}".format(" " * indent, class_name)
        message_list.append(message)
    if dict_.get("action_list"):
        action_list = dict_.pop("action_list")
        action_list_string = action_list_to_string(action_list)
        message = "{}<cyan>action_list:</cyan> {}".format(
            " " * indent, action_list_string
        )
        message_list.append(message)
    sorted_keys = sorted(dict_.keys())
    for key in sorted_keys:
        if key == "password":
            message = "{}<cyan>password:</cyan> ******".format(" " * indent)
            message_list.append(message)
            continue
        if isinstance(dict_[key], dict):
            message = "{}<cyan>{}:</cyan>".format(" " * indent, key)
            message_list.append(message)
            cli_message_dict(
                dict_[key],
                indent=indent + 2,
                message_list=message_list,
                recursion_flag=True,
            )
        else:
            message = "{}<cyan>{}:</cyan> {}".format(" " * indent, key, str(dict_[key]))
            message_list.append(message)
    if not recursion_flag:
        if bullet_char and indent > 1:
            first = message_list[0]
            new_first = first[:1] + bullet_char + first[2:]
            message_list[0] = new_first
        cli_message_list(message_list)


def is_sane_slack_webhook(url):
    """Really basic sanity checking."""
    if url is None:
        return False

    return url.strip().startswith("https://hooks.slack.com/")


def is_library_loadable(library_name: str) -> bool:
    module_obj: Union[ModuleType, None] = import_library_module(
        module_name=library_name
    )
    return module_obj is not None


def library_install_load_check(
    python_import_name: str, pip_library_name: str
) -> Union[int, None]:
    """
    Dynamically load a module from strings, attempt a pip install or raise a helpful error.

    :return: True if the library was loaded successfully, False otherwise

    Args:
        pip_library_name: name of the library to load
        python_import_name (str): a module to import to verify installation
    """
    # TODO[Taylor+Alex] integration tests
    if is_library_loadable(library_name=python_import_name):
        return None

    status_code: int = execute_shell_command_with_progress_polling(
        f"pip install {pip_library_name}"
    )

    pkg_resources.working_set = pkg_resources.WorkingSet._build_master()

    library_loadable: bool = is_library_loadable(library_name=python_import_name)

    if status_code == 0 and library_loadable:
        return 0

    if not library_loadable:
        cli_message(
            f"""<red>ERROR: Great Expectations relies on the library `{pip_library_name}` to connect to your data.</red>
        - Please `pip install {pip_library_name}` before trying again."""
        )
        return 1

    return status_code


def reload_modules_containing_pattern(pattern: str = None) -> None:
    module_name: str
    for module_name in get_ge_module_names():
        if module_name in sys.modules.keys():
            module_obj: Union[ModuleType, None] = import_library_module(
                module_name=module_name, pattern=pattern
            )
            if module_obj is not None:
                try:
                    _ = importlib.reload(module_obj)
                except RuntimeError:
                    pass


def verify_library_dependent_modules(
    python_import_name: str,
    pip_library_name: str,
    pattern: str = None,
    force_reload_if_package_loaded: bool = False,
) -> Dict[str, bool]:
    library_status_code: Union[int, None]

    library_status_code = library_install_load_check(
        python_import_name=python_import_name, pip_library_name=pip_library_name
    )

    do_reload: bool
    success: bool

    if library_status_code == 0:
        do_reload = True
        success = True
    elif library_status_code is None:
        do_reload = force_reload_if_package_loaded
        success = True
    else:
        do_reload = False
        success = False

    if do_reload:
        reload_modules_containing_pattern(pattern=pattern)

    return {"success": success, "reloaded": do_reload}


def get_ge_module_names() -> list:
    module_name: str
    return [
        module_name
        for module_name in sys.modules.keys()
        if module_name.split(".")[0] == "great_expectations"
    ]
