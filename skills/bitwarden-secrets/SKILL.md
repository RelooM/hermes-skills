---
name: bitwarden-secrets
description: Retrieve and use Bitwarden secrets via bws
category: devops
---

# Bitwarden Secrets Management

This module provides utilities for retrieving and using secrets stored in Bitwarden
using the `bws` CLI, with configurable persistent storage and session caching.

## Key Features:
- **Default Session-Only Storage**: Secrets are kept in-memory and never written to disk unless explicitly persisted with `--persist`.
- **Persistent Storage Support**: Secrets can be stored in files (configurable location, e.g., `/tmp/hermes-bitwarden` by default).
- **In-Memory Caching**: Secrets are cached for the session; use `--cache-only` to retrieve without calling Bitwarden.
- **Cache Clearing**: Use `--clear-cache` to wipe both in-memory and persistent cache.

## Configuration

| Variable | Default | Description |
|--------------------------|---------|------------------------------------------------------------------------------------------|
| `BITWARDEN_SESSION_ONLY` | `true` | When `true`, secrets are stored in-memory for the session only — never written to disk. |
| `BWS_ACCESS_TOKEN` | — | Bitwarden machine account access token (required). |
| `BWS_SERVER_URL` | — | Custom Bitwarden server URL (optional, e.g. `https://vault.bitwarden.eu`). |
| `BWS_BIN` | auto | Explicit path to the Bitwarden CLI binary. Auto-detected if not set. |
| `BITWARDEN_STORAGE_PATH` | `/tmp/hermes-bitwarden` | Directory for persistent secret storage. |

## New Script: `scripts/bitwarden_secrets.py`

The skill includes a Python script with the following capabilities:
- **Session-Only Storage**: Secrets stored in-memory by default.
- **Persistent Storage**: Use `--persist` to write secrets to disk.
- **Caching Logistics**:
  - `--cache-only`: Retrieve from cache without calling Bitwarden.
  - `--clear-cache`: Delete all secrets from both memory and disk.

## Commands and Usage

### 1. Retrieve a Secret
```bash
python3 scripts/bitwarden_secrets.py <SECRET_ID>
``` Retrieves a secret, storing it in-memory by default.

### 2. Persist a Secret to Disk
```bash
python3 scripts/bitwarden_secrets.py <SECRET_ID> --persist
``` Explicitly writes the secret to persistent storage.

### 3. Retrieve from Cache
```bash
python3 scripts/bitwarden_secrets.py <SECRET_ID> --cache-only
``` Fetches from in-memory or disk cache without calling Bitwarden.

### 4. Clear All Caches
```bash
python3 scripts/bitwarden_secrets.py --clear-cache
``` Wipes both in-memory and persistent storage caches.

### 5. List All Secret UUIDs
```bash
python3 scripts/bitwarden_secrets.py --list-uuids
``` Displays all available secret UUIDs from Bitwarden.

### 6. List All Secret Keys with UUIDs
```bash
python3 scripts/bitwarden_secrets.py --list-keys
``` Lists all secret keys paired with their UUIDs.

## Persistent Storage
- **Location**: Configurable via `BITWARDEN_STORAGE_PATH` (default `/tmp/hermes-bitwarden`).
- **File Structure**: Secrets stored as `<SECRET_ID>.txt` in the configured directory.

## Caching Logic
- **Session Cache**: `session_secrets` dictionary, cleared on process exit.
- **Persistent Cache**: Wiped with `--clear-cache` command.

## GitHub Pull Request

The updates are reflects in PR #5: <https://github.com/RelooM/hermes-skills/pull/5>

## Troubleshooting
- **Authentication Issues**: Ensure correct `BWS_ACCESS_TOKEN` and server URL.
- **Permission Errors**: Verify write access to the persistent storage directory.
- **Cache Not Found**: Ensure `--cache-only` is used after a secret has been retrieved in the session.

## Documentation

### SKILL.md Updates
- Added `BITWARDEN_STORAGE_PATH` configuration option.
- Updated `--clear-cache` command description.
- Enhanced caching logic explanations.

### Script Changes
- Implemented persistent storage with configurable directory.
- Enhanced caching and cache-clearing mechanisms.

## References

- Bitwarden API Docs: https://bitwarden.com/api/
- Bitwarden CLI Repository: https://github.com/bitwarden/cli
