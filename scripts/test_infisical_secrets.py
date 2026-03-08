#!/usr/bin/env python3
"""
Test Infisical secret create and list/get via Morphso API.

Requires:
- Morphso running at MORPHSO_URL (default http://localhost:8013) with
  INFISICAL_HOST, INFISICAL_TOKEN (or INFISICAL_CLIENT_ID + INFISICAL_CLIENT_SECRET),
  and optionally INFISICAL_PROJECT_ID set.
- Env for this script: INFISICAL_PROJECT_ID (or pass as first arg) for request bodies.

Usage:
  export INFISICAL_PROJECT_ID=<your-project-id>
  export INFISICAL_TOKEN=<token>   # and run Morphso with same
  # Start Morphso: docker run -p 8013:8013 -e INFISICAL_HOST=... -e INFISICAL_TOKEN=... -e INFISICAL_PROJECT_ID=... morphso:test
  python scripts/test_infisical_secrets.py
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

try:
    import requests
except ImportError:
    print("pip install requests")
    sys.exit(1)

# Organization: neunexus (organization_id: 822f8bc9-f076-4a39-b164-bd20248cb1b4)
# You need the *project* ID from Infisical (Project Settings) under this org.
MORPHSO_URL = os.getenv("MORPHSO_URL", "http://localhost:8013").rstrip("/")
PROJECT_ID = os.getenv("INFISICAL_PROJECT_ID") or (sys.argv[1] if len(sys.argv) > 1 else None)
ENVIRONMENT = os.getenv("INFISICAL_ENVIRONMENT_SLUG", "dev")
SECRET_PATH = os.getenv("INFISICAL_SECRET_PATH", "/")

# Secrets to create (key -> value)
SECRETS_TO_CREATE = {
    "POSTGRES_USER": "nexus_admin",
    "POSTGRES_PASSWORD": "nexus_admin1q!2w@3e#",
    "POSTGRES_DB": "neunexus_postgres_db",
    "POSTGRES_HOST": "toji.homes",
    "POSTGRES_PORT": "5432",
    "POSTGRES_DNS_HOST": "postgres_db",
}


def main():
    if not PROJECT_ID:
        print("Set INFISICAL_PROJECT_ID (or pass project_id as first arg). Get it from Infisical Project Settings.")
        sys.exit(2)

    base = f"{MORPHSO_URL}/api/v1/secret"
    params = {"project_id": PROJECT_ID, "environment_slug": ENVIRONMENT, "secret_path": SECRET_PATH}

    # 1) Create secrets
    print("Creating secrets...")
    for name, value in SECRETS_TO_CREATE.items():
        r = requests.post(
            f"{base}/secrets",
            json={
                "project_id": PROJECT_ID,
                "environment_slug": ENVIRONMENT,
                "secret_path": SECRET_PATH,
                "secret_name": name,
                "secret_value": value,
            },
            timeout=30,
        )
        if r.status_code in (200, 201):
            print(f"  OK  {name}")
        elif r.status_code == 409 or "already exists" in (r.text or "").lower():
            print(f"  EXISTS (update) {name}")
            ru = requests.put(
                f"{base}/secrets",
                json={
                    "project_id": PROJECT_ID,
                    "environment_slug": ENVIRONMENT,
                    "secret_path": SECRET_PATH,
                    "current_secret_name": name,
                    "secret_value": value,
                },
                timeout=30,
            )
            if ru.status_code == 200:
                print(f"  OK  {name} (updated)")
            else:
                print(f"  FAIL {name}: {ru.status_code} {ru.text[:200]}")
        else:
            print(f"  FAIL {name}: {r.status_code} {r.text[:300]}")
            if r.status_code == 503:
                print("  (Is Morphso running with INFISICAL_TOKEN / INFISICAL_HOST set?)")
            return 1

    # 2) List secrets
    print("\nListing secrets...")
    r = requests.get(f"{base}/secrets", params=params, timeout=30)
    if r.status_code != 200:
        print(f"  List failed: {r.status_code} {r.text[:300]}")
        return 1
    data = r.json()
    secrets_list = data.get("secrets") or []
    print(f"  Found {len(secrets_list)} secret(s)")
    for s in secrets_list:
        key = s.get("secretKey") or s.get("secret_key")
        val = s.get("secretValue") or s.get("secret_value")
        if val and val != "<hidden>":
            print(f"    {key} = {val[:20]}...")
        else:
            print(f"    {key} = <hidden>")

    # 3) Get by name (sample)
    print("\nGet by name (POSTGRES_USER, POSTGRES_DB)...")
    for name in ("POSTGRES_USER", "POSTGRES_DB"):
        r = requests.get(
            f"{base}/secrets/{name}",
            params=params,
            timeout=30,
        )
        if r.status_code == 200:
            d = r.json()
            print(f"  {name} = {d.get('secretValue', d.get('secret_value', ''))}")
        else:
            print(f"  {name}: {r.status_code} {r.text[:200]}")

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
