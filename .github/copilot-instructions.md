# Copilot Instructions

## Repository Context

This repository is a local-first AI DevOps assistant with:

- FastAPI backend services
- PostgreSQL with pgvector for RAG and memory retrieval
- Ollama-backed local LLM inference
- modular tool execution and lightweight orchestration
- Streamlit frontend
- Docker Compose for local environment orchestration

Treat this codebase as an enterprise-oriented local AI platform, not a demo chatbot and not a generalized multi-agent framework.

## Primary Goals

- keep the system local-first by default
- prefer retrieval-first application behavior
- preserve deterministic behavior where practical
- keep services maintainable and observable
- ship production-ready code, not prototypes or pseudocode
- favor small, explicit orchestration over autonomous agent loops

## Preferred Stack

- FastAPI
- SQLAlchemy
- pgvector
- Streamlit
- Docker Compose
- Ollama

## Coding Standards

- Target Python 3.12 compatibility.
- Write typed Python code throughout.
- Prefer async-first service design for I/O-bound code.
- Use modular service classes instead of large procedural files.
- Follow clean architecture boundaries between API routes, services, data access, and tools.
- Produce production-ready code with real implementations.
- Use structured logging for operationally relevant flows.
- Apply dependency injection where it improves testability and clarity.
- Keep interfaces explicit and predictable.
- Use Pydantic models for request/response contracts and validation.
- Avoid placeholder implementations, TODO-only scaffolds, and pseudocode.

## Architectural Principles

- retrieval-first design for assistant responses
- deterministic heuristics where possible before introducing model-driven routing
- observable systems with traceable execution paths
- maintainable services with clear ownership and bounded responsibilities
- minimal complexity and minimal moving parts
- extensible enough for future specialized agents, but do not design for swarms today

## Required Design Patterns

### FastAPI

- Keep route handlers thin.
- Put orchestration and business logic in service classes under `app/services/`.
- Keep request parsing, validation, and HTTP concerns in `app/api/`.
- Return explicit response models.

### Database and RAG

- Use SQLAlchemy models and async sessions consistently.
- Keep pgvector retrieval logic in dedicated retrieval or memory services.
- Preserve source traceability and citations in assistant responses.
- Treat memory and retrieval as related but distinct concerns.

### Tools

- Keep tools modular under `app/tools/`.
- Prefer one tool per integration or responsibility.
- Validate tool inputs explicitly.
- Preserve safe execution boundaries, timeout handling, and execution tracing.
- Do not hide important tool behavior behind magic abstractions.

### Orchestration

- Prefer lightweight orchestration.
- Follow the current flow shape:
  - user message
  - retrieval
  - optional tool decision
  - optional single tool execution
  - response synthesis
- Avoid recursive orchestration, self-reflective loops, and uncontrolled tool chaining.
- If adding future agent capabilities, keep them optional and isolated from the default flow.

### Frontend

- Keep the Streamlit UI low-code, fast to iterate on, and professional in appearance.
- Prefer clean panels and straightforward state management over custom frontend frameworks.
- Use the FastAPI API as the source of truth.

## What To Avoid

- monolithic files that combine routes, business logic, persistence, and UI concerns
- tightly coupled logic across services
- unnecessary frameworks or orchestration layers
- excessive abstraction without a clear operational benefit
- Rasa-style intent systems, stories, or rule engines
- overengineered agent swarms or autonomous multi-agent loops
- placeholder code that requires the user to finish the implementation manually

## Implementation Guidance

- When changing behavior, prefer fixing the responsible service rather than adding wrapper logic elsewhere.
- When adding new functionality, extend the existing service and tool architecture instead of creating parallel patterns.
- When adding integrations, make them explicit, typed, observable, and safe by default.
- When adding new endpoints, expose only the minimum backend surface needed by the frontend or operator workflow.
- When adding config, use environment-driven settings through the central settings model.
- Keep Docker Compose and local developer ergonomics in mind for all runtime changes.

## Quality Bar

Changes should generally:

- compile cleanly
- preserve typed interfaces
- fit the existing modular structure
- include real wiring, not fragments
- be ready to run locally with Docker Compose or the documented local Python workflow

## Repository Mental Model

This repository is best understood as:

- a local AI assistant platform
- with FastAPI as the backend control plane
- pgvector-backed retrieval and memory
- optional safe tool execution
- Ollama-backed inference
- Streamlit as the operator UI

It is not:

- a legacy intent-classification bot
- a monolithic chatbot app
- a swarm-agent experiment
- a framework playground
