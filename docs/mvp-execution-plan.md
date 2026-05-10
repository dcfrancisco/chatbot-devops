# Legacy Rasa to Local AI Assistant MVP Execution Plan

## Objective

Migrate a legacy Rasa chatbot into a local-first AI assistant platform using:

- FastAPI
- PostgreSQL + pgvector
- Ollama
- Streamlit
- Docker Compose

The target outcome is an enterprise-demo-ready MVP for a single developer with Python and Docker experience.

## MVP Definition

The MVP is complete when the system can reliably do all of the following on a local machine:

- answer knowledge-base questions with semantic retrieval
- ingest curated documents into PostgreSQL + pgvector
- use Ollama for local chat and embedding inference
- execute Jenkins operations through explicit tools
- persist conversations and memory across turns
- show citations and execution traces in a Streamlit UI
- run end-to-end through Docker Compose with repeatable startup

The MVP is not intended to include:

- autonomous agent swarms
- recursive planning loops
- generalized workflow orchestration
- multi-tenant security boundaries
- advanced RBAC or full production operations
- cloud deployment automation

## Planning Assumptions

- single developer
- existing Python experience
- existing chatbot codebase exists and is already partially understood
- existing Docker familiarity
- local-first scope is acceptable for the first milestone
- Jenkins integration is the primary reusable legacy integration

## Delivery Strategy

Use a phased migration with a working vertical slice as early as possible.

Guiding principle:

1. reduce architecture complexity first
2. extract the only reusable business integration
3. stand up the local AI stack
4. make retrieval useful before expanding orchestration
5. treat UI polish and demo-readiness as explicit phases, not leftovers

## Realistic Timeline

For one developer, a realistic MVP window is about **5 to 7 weeks** of focused implementation.

Recommended planning assumption:

- best case: 4 weeks if the document set is clean, Jenkins integration is simple, and no major environment issues appear
- realistic case: 6 weeks
- conservative case: 7 to 8 weeks if ingestion, local inference, or demo polish takes longer than expected

## Implementation Priorities

Priority order:

1. local runtime and architecture baseline
2. retrieval and ingestion
3. Jenkins tool extraction
4. conversation memory and orchestration
5. Streamlit demo UI
6. stability, observability, and demo hardening

This order matters because everything user-facing depends on reliable local runtime, retrievable data, and at least one working enterprise integration.

## Phase Roadmap

## Phase 0: Scope Lock and Legacy Audit

### Goal

Freeze scope and identify the minimum business value worth carrying forward.

### Duration

`2 to 3 days`

### Deliverables

- confirmed MVP definition
- inventory of reusable legacy logic
- list of Rasa-specific assets to delete, ignore, or mine for examples
- curated seed document list for RAG
- agreed demo script outline

### Tasks

- review legacy Rasa runtime and custom actions
- isolate Jenkins logic from framework glue
- review `assets/` and remove noisy documents from ingestion scope
- identify any still-exposed secrets and rotate them
- define the demo narrative: what the assistant must show live

### Dependencies

- none

### Exit Criteria

- no unresolved debate about whether the MVP is "chatbot parity" versus a smaller local assistant
- no open question about whether Rasa intent/stories must be preserved

## Phase 1: Platform Skeleton and Local Runtime

### Goal

Stand up the new application skeleton and local stack without relying on Rasa.

### Duration

`4 to 5 days`

### Deliverables

- FastAPI application structure
- PostgreSQL + pgvector wired through SQLAlchemy
- Ollama connected for chat + embeddings
- Docker Compose environment for backend, DB, Ollama, and Streamlit
- typed settings and structured logging

### Tasks

- create service boundaries under `app/api`, `app/services`, `app/rag`, `app/tools`, `app/db`
- configure async SQLAlchemy session handling
- define baseline schemas for documents, chunks, conversations, messages, citations, and memory
- wire health checks and startup flow
- validate local LLM and embedding model calls via Ollama

### Dependencies

- Phase 0 scope lock

### Exit Criteria

- `docker compose up --build` works consistently
- backend health check verifies database and Ollama
- local environment can call the chat and embedding models

## Phase 2: Retrieval and Document Ingestion MVP

### Goal

Deliver the first useful semantic KB assistant behavior.

### Duration

`6 to 8 days`

### Deliverables

- file/document ingestion pipeline
- chunking strategy for markdown, text, yaml, and pdf
- vector storage in pgvector
- retrieval service with citations
- ingestion CLI and API path

### Tasks

- finalize document parser and splitter flow
- support incremental ingestion by checksum
- store source metadata and ingestion run metadata
- implement top-k retrieval with citations and traceable source blocks
- validate curated `assets/` corpus quality

### Dependencies

- working FastAPI + DB + Ollama baseline

### Exit Criteria

