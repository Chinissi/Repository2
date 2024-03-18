import json
import logging
from typing import Type, Union
from unittest import mock

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture
from requests import Session

from great_expectations import set_context
from great_expectations.checkpoint.actions import (
    APINotificationAction,
    EmailAction,
    MicrosoftTeamsNotificationAction,
    OpsgenieAlertAction,
    PagerdutyAlertAction,
    SlackNotificationAction,
    SNSNotificationAction,
    StoreValidationResultAction,
    UpdateDataDocsAction,
    ValidationAction,
)
from great_expectations.checkpoint.util import smtplib
from great_expectations.compatibility.pydantic import BaseModel, Field, ValidationError
from great_expectations.core.expectation_validation_result import (
    ExpectationSuiteValidationResult,
)
from great_expectations.core.run_identifier import RunIdentifier
from great_expectations.data_context.data_context.abstract_data_context import (
    AbstractDataContext,
)
from great_expectations.data_context.store import ValidationsStore
from great_expectations.data_context.types.resource_identifiers import (
    BatchIdentifier,
    ExpectationSuiteIdentifier,
    ValidationResultIdentifier,
)
from great_expectations.render.renderer.renderer import Renderer
from great_expectations.util import is_library_loadable
from tests.test_ge_utils import file_data_asset

logger = logging.getLogger(__name__)


@pytest.fixture
def mock_context(mocker: MockerFixture):
    context = mocker.MagicMock(spec=AbstractDataContext)
    set_context(context)
    return context


class MockTeamsResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = "test_text"


class MockSlackResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = "ok"
        self.content = json.dumps({"ok": "True"})

    def json(self):
        return {"ok": "True"}


class MockCloudResponse:
    def __init__(self, status_code):
        self.status_code = status_code
        self.text = "test_text"
        self.content = json.dumps({"ok": "True"})


@pytest.mark.big
@freeze_time("09/26/2019 13:42:41")
def test_StoreAction(mock_context):
    fake_in_memory_store = ValidationsStore(
        store_backend={
            "class_name": "InMemoryStoreBackend",
        }
    )
    stores = {"fake_in_memory_store": fake_in_memory_store}

    class Object:
        cloud_mode = False

    data_context = Object()
    data_context.stores = stores

    action = StoreValidationResultAction(
        data_context=data_context,
        target_store_name="fake_in_memory_store",
    )
    assert fake_in_memory_store.list_keys() == []

    action.run(
        validation_result_suite_identifier=ValidationResultIdentifier(
            expectation_suite_identifier=ExpectationSuiteIdentifier(
                name="default_expectations"
            ),
            run_id=RunIdentifier(run_name="prod_20190801"),
            batch_identifier="1234",
        ),
        validation_result_suite=ExpectationSuiteValidationResult(
            success=False, results=[]
        ),
        data_asset=None,
    )

    expected_run_id = RunIdentifier(
        run_name="prod_20190801", run_time="20190926T134241.000000Z"
    )

    assert len(fake_in_memory_store.list_keys()) == 1
    stored_identifier = fake_in_memory_store.list_keys()[0]
    assert stored_identifier.batch_identifier == "1234"
    assert stored_identifier.expectation_suite_identifier.name == "default_expectations"
    assert stored_identifier.run_id == expected_run_id

    assert fake_in_memory_store.get(
        ValidationResultIdentifier(
            expectation_suite_identifier=ExpectationSuiteIdentifier(
                name="default_expectations"
            ),
            run_id=expected_run_id,
            batch_identifier="1234",
        )
    ) == ExpectationSuiteValidationResult(success=False, results=[])


