from __future__ import annotations

import os
import pathlib
from typing import TYPE_CHECKING, Callable, Final, Union

import pydantic
import pytest
from pact import Consumer, Pact, Provider
from pact.matchers import Matcher

from great_expectations.core.http import create_session

if TYPE_CHECKING:
    from requests import Session

CONSUMER: Final[str] = "great_expectations"
PROVIDER: Final[str] = "mercury"

PACT_BROKER_BASE_URL: Final[str] = "https://greatexpectations.pactflow.io"
PACT_BROKER_TOKEN: Final[str] = os.environ.get("PACT_BROKER_READ_ONLY_TOKEN")
PACT_MOCK_HOST: Final[str] = "localhost"
PACT_MOCK_PORT: Final[int] = 9292
PACT_DIR: Final[str] = str(pathlib.Path(__file__).parent.resolve())
PACT_MOCK_MERCURY_URL: Final[str] = f"http://{PACT_MOCK_HOST}:{PACT_MOCK_PORT}"


@pytest.fixture
def session() -> Session:
    return create_session(access_token=os.environ.get("GX_CLOUD_ACCESS_TOKEN"))


@pytest.fixture
def pact(request) -> Pact:
    pact: Pact = Consumer(CONSUMER).has_pact_with(
        Provider(PROVIDER),
        broker_base_url=PACT_BROKER_BASE_URL,
        broker_token=PACT_BROKER_TOKEN,
        host_name=PACT_MOCK_HOST,
        port=PACT_MOCK_PORT,
        pact_dir=PACT_DIR,
    )
    pact.start_service()
    yield pact
    pact.stop_service()


class ContractInteraction(pydantic.BaseModel):
    class Config:
        arbitrary_types_allowed = True

    method: str
    upon_receiving: str
    given: str
    request_body: Union[dict, Matcher, None] = None
    request_headers: Union[dict, None] = None
    response_status: int
    response_body: Union[dict, Matcher]


@pytest.fixture
def run_pact_test(
    session: Session,
    pact: Pact,
) -> Callable:
    def _run_pact_test(
        path: str,
        contract_interaction: ContractInteraction,
    ):
        request = {
            "method": contract_interaction.method,
            "path": path,
        }
        if contract_interaction.request_body is not None:
            request["body"] = contract_interaction.request_body
        if contract_interaction.request_headers is not None:
            request["headers"] = contract_interaction.request_headers

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

        request_url = f"{PACT_MOCK_MERCURY_URL}{path}"

        with pact:
            session.get(request_url)

    return _run_pact_test
