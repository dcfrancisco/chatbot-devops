from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import httpx
import streamlit as st


DEFAULT_API_BASE_URL = os.getenv("STREAMLIT_API_BASE_URL", "http://localhost:8000")


@dataclass(slots=True)
class ApiClient:
    base_url: str
    timeout: float = 60.0

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def get_json(self, path: str) -> Any:
        response = httpx.get(self._url(path), timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def post_json(self, path: str, payload: dict[str, Any]) -> Any:
        response = httpx.post(self._url(path), json=payload, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def stream_chat(self, payload: dict[str, Any]):
        with httpx.stream("POST", self._url("/chat"), json=payload, timeout=None) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                if line.startswith("data: "):
                    yield json.loads(line[6:])


def init_state() -> None:
    st.session_state.setdefault("api_base_url", DEFAULT_API_BASE_URL)
    st.session_state.setdefault("conversation_id", None)
    st.session_state.setdefault("chat_messages", [])
    st.session_state.setdefault("pending_user_message", None)
    st.session_state.setdefault("selected_conversation_label", "New conversation")


def apply_theme() -> None:
    st.set_page_config(page_title="AI DevOps Assistant", page_icon="AI", layout="wide", initial_sidebar_state="expanded")
    st.markdown(
        """
        <style>
        :root {
          --bg: #0b1020;
          --panel: #131a2b;
          --panel-soft: #182238;
          --border: rgba(255,255,255,0.08);
          --text: #e8edf7;
          --muted: #93a4c3;
          --accent: #4cc9f0;
          --accent-2: #7ef0c7;
        }
        .stApp {
          background:
            radial-gradient(circle at top right, rgba(76,201,240,0.14), transparent 26%),
            radial-gradient(circle at left top, rgba(126,240,199,0.08), transparent 22%),
            linear-gradient(180deg, #09101b 0%, #0b1020 100%);
          color: var(--text);
        }
        .block-container {
          padding-top: 1.4rem;
          padding-bottom: 1.2rem;
          max-width: 1500px;
        }
        div[data-testid="stSidebar"] {
          background: linear-gradient(180deg, rgba(10,16,30,0.98), rgba(13,19,34,0.98));
          border-right: 1px solid var(--border);
        }
        .panel {
          background: linear-gradient(180deg, rgba(19,26,43,0.92), rgba(13,18,31,0.96));
          border: 1px solid var(--border);
          border-radius: 20px;
          padding: 1rem 1rem 0.95rem 1rem;
          box-shadow: 0 20px 60px rgba(0,0,0,0.25);
        }
        .hero {
          background: linear-gradient(135deg, rgba(24,34,56,0.95), rgba(12,18,31,0.98));
          border: 1px solid var(--border);
          border-radius: 24px;
          padding: 1.25rem 1.3rem;
          margin-bottom: 1rem;
        }
        .hero-title {
          font-size: 1.35rem;
          font-weight: 700;
          color: var(--text);
          letter-spacing: -0.02em;
        }
        .hero-subtitle {
          color: var(--muted);
          font-size: 0.95rem;
          margin-top: 0.35rem;
        }
        .pill {
          display: inline-block;
          padding: 0.28rem 0.55rem;
          border-radius: 999px;
          font-size: 0.74rem;
          background: rgba(76,201,240,0.12);
          color: #9ae9ff;
          border: 1px solid rgba(76,201,240,0.18);
          margin-right: 0.45rem;
          margin-top: 0.5rem;
        }
        .metric-card {
          background: rgba(255,255,255,0.02);
          border: 1px solid var(--border);
          border-radius: 16px;
          padding: 0.8rem;
        }
        .section-title {
          font-size: 0.86rem;
          font-weight: 700;
          color: #d5def0;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          margin-bottom: 0.8rem;
        }
        .source-card, .memory-card, .doc-card {
          background: rgba(255,255,255,0.02);
          border: 1px solid var(--border);
          border-radius: 14px;
          padding: 0.75rem 0.85rem;
          margin-bottom: 0.55rem;
        }
        .tiny {
          color: var(--muted);
          font-size: 0.78rem;
        }
        .citation-card {
          background: rgba(255,255,255,0.03);
          border-left: 3px solid rgba(76,201,240,0.6);
          border-radius: 10px;
          padding: 0.7rem 0.8rem;
          margin-bottom: 0.55rem;
        }
        .tool-indicator {
          border-radius: 999px;
          padding: 0.22rem 0.5rem;
          font-size: 0.73rem;
          display: inline-block;
          background: rgba(126,240,199,0.12);
          color: #9ff6da;
          border: 1px solid rgba(126,240,199,0.16);
        }
        .stChatMessage {
          background: transparent;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def conversation_label(item: dict[str, Any]) -> str:
    title = item.get("title") or "Conversation"
    count = item.get("message_count", 0)
    return f"{title} ({count})"


def fetch_dashboard_data(client: ApiClient) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    conversations = client.get_json("/conversations")
    sources = client.get_json("/kb/sources")
    documents = client.get_json("/kb/documents")
    tools = client.get_json("/tools")
    return conversations, sources, documents, tools


def load_conversation(client: ApiClient, conversation_id: str | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not conversation_id:
        return [], []
    messages = client.get_json(f"/conversations/{conversation_id}/messages")
    memory = client.get_json(f"/conversations/{conversation_id}/memory")
    return messages, memory


def sync_chat_state(messages: list[dict[str, Any]]) -> None:
    st.session_state.chat_messages = [
        {
            "role": item["role"],
            "content": item["content"],
            "citations": item.get("citations", []),
            "metadata": item.get("metadata", {}),
        }
        for item in messages
    ]


def render_sidebar(conversations: list[dict[str, Any]]) -> None:
    st.sidebar.markdown("### Conversations")
    if st.sidebar.button("New Conversation", use_container_width=True):
        st.session_state.conversation_id = None
        st.session_state.chat_messages = []
        st.session_state.selected_conversation_label = "New conversation"
        st.rerun()

    options = ["New conversation", *[conversation_label(item) for item in conversations]]
    selected = st.sidebar.radio(
        "Chat Sidebar",
        options=options,
        index=options.index(st.session_state.selected_conversation_label) if st.session_state.selected_conversation_label in options else 0,
        label_visibility="collapsed",
    )
    if selected != st.session_state.selected_conversation_label:
        st.session_state.selected_conversation_label = selected
        if selected == "New conversation":
            st.session_state.conversation_id = None
            st.session_state.chat_messages = []
        else:
            selected_item = next(item for item in conversations if conversation_label(item) == selected)
            st.session_state.conversation_id = selected_item["id"]
        st.rerun()

    st.sidebar.markdown("### Backend")
    st.session_state.api_base_url = st.sidebar.text_input("FastAPI URL", value=st.session_state.api_base_url)
    st.sidebar.caption("Default: http://localhost:8000")


def render_topbar(conversations: list[dict[str, Any]], sources: list[dict[str, Any]], documents: list[dict[str, Any]], tools: list[dict[str, Any]]) -> None:
    st.markdown(
        """
        <div class="hero">
          <div class="hero-title">Local AI DevOps Assistant</div>
          <div class="hero-subtitle">FastAPI-backed chat, retrieval-first orchestration, live tool indicators, and persistent conversation state.</div>
          <div>
            <span class="pill">Dark modern MVP</span>
            <span class="pill">Streaming chat</span>
            <span class="pill">Memory-aware</span>
            <span class="pill">KB + tools</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="tiny">Conversations</div><div style="font-size:1.4rem;font-weight:700">{len(conversations)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="tiny">KB Sources</div><div style="font-size:1.4rem;font-weight:700">{len(sources)}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="tiny">Documents</div><div style="font-size:1.4rem;font-weight:700">{len(documents)}</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="tiny">Registered Tools</div><div style="font-size:1.4rem;font-weight:700">{len(tools)}</div></div>', unsafe_allow_html=True)


def render_chat(messages: list[dict[str, Any]]) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Assistant Chat</div>', unsafe_allow_html=True)
    for message in messages:
        with st.chat_message("assistant" if message["role"] == "assistant" else "user"):
            st.markdown(message["content"])
            render_tool_indicator(message.get("metadata", {}))
            if message["role"] == "assistant":
                render_citations(message.get("citations", []))
    st.markdown('</div>', unsafe_allow_html=True)


def render_citations(citations: list[dict[str, Any]]) -> None:
    if not citations:
        return
    with st.expander("Source citations", expanded=False):
        for citation in citations:
            st.markdown(
                f"<div class='citation-card'><strong>{citation.get('document_title', 'Source')}</strong><br><span class='tiny'>{citation.get('source_id', '')} • chunk {citation.get('chunk_index', '')}</span><br><div style='margin-top:0.35rem'>{citation.get('snippet', '')}</div></div>",
                unsafe_allow_html=True,
            )


def render_tool_indicator(metadata: dict[str, Any]) -> None:
    tool_used = metadata.get("tool_used")
    if not tool_used:
        return
    st.markdown(
        f"<div class='tool-indicator'>Tool: {tool_used.get('name', 'unknown')} • {tool_used.get('status', 'unknown')} • {tool_used.get('trace_id', '')[:8]}</div>",
        unsafe_allow_html=True,
    )


def render_kb_panel(sources: list[dict[str, Any]], documents: list[dict[str, Any]]) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">KB Source Panel</div>', unsafe_allow_html=True)
    for source in sources[:8]:
        st.markdown(
            f"<div class='source-card'><strong>{source['source_key']}</strong><br><span class='tiny'>{source['source_type']} • {source['document_count']} docs • {source['chunk_count']} chunks</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown('<div class="section-title" style="margin-top:1rem">Uploaded Documents</div>', unsafe_allow_html=True)
    for document in documents[:10]:
        st.markdown(
            f"<div class='doc-card'><strong>{document['title']}</strong><br><span class='tiny'>{document['source_key']} • {document['mime_type']} • {document['chunk_count']} chunks</span></div>",
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)


def render_memory_panel(memory: list[dict[str, Any]], tools: list[dict[str, Any]]) -> None:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Memory Visualization</div>', unsafe_allow_html=True)
    if not memory:
        st.caption("No conversation memory stored yet for this thread.")
    for item in memory[:8]:
        importance_pct = int(float(item.get("importance", 0.0)) * 100)
        st.markdown(
            f"<div class='memory-card'><strong>{item['memory_type']}</strong><br><span class='tiny'>Importance {importance_pct}% • {item['key']}</span><br><div style='margin-top:0.35rem'>{item['content']}</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown('<div class="section-title" style="margin-top:1rem">Tool Registry</div>', unsafe_allow_html=True)
    for tool in tools:
        tags = ", ".join(tool.get("tags", [])) or "tool"
        st.markdown(
            f"<div class='memory-card'><strong>{tool['name']}</strong><br><span class='tiny'>{tags} • timeout {tool['timeout_seconds']}s</span><br><div style='margin-top:0.35rem'>{tool['description']}</div></div>",
            unsafe_allow_html=True,
        )
    st.markdown('</div>', unsafe_allow_html=True)


def submit_user_message(client: ApiClient, prompt: str) -> None:
    st.session_state.chat_messages.append({"role": "user", "content": prompt, "citations": [], "metadata": {}})
    with st.chat_message("user"):
        st.markdown(prompt)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        status = st.empty()
        response_chunks: list[str] = []
        done_payload: dict[str, Any] | None = None
        payload = {
            "message": prompt,
            "conversation_id": st.session_state.conversation_id,
            "stream": True,
        }
        try:
            for event in client.stream_chat(payload):
                if event.get("type") == "token":
                    response_chunks.append(event.get("delta", ""))
                    placeholder.markdown("".join(response_chunks))
                elif event.get("type") == "done":
                    done_payload = event
        except httpx.HTTPError as exc:
            placeholder.error(f"Backend error: {exc}")
            return

        response_text = "".join(response_chunks).strip()
        status.markdown("")
        citations = done_payload.get("citations", []) if done_payload else []
        orchestration = done_payload.get("orchestration", {}) if done_payload else {}
        tool_used = orchestration.get("tool_invocation") if orchestration else None
        st.session_state.conversation_id = done_payload.get("conversation_id") if done_payload else st.session_state.conversation_id
        metadata = {"tool_used": tool_used, "orchestration": orchestration}
        st.session_state.chat_messages.append(
            {"role": "assistant", "content": response_text, "citations": citations, "metadata": metadata}
        )
        render_tool_indicator(metadata)
        render_citations(citations)


def main() -> None:
    init_state()
    apply_theme()

    client = ApiClient(st.session_state.api_base_url)
    try:
        conversations, sources, documents, tools = fetch_dashboard_data(client)
        messages, memory = load_conversation(client, st.session_state.conversation_id)
        if messages and not st.session_state.pending_user_message:
            sync_chat_state(messages)
    except httpx.HTTPError as exc:
        st.error(f"Could not reach FastAPI backend at {st.session_state.api_base_url}: {exc}")
        st.stop()

    render_sidebar(conversations)
    render_topbar(conversations, sources, documents, tools)

    main_col, kb_col, side_col = st.columns([1.7, 1.0, 0.95], gap="large")
    with main_col:
        render_chat(st.session_state.chat_messages)
        prompt = st.chat_input("Ask about docs, Jenkins, or your local DevOps setup")
        if prompt:
            submit_user_message(client, prompt)
            st.rerun()
    with kb_col:
        render_kb_panel(sources, documents)
    with side_col:
        render_memory_panel(memory, tools)


if __name__ == "__main__":
    main()