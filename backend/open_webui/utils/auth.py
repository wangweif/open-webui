import logging
import uuid
import jwt
import base64
import hmac
import hashlib
import requests
import os


from datetime import datetime, timedelta
import pytz
from pytz import UTC
from typing import Optional, Union, List, Dict

from open_webui.models.users import Users
from open_webui.models.groups import Groups

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import (
    WEBUI_SECRET_KEY,
    TRUSTED_SIGNATURE_KEY,
    STATIC_DIR,
    SRC_LOG_LEVELS,
)

from fastapi import BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext


logging.getLogger("passlib").setLevel(logging.ERROR)

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OAUTH"])

SESSION_SECRET = WEBUI_SECRET_KEY
ALGORITHM = "HS256"

##############
# Auth Utils
##############


def verify_signature(payload: str, signature: str) -> bool:
    """
    Verifies the HMAC signature of the received payload.
    """
    try:
        expected_signature = base64.b64encode(
            hmac.new(TRUSTED_SIGNATURE_KEY, payload.encode(), hashlib.sha256).digest()
        ).decode()

        # Compare securely to prevent timing attacks
        return hmac.compare_digest(expected_signature, signature)

    except Exception:
        return False


def override_static(path: str, content: str):
    # Ensure path is safe
    if "/" in path or ".." in path:
        log.error(f"Invalid path: {path}")
        return

    file_path = os.path.join(STATIC_DIR, path)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(content))  # Convert Base64 back to raw binary


def get_license_data(app, key):
    if key:
        try:
            res = requests.post(
                "https://api.openwebui.com/api/v1/license/",
                json={"key": key, "version": "1"},
                timeout=5,
            )

            if getattr(res, "ok", False):
                payload = getattr(res, "json", lambda: {})()
                for k, v in payload.items():
                    if k == "resources":
                        for p, c in v.items():
                            globals().get("override_static", lambda a, b: None)(p, c)
                    elif k == "count":
                        setattr(app.state, "USER_COUNT", v)
                    elif k == "name":
                        setattr(app.state, "WEBUI_NAME", v)
                    elif k == "metadata":
                        setattr(app.state, "LICENSE_METADATA", v)
                return True
            else:
                log.error(
                    f"License: retrieval issue: {getattr(res, 'text', 'unknown error')}"
                )
        except Exception as ex:
            log.exception(f"License: Uncaught Exception: {ex}")
    return False


bearer_security = HTTPBearer(auto_error=False)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return (
        pwd_context.verify(plain_password, hashed_password) if hashed_password else None
    )


def get_password_hash(password):
    return pwd_context.hash(password)


def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
    """
    验证密码强度
    要求：
    - 最少8位
    - 由大写、小写、数字、特殊字符中的3种及以上组成
    
    返回: (是否有效, 错误消息)
    """
    if len(password) < 8:
        return False, "密码长度至少需要8位"
    
    # 检查字符类型
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" for c in password)
    
    type_count = sum([has_upper, has_lower, has_digit, has_special])
    
    if type_count < 3:
        return False, "密码必须包含大写字母、小写字母、数字、特殊字符中的至少3种"
    
    return True, None


def is_password_expired(password_changed_at: Optional[int], days: int = 90) -> bool:
    """
    检查密码是否过期
    password_changed_at: 密码最后修改时间（时间戳）
    days: 密码有效期（天数），默认90天
    返回: True表示已过期，False表示未过期
    """
    if password_changed_at is None:
        # 如果没有记录修改时间，认为未过期（兼容旧数据）
        return False
    
    import time
    current_time = int(time.time())
    days_in_seconds = days * 24 * 60 * 60
    return (current_time - password_changed_at) > days_in_seconds


