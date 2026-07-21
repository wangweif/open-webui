"""
OAuth 客户端管理 API (管理员)
- /api/v1/oauth/clients    CRUD
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from open_webui.models.oauth_clients import (
    OAuthClients,
    OAuthClientCreateForm,
    OAuthClientUpdateForm,
    OAuthClientResponse,
)
from open_webui.utils.auth import get_admin_user
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OAUTH"])

router = APIRouter()


class CreateClientResponse(BaseModel):
    client_id: str
    client_name: str
    client_secret: str  # 明文, 仅返回一次
    redirect_uris: str
    grant_types: str
    scope: str
    status: str
    created_at: int


@router.get("/clients")
async def list_clients(user=Depends(get_admin_user)):
    clients = OAuthClients.get_all_clients()
    return [
        {
            "client_id": c.client_id,
            "client_name": c.client_name,
            "redirect_uris": c.redirect_uris,
            "grant_types": c.grant_types,
            "scope": c.scope,
            "status": c.status,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
        }
        for c in clients
    ]


@router.post("/clients", response_model=CreateClientResponse)
async def create_client(form: OAuthClientCreateForm, user=Depends(get_admin_user)):
    if not form.client_id or not form.client_id.strip():
        raise HTTPException(status_code=400, detail="client_id is required")
    if not form.client_name or not form.client_name.strip():
        raise HTTPException(status_code=400, detail="client_name is required")
    if not form.redirect_uris or not form.redirect_uris.strip():
        raise HTTPException(status_code=400, detail="redirect_uris is required")

    existing = OAuthClients.get_client_by_id(form.client_id.strip())
    if existing:
        raise HTTPException(status_code=409, detail="Client ID already exists")

    client, plain_secret = OAuthClients.create_client(form)
    if client is None or plain_secret is None:
        raise HTTPException(status_code=500, detail="Failed to create client")

    return {
        "client_id": client.client_id,
        "client_name": client.client_name,
        "client_secret": plain_secret,
        "redirect_uris": client.redirect_uris,
        "grant_types": client.grant_types,
        "scope": client.scope,
        "status": client.status,
        "created_at": client.created_at,
    }


@router.get("/clients/{client_id}")
async def get_client(client_id: str, user=Depends(get_admin_user)):
    client = OAuthClients.get_client_by_id(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return {
        "client_id": client.client_id,
        "client_name": client.client_name,
        "redirect_uris": client.redirect_uris,
        "grant_types": client.grant_types,
        "scope": client.scope,
        "status": client.status,
        "created_at": client.created_at,
        "updated_at": client.updated_at,
    }


@router.post("/clients/{client_id}/update")
async def update_client(client_id: str, form: OAuthClientUpdateForm, user=Depends(get_admin_user)):
    client = OAuthClients.get_client_by_id(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    success = OAuthClients.update_client(client_id, form)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update client")
    return {"detail": "ok"}


@router.delete("/clients/{client_id}")
async def delete_client(client_id: str, user=Depends(get_admin_user)):
    client = OAuthClients.get_client_by_id(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    OAuthClients.delete_client(client_id)
    return {"detail": "ok"}


class ResetSecretResponse(BaseModel):
    client_secret: str


@router.post("/clients/{client_id}/reset-secret", response_model=ResetSecretResponse)
async def reset_secret(client_id: str, user=Depends(get_admin_user)):
    client = OAuthClients.get_client_by_id(client_id)
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    new_secret = OAuthClients.reset_secret(client_id)
    if new_secret is None:
        raise HTTPException(status_code=500, detail="Failed to reset secret")
    return {"client_secret": new_secret}
