import logging
import secrets
import time
from typing import Optional

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Boolean, Column, String, Text

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


class OAuthRefreshToken(Base):
    __tablename__ = "oauth_refresh_token"

    token = Column(String(255), primary_key=True)
    client_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    scope = Column(String(255), nullable=False)
    expires_at = Column(BigInteger, nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)


class OAuthRefreshTokenModel(BaseModel):
    token: str
    client_id: str
    user_id: str
    scope: str
    expires_at: int
    revoked: bool = False

    model_config = ConfigDict(from_attributes=True)


class OAuthRefreshTokenTable:
    def create_token(
        self,
        client_id: str,
        user_id: str,
        scope: str,
        expires_in: int = 30 * 24 * 3600,
    ) -> Optional[str]:
        """创建 refresh token,返回 token 字符串。默认 30 天。"""
        token = secrets.token_urlsafe(64)
        expires_at = int(time.time()) + expires_in
        try:
            with get_db() as db:
                db.add(
                    OAuthRefreshToken(
                        token=token,
                        client_id=client_id,
                        user_id=user_id,
                        scope=scope,
                        expires_at=expires_at,
                        revoked=False,
                    )
                )
                db.commit()
                return token
        except Exception as e:
            log.error(f"create_token: {e}")
            return None

    def get_valid_token(self, token: str) -> Optional[OAuthRefreshTokenModel]:
        """获取有效的 refresh token。过期/revoked 返回 None。"""
        try:
            with get_db() as db:
                row = db.query(OAuthRefreshToken).filter_by(token=token, revoked=False).first()
                if row is None:
                    return None
                if row.expires_at < int(time.time()):
                    return None
                return OAuthRefreshTokenModel.model_validate(row)
        except Exception as e:
            log.error(f"get_valid_token: {e}")
            return None

    def revoke_token(self, token: str) -> bool:
        try:
            with get_db() as db:
                db.query(OAuthRefreshToken).filter_by(token=token).update({"revoked": True})
                db.commit()
                return True
        except Exception as e:
            log.error(f"revoke_token: {e}")
            return False


OAuthTokens = OAuthRefreshTokenTable()
