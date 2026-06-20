#!/usr/bin/env python3
"""
Bitwarden Secrets Management Skill

This module provides utilities for retrieving and using secrets stored in Bitwarden
using the `bws` CLI, with optional session-only storage for sensitive credentials.
"""

import os
import subprocess
import json


# ============================================================================
# Configuration
# ============================================================================

# Toggle to keep retrieved secrets in active session memory only.
# Set BITWARDEN_SESSION_ONLY="true" in your environment to enable.
SESSION_ONLY_STORAGE = os.getenv("BITWARDEN_SESSION_ONLY", "false").lower() in ("1", "true", "yes", "on")

# In-memory session storage for secrets when SESSION_ONLY_STORAGE is enabled.
# This dictionary exists only for the duration of the Python process/session.
session_secrets = {}


# ============================================================================
# Utility Functions
# ============================================================================

def get_bws_bin() -> str:
    """
    Detect the Bitwarden Secrets CLI binary location.
    
    Detection order:
    1. $HERMES_HOME/bin/bws (Hermes-managed)
    2. $HOME/bin/bws (user-local)
    3. System PATH (via command -v bws)
    """
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
    """
    Execute a bws command and return its stdout.
    """
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
    """
    Retrieve a secret from Bitwarden using the bws CLI.
    """
    output = run_bws_command([
        "secret", "get", secret_id,
        "--output", "json",
    ])
    
    data = json.loads(output)
    return data.get("value", "")


def write_to_persistent_store(secret_id: str, secret_value: str) -> None:
    """
    Placeholder for persistent storage logic.
    
    This function should be implemented based on your specific storage requirements.
    By default, this is a no-op to avoid accidental writes.
    """
    # Implement your persistent storage logic here if needed.
    # Example:
    # - Write to a secure file (encrypted)
    # - Store in a database
    # - Update environment variables
    #
    # IMPORTANT: Only enable this when explicitly configured.
    pass


# ============================================================================
# Main API
# ============================================================================

def retrieve_secret(secret_id: str, persist: bool = False) -> str:
    """
    Retrieve a secret from Bitwarden and apply storage logic based on configuration.
    
    Args:
        secret_id: The UUID of the secret to retrieve.
        persist: If True, explicitly write to persistent storage even when
                 SESSION_ONLY_STORAGE is enabled. This should only be used when
                 explicitly configured by the user.
    
    Returns:
        The secret value.
    """
    global session_secrets
    
    secret_value = fetch_secret_from_bitwarden(secret_id)
    
    if SESSION_ONLY_STORAGE and not persist:
        # Store in-memory for this session only
        session_secrets[secret_id] = secret_value
        # NO persistent storage write
        return secret_value
    
    # Default behavior: persistent storage (if configured)
    if persist:
        write_to_persistent_store(secret_id, secret_value)
    
    return secret_value


def get_cached_secret(secret_id: str) -> str | None:
    """
    Retrieve a secret from the in-memory session cache.
    
    Args:
        secret_id: The UUID of the secret to retrieve.
    
    Returns:
        The secret value if found in session cache, otherwise None.
    """
    return session_secrets.get(secret_id)


def clear_session_cache() -> None:
    """
    Clear all secrets from the in-memory session cache.
    """
    session_secrets.clear()


# ============================================================================
# CLI Entry Point (Optional)
# ============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Retrieve Bitwarden secrets")
    parser.add_argument("secret_id", help="Secret UUID to retrieve")
    parser.add_argument(
        "--persist",
        action="store_true",
        help="Explicitly write to persistent storage even when BITWARDEN_SESSION_ONLY is enabled",
    )
    parser.add_argument(
        "--cache-only",
        action="store_true",
        help="Retrieve from in-memory session cache only",
    )
    
    args = parser.parse_args()
    
    if args.cache_only:
        value = get_cached_secret(args.secret_id)
        if value is None:
            raise SystemExit(f"Secret '{args.secret_id}' not found in session cache")
    else:
        value = retrieve_secret(args.secret_id, persist=args.persist)
    
    print(value)
