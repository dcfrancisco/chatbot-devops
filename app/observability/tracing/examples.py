from __future__ import annotations

from app.observability.tracing.correlation import CorrelationContext
from app.observability.tracing.spans.models import SpanKind


TRACE_EXAMPLE_ATTRIBUTES: dict[str, object] = {
    "propagation": CorrelationContext(
        trace_id="trace-123",
        correlation_id="req-123",
        span_id="span-123",
    ).as_headers(),
    "runtime": {
        "root_name": "orchestration.run",
        "attributes": {
            "agent_name": "conversation",
            "correlation_id": "req-123",
        },
    },
    "span_examples": [
        {"name": "orchestration.run", "kind": SpanKind.TRACE_ROOT, "component": "observability"},
        {"name": "pipeline.RequestReceived", "kind": SpanKind.PIPELINE_STAGE, "component": "orchestration"},
        {"name": "agent.run", "kind": SpanKind.AGENT_EXECUTION, "component": "agents"},
        {"name": "retrieval.query_vector_store", "kind": SpanKind.KB_RETRIEVAL, "component": "rag"},
        {"name": "memory.rank_relevance", "kind": SpanKind.MEMORY_RETRIEVAL, "component": "memory"},
        {"name": "prompt.assemble", "kind": SpanKind.PROMPT_ASSEMBLY, "component": "orchestration"},
        {"name": "llm.generate", "kind": SpanKind.LLM_EXECUTION, "component": "llm"},
        {"name": "tool.execution.attempts", "kind": SpanKind.TOOL_EXECUTION, "component": "tools"},
    ],
    "replay": {
        "replayable": True,
        "expected_hierarchy": [
            "orchestration.run",
            "retrieval.query_vector_store",
            "prompt.assemble",
        ],
    },
}