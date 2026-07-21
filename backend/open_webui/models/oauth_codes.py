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


class OAuthAuthorizationCode(Base):
    __tablename__ = "oauth_code"

    code = Column(String(255), primary_key=True)
    client_id = Column(String(255), nullable=False)
    user_id = Column(String(255), nullable=False)
    redirect_uri = Column(Text, nullable=False)
    scope = Column(String(255), nullable=False)
    state = Column(String(255), nullable=True)
    expires_at = Column(BigInteger, nullable=False)
    used = Column(Boolean, nullable=False, default=False)


class OAuthCodeModel(BaseModel):
    code: str
    client_id: str
    user_id: str
    redirect_uri: str
    scope: str
    state: Optional[str] = None
    expires_at: int
    used: bool = False

    model_config = ConfigDict(from_attributes=True)


class OAuthCodeTable:
    def create_code(
        self,
        client_id: str,
        user_id: str,
        redirect_uri: str,
        scope: str,
        state: Optional[str] = None,
        expires_in: int = 300,
    ) -> Optional[str]:
        """创建授权码,返回 code 字符串。"""
        code = secrets.token_urlsafe(48)
        expires_at = int(time.time()) + expires_in
        try:
            with get_db() as db:
                db.add(
                    OAuthAuthorizationCode(
                        code=code,
                        client_id=client_id,
                        user_id=user_id,
                        redirect_uri=redirect_uri,
                        scope=scope,
                        state=state,
                        expires_at=expires_at,
                        used=False,
                    )
                )
                db.commit()
                return code
        except Exception as e:
            log.error(f"create_code: {e}")
            return None

    def consume_code(self, code: str, redirect_uri: str) -> Optional[OAuthCodeModel]:
        """一次性消费授权码:标记 used=True,返回 model。过期、已用或 redirect_uri 不匹配返回 None。"""
        try:
            with get_db() as db:
                row = db.query(OAuthAuthorizationCode).filter_by(code=code).first()
                if row is None:
                    return None
                now = int(time.time())
                if row.used or row.expires_at < now:
                    return None
                if row.redirect_uri != redirect_uri:
                    return None
                row.used = True
                db.commit()
                db.refresh(row)
                return OAuthCodeModel.model_validate(row)
        except Exception as e:
            log.error(f"consume_code: {e}")
            return None


OAuthCodes = OAuthCodeTable()
