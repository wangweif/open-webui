import logging
import time
from datetime import datetime, timedelta
from typing import Optional

from open_webui.utils.auth import create_token, decode_token, SESSION_SECRET, ALGORITHM
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OAUTH"])

ACCESS_TOKEN_EXPIRES = 7200  # 2 小时
ID_TOKEN_EXPIRES = 3600      # 1 小时


def generate_access_token(
    user_id: str,
    username: str,
    nickname: str,
    email: str,
    client_id: str,
    scope: str,
    issuer: str,
) -> str:
    """签发 OAuth access_token (JWT, HS256)。"""
    now = datetime.now(tz=None)
    now_ts = int(now.timestamp())
    payload = {
        "sub": user_id,
        "username": username,
        "nickname": nickname,
        "email": email,
        "client_id": client_id,
        "scope": scope,
        "iss": issuer,
        "iat": now_ts,
        "exp": now_ts + ACCESS_TOKEN_EXPIRES,
        "type": "access_token",
    }
    return create_token(payload, expires_delta=timedelta(seconds=ACCESS_TOKEN_EXPIRES))


def generate_id_token(
    user_id: str,
    username: str,
    nickname: str,
    email: str,
    client_id: str,
    scope: str,
    issuer: str,
) -> str:
    """签发 OIDC id_token (JWT, HS256)。"""
    now = datetime.now(tz=None)
    now_ts = int(now.timestamp())
    payload = {
        "sub": user_id,
        "username": username,
        "nickname": nickname,
        "email": email,
        "aud": client_id,
        "iss": issuer,
        "iat": now_ts,
        "exp": now_ts + ID_TOKEN_EXPIRES,
    }
    return create_token(payload, expires_delta=timedelta(seconds=ID_TOKEN_EXPIRES))


def verify_access_token(token: str) -> Optional[dict]:
    """解码 access_token,校验 type=access_token。"""
    data = decode_token(token)
    if data is None:
        return None
    if data.get("type") != "access_token":
        return None
    return data
