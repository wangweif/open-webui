import datetime
import logging
import time
import uuid
from typing import Optional
from urllib.parse import quote

import requests
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from open_webui.config import BASE_TEAM_ID, TENANT_ID

from open_webui.env import (
    ENABLE_SEEYON_SSO,
    SEEYON_SSO_VALIDATE_URL,
    SEEYON_SSO_TIMEOUT,
    SEEYON_SSO_VERIFY_SSL,
    SEEYON_SSO_EMAIL_SUFFIX,
    SEEYON_SSO_DEFAULT_ROLE,
    SRC_LOG_LEVELS,
    WEBUI_AUTH_COOKIE_SAME_SITE,
    WEBUI_AUTH_COOKIE_SECURE,
)
from open_webui.models.auths import Auths
from open_webui.models.users import Users
from open_webui.models.user_logins import UserLogins
from open_webui.utils.auth import create_token
from open_webui.utils.misc import parse_duration, validate_email_format
from open_webui.utils.ragflow_assistant import (
    create_assistant,
    assign_base_kb_permission,
    add_user_to_user_tenant,
)
from open_webui.routers.groups import add_user_to_tourist_group

router = APIRouter()

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MAIN"])

SSO_LOGIN_METHOD = "seeyon_sso"
SSO_OAUTH_SUB_PREFIX = "seeyon:"


def _get_client_ip(request: Request) -> str:
    """获取客户端真实 IP（兼容反向代理）。"""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


def _fetch_oa_user(ticket: str) -> Optional[dict]:
    """回调 OA 校验接口，用 ticket 换取用户信息。

    返回 {"login_name", "member_id", "member_name"}；校验失败返回 None。
    """
    url = SEEYON_SSO_VALIDATE_URL
    try:
        resp = requests.get(
            url,
            params={"ticket": ticket},
            timeout=SEEYON_SSO_TIMEOUT,
            verify=SEEYON_SSO_VERIFY_SSL,
        )
    except Exception as exc:
        log.error(f"Seeyon SSO: 回调 OA 校验接口失败: {exc}")
        return None

    if resp.status_code != 200:
        log.error(f"Seeyon SSO: OA 校验接口返回非 200: status={resp.status_code}")
        return None

    # 失败标识兼容两种表达：响应头 SSOLogoutError / 响应体 SSOLogoutError
    if resp.headers.get("SSOLogoutError") or resp.text.strip() == "SSOLogoutError":
        log.warning("Seeyon SSO: OA 校验接口返回失败标识 SSOLogoutError")
        return None

    login_name = (resp.headers.get("LoginName") or "").strip()
    if not login_name:
        # 兜底：部分版本响应体正文即登录名（text/plain）
        body = resp.text.strip()
        if body and body not in ("SSOOK", "SSOLogoutError"):
            login_name = body

    if not login_name:
        log.error("Seeyon SSO: OA 校验接口未返回 LoginName")
        return None

    return {
        "login_name": login_name,
        "member_id": (resp.headers.get("MemberId") or "").strip(),
        "member_name": (resp.headers.get("MemberName") or "").strip(),
    }


