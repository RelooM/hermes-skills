---
name: bitwarden-secrets
description: Retrieve and use Bitwarden secrets via bws
category: devops
---

# Bitwarden Secrets Management

This skill documents the workflow for retrieving and using secrets stored in Bitwarden using the `bws` CLI, including handling machine account tokens, custom server URLs, and binary location detection.

## Binary Location & Installation

### Required Dependency

- **`jq`**: Required to parse JSON output from `bws` commands. Must be installed separately by the user before using this skill.

### Installation Method

**Only use the Hermes Bitwarden wizard** - do not install `bws` through any other method:

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

### Binary Detection\n\nThe skill automatically detects `bws` in this order:\n1. `$HERMES_HOME/bin/bws` (Hermes-managed)\n2. `$HOME/bin/bws` (user-local)\n\n### New Configuration Option\n\n| Variable               | Default | Description                                                                                                                                       |\n|------------------------|---------|----------------------------------------------------------------------------------------------------------------------------------------------------|\n| `BITWARDEN_SESSION_ONLY` | `False` | Store secrets in-memory for the session only. Set to `True` via .env or config.yaml.                                                                |\n\nDetect path without modifying PATH:
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
   ```
   
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

## References

- Bitwarden API Docs: https://bitwarden.com/api/
- `bws` CLI Repository: https://github.com/bitwarden/cli