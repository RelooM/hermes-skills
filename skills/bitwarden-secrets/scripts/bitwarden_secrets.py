#!/usr/bin/env python3
"""
Bitwarden Secrets Management Skill

This module provides utilities for retrieving and using secrets stored in Bitwarden
using the `bws` CLI, with configurable persistent storage and session caching.
"""

import os
import subprocess
import json
import sys


# ============================================================================
# Configuration
# ============================================================================

# Toggle to keep retrieved secrets in active session memory only.
# Default is TRUE — secrets are never written to disk unless explicitly persisted.
SESSION_ONLY_STORAGE = os.getenv("BITWARDEN_SESSION_ONLY", "true").lower() in ("1", "true", "yes", "on")

# Persistent storage directory (default /tmp/hermes-bitwarden)
STORAGE_PATH = os.getenv("BITWARDEN_STORAGE_PATH", "/tmp/hermes-bitwarden")

# In-memory session storage for secrets when SESSION_ONLY_STORAGE is enabled.
# This dictionary exists only for the duration of the Python process/session.
session_secrets = {}


# ============================================================================
# Utility Functions
# ============================================================================

def get_bws_bin() -> str:
    """Detect the Bitwarden CLI binary location."""
    if os.getenv("BWS_BIN"):
        return os.environ["BWS_BIN"]

    hermes_home = os.getenv("HERMES_HOME", os.path.expanduser("~/.hermes"))
    candidates = [
        os.path.join(hermes_home, "bin", "bws"),
        os.path.join(os.path.expanduser("~"), "bin", "bws"),
    ]

    for candidate in candidates:
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate

    # Fall back to PATH lookup
    return "bws"


def run_bws_command(args: list[str], check: bool = True) -> str:
    """Execute a bws command and return its stdout."""
    bws_bin = get_bws_bin()
    cmd = [bws_bin] + args

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if check and result.returncode != 0:
        raise RuntimeError(
            f"bws command failed with exit code {result.returncode}: {result.stderr}"
        )

    return result.stdout


def fetch_secret_from_bitwarden(secret_id: str) -> str:
    """Retrieve a secret from Bitwarden using the bws CLI."""
    output = run_bws_command([
        "secret", "get", secret_id,
        "--output", "json",
    ])

    data = json.loads(output)
    return data.get("value", "")


def write_to_persistent_store(secret_id: str, secret_value: str) -> None:
    """Store secret in configurable persistent storage location."""
    # Create storage directory if it doesn't exist
    os.umask(0o077)
    os.makedirs(STORAGE_PATH, exist_ok=True)

    # Write secret to file
    secret_path = os.path.join(STORAGE_PATH, f"{secret_id}.txt")

    with open(secret_path, "w") as f:
        f.write(secret_value)


def read_from_persistent_store(secret_id: str) -> str | None:
    """Retrieve secret from persistent storage."""
    secret_path = os.path.join(STORAGE_PATH, f"{secret_id}.txt")

    if not os.path.exists(secret_path):
        return None

    with open(secret_path, "r") as f:
        return f.read().strip()


# ============================================================================
# Main API
# ============================================================================

def retrieve_secret(secret_id: str, persist: bool = False) -> str:
    """Retrieve a secret with storage logic."""
    global session_secrets

    # Check persistent storage first if not in session-only mode
    if not SESSION_ONLY_STORAGE:
        cached_value = read_from_persistent_store(secret_id)
        if cached_value:
            session_secrets[secret_id] = cached_value
            return cached_value

    # Fetch from Bitwarden
    secret_value = fetch_secret_from_bitwarden(secret_id)

    if SESSION_ONLY_STORAGE and not persist:
        session_secrets[secret_id] = secret_value
        return secret_value

    # Write to persistent storage if requested or not in session-only mode
    if persist or not SESSION_ONLY_STORAGE:
        write_to_persistent_store(secret_id, secret_value)

    return secret_value


def get_cached_secret(secret_id: str) -> str | None:
    """Retrieve from in-memory session cache or persistent storage."""
    # First check in-memory cache
    value = session_secrets.get(secret_id)
    if value is not None:
        return value

    # If not in session cache, check persistent storage (when not session-only)
    if not SESSION_ONLY_STORAGE:
        return read_from_persistent_store(secret_id)

    return None


def clear_session_cache() -> None:
    """Clear both in-memory session cache and persistent storage."""
    global session_secrets
    session_secrets.clear()

    # Wipe persistent storage directory
    if os.path.exists(STORAGE_PATH):
        for file in os.listdir(STORAGE_PATH):
            os.remove(os.path.join(STORAGE_PATH, file))
        os.rmdir(STORAGE_PATH)


# ============================================================================
# CLI Entry Point
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Retrieve Bitwarden secrets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s <secret-uuid>                  Retrieve a secret value
  %(prog)s <secret-uuid> --persist       Retrieve and persist to disk
  %(prog)s <secret-uuid> --cache-only     Retrieve from cache (session or persistent)
  %(prog)s --list-uuids                   List all secret UUIDs
  %(prog)s --list-keys                    List all secret keys with UUIDs
  %(prog)s --clear-cache                 Clear both session and persistent cache
""",
    )

    parser.add_argument("secret_id", nargs="?", help="Secret UUID to retrieve")
    parser.add_argument("--persist", action="store_true", help="Write to persistent storage even when BITWARDEN_SESSION_ONLY is enabled")
    parser.add_argument("--cache-only", action="store_true", help="Retrieve from cache (session memory or disk) without calling Bitwarden")
    parser.add_argument("--list-uuids", action="store_true", help="List all available secret UUIDs")
    parser.add_argument("--list-keys", action="store_true", help="List all secret keys with their UUIDs")
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached secrets (memory and persistent storage)")

    args = parser.parse_args()

    try:
        if args.clear_cache:
            clear_session_cache()
            print("Cached secrets cleared")
            sys.exit(0)

        if args.list_uuids:
            uuids = subprocess.check_output([
                get_bws_bin(),
                "secret", "list", "--output", "json"
            ]).decode("utf-8")
            # Parse and print just the IDs
            secrets = json.loads(uuids)
            print(json.dumps([s["id"] for s in secrets], indent=2))
            sys.exit(0)

        if args.list_keys:
            keys_output = subprocess.check_output([
                get_bws_bin(),
                "secret", "list", "--output", "json"
            ]).decode("utf-8")
            secrets = json.loads(keys_output)
            keys = [{"key": s["key"], "id": s["id"]} for s in secrets]
            print(json.dumps(keys, indent=2))
            sys.exit(0)

        if not args.secret_id:
            parser.error("secret_id is required unless using --list-uuids, --list-keys, or --clear-cache")

        if args.cache_only:
            value = get_cached_secret(args.secret_id)
            if value is None:
                raise SystemExit(f"Secret '{args.secret_id}' not found in cache")
        else:
            value = retrieve_secret(args.secret_id, args.persist)

        print(value)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