- ingesting the seed knowledge base succeeds locally
- user questions against ingested docs return grounded answers with citations
- retrieval quality is good enough to support a demo without constant prompt intervention

### Why This Phase Matters

Without retrieval working, the assistant is not yet an enterprise demo. It is only an LLM shell.

## Phase 3: Jenkins Tool Extraction and Tool Framework

### Goal

Carry forward the only meaningful legacy business integration in a maintainable form.

### Duration

`4 to 6 days`

### Deliverables

- typed Jenkins service/client
- modular tool registry
- tool execution service with validation, retry, timeout, and tracing
- safe Jenkins tool operations for listing jobs and basic job actions

### Tasks

- extract Jenkins HTTP behavior from the legacy chatbot logic
- validate the real Jenkins API contract used in local dev
- implement tool descriptors and standardized responses
- preserve structured logging and trace IDs
- ensure tool failures degrade cleanly into explainable assistant behavior

### Dependencies

- platform baseline
- ideally retrieval already in place so tool usage can be combined with KB grounding

### Exit Criteria

- Jenkins tools run from FastAPI without Rasa
- tool execution is observable, bounded, and safe by default
- at least one demo-worthy Jenkins scenario works end-to-end

## Phase 4: Lightweight Orchestration and Memory

### Goal

Introduce practical orchestration without overengineering.

### Duration

`4 to 5 days`

### Deliverables

- retrieval-first orchestration service
- optional single-tool invocation path
- conversation persistence
- episodic memory storage and reuse
- orchestration metadata exposed in responses

### Tasks

- implement deterministic tool decision heuristics
- include retrieval, recent history, and memory in synthesis prompts
- persist message citations and tool traces
- store useful user-turn memories with embeddings
- keep orchestration single-turn and non-recursive

### Dependencies

- retrieval working
- tool execution working

### Exit Criteria

- assistant can answer KB questions, optionally use Jenkins, and maintain conversation continuity
- memory improves repeated interactions without introducing unpredictable behavior

## Phase 5: Streamlit UI and Demo Readiness

### Goal

Turn the backend into a credible enterprise demo.

### Duration

`4 to 6 days`

### Deliverables

- modern Streamlit UI
- streamed chat responses
- conversation history sidebar
- source citation panel
- memory visualization
- KB source/document panels
- tool execution indicators

### Tasks

- wire Streamlit to FastAPI APIs
- expose backend read-only endpoints for dashboard panels
- ensure session persistence across Streamlit refreshes
- improve visual polish and responsive layout
- ensure the demo script can be performed without manual backend patching

### Dependencies

- orchestration path complete
- backend APIs stable enough for UI integration

### Exit Criteria

- one operator can run the full stack locally and walk through the demo from the UI only

## Phase 6: Hardening, Testing, and Demo Packaging

### Goal

Reduce failure risk right before demo use.

### Duration

`3 to 5 days`

### Deliverables

- smoke tests for ingestion, retrieval, tools, and chat
- improved logs and troubleshooting notes
- updated README and demo runbook
- seeded local environment for repeatable demo startup

### Tasks

- test happy-path ingestion and chat flows
- test Jenkins tool failure handling
- verify Compose startup ordering and health checks
- confirm model pull timing and local machine prerequisites
- write a concise demo checklist and reset workflow

### Dependencies

- all functional MVP pieces present

### Exit Criteria

- demo can be rehearsed start-to-finish on a clean local environment
- likely failure modes have documented recovery steps

## Dependency Ordering

Critical path:

1. scope lock
2. runtime baseline
3. ingestion + retrieval
4. Jenkins tool extraction
5. orchestration + memory
6. Streamlit UI
7. hardening and demo packaging

Important dependency notes:

- UI should not be started before the backend contract stabilizes
- memory is useful only after conversation persistence exists
- tool orchestration should not be made dynamic before the core tool execution service is reliable
- document ingestion quality directly affects assistant credibility, so treat corpus curation as part of delivery, not an afterthought

## Milestone Checklist

## Milestone 1: Local Stack Running

- [ ] FastAPI starts locally and in Docker Compose
- [ ] PostgreSQL + pgvector is initialized
- [ ] Ollama serves chat and embedding models
- [ ] health checks pass consistently

## Milestone 2: Knowledge Base Chatbot

- [ ] documents ingest successfully
- [ ] retrieval returns relevant chunks
- [ ] assistant answers with citations
- [ ] KB chat is good enough to demo without Jenkins

## Milestone 3: Enterprise Integration Demo

- [ ] Jenkins tool is extracted from legacy logic
- [ ] tool execution is validated and traced
- [ ] assistant can ground answers and invoke Jenkins when needed

## Milestone 4: Memory-Aware Assistant

- [ ] conversations persist
- [ ] memory entries are stored and reused
- [ ] multi-turn continuity works reliably

## Milestone 5: Demo-Ready UI

