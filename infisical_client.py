"""
Infisical Python SDK client wrapper for Morphso.
Uses INFISICAL_TOKEN or Universal Auth (INFISICAL_CLIENT_ID + INFISICAL_CLIENT_SECRET).
"""
import os
from typing import Optional, Any

from dotenv import load_dotenv
load_dotenv()

_client: Optional[Any] = None


def _get_host() -> str:
    return os.getenv("INFISICAL_HOST", "https://app.infisical.com").rstrip("/")


def get_client():
    """Return a configured InfisicalSDKClient. Uses token or Universal Auth."""
    global _client
    if _client is not None:
        return _client

    from infisical_sdk import InfisicalSDKClient

    host = _get_host()
    token = os.getenv("INFISICAL_TOKEN")
    client_id = os.getenv("INFISICAL_CLIENT_ID")
    client_secret = os.getenv("INFISICAL_CLIENT_SECRET")

    if token:
        _client = InfisicalSDKClient(host=host, token=token)
        return _client
    if client_id and client_secret:
        _client = InfisicalSDKClient(host=host)
        _client.auth.universal_auth.login(
            client_id=client_id,
            client_secret=client_secret,
        )
        return _client
    raise RuntimeError(
        "Infisical not configured: set INFISICAL_TOKEN or "
        "INFISICAL_CLIENT_ID and INFISICAL_CLIENT_SECRET"
    )


def get_default_project_id() -> Optional[str]:
    return os.getenv("INFISICAL_PROJECT_ID")


def get_default_environment() -> str:
    return os.getenv("INFISICAL_ENVIRONMENT_SLUG", "dev")


def get_default_secret_path() -> str:
    return os.getenv("INFISICAL_SECRET_PATH", "/")
