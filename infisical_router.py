"""FastAPI router for Infisical secret management at /api/v1/secret."""
from typing import Optional, List, Any

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from infisical_client import (
    get_client,
    get_default_project_id,
    get_default_environment,
    get_default_secret_path,
)

router = APIRouter(prefix="/api/v1/secret", tags=["secret"])


def _project_id(project_id: Optional[str] = None) -> str:
    pid = project_id or get_default_project_id()
    if not pid:
        raise HTTPException(
            status_code=400,
            detail="project_id required in body or INFISICAL_PROJECT_ID in env",
        )
    return pid


# --- Auth ---


class UniversalAuthRequest(BaseModel):
    client_id: str = Field(..., description="Machine identity client ID")
    client_secret: str = Field(..., description="Machine identity client secret")


class TokenAuthRequest(BaseModel):
    token: str = Field(..., description="Infisical access token")


@router.post("/auth/universal")
async def auth_universal(body: UniversalAuthRequest):
    """Authenticate using Universal Auth (machine identity)."""
    try:
        from infisical_sdk import InfisicalSDKClient
        import os
        host = os.getenv("INFISICAL_HOST", "https://app.infisical.com").rstrip("/")
        c = InfisicalSDKClient(host=host)
        c.auth.universal_auth.login(
            client_id=body.client_id,
            client_secret=body.client_secret,
        )
        return {"status": "ok", "message": "Universal auth successful"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/auth/token")
async def auth_token(body: TokenAuthRequest):
    """Validate token auth (typically token is set via INFISICAL_TOKEN env)."""
    try:
        from infisical_sdk import InfisicalSDKClient
        import os
        host = os.getenv("INFISICAL_HOST", "https://app.infisical.com").rstrip("/")
        c = InfisicalSDKClient(host=host, token=body.token)
        return {"status": "ok", "message": "Token accepted"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


# --- Secrets ---


@router.get("/secrets")
async def list_secrets(
    project_id: Optional[str] = None,
    environment_slug: Optional[str] = None,
    secret_path: Optional[str] = None,
    recursive: bool = False,
):
    """List secrets for a project/environment/path."""
    try:
        client = get_client()
        pid = _project_id(project_id)
        env = environment_slug or get_default_environment()
        path = secret_path if secret_path is not None else get_default_secret_path()
        resp = client.secrets.list_secrets(
            project_id=pid,
            environment_slug=env,
            secret_path=path,
            recursive=recursive,
        )
        items = []
        if hasattr(resp, "secrets"):
            for s in resp.secrets:
                items.append({
                    "secretKey": getattr(s, "secretKey", getattr(s, "secret_key", None)),
                    "secretValue": getattr(s, "secretValue", getattr(s, "secret_value", None)) if hasattr(s, "secretValue") else "<hidden>",
                })
        return {"secrets": items, "environment": env, "path": path}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateSecretRequest(BaseModel):
    project_id: Optional[str] = None
    environment_slug: Optional[str] = None
    secret_path: Optional[str] = None
    secret_name: str = Field(..., min_length=1)
    secret_value: str = Field(...)


@router.post("/secrets")
async def create_secret(body: CreateSecretRequest):
    """Create a secret by name."""
    try:
        client = get_client()
        pid = _project_id(body.project_id)
        env = body.environment_slug or get_default_environment()
        path = body.secret_path if body.secret_path is not None else get_default_secret_path()
        secret = client.secrets.create_secret_by_name(
            secret_name=body.secret_name,
            project_id=pid,
            environment_slug=env,
            secret_path=path,
            secret_value=body.secret_value,
        )
        return {
            "secretKey": getattr(secret, "secretKey", getattr(secret, "secret_key", body.secret_name)),
            "message": "Secret created",
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateSecretRequest(BaseModel):
    project_id: Optional[str] = None
    environment_slug: Optional[str] = None
    secret_path: Optional[str] = None
    current_secret_name: str = Field(..., min_length=1)
    secret_value: str = Field(...)
    new_secret_name: Optional[str] = None


@router.put("/secrets")
async def update_secret(body: UpdateSecretRequest):
    """Update a secret by name."""
    try:
        client = get_client()
        pid = _project_id(body.project_id)
        env = body.environment_slug or get_default_environment()
        path = body.secret_path if body.secret_path is not None else get_default_secret_path()
        secret = client.secrets.update_secret_by_name(
            current_secret_name=body.current_secret_name,
            project_id=pid,
            environment_slug=env,
            secret_path=path,
            secret_value=body.secret_value,
            new_secret_name=body.new_secret_name,
        )
        return {
            "secretKey": getattr(secret, "secretKey", getattr(secret, "secret_key", body.current_secret_name)),
            "message": "Secret updated",
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/secrets/{secret_name}")
async def get_secret_by_name(
    secret_name: str,
    project_id: Optional[str] = None,
    environment_slug: Optional[str] = None,
    secret_path: Optional[str] = None,
):
    """Get a secret by name."""
    try:
        client = get_client()
        pid = _project_id(project_id)
        env = environment_slug or get_default_environment()
        path = secret_path if secret_path is not None else get_default_secret_path()
        secret = client.secrets.get_secret_by_name(
            secret_name=secret_name,
            project_id=pid,
            environment_slug=env,
            secret_path=path,
        )
        return {
            "secretKey": getattr(secret, "secretKey", getattr(secret, "secret_key", secret_name)),
            "secretValue": getattr(secret, "secretValue", getattr(secret, "secret_value", None)),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/secrets/{secret_name}")
async def delete_secret_by_name(
    secret_name: str,
    project_id: Optional[str] = None,
    environment_slug: Optional[str] = None,
    secret_path: Optional[str] = None,
):
    """Delete a secret by name."""
    try:
        client = get_client()
        pid = _project_id(project_id)
        env = environment_slug or get_default_environment()
        path = secret_path if secret_path is not None else get_default_secret_path()
        client.secrets.delete_secret_by_name(
            secret_name=secret_name,
            project_id=pid,
            environment_slug=env,
            secret_path=path,
        )
        return {"message": f"Secret '{secret_name}' deleted"}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Dynamic secrets ---


class CreateDynamicSecretRequest(BaseModel):
    project_slug: Optional[str] = None
    project_id: Optional[str] = None
    environment_slug: Optional[str] = None
    path: Optional[str] = None
    name: str = Field(..., min_length=1)
    provider_type: str = Field(..., description="e.g. SQL_DATABASE")
    inputs: dict = Field(default_factory=dict)
    default_ttl: str = Field(default="1h")
    max_ttl: str = Field(default="24h")


@router.post("/dynamic-secrets")
async def create_dynamic_secret(body: CreateDynamicSecretRequest):
    """Create a dynamic secret."""
    try:
        client = get_client()
        proj = body.project_slug or body.project_id or get_default_project_id()
        if not proj:
            raise HTTPException(status_code=400, detail="project_slug or project_id or INFISICAL_PROJECT_ID required")
        env = body.environment_slug or get_default_environment()
        path = body.path if body.path is not None else get_default_secret_path()
        from infisical_sdk import DynamicSecretProviders
        provider = getattr(DynamicSecretProviders, body.provider_type, body.provider_type)
        ds = client.dynamic_secrets.create(
            name=body.name,
            provider_type=provider,
            inputs=body.inputs,
            default_ttl=body.default_ttl,
            max_ttl=body.max_ttl,
            project_slug=proj,
            environment_slug=env,
            path=path,
        )
        return {"name": body.name, "message": "Dynamic secret created", "id": getattr(ds, "id", None)}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dynamic-secrets/{name}")
async def get_dynamic_secret_by_name(
    name: str,
    project_slug: Optional[str] = None,
    project_id: Optional[str] = None,
    environment_slug: Optional[str] = None,
    path: Optional[str] = None,
):
    """Get a dynamic secret by name."""
    try:
        client = get_client()
        proj = project_slug or project_id or get_default_project_id()
        if not proj:
            raise HTTPException(status_code=400, detail="project_slug or project_id or INFISICAL_PROJECT_ID required")
        env = environment_slug or get_default_environment()
        p = path if path is not None else get_default_secret_path()
        ds = client.dynamic_secrets.get_by_name(
            name=name,
            project_slug=proj,
            environment_slug=env,
            path=p,
        )
        return {"name": name, "id": getattr(ds, "id", None)}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class UpdateDynamicSecretRequest(BaseModel):
    project_slug: Optional[str] = None
    project_id: Optional[str] = None
    environment_slug: Optional[str] = None
    path: Optional[str] = None
    default_ttl: Optional[str] = None
    max_ttl: Optional[str] = None
    new_name: Optional[str] = None
    inputs: Optional[dict] = None


@router.put("/dynamic-secrets/{name}")
async def update_dynamic_secret(name: str, body: UpdateDynamicSecretRequest):
    """Update a dynamic secret."""
    try:
        client = get_client()
        proj = body.project_slug or body.project_id or get_default_project_id()
        if not proj:
            raise HTTPException(status_code=400, detail="project_slug or project_id or INFISICAL_PROJECT_ID required")
        env = body.environment_slug or get_default_environment()
        p = body.path if body.path is not None else get_default_secret_path()
        ds = client.dynamic_secrets.update(
            name=name,
            project_slug=proj,
            environment_slug=env,
            path=p,
            default_ttl=body.default_ttl,
            max_ttl=body.max_ttl,
            new_name=body.new_name,
            inputs=body.inputs,
        )
        return {"name": name, "message": "Dynamic secret updated"}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Folders ---


@router.get("/folders")
async def list_folders(
    project_id: Optional[str] = None,
    environment_slug: Optional[str] = None,
    path: Optional[str] = None,
    recursive: bool = False,
):
    """List folders."""
    try:
        client = get_client()
        pid = _project_id(project_id)
        env = environment_slug or get_default_environment()
        p = path if path is not None else get_default_secret_path()
        resp = client.folders.list_folders(
            project_id=pid,
            environment_slug=env,
            path=p,
            recursive=recursive,
        )
        items = []
        if hasattr(resp, "folders"):
            for f in resp.folders:
                items.append({"id": getattr(f, "id", None), "name": getattr(f, "name", None)})
        return {"folders": items}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateFolderRequest(BaseModel):
    project_id: Optional[str] = None
    environment_slug: Optional[str] = None
    path: Optional[str] = None
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


@router.post("/folders")
async def create_folder(body: CreateFolderRequest):
    """Create a folder."""
    try:
        client = get_client()
        pid = _project_id(body.project_id)
        env = body.environment_slug or get_default_environment()
        p = body.path if body.path is not None else get_default_secret_path()
        folder = client.folders.create_folder(
            name=body.name,
            environment_slug=env,
            project_id=pid,
            path=p,
            description=body.description,
        )
        return {"id": getattr(folder, "id", None), "name": body.name, "message": "Folder created"}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/folders/{folder_id}")
async def get_folder_by_id(folder_id: str):
    """Get a folder by ID."""
    try:
        client = get_client()
        folder = client.folders.get_folder_by_id(id=folder_id)
        return {"id": getattr(folder, "id", folder_id), "name": getattr(folder, "name", None)}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
