"""Pydantic AI tool integration for Valmar.

Provides a ready-made tool function that AI agents can call to retrieve
organizational context via the Valmar API.  Install with::

    pip install valmar[ai]

Usage with pydantic-ai::

    from pydantic_ai import Agent
    from valmar.tools import valmar_context_tool

    tool = valmar_context_tool(
        api_key="valmr_proj_sk_...",
        organization_id="...",
        project_id="...",
    )

    agent = Agent("openai:gpt-4o", tools=[tool])
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from valmar.client import ValmarClient


def valmar_context_tool(
    api_key: str,
    *,
    base_url: str = "https://api.valmar.dev",
    organization_id: UUID | str | None = None,
    project_id: UUID | str | None = None,
    requesting_application: str = "pydantic-ai-agent",
    search_threshold: int = 3,
) -> Any:
    """Return a Pydantic AI tool function for retrieving Valmar context.

    The tool first searches existing knowledge. If fewer than
    ``search_threshold`` results are found, it falls back to creating a
    context-gathering request.

    Parameters
    ----------
    api_key:
        Valmar project API key (``valmr_proj_sk_...``).
    base_url:
        Base URL of the Valmar API.
    organization_id:
        Organization UUID (required for search operations).
    project_id:
        Project UUID (required for context gather operations).
    requesting_application:
        Application name passed to context-gather requests.
    search_threshold:
        Minimum number of search results required before the tool skips
        the fallback gather step.

    Returns
    -------
    A callable compatible with ``pydantic_ai.Tool``.
    """
    try:
        from pydantic_ai import Tool
    except ImportError as exc:
        raise ImportError(
            "pydantic-ai is required for tool integration. "
            "Install it with: pip install valmar[ai]"
        ) from exc

    client = ValmarClient(
        api_key=api_key,
        base_url=base_url,
        organization_id=organization_id,
        project_id=project_id,
    )

    async def get_valmar_context(question: str) -> str:
        """Search Valmar's knowledge base for organizational context.

        If insufficient results are found, a context-gathering request is
        created to collect the information from team members.

        Args:
            question: The question or topic to look up in the knowledge base.
        """
        # Step 1: search existing knowledge
        search_result = client.knowledge.search(question, limit=10)

        if len(search_result.items) >= search_threshold:
            parts = []
            for item in search_result.items:
                parts.append(f"## {item.title}\n{item.content_md}")
            return "\n\n---\n\n".join(parts)

        # Step 2: fall back to context gather if project_id is available
        if client.project_id is not None:
            handle = client.context.gather(
                question,
                requesting_application=requesting_application,
            )
            # Include any search results we did find
            existing = ""
            if search_result.items:
                snippets = [f"- {item.title}: {item.content_md[:200]}" for item in search_result.items]
                existing = "Existing partial results:\n" + "\n".join(snippets) + "\n\n"

            return (
                f"{existing}"
                f"A context-gathering request has been created "
                f"(ID: {handle.context_request_id}, status: {handle.status}). "
                f"Valmar will reach out to team members to collect this information. "
                f"You can check the status later with the request ID."
            )

        # No project_id, just return what we have
        if search_result.items:
            parts = []
            for item in search_result.items:
                parts.append(f"## {item.title}\n{item.content_md}")
            return "\n\n---\n\n".join(parts)

        return "No relevant context found in the knowledge base."

    return Tool(get_valmar_context, name="valmar_context")
