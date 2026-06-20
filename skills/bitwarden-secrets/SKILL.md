---
name: bitwarden-secrets
description: Retrieve and use Bitwarden secrets via bws
category: devops
---

# Bitwarden Secrets Management

This skill documents the workflow for retrieving and using secrets stored in Bitwarden using the `bws` CLI, including handling machine account tokens, custom server URLs, and binary location detection.

## New Script: `scripts/bitwarden_secrets.py`

The skill includes a dedicated Python script at `scripts/bitwarden_secrets.py` that provides:

- **Session-only storage** — When `BITWARDEN_SESSION_ONLY` is set to `true`, retrieved secrets are kept in an in-memory dictionary and never written to disk. This is now the **default behavior**.
- **Explicit persistence** — Pass `--persist` to explicitly write to persistent storage even when session-only mode is enabled.
- **Session cache lookup** — Pass `--cache-only` to retrieve a previously fetched secret from the in-memory cache.
- **CLI interface** — The script can be invoked directly:
 ```bash
python3 scripts/bitwarden_secrets.py <secret-uuid>
python3 scripts/bitwarden_secrets.py <secret-uuid> --persist
python3 scripts/bitwarden_secrets.py <secret-uuid> --cache-only
python3 scripts/bitwarden_secrets.py --list-uuids
```
- **Python API** — Import and use programmatically:
 ```python
from bitwarden_secrets import retrieve_secret, get_cached_secret, clear_session_cache, list_secret_uuids
```