# Contributing to Valmar Python

Thanks for improving the Valmar Python SDK.

## Development

Use `uv` from the repository root:

```bash
uv run python -m pytest
uv build --sdist --wheel
```

The SDK requires callers to pass their Valmar deployment URL explicitly with `base_url`; do not add a default API host.

## Pull Requests

- Keep public API changes reflected in `README.md`.
- Add or update tests for client behavior changes.
- Run tests and build checks before requesting review.
- Do not commit generated caches, virtual environments, or local `.env` files.

## Releases

Releases are published from the public mirror repository through GitHub Actions and PyPI Trusted Publishing.
