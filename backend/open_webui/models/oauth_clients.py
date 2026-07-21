import logging
import secrets
import time
from typing import List, Optional

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from open_webui.utils.auth import get_password_hash
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, String, Text

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


class OAuthClient(Base):
    __tablename__ = "oauth_client"

    client_id = Column(String(255), primary_key=True)
    client_secret = Column(Text, nullable=False)
    client_name = Column(String(255), nullable=False)
    redirect_uris = Column(Text, nullable=False)
    grant_types = Column(String(255), nullable=False)
    scope = Column(String(255), nullable=False)
    status = Column(String(20), nullable=False)
    created_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)


class OAuthClientModel(BaseModel):
    client_id: str
    client_secret: str
    client_name: str
    redirect_uris: str
    grant_types: str = "authorization_code,refresh_token"
    scope: str = "openid profile"
    status: str = "active"
    created_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class OAuthClientResponse(BaseModel):
    client_id: str
    client_name: str
    redirect_uris: str
    grant_types: str
    scope: str
    status: str
    created_at: int
    updated_at: int


class OAuthClientCreateForm(BaseModel):
    client_id: str
    client_name: str
    redirect_uris: str
    grant_types: Optional[str] = "authorization_code,refresh_token"
    scope: Optional[str] = "openid profile"


class OAuthClientUpdateForm(BaseModel):
    client_name: Optional[str] = None
    redirect_uris: Optional[str] = None
    grant_types: Optional[str] = None
    scope: Optional[str] = None
    status: Optional[str] = None


class OAuthClientsTable:
    def create_client(self, form: OAuthClientCreateForm) -> tuple[Optional[OAuthClientModel], Optional[str]]:
        """创建客户端,返回(model, 明文secret) tuple。secret仅此时返回一次。"""
        plain_secret = secrets.token_urlsafe(48)
        hashed_secret = get_password_hash(plain_secret)
        now = int(time.time())
        client = OAuthClientModel(
            client_id=form.client_id.strip(),
            client_secret=hashed_secret,
            client_name=form.client_name.strip(),
            redirect_uris=form.redirect_uris.strip(),
            grant_types=form.grant_types or "authorization_code,refresh_token",
            scope=form.scope or "openid profile",
            status="active",
            created_at=now,
            updated_at=now,
        )
        try:
            with get_db() as db:
                db.add(OAuthClient(**client.model_dump()))
                db.commit()
                return client, plain_secret
        except Exception as e:
            log.error(f"create_client: {e}")
            return None, None

    def get_client_by_id(self, client_id: str) -> Optional[OAuthClientModel]:
        try:
            with get_db() as db:
                row = db.query(OAuthClient).filter_by(client_id=client_id).first()
                return OAuthClientModel.model_validate(row) if row else None
        except Exception as e:
            log.error(f"get_client_by_id: {e}")
            return None

    def get_all_clients(self) -> List[OAuthClientModel]:
        try:
            with get_db() as db:
                rows = db.query(OAuthClient).all()
                return [OAuthClientModel.model_validate(r) for r in rows]
        except Exception as e:
            log.error(f"get_all_clients: {e}")
            return []

    def update_client(self, client_id: str, form: OAuthClientUpdateForm) -> bool:
        try:
            with get_db() as db:
                values = {"updated_at": int(time.time())}
                for k in ("client_name", "redirect_uris", "grant_types", "scope", "status"):
                    v = getattr(form, k, None)
                    if v is not None:
                        values[k] = v
                db.query(OAuthClient).filter_by(client_id=client_id).update(values)
                db.commit()
                return True
        except Exception as e:
            log.error(f"update_client: {e}")
            return False

    def delete_client(self, client_id: str) -> bool:
        try:
            with get_db() as db:
                db.query(OAuthClient).filter_by(client_id=client_id).delete()
                db.commit()
                return True
        except Exception as e:
            log.error(f"delete_client: {e}")
            return False

    def reset_secret(self, client_id: str) -> Optional[str]:
        """重置 client_secret,返回新的明文。"""
        plain_secret = secrets.token_urlsafe(48)
        hashed_secret = get_password_hash(plain_secret)
        try:
            with get_db() as db:
                db.query(OAuthClient).filter_by(client_id=client_id).update(
                    {"client_secret": hashed_secret, "updated_at": int(time.time())}
                )
                db.commit()
                return plain_secret
        except Exception as e:
            log.error(f"reset_secret: {e}")
            return None

    def verify_client(self, client_id: str, client_secret: str) -> Optional[OAuthClientModel]:
        """校验 client_id + client_secret。客户端 inactive 则返回 None。"""
        from open_webui.utils.auth import verify_password

        client = self.get_client_by_id(client_id)
        if client is None or client.status != "active":
            return None
        if not verify_password(client_secret, client.client_secret):
            return None
        return client

    def check_redirect_uri(self, client_id: str, redirect_uri: str) -> bool:
        """检查 redirect_uri 是否在客户端注册的列表中(完全匹配)。"""
        client = self.get_client_by_id(client_id)
        if client is None:
            return False
        allowed = [u.strip() for u in client.redirect_uris.split(",")]
        return redirect_uri.strip() in allowed


OAuthClients = OAuthClientsTable()