@pytest.mark.big
@mock.patch.object(Session, "post", return_value=MockSlackResponse(200))
def test_SlackNotificationAction(
    validation_result_suite,
    validation_result_suite_id,
    mock_context,
):
    renderer = {
        "module_name": "great_expectations.render.renderer.slack_renderer",
        "class_name": "SlackRenderer",
    }
    slack_webhook = "https://hooks.slack.com/services/test/slack/webhook"
    slack_token = "test"
    slack_channel = "test"
    notify_on = "all"

    # test with just web_hook set; expect pass
    slack_action = SlackNotificationAction(
        renderer=renderer,
        slack_webhook=slack_webhook,
        notify_on=notify_on,
    )

    assert slack_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"slack_notification_result": "Slack notification succeeded."}

    # Test with slack_token and slack_channel set; expect pass
    slack_action = SlackNotificationAction(
        renderer=renderer,
        slack_token=slack_token,
        slack_channel=slack_channel,
        notify_on=notify_on,
    )

    assert slack_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"slack_notification_result": "Slack notification succeeded."}

    # test for long text message - should be split into multiple messages
    long_text = "a" * 10000
    validation_result_suite.meta = {
        "active_batch_definition": BatchIdentifier(
            batch_identifier="1234", data_asset_name=long_text
        ),
    }

    assert slack_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"slack_notification_result": "Slack notification succeeded."}

    # Test with just slack_token set; expect fail
    with pytest.raises(ValidationError):
        SlackNotificationAction(
            renderer=renderer,
            slack_token=slack_token,
            notify_on=notify_on,
        )

    # Test with just slack_channel set; expect fail
    with pytest.raises(ValidationError):
        slack_action = SlackNotificationAction(
            renderer=renderer,
            slack_channel=slack_channel,
            notify_on=notify_on,
        )

    # Test with slack_channel, slack_token, and slack_webhook set; expect fail
    with pytest.raises(ValidationError):
        SlackNotificationAction(
            renderer=renderer,
            slack_channel=slack_channel,
            slack_token=slack_token,
            slack_webhook=slack_webhook,
            notify_on=notify_on,
        )

    # test notify on with failed run; expect pass
    notify_on = "failure"
    slack_action = SlackNotificationAction(
        renderer=renderer,
        slack_webhook=slack_webhook,
        notify_on=notify_on,
    )

    assert slack_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=ExpectationSuiteValidationResult(
            success=False,
            results=[],
            statistics={
                "successful_expectations": [],
                "evaluated_expectations": [],
            },
        ),
        data_asset=None,
    ) == {"slack_notification_result": "Slack notification succeeded."}

    # test notify on with successful run; expect pass
    notify_on = "failure"
    validation_result_suite.success = False
    slack_action = SlackNotificationAction(
        renderer=renderer,
        slack_webhook=slack_webhook,
        notify_on=notify_on,
    )

    assert slack_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=ExpectationSuiteValidationResult(
            success=True,
            results=[],
            statistics={
                "successful_expectations": [],
                "evaluated_expectations": [],
            },
        ),
        data_asset=None,
    ) == {"slack_notification_result": "none required"}


@pytest.mark.big
@pytest.mark.skipif(
    not is_library_loadable(library_name="pypd"),
    reason="pypd is not installed",
)
@mock.patch("pypd.EventV2")
def test_PagerdutyAlertAction(
    validation_result_suite,
    validation_result_suite_id,
    mock_context,
):
    api_key = "test"
    routing_key = "test"

    pagerduty_action = PagerdutyAlertAction(
        api_key=api_key,
        routing_key=routing_key,
    )

    # Make sure the alert is sent by default when the validation has success = False
    validation_result_suite.success = False

    assert pagerduty_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"pagerduty_alert_result": "success"}

    # Make sure the alert is not sent by default when the validation has success = True
    validation_result_suite.success = True

    assert pagerduty_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"pagerduty_alert_result": "none sent"}


@pytest.mark.big
def test_OpsgenieAlertAction(
    validation_result_suite,
    validation_result_suite_id,
    mock_context,
):
    renderer = {
        "module_name": "great_expectations.render.renderer.opsgenie_renderer",
        "class_name": "OpsgenieRenderer",
    }
    opsgenie_action = OpsgenieAlertAction(
        renderer=renderer,
        api_key="testapikey",
        region=None,
        priority="P3",
        notify_on="all",
    )

    # Make sure the alert is sent by default when the validation has success = False
    validation_result_suite.success = False

    assert opsgenie_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"opsgenie_alert_result": "error"}

    # Make sure the alert is not sent by default when the validation has success = True
    validation_result_suite.success = True

    assert opsgenie_action.run(
        validation_result_suite_identifier=validation_result_suite_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"opsgenie_alert_result": "error"}


