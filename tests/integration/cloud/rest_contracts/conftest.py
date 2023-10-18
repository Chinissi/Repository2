from __future__ import annotations

import enum
import os
import pathlib
import subprocess
from typing import TYPE_CHECKING, Callable, Final, Union

import pytest
from pact import Consumer, Pact, Provider
from pact.matchers import Matcher  # noqa: TCH002
from typing_extensions import Annotated  # noqa: TCH002

from great_expectations.compatibility import pydantic
from great_expectations.core.http import create_session

if TYPE_CHECKING:
    from requests import Session


PACT_MOCK_HOST: Final[str] = "localhost"
PACT_MOCK_PORT: Final[int] = 9292
PACT_DIR: Final[str] = str(
    pathlib.Path(pathlib.Path(__file__).parent, "pacts").resolve()
)


@pytest.fixture
def organization_id() -> str:
    try:
        return os.environ["GX_CLOUD_ORGANIZATION_ID"]
    except KeyError as e:
        raise OSError("GX_CLOUD_ORGANIZATION_ID is not set in this environment.") from e


class RequestMethods(str, enum.Enum):
    DELETE = "DELETE"
    GET = "GET"
    PATCH = "PATCH"
    POST = "POST"
    PUT = "PUT"


@pytest.fixture
def session() -> Session:
    try:
        access_token = os.environ["GX_CLOUD_ACCESS_TOKEN"]
    except KeyError as e:
        raise OSError("GX_CLOUD_ACCESS_TOKEN is not set in this environment.") from e
    return create_session(access_token=access_token)


def get_git_commit_hash() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"]).decode("ascii").strip()


@pytest.fixture
def pact(request) -> Pact:
    pact_broker_base_url = "https://greatexpectations.pactflow.io"
    consumer_name = "great_expectations"
    provider_name = "mercury"

    broker_token: str
    publish_to_broker: bool
    if os.environ.get("PACT_BROKER_READ_WRITE_TOKEN"):
        broker_token = os.environ.get("PACT_BROKER_READ_WRITE_TOKEN")
        publish_to_broker = True
    else:
        broker_token = os.environ.get("PACT_BROKER_READ_ONLY_TOKEN")
        publish_to_broker = False

    pact: Pact = Consumer(
        name=consumer_name,
        version=get_git_commit_hash(),
        tag_with_git_branch=True,
        auto_detect_version_properties=True,
    ).has_pact_with(
        Provider(name=provider_name),
        broker_base_url=pact_broker_base_url,
        broker_token=broker_token,
        host_name=PACT_MOCK_HOST,
        port=PACT_MOCK_PORT,
        pact_dir=PACT_DIR,
        publish_to_broker=publish_to_broker,
    )

    pact.start_service()
    yield pact
    pact.stop_service()


class ContractInteraction(pydantic.BaseModel):
    """Represents a Python API (Consumer) request and expected minimal response,
       given a state in the Cloud backend (Provider).

    The given state is something you know to be true about the Cloud backend data requested.

    Args:
        method: A string (e.g. "GET" or "POST") or attribute of the RequestMethods class representing a request method.
        upon_receiving: A string description of the type of request being made.
        given: A string description of the state of the Cloud backend data requested.
        response_status: The status code associated with the response. An integer between 100 and 599.
        response_body: A dictionary or Pact Matcher object representing the response body.
        request_body (Optional): A dictionary or Pact Matcher object representing the request body.
        request_headers (Optional): A dictionary representing the request headers.

    Returns:
        ContractInteraction
    """

    class Config:
        arbitrary_types_allowed = True

    method: RequestMethods
    upon_receiving: pydantic.StrictStr
    given: pydantic.StrictStr
    response_status: Annotated[int, pydantic.Field(strict=True, ge=100, lt=600)]
    response_body: Union[dict, Matcher]
    request_body: Union[dict, Matcher, None] = None
    request_headers: Union[dict, None] = None


@pytest.fixture
def run_pact_test(
    session: Session,
    pact: Pact,
) -> Callable:
    def _run_pact_test(
        path: pathlib.Path,
        contract_interaction: ContractInteraction,
    ):
        request = {
            "method": contract_interaction.method,
            "path": str(path),
        }
        if contract_interaction.request_body is not None:
            request["body"] = contract_interaction.request_body

        request["headers"] = dict(session.headers)
        if contract_interaction.request_headers is not None:
            request["headers"].update(contract_interaction.request_headers)
            session.headers.update(contract_interaction.request_headers)

        response = {
            "status": contract_interaction.response_status,
            "body": contract_interaction.response_body,
        }

        (
            pact.given(provider_state=contract_interaction.given)
            .upon_receiving(scenario=contract_interaction.upon_receiving)
            .with_request(**request)
            .will_respond_with(**response)
        )

        request_url = f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}{path}"

        with pact:
            session.get(request_url)

    return _run_pact_test
