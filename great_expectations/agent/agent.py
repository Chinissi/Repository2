import os
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from functools import partial
from typing import TYPE_CHECKING, Dict, Optional

import pydantic
from pydantic import AmqpDsn
from pydantic.dataclasses import dataclass

from great_expectations import get_context
from great_expectations.agent.event_handler import (
    EventHandler,
    EventHandlerResult,
    UnknownEventError,
)
from great_expectations.agent.message_service.rabbit_mq_client import (
    ClientError,
    RabbitMQClient,
)
from great_expectations.agent.message_service.subscriber import (
    EventContext,
    OnMessageCallback,
    Subscriber,
    SubscriberError,
)

HandlerMap = Dict[str, OnMessageCallback]


if TYPE_CHECKING:
    from great_expectations.data_context import CloudDataContext


@dataclass(frozen=True)
class GXAgentConfig:
    """GXAgent configuration.
    Attributes:
        organization_id: GX Cloud organization identifier
        broker_url: address of broker service
    """

    organization_id: str
    broker_url: AmqpDsn


class GXAgent:
    """
    Run GX in any environment from GX Cloud.

    To start the agent, install Python and great_expectations and run `gx-agent`.
    The agent loads a DataContext configuration from GX Cloud, and listens for
    user events triggered from the UI.
    """

    def __init__(self):
        print("Initializing GX-Agent")
        self._config = self._get_config_from_env()
        print("Loading a DataContext - this might take a moment.")
        self._context: CloudDataContext = get_context(cloud_mode=True)
        print("DataContext is ready.")

        # Create a thread pool with a single worker, so we can run long-lived
        # GX processes and maintain our connection to the broker. Note that
        # the CloudDataContext cached here is used by the worker, therefore
        # it isn't safe to increase the number of workers.
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._current_task: Optional[Future] = None

    def run(self) -> None:
        """Open a connection to GX Cloud."""

        print("Opening connection to GX Cloud")
        self._listen()
        print("Connection to GX Cloud has been closed.")

    def _listen(self) -> None:
        """Manage connection lifecycle."""
        subscriber = None
        try:
            client = RabbitMQClient(url=self._config.broker_url)
            subscriber = Subscriber(client=client)
            print("GX-Agent is ready.")
            # Open a blocking connection until encountering a shutdown event
            subscriber.consume(
                queue=self._config.organization_id,
                on_message=self._handle_event_as_thread_enter,
                wait=1,
            )
        except KeyboardInterrupt:
            print("Received request to shutdown.")
        except (SubscriberError, ClientError) as e:
            print("Connection to GX Cloud has encountered an error.")
            print("Please restart the agent and try your action again.")
            print(e)
        finally:
            self._close_subscriber(subscriber)

    def _handle_event_as_thread_enter(self, event_context: EventContext) -> None:
        """Schedule _handle_event to run in a thread.

        Callback passed to Subscriber.consume which forwards events to
        the EventHandler for processing.

        Args:
            event_context: An Event with related properties and actions.
        """
        if self._can_accept_new_task() is not True:
            # signal to Subscriber that we can't process this message right now
            return event_context.event_processed(retry=True)
        self._current_task = self._executor.submit(
            self._handle_event, event_context=event_context
        )
        # TODO lakitu-139: record job as started

        # When the thread exits the results are processed in _handle_event_as_thread_exit.
        # Curry the event_context, so it's available after the GX process exits.
        on_exit_callback = partial(
            self._handle_event_as_thread_exit, event_context=event_context
        )
        self._current_task.add_done_callback(on_exit_callback)

    def _handle_event(self, event_context: EventContext) -> EventHandlerResult:
        """Pass events to EventHandler.

        Callback passed to Subscriber.consume which forwards events to
        the EventHandler for processing.

        Args:
            event_context: An Event with related properties and actions.
        """
        # warning:  this method will be executed in a different thread than
        #           where it was defined, so take care with shared resources.
        #           It's safe to use self._context because we restrict ourselves
        #           to a single worker thread at any given time. The ack/nack
        #           callback provided by the Subscriber in event_context will fail,
        #           since it depends on the channel available in the main thread.

        handler = EventHandler(context=self._context)
        result = handler.handle_event(event_context=event_context)
        return result

    def _handle_event_as_thread_exit(
        self, future: Future, event_context: EventContext
    ) -> None:
        """Callback invoked when the thread running GX exits."""
        # this method will be invoked in the main thread after the worker exits

        # get results or errors from the thread
        error = future.exception()
        if error is not None:
            print("Encountered an error while running job.")
            print(error)
        else:
            print("Job finished successfully.")
            result = future.result()
            print(result)

        # TODO lakitu-139: record job as complete and send results

        # ack message and cleanup resources
        if isinstance(error, UnknownEventError):
            # We might not have the latest Event definitions, so we requeue
            # this event in the hope that another agent will understand it.
            retry = True
        else:
            retry = False
        event_context.event_processed(retry=retry)
        self._current_task = None

    def _can_accept_new_task(self) -> bool:
        return self._current_task is None or self._current_task.done()

    def _close_subscriber(self, subscriber: Optional[Subscriber]) -> None:
        """Ensure the subscriber has been closed."""
        if subscriber is None:
            return  # nothing to close
        try:
            subscriber.close()
        except SubscriberError as e:
            print("Subscriber encountered an error while closing:")
            print(e)

    @classmethod
    def _get_config_from_env(cls) -> GXAgentConfig:
        """Construct GXAgentConfig from available environment variables"""
        url = os.environ.get("BROKER_URL", None)
        org_id = os.environ.get("GE_CLOUD_ORGANIZATION_ID", None)
        try:
            # pydantic will coerce the url to the correct type
            return GXAgentConfig(
                organization_id=org_id, broker_url=url  # type: ignore[arg-type]
            )
        except pydantic.ValidationError as validation_err:
            raise GXAgentError(
                f"Missing or badly formed environment variable\n{validation_err.errors()}"
            ) from validation_err


class GXAgentError(Exception):
    ...