@pytest.mark.big
@mock.patch.object(Session, "post", return_value=MockTeamsResponse(200))
def test_MicrosoftTeamsNotificationAction_good_request(
    validation_result_suite,
    validation_result_suite_extended_id,
    mock_context,
):
    renderer = {
        "module_name": "great_expectations.render.renderer.microsoft_teams_renderer",
        "class_name": "MicrosoftTeamsRenderer",
    }
    teams_webhook = "http://testing"
    notify_on = "all"
    teams_action = MicrosoftTeamsNotificationAction(
        renderer=renderer,
        teams_webhook=teams_webhook,
        notify_on=notify_on,
    )

    # validation_result_suite is None
    assert (
        teams_action.run(
            validation_result_suite_identifier=validation_result_suite_extended_id,
            validation_result_suite=None,
            data_asset=None,
        )
        is None
    )

    # if validation_result_suite_identifier is not ValidationResultIdentifier
    with pytest.raises(TypeError):
        teams_action.run(
            validation_result_suite_identifier="i_wont_work",
            validation_result_suite=validation_result_suite,
            data_asset=None,
        )

    assert teams_action.run(
        validation_result_suite_identifier=validation_result_suite_extended_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {
        "microsoft_teams_notification_result": "Microsoft Teams notification succeeded."
    }

    # notify_on = success will return "Microsoft Teams notification succeeded" message
    # only if validation_result_suite.success = True
    validation_result_suite.success = False
    notify_on = "success"
    teams_action = MicrosoftTeamsNotificationAction(
        renderer=renderer,
        teams_webhook=teams_webhook,
        notify_on=notify_on,
    )
    assert teams_action.run(
        validation_result_suite_identifier=validation_result_suite_extended_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"microsoft_teams_notification_result": None}

    validation_result_suite.success = True
    notify_on = "success"
    teams_action = MicrosoftTeamsNotificationAction(
        renderer=renderer,
        teams_webhook=teams_webhook,
        notify_on=notify_on,
    )
    assert teams_action.run(
        validation_result_suite_identifier=validation_result_suite_extended_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {
        "microsoft_teams_notification_result": "Microsoft Teams notification succeeded."
    }

    # notify_on failure will return "Microsoft Teams notification succeeded" message
    # only if validation_result_suite.success = False
    validation_result_suite.success = False
    notify_on = "failure"
    teams_action = MicrosoftTeamsNotificationAction(
        renderer=renderer,
        teams_webhook=teams_webhook,
        notify_on=notify_on,
    )
    assert teams_action.run(
        validation_result_suite_identifier=validation_result_suite_extended_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {
        "microsoft_teams_notification_result": "Microsoft Teams notification succeeded."
    }

    validation_result_suite.success = True
    notify_on = "failure"
    teams_action = MicrosoftTeamsNotificationAction(
        renderer=renderer,
        teams_webhook=teams_webhook,
        notify_on=notify_on,
    )
    assert teams_action.run(
        validation_result_suite_identifier=validation_result_suite_extended_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"microsoft_teams_notification_result": None}


@pytest.mark.big
@mock.patch.object(Session, "post", return_value=MockTeamsResponse(400))
def test_MicrosoftTeamsNotificationAction_bad_request(
    validation_result_suite,
    validation_result_suite_extended_id,
    caplog,
    mock_context,
):
    caplog.set_level(logging.WARNING)
    renderer = {
        "module_name": "great_expectations.render.renderer.microsoft_teams_renderer",
        "class_name": "MicrosoftTeamsRenderer",
    }
    teams_webhook = "http://testing"

    # notify : all
    notify_on = "all"
    teams_action = MicrosoftTeamsNotificationAction(
        renderer=renderer,
        teams_webhook=teams_webhook,
        notify_on=notify_on,
    )
    assert teams_action.run(
        validation_result_suite_identifier=validation_result_suite_extended_id,
        validation_result_suite=validation_result_suite,
        data_asset=None,
    ) == {"microsoft_teams_notification_result": None}

    assert "Request to Microsoft Teams webhook returned error 400" in caplog.text


class MockSMTPServer:
    def __init__(self, raise_on, exception):
        self.raise_on = raise_on
        self.exception = exception

    def __call__(self, *arg, **kwargs):
        if self.raise_on == "__init__":
            raise self.exception
        return self

    def starttls(self, *args, **kwargs):
        if self.raise_on == "starttls":
            raise self.exception

    def login(self, *args, **kwargs):
        if self.raise_on == "login":
            raise self.exception

    def sendmail(self, *args, **kwargs):
        if self.raise_on == "sendmail":
            raise self.exception

    def quit(self, *args, **kwargs):
        if self.raise_on == "quit":
            raise self.exception


@pytest.mark.parametrize(
    (
        "class_to_patch,use_tls,use_ssl,sender_login,sender_password,raise_on,exception,expected,"
        "validation_result_suite,validation_result_suite_id"
    ),
    [
        ("SMTP", False, False, "test", "test", None, None, "success", None, None),
        ("SMTP", True, False, "test", "test", None, None, "success", None, None),
        ("SMTP", False, False, "test", "test", None, None, "success", None, None),
        (
            "SMTP_SSL",
            False,
            True,
            "test",
            "test",
            None,
            None,
            "success",
            None,
            None,
        ),
        (
            "SMTP_SSL",
            False,
            True,
            "test",
            "test",
            "__init__",
            smtplib.SMTPConnectError(421, "Can't connect"),
            None,
            None,
            None,
        ),
        (
            "SMTP",
            True,
            False,
            "test",
            "test",
            "starttls",
            smtplib.SMTPConnectError(421, "Can't connect"),
            None,
            None,
            None,
        ),
        (
            "SMTP",
            True,
            False,
            "test",
            "test",
            "login",
            smtplib.SMTPAuthenticationError(534, "Can't authenticate"),
            None,
            None,
            None,
        ),
        (
            "SMTP",
            False,
            False,
            None,
            None,
            "login",
            smtplib.SMTPAuthenticationError(534, "Can't authenticate"),
            "success",
            None,
            None,
        ),
    ],
    indirect=[
        "validation_result_suite",
        "validation_result_suite_id",
    ],
    scope="module",
)
@pytest.mark.big
def test_EmailAction(
    class_to_patch,
    use_tls,
    use_ssl,
    sender_login,
    sender_password,
    raise_on,
    exception,
    expected,
    validation_result_suite,
    validation_result_suite_id,
    mock_context,
):
    with mock.patch.object(
        smtplib,
        class_to_patch,
        new=MockSMTPServer(raise_on=raise_on, exception=exception),
    ):
        renderer = {
            "module_name": "great_expectations.render.renderer.email_renderer",
            "class_name": "EmailRenderer",
        }
        smtp_address = "test"
        smtp_port = 999
        sender_alias = "other"
        receiver_emails = "test"
        notify_on = "all"
        email_action = EmailAction(
            renderer=renderer,
            smtp_address=smtp_address,
            smtp_port=smtp_port,
            sender_login=sender_login,
            sender_password=sender_password,
            sender_alias=sender_alias,
            receiver_emails=receiver_emails,
            notify_on=notify_on,
            use_tls=use_tls,
            use_ssl=use_ssl,
        )
        assert email_action.sender_login != email_action.sender_alias
        assert email_action.run(
            validation_result_suite_identifier=validation_result_suite_id,
            validation_result_suite=validation_result_suite,
            data_asset=None,
        ) == {"email_result": expected}


@pytest.mark.unit
def test_api_action_create_payload(mock_context):
    mock_validation_results = []
    expected_payload = '{"test_suite_name": "my_suite", "data_asset_name": "my_schema.my_table", "validation_results": []}'
    api_notification_action = APINotificationAction(url="http://www.example.com")
    payload = api_notification_action.create_payload(
        "my_schema.my_table", "my_suite", mock_validation_results
    )
    assert payload == expected_payload


@pytest.mark.big
@mock.patch("great_expectations.checkpoint.actions.requests")
def test_api_action_run(
    mock_requests,
    validation_result_suite,
    validation_result_suite_id,
    mocker: MockerFixture,
    mock_context,
):
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_requests.post.return_value = mock_response
    api_notification_action = APINotificationAction(url="http://www.example.com")
    response = api_notification_action.run(
        validation_result_suite, validation_result_suite_id, file_data_asset
    )
    assert response == "Successfully Posted results to API, status code - 200"


@pytest.mark.cloud
def test_cloud_sns_notification_action(
    sns,
    validation_result_suite,
    validation_result_suite_id,
    aws_credentials,
    mock_context,
):
    subj_topic = "test-subj"
    created_subj = sns.create_topic(Name=subj_topic)
    arn = created_subj.get("TopicArn")
    sns_action = SNSNotificationAction(
        sns_topic_arn=arn,
        sns_message_subject="Subject",
    )
    assert sns_action.run(
        validation_result_suite=validation_result_suite,
        validation_result_suite_identifier=validation_result_suite_id,
        data_asset=None,
    ).endswith("Subject")


class TestActionSerialization:
    EXAMPLE_SLACK_WEBHOOK = "https://hooks.slack.com/services/test/slack/webhook"
    EXAMPLE_TEAMS_WEBHOOK = "https://hooks.microsoft.com/services/test/teams/webhook"
    EXAMPLE_API_KEY = "testapikey"
    EXAMPLE_SMTP_ADDRESS = "smtp.test.com"
    EXAMPLE_SMTP_PORT = 587
    EXAMPLE_EMAILS = "bob@gmail.com, jim@hotmail.com"
    EXAMPLE_SITE_NAMES = ["one_site", "two_site", "red_site", "blue_site"]
    EXAMPLE_SNS_TOPIC_ARN = "my_test_arn"
    EXAMPLE_URL = "http://www.example.com"

    ACTION_INIT_PARAMS = {
        SlackNotificationAction: {"slack_webhook": EXAMPLE_SLACK_WEBHOOK},
        MicrosoftTeamsNotificationAction: {"teams_webhook": EXAMPLE_TEAMS_WEBHOOK},
        OpsgenieAlertAction: {"api_key": EXAMPLE_API_KEY},
        EmailAction: {
            "smtp_address": EXAMPLE_SMTP_ADDRESS,
            "smtp_port": EXAMPLE_SMTP_PORT,
            "receiver_emails": EXAMPLE_EMAILS,
        },
        UpdateDataDocsAction: {"site_names": EXAMPLE_SITE_NAMES},
        SNSNotificationAction: {"sns_topic_arn": EXAMPLE_SNS_TOPIC_ARN},
        APINotificationAction: {"url": EXAMPLE_URL},
    }

    SERIALIZED_ACTIONS = {
        SlackNotificationAction: {
            "notify_on": "all",
            "notify_with": None,
            "renderer": {
                "class_name": "SlackRenderer",
                "module_name": "great_expectations.render.renderer.slack_renderer",
            },
            "show_failed_expectations": False,
            "slack_channel": None,
            "slack_token": None,
            "slack_webhook": EXAMPLE_SLACK_WEBHOOK,
            "type": "slack",
        },
        MicrosoftTeamsNotificationAction: {
            "notify_on": "all",
            "renderer": {
                "class_name": "MicrosoftTeamsRenderer",
                "module_name": "great_expectations.render.renderer.microsoft_teams_renderer",
            },
            "teams_webhook": EXAMPLE_TEAMS_WEBHOOK,
            "type": "microsoft",
        },
        OpsgenieAlertAction: {
            "api_key": EXAMPLE_API_KEY,
            "notify_on": "failure",
            "priority": "P3",
            "region": None,
            "renderer": {
                "class_name": "OpsgenieRenderer",
                "module_name": "great_expectations.render.renderer.opsgenie_renderer",
            },
            "tags": None,
            "type": "opsgenie",
        },
        EmailAction: {
            "notify_on": "all",
            "notify_with": None,
            "receiver_emails": EXAMPLE_EMAILS,
            "renderer": {
                "class_name": "EmailRenderer",
                "module_name": "great_expectations.render.renderer.email_renderer",
            },
            "sender_alias": None,
            "sender_login": None,
            "sender_password": None,
            "smtp_address": EXAMPLE_SMTP_ADDRESS,
            "smtp_port": str(EXAMPLE_SMTP_PORT),
            "type": "email",
            "use_ssl": None,
            "use_tls": None,
        },
        UpdateDataDocsAction: {
            "site_names": EXAMPLE_SITE_NAMES,
            "type": "update_data_docs",
        },
        SNSNotificationAction: {
            "sns_message_subject": None,
            "sns_topic_arn": EXAMPLE_SNS_TOPIC_ARN,
            "type": "sns",
        },
        APINotificationAction: {"type": "api", "url": EXAMPLE_URL},
    }

    @pytest.mark.parametrize(
        "action_class, init_params",
        [(k, v) for k, v in ACTION_INIT_PARAMS.items()],
        ids=[k.__name__ for k in ACTION_INIT_PARAMS],
    )
    @pytest.mark.unit
    def test_action_serialization_and_deserialization(
        self,
        mock_context,
        action_class: Type[ValidationAction],
        init_params: dict,
    ):
        expected = self.SERIALIZED_ACTIONS[action_class]

        action = action_class(**init_params)
        json_dict = action.json()
        actual = json.loads(json_dict)

        assert actual == expected

    @pytest.mark.parametrize(
        "action_class, serialized_action",
        [(k, v) for k, v in SERIALIZED_ACTIONS.items()],
        ids=[k.__name__ for k in SERIALIZED_ACTIONS],
    )
    @pytest.mark.unit
    def test_action_deserialization(
        self, action_class: Type[ValidationAction], serialized_action: dict
    ):
        actual = action_class.parse_obj(serialized_action)
        assert isinstance(actual, action_class)

    @pytest.mark.parametrize(
        "action_class, init_params",
        [(k, v) for k, v in ACTION_INIT_PARAMS.items()],
        ids=[k.__name__ for k in ACTION_INIT_PARAMS],
    )
    @pytest.mark.unit
    def test_action_deserialization_within_parent_class(
        self, action_class: ValidationAction, init_params: dict
    ):
        """
        The matter of deserializing an Action into the relevant subclass is the responsibility of
        the Checkpoint in production code.

        In order to test Actions alone, we utilize a dummy class with a single field to ensure
        properly implementation of Pydantic discriminated unions.

        Ref: https://docs.pydantic.dev/1.10/usage/types/#discriminated-unions-aka-tagged-unions
        """

        # This somewhat feels like we're testing Pydantic code but it's the only way to ensure that
        # we've properly implemented the Pydantic discriminated union feature.
        class DummyClassWithActionChild(BaseModel):
            class Config:
                # Due to limitations of Pydantic V1, we need to specify the json_encoders at every level of the hierarchy
                json_encoders = {Renderer: lambda r: r.serialize()}

            action: Union[
                APINotificationAction,
                EmailAction,
                MicrosoftTeamsNotificationAction,
                OpsgenieAlertAction,
                PagerdutyAlertAction,
                SlackNotificationAction,
                SNSNotificationAction,
                StoreValidationResultAction,
                UpdateDataDocsAction,
            ] = Field(..., discriminator="type")

        action = action_class(**init_params)
        instance = DummyClassWithActionChild(action=action)

        json_dict = instance.json()
        parsed_action = DummyClassWithActionChild.parse_raw(json_dict)

        assert isinstance(parsed_action.action, action_class)
