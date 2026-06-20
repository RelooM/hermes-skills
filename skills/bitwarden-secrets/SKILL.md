---
name: bitwarden-secrets
description: Retrieve and use Bitwarden secrets via bws
category: devops
---

# Bitwarden Secrets Management

This skill documents the workflow for retrieving and using secrets stored in Bitwarden using the `bws` CLI, including handling machine account tokens, custom server URLs, and binary location detection.

## New Script: `scripts/bitwarden_secrets.py`

The skill includes a dedicated Python script at `scripts/bitwarden_secrets.py` that provides:

- **Session-only storage** — When `BITWARDEN_SESSION_ONLY` is set to `true`, retrieved secrets are kept in an in-memory dictionary and never written to disk or any persistent store.
- **Explicit persistence** — Pass `--persist` to explicitly write to persistent storage even when session-only mode is enabled.
- **Session cache lookup** — Pass `--cache-only` to retrieve a previously fetched secret from the in-memory cache without calling Bitwarden again.
- **CLI interface** — The script can be invoked directly:
  ```bash
  # Retrieve a secret (respects BITWARDEN_SESSION_ONLY)
  python3 scripts/bitwarden_secrets.py <secret-uuid>

  # Retrieve and explicitly persist
  python3 scripts/bitwarden_secrets.py <secret-uuid> --persist

  # Retrieve from session cache only
  python3 scripts/bitwarden_secrets.py <secret-uuid> --cache-only
  ```
- **Python API** — Import and use programmatically:
  ```python
  from bitwarden_secrets import retrieve_secret, get_cached_secret, clear_session_cache

  value = retrieve_secret("<secret-uuid>")
  cached = get_cached_secret("<secret-uuid>")
  clear_session_cache()
  ```

No additional dependencies beyond `bws` and `jq` are required.

## Configuration

| Variable                 | Default | Description                                                                              |
|--------------------------|---------|------------------------------------------------------------------------------------------|
| `BITWARDEN_SESSION_ONLY` | `false` | When `true`, secrets are stored in-memory for the session only — never written to disk.  |
| `BWS_ACCESS_TOKEN`       | —       | Bitwarden machine account access token (required).                                       |
| `BWS_SERVER_URL`         | —       | Custom Bitwarden server URL (optional, e.g. `https://vault.bitwarden.eu`).              |
| `BWS_BIN`                | auto    | Explicit path to the `bws` binary. Auto-detected if not set.                            |

### Session-Only Mode

Enable session-only mode by setting the environment variable before running the skill:

```bash
export BITWARDEN_SESSION_ONLY=true
```

When enabled:
- Secrets are stored in a Python dictionary (`session_secrets`) that lives only for the duration of the process.
- No file writes, no database updates, no persistent storage of any kind.
- Once the process ends, all cached secrets are lost.

To explicitly persist a secret even in session-only mode, use the `--persist` flag.

## Binary Location & Installation

### Required Dependency

- **`jq`**: Required to parse JSON output from `bws` commands. Must be installed separately by the user before using this skill.

### Installation Method

**Only use the Hermes Bitwarden wizard** — do not install `bws` through any other method:

```bash
hermes secrets bitwarden setup
```

This wizard will:
1. Download and verify `bws` into `$HERMES_HOME/bin/bws`
2. Prompt for the access token (hidden input) and store it as `BWS_ACCESS_TOKEN`
3. Ask for Bitwarden region and store it as `BWS_SERVER_URL`
4. List accessible projects and let you pick one
5. Test-fetch secrets and show which env vars will resolve
6. Enable the Bitwarden secrets integration

For non-interactive setup:
```bash
hermes secrets bitwarden setup \
  --access-token "$BWS_ACCESS_TOKEN" \
  --server-url https://vault.bitwarden.eu \
  --project-id <project-uuid>
```

### Binary Detection

The skill automatically detects `bws` in this order:
1. `$HERMES_HOME/bin/bws` (Hermes-managed)
2. `$HOME/bin/bws` (user-local)

Detect path without modifying PATH:
```bash
BWS_BIN="${BWS_BIN:-$(command -v bws 2>/dev/null || echo \"${HERMES_HOME:-$HOME/.hermes}/bin/bws\")}"
```

## Quick Start

1. **Install `bws`** using one of the methods above
2. **Export credentials**:
   ```bash
   export BWS_ACCESS_TOKEN=your_machine_account_token
   export BWS_SERVER_URL=https://vault.bitwarden.eu  # Optional
   ```

3. **List Secrets**:
   ```bash
   $BWS_BIN secret list --output json
   ```

4. **Retrieve Secret**:
   ```bash
   SECRET_UUID="<uuid>"
   SECRET_VALUE=$($BWS_BIN secret get "$SECRET_UUID" --output json | jq -r '.value')
   echo "$SECRET_VALUE"
   ```

5. **Use the Secret in a Command**:
   ```bash
   # Example: inject as environment variable
   export API_KEY="$SECRET_VALUE"
   ./some-command-that-uses-api-key

   # Or use bws run to automatically inject the secret
   $BWS_BIN run -- ./some-command-that-needs-secret
   ```

## Common Pitfalls

- **401 Unauthorized** – Verify the token is valid and has the `secrets.read` scope.
- **Invalid decryption key** – Ensure you are using an Access Token generated from Bitwarden's UI.
- **Missing `jq`** – `jq` is required to parse JSON output. Install it with your system's package manager if not present.
- **Binary not found** – Ensure `bws` is in one of the expected locations or set `BWS_BIN` explicitly.
- **Environment variables not set** – Both `BWS_ACCESS_TOKEN` and optionally `BWS_SERVER_URL` must be exported before use.
- **Permission denied** – Ensure the binary is executable (`chmod +x $BWS_BIN`).
- **Network issues** – Verify connectivity to your Bitwarden instance (default: https://api.bitwarden.com).
- **Secrets not persisting** – If `BITWARDEN_SESSION_ONLY=true`, secrets are intentionally not written to disk. Use `--persist` to override.

## References

- Bitwarden API Docs: https://bitwarden.com/api/
- `bws` CLI Repository: https://github.com/bitwarden/cli