- [ ] Streamlit UI shows chat, citations, memory, and KB panels
- [ ] streamed responses work
- [ ] conversation history is visible
- [ ] tool indicators are visible

## Milestone 6: Demo Freeze

- [ ] startup instructions are documented
- [ ] smoke tests pass
- [ ] demo script is rehearsed
- [ ] known failure recovery steps are documented

## Demo Milestones

Recommended demo sequence:

### Demo A: Semantic Knowledge Assistant

- ingest a curated document set
- ask a KB question
- show grounded answer with citations

### Demo B: Enterprise Tooling

- ask about Jenkins job state
- show live tool execution indicator
- return tool-backed answer

### Demo C: Memory-Aware Conversation

- ask a follow-up question referencing prior context
- show that conversation memory improves continuity

### Demo D: Operator-Friendly UI

- show source panel, uploaded documents list, chat sidebar, and memory panel
- demonstrate that the system is understandable, not a black box

## Risk Analysis

## High-Risk Areas

### 1. Retrieval quality risk

Risk:
Weak chunking or low-quality source documents make the assistant appear unreliable.

Mitigation:

- curate the initial corpus aggressively
- validate chunking against real questions early
- prefer fewer high-quality documents over indexing everything

### 2. Local inference performance risk

Risk:
Ollama latency or hardware constraints degrade the demo experience.

Mitigation:

- lock a known-good chat model and embedding model early
- test on the actual demo hardware
- keep context size and retrieval window conservative

### 3. Jenkins API drift risk

Risk:
Legacy assumptions about Jenkins endpoints are incomplete or wrong.

Mitigation:

- validate every endpoint against the current local Jenkins instance
- keep the first tool scope small and proven
- do not promise unsupported job flows in the MVP

### 4. Environment and startup risk

Risk:
Compose startup issues or model-pull timing derail the first-run experience.

Mitigation:

- keep health checks explicit
- document warm-up time for Ollama
- test clean startup from scratch more than once

## Medium-Risk Areas

- stale secrets or config carried forward from the legacy repo
- overexpansion of MVP scope into generic agent features
- UI work starting too early before backend contracts settle
- memory adding unpredictability if heuristics are too loose

## Technical Debt Considerations

Acceptable MVP debt:

- heuristic-based tool decision logic instead of a more advanced policy engine
- Streamlit UI instead of a custom frontend
- limited Jenkins tool surface
- modest test coverage focused on smoke paths rather than exhaustive cases

Debt to avoid even for MVP:

- reintroducing framework-style intent systems
- duplicating orchestration logic across API, UI, and tools
- monolithic service files that mix retrieval, tool execution, and persistence
- unsafe direct tool invocation without validation or tracing
- undocumented local environment assumptions

Recommended debt register to track explicitly:

- stronger retrieval evaluation
- richer memory scoring or summarization
- broader tool catalog
- caching strategy if Redis becomes necessary
- auth and operator controls for post-MVP use

## What Can Be Deferred Safely

Good post-MVP candidates:

- advanced tool planning
- richer Jenkins workflows beyond read/list and one verified mutation path
- Redis-backed caching and session optimization
- multi-user support
- cloud deployment
- prompt optimization and eval automation
- agent specialization beyond the single orchestrator path

## Future Evolution Path

### Near-Term After MVP

- add more enterprise tools beyond Jenkins
- add ingestion scheduling or watch-based refresh
- improve retrieval evaluation and benchmark prompts
- add conversation summarization and better memory compaction

### Mid-Term

- introduce role-based admin operations
- add optional cache layer for performance
- add basic observability dashboards and evaluation traces
- support multi-project or multi-knowledge-base segmentation

### Longer-Term

- add specialized assistants or bounded sub-agents only if there is proven need
- move from deterministic heuristics to a slightly more capable planner only if tool selection becomes a real bottleneck
- add deployment and hosting options once the local-first workflow is stable

## Suggested Solo-Developer Execution Rhythm

For a single developer, the safest rhythm is:

- week 1: scope lock + runtime baseline
- week 2: ingestion + retrieval
- week 3: Jenkins tools + initial orchestration
- week 4: memory + stabilized backend contract
- week 5: Streamlit UI + demo path
- week 6: hardening, cleanup, and rehearsal

If time compresses, protect these first:

1. retrieval quality
2. one working Jenkins tool path
3. local Compose startup
4. citations in the UI

If time expands, invest next in:

1. better ingestion quality
2. better retrieval evaluation
3. improved memory quality
4. additional demo scenarios

## Recommended MVP Success Criteria

The MVP should be considered successful if all of the following are true:

- a new developer can start the stack locally with the documented workflow
- the assistant answers KB questions with citations from curated documents
- Jenkins tool execution works without Rasa dependencies
- the UI demonstrates memory, citations, and tool usage clearly
- the system feels like a coherent local AI platform rather than a patched chatbot migration