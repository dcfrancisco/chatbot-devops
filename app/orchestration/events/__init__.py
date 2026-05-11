"""Event-driven runtime orchestration.

Example:

    event_bus = InMemoryEventBus([StructuredLogEventSubscriber(logging_service)])
    publisher = EventPublisher(event_bus)
    await publisher.publish_runtime(
        context=context,
        event_name=RuntimeEventName.REQUEST_STARTED,
        metadata={"agent_name": context.agent_name},
    )
"""

from app.orchestration.events.bus import EventBus, InMemoryEventBus
from app.orchestration.events.models import EventCorrelation, ExecutionEvent, RuntimeEventName, RuntimeExecutionEvent, TracingExecutionEvent
from app.orchestration.events.publishers import EventPublisher
from app.orchestration.events.subscribers import EventSubscriber, InMemoryEventSubscriber, StructuredLogEventSubscriber
from app.orchestration.events.tracing import EventFactory, TracingEventSubscriber

__all__ = [
    "EventBus",
    "EventCorrelation",
    "EventFactory",
    "EventPublisher",
    "EventSubscriber",
    "ExecutionEvent",
    "InMemoryEventBus",
    "InMemoryEventSubscriber",
    "RuntimeEventName",
    "RuntimeExecutionEvent",
    "StructuredLogEventSubscriber",
    "TracingEventSubscriber",
    "TracingExecutionEvent",
]