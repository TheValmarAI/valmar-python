# valmar

Python SDK for the Valmar platform.

Documentation: https://docs.getvalmar.com

Source: https://github.com/TheValmarAI/valmar-python

License: Apache-2.0

## Installation

```bash
uv add valmar
```

## Quick start

```python
from valmar import Valmar

client = Valmar(
    api_key="valmr_proj_sk_...",
    base_url="https://your-valmar-deployment.example.com",
    organization_id="your-org-id",
    project_id="your-project-id",
)
```

`base_url` is required because Valmar is deployed per customer. Use the base URL for your own Valmar deployment.

## Search context

Find relevant saved knowledge across the configured project.

```python
results = client.context.search("deployment process")

for hit in results.hits:
    resource = client.context.read(hit.reference)
    print(f"{hit.title} ({hit.score})")
    print(resource.content_md)

    trace = client.context.trace(hit.reference)
    print(trace.source_thread_ids)
```

## Create a context request

Create a knowledge request that gets routed to the right people in your organization.

```python
handle = client.context_requests.create(
    "How do we handle database migrations in production?",
    background_context="Planning a schema change for the orders table",
)

print(f"Request created: {handle.context_request_id}")
print(f"Status: {handle.status}")

request = client.context_requests.get(handle.context_request_id)
if request.status == "completed":
    print(request.result_summary)
```

## List and import people

```python
from valmar import CreatePersonInput

people = client.people.list()

result = client.people.import_bulk(
    [
        CreatePersonInput(
            email="ada@example.com",
            display_name="Ada Lovelace",
            timezone="UTC",
            title="Principal Engineer",
        )
    ]
)
```

## Run Knowledge Gap analysis

Use the active connection configured by a project administrator.

```python
overview = client.knowledge_gaps.overview()
run = client.knowledge_gaps.start_run(custom_instructions="Focus on incident workflows")

# After the run completes:
ranking = client.knowledge_gaps.get_run_artifact(run.run_id, "ranking.json")
submissions = client.knowledge_gaps.submit_ranked_gaps(run.run_id, gap_ranks=[1, 2])
```

## Context manager

```python
with Valmar(
    api_key="valmr_proj_sk_...",
    base_url="https://your-valmar-deployment.example.com",
    organization_id="your-org-id",
    project_id="your-project-id",
) as client:
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
