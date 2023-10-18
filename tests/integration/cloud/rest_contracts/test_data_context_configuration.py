from __future__ import annotations

import pathlib
from typing import Callable

import pytest
from pact import Like

from tests.integration.cloud.rest_contracts.conftest import (
    ContractInteraction,
    organization_id,
)


@pytest.mark.cloud
@pytest.mark.parametrize(
    "contract_interaction",
    [
        ContractInteraction(
            method="GET",
            upon_receiving="a request for a Data Context",
            given="the Data Context exists",
            response_status=200,
            response_body={
                "anonymous_usage_statistics": Like(
                    {
                        "data_context_id": organization_id(),
                        "enabled": True,
                    }
                ),
                "datasources": Like({}),
                "include_rendered_content": {
                    "globally": True,
                    "expectation_validation_result": True,
                    "expectation_suite": True,
                },
            },
        ),
    ],
)
def test_data_context_configuration(
    contract_interaction: ContractInteraction,
    run_pact_test: Callable,
    organziation_id: str,
):
    path = pathlib.Path(
        "/", "organizations", organziation_id, "data-context-configuration"
    )
    run_pact_test(
        path=path,
        contract_interaction=contract_interaction,
    )
