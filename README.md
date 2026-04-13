# valmar

Python SDK for the Valmar platform.

## Installation

```bash
pip install valmar
```

## Quick start

```python
from valmar import ValmarClient

client = ValmarClient(
    api_key="valmr_proj_sk_...",
    organization_id="your-org-id",
    project_id="your-project-id",
)
```

## Examples

### Search context

Find relevant context across your organization's knowledge base.

```python
results = client.context.search("deployment process")

for item in results.items:
    print(f"{item.title} ({item.confidence})")
    print(item.content_md)
```

### Gather context

Create a context request that gets routed to the right people in your org.

```python
handle = client.context.gather(
    "How do we handle database migrations in production?",
    background_context="Planning a schema change for the orders table",
)

print(f"Request created: {handle.context_request_id}")
print(f"Status: {handle.status}")

# Poll for the result later
request = client.context.get(handle.context_request_id)
if request.status == "completed":
    print(request.result_summary)
```

### Find experts

Discover who in your org knows about a given topic.

```python
expert_parts = client.people.find_experts("Kubernetes")

for part in expert_parts:
    print(f"{part.title} — mentioned members: {part.related_member_ids}")
```

### List members

```python
members = client.members.list()

for member in members:
    print(f"{member.display_name} <{member.email}>")
```

## Context manager

The client can be used as a context manager to ensure the HTTP connection is properly closed.

```python
with ValmarClient(api_key="valmr_proj_sk_...") as client:
    results = client.context.search("onboarding process")
```

## Error handling

The SDK raises `httpx.HTTPStatusError` for non-2xx responses.

```python
import httpx

try:
    client.context.search("test")
except httpx.HTTPStatusError as e:
    print(f"API error {e.response.status_code}: {e.response.text}")
```