def create_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    payload = data.copy()

    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
        payload.update({"exp": expire})

    encoded_jwt = jwt.encode(payload, SESSION_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    try:
        decoded = jwt.decode(token, SESSION_SECRET, algorithms=[ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        return None
    except Exception:
        return None


def extract_token_from_auth_header(auth_header: str):
    return auth_header[len("Bearer ") :]


def create_api_key():
    key = str(uuid.uuid4()).replace("-", "")
    return f"sk-{key}"


def get_http_authorization_cred(auth_header: Optional[str]):
    if not auth_header:
        return None
    try:
        scheme, credentials = auth_header.split(" ")
        return HTTPAuthorizationCredentials(scheme=scheme, credentials=credentials)
    except Exception:
        return None


def get_current_user(
    request: Request,
    background_tasks: BackgroundTasks,
    auth_token: HTTPAuthorizationCredentials = Depends(bearer_security),
):
    token = None

    if auth_token is not None:
        token = auth_token.credentials

    if token is None and "token" in request.cookies:
        token = request.cookies.get("token")

    if token is None:
        raise HTTPException(status_code=403, detail="Not authenticated")

    # auth by api key
    if token.startswith("sk-"):
        if not request.state.enable_api_key:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.API_KEY_NOT_ALLOWED
            )

        if request.app.state.config.ENABLE_API_KEY_ENDPOINT_RESTRICTIONS:
            allowed_paths = [
                path.strip()
                for path in str(
                    request.app.state.config.API_KEY_ALLOWED_ENDPOINTS
                ).split(",")
            ]

            # Check if the request path matches any allowed endpoint.
            if not any(
                request.url.path == allowed
                or request.url.path.startswith(allowed + "/")
                for allowed in allowed_paths
            ):
                raise HTTPException(
                    status.HTTP_403_FORBIDDEN, detail=ERROR_MESSAGES.API_KEY_NOT_ALLOWED
                )

        return get_current_user_by_api_key(token)

    # auth by jwt token
    try:
        data = decode_token(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    if data is None:
        # Token无效或已过期
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.INVALID_TOKEN,
        )

    if "id" in data:
        user = Users.get_user_by_id(data["id"])
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ERROR_MESSAGES.INVALID_TOKEN,
            )
        else:
            # Refresh the user's last active timestamp asynchronously
            # to prevent blocking the request
            if background_tasks:
                background_tasks.add_task(Users.update_user_last_active_by_id, user.id)
        return user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.UNAUTHORIZED,
        )


def get_current_user_by_api_key(api_key: str):
    user = Users.get_user_by_api_key(api_key)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.INVALID_TOKEN,
        )
    else:
        Users.update_user_last_active_by_id(user.id)

    return user


def get_verified_user(user=Depends(get_current_user)):
    if user.role not in {"user", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return user


def get_admin_user(user=Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )
    return user


def get_audit_user(user=Depends(get_current_user)):
    """
    检查用户是否是审计用户
    审计用户是指属于审计权限组的用户
    """
    
    # 检查用户是否属于审计权限组
    try:
        user_groups = Groups.get_groups_by_member_id(user.id)
        user_group_names = [group.name for group in user_groups]
        # 检查用户的任何组是否在审计权限组列表中
        if any(group_name == "审计" for group_name in user_group_names):
            return user
    except Exception as e:
        log = logging.getLogger(__name__)
        log.error(f"检查用户是否属于审计权限组错误: {str(e)}", exc_info=True)
    
    # 不属于审计权限组，拒绝访问
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
    )


def get_security_admin_user(user=Depends(get_current_user)):
    """
    检查用户是否是安全管理员
    安全管理员是指属于安全管理员组的用户
    """
    
    # 检查用户是否属于安全管理员组
    try:
        user_groups = Groups.get_groups_by_member_id(user.id)
        user_group_names = [group.name for group in user_groups]
        # 检查用户的任何组是否在安全管理员组列表中
        if any(group_name == "安全管理员" for group_name in user_group_names):
            return user
    except Exception as e:
        log = logging.getLogger(__name__)
        log.error(f"检查用户是否属于安全管理员组错误: {str(e)}", exc_info=True)
    
    # 不属于安全管理员组，拒绝访问
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
    )