async def _resolve_or_create_user(login_name: str, member_name: str):
    """根据 OA 登录名解析或自动创建本地用户。"""
    oauth_sub = f"{SSO_OAUTH_SUB_PREFIX}{login_name}"

    # 1) 优先按 oauth_sub 匹配（避免本地 email 变更后重复建号）
    user = Users.get_user_by_oauth_sub(oauth_sub)
    if user:
        return user

    email = login_name.lower()
    if not validate_email_format(email):
        if SEEYON_SSO_EMAIL_SUFFIX:
            email = f"{login_name}@{SEEYON_SSO_EMAIL_SUFFIX}".lower()
        else:
            email = f"{login_name}@localhost"

    # 2) 按 email 匹配已有用户
    user = Users.get_user_by_email(email)
    if user:
        return user

    # 3) 自动开户（随机密码，SSO 用户不使用密码登录）
    user = Auths.insert_new_auth(
        email=email,
        password=str(uuid.uuid4()),
        name=member_name or login_name,
        role=SEEYON_SSO_DEFAULT_ROLE,
        oauth_sub=oauth_sub,
        team_id=BASE_TEAM_ID,
        tenant_id=TENANT_ID,
    )
    if user:
        log.info(
            f"Seeyon SSO: 已自动创建用户 email={user.email} name={user.name}"
        )
        # 用户开通：分配知识库权限 + 添加到租户 + 加游客组 + 创建助手（与注册逻辑一致）
        await assign_base_kb_permission(user.ragflow_user_id)
        await add_user_to_user_tenant(TENANT_ID, user.ragflow_user_id)
        await add_user_to_tourist_group(user.id)
        assistant_id = await create_assistant(user.ragflow_user_id)
        Users.update_user_by_id(user.id, {"assistant_id": assistant_id})
    return user


def _login_redirect_url(request: Request, token: str, redirect: str = "") -> str:
    """跳转前端 /auth 完成会话；支持深链 redirect（仅允许站内相对路径）。"""
    base = str(request.base_url)
    if redirect and redirect.startswith("/") and not redirect.startswith("//"):
        # 前端 /auth 页面从 query string 读取 redirect 参数
        quoted_redirect = quote(redirect, safe="")
        return f"{base}auth?redirect={quoted_redirect}#token={token}"
    return f"{base}auth#token={token}"


@router.get("/sso/seeyon/login")
async def seeyon_sso_login(
    request: Request, ticket: str = "", redirect: str = ""
):
    """致远 OA 单点登录入口（单地址模式）。

    OA 点击页签/菜单时把浏览器重定向到本地址并拼接 ?ticket=XXX；
    本接口回调 OA 校验接口（thirdpartyController.do）换取用户信息，
    自动开户并直接登录（写 JWT Cookie），随后 302 到前端 /auth#token=... 完成会话。
    """
    login_page = f"{request.base_url}auth"

    if not ENABLE_SEEYON_SSO:
        log.warning("Seeyon SSO: 未启用（ENABLE_SEEYON_SSO=false），跳转登录页")
        return RedirectResponse(url=login_page)

    if not ticket:
        log.warning("Seeyon SSO: 缺少 ticket 参数")
        return RedirectResponse(url=login_page)

    info = _fetch_oa_user(ticket)
    if not info:
        log.error("Seeyon SSO: ticket 校验失败，跳转登录页")
        return RedirectResponse(url=login_page)

    user = await _resolve_or_create_user(info["login_name"], info["member_name"])
    if not user:
        log.error("Seeyon SSO: 用户解析/创建失败，跳转登录页")
        return RedirectResponse(url=login_page)

    expires_delta = parse_duration(request.app.state.config.JWT_EXPIRES_IN)
    expires_at = None
    if expires_delta:
        expires_at = int(time.time()) + int(expires_delta.total_seconds())

    token = create_token(data={"id": user.id}, expires_delta=expires_delta)

    datetime_expires_at = (
        datetime.datetime.fromtimestamp(expires_at, datetime.timezone.utc)
        if expires_at
        else None
    )

    response = RedirectResponse(
        url=_login_redirect_url(request, token, redirect)
    )
    response.set_cookie(
        key="token",
        value=token,
        expires=datetime_expires_at,
        httponly=True,  # Ensures the cookie is not accessible via JavaScript
        samesite=WEBUI_AUTH_COOKIE_SAME_SITE,
        secure=WEBUI_AUTH_COOKIE_SECURE,
    )

    try:
        UserLogins.record_login(
            user_id=user.id,
            ip_address=_get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            login_method=SSO_LOGIN_METHOD,
            success=True,
        )
    except Exception as exc:
        log.error(f"Seeyon SSO: 记录登录日志失败: {exc}")

    log.info(f"Seeyon SSO: 用户 {user.email} 单点登录成功")
    return response
