"""
OAuth2 + OIDC 授权服务器路由
- /oauth/authorize           授权入口(未登录→302登录页, 已登录→返回内嵌授权确认页)
- /oauth/authorize/consent   用户确认授权(POST)
- /oauth/token               token 端点
- /oauth/userinfo            用户信息
- /oauth/introspect          token 校验
- /.well-known/openid-configuration  OIDC discovery
- /oauth/client-info/{client_id}  获取客户端名称(scopes)
"""

import logging
from typing import Optional
from urllib.parse import urlencode, urlparse

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel

from open_webui.models.oauth_clients import OAuthClients
from open_webui.models.oauth_codes import OAuthCodes, OAuthCodeModel
from open_webui.models.oauth_tokens import OAuthTokens
from open_webui.models.users import Users
from open_webui.models.user_logins import UserLogins
from open_webui.utils.auth import get_current_user, get_password_hash
from open_webui.utils.oauth_server import (
    generate_access_token,
    generate_id_token,
    verify_access_token,
    ACCESS_TOKEN_EXPIRES,
)
from open_webui.env import SRC_LOG_LEVELS

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["OAUTH"])

router = APIRouter()


def _build_issuer(request: Request) -> str:
    return f"{request.base_url.scheme}://{request.base_url.netloc}"


# ═══ Consent page HTML ═══

CONSENT_PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{app_name} - 授权登录</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: {bg};
    color: {text};
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 16px;
}}
.card {{
    background: {card_bg};
    border: 1px solid {border};
    border-radius: 16px;
    padding: 32px;
    width: 100%;
    max-width: 420px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
}}
.icon {{
    width: 56px; height: 56px;
    margin: 0 auto 16px;
    border-radius: 50%;
    background: {icon_bg};
    display: flex;
    align-items: center;
    justify-content: center;
}}
.icon svg {{ width: 28px; height: 28px; color: {icon_color}; }}
h1 {{ font-size: 20px; text-align: center; margin-bottom: 4px; color: {text}; }}
.sub {{ font-size: 13px; text-align: center; color: {text_secondary}; margin-bottom: 6px; }}
.sub strong {{ color: {text}; }}
.current-user {{
    text-align: center;
    font-size: 13px;
    color: {text_secondary};
    margin-bottom: 16px;
    padding: 8px 12px;
    background: {bg};
    border-radius: 8px;
    display: inline-block;
    width: 100%;
}}
.current-user .uname {{
    font-weight: 600;
    color: {text};
    margin-right: 6px;
}}
.scopes {{
    border-top: 1px solid {border};
    padding-top: 16px;
    margin-bottom: 24px;
}}
.scopes p {{ font-size: 13px; color: {text_secondary}; margin-bottom: 10px; }}
.scope-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: {text};
    padding: 4px 0;
}}
.scope-item svg {{ width: 16px; height: 16px; color: #16a34a; flex-shrink: 0; }}
.actions {{ display: flex; gap: 12px; }}
.btn {{
    flex: 1;
    padding: 11px 0;
    border-radius: 10px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    border: none;
    transition: all 0.15s;
}}
.btn-cancel {{
    background: transparent;
    border: 1px solid {border};
    color: {text};
}}
.btn-cancel:hover {{ background: {bg}; }}
.btn-approve {{
    background: #2563eb;
    color: #fff;
}}
.btn-approve:hover {{ background: #1d4ed8; }}
</style>
</head>
<body>
<div class="card">
    <div class="icon">
        <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
        </svg>
    </div>
    <h1>授权登录</h1>
    <p class="sub"><strong>{app_name}</strong> 请求访问你的账户信息</p>
    <div class="current-user">
        当前登录：<span class="uname">{username}</span>
    </div>
    <div class="scopes">
        <p>该应用将获取以下权限：</p>
        {scope_items}
    </div>
    <div class="actions">
        <button class="btn btn-cancel" onclick="deny()">取消</button>
        <button class="btn btn-approve" onclick="approve()">同意授权</button>
    </div>
</div>
<form id="f" method="post" action="{consent_url}">
    <input type="hidden" name="client_id" value="{client_id}">
    <input type="hidden" name="redirect_uri" value="{redirect_uri}">
    <input type="hidden" name="scope" value="{scope}">
    <input type="hidden" name="state" value="{state}">
    <input type="hidden" name="response_type" value="{response_type}">
</form>
<script>
function approve() {{ document.getElementById('f').submit(); }}
function deny() {{
    var p = new URLSearchParams({{ error: 'access_denied'{deny_state} }});
    window.location.href = '{redirect_uri}?' + p.toString();
}}
</script>
</body>
</html>"""

SCOPE_LABELS = {
    "openid": "身份标识（openid）",
    "profile": "用户基本信息（昵称、头像）",
    "email": "邮箱地址",
}

SCOPE_ITEM_HTML = '<div class="scope-item"><svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>{label}</div>'


def _build_consent_html(
    app_name: str,
    client_id: str,
    redirect_uri: str,
    scope: str,
    state: str,
    response_type: str,
    consent_url: str,
    username: str = "",
) -> str:
    scope_list = [s.strip() for s in scope.split() if s.strip()]
    scope_items_html = "".join(
        SCOPE_ITEM_HTML.format(label=SCOPE_LABELS.get(s, s)) for s in scope_list
    )
    deny_state = f", state: '{state}'" if state else ""
    return CONSENT_PAGE_TEMPLATE.format(
        app_name=app_name,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state or "",
        response_type=response_type,
        consent_url=consent_url,
        scope_items=scope_items_html,
        deny_state=deny_state,
        username=username,
        # Light/dark theme support
        bg="#f5f5f5",
        card_bg="#fff",
        text="#333",
        text_secondary="#666",
        border="#e0e0e0",
        icon_bg="#dbeafe",
        icon_color="#2563eb",
    )


# ═══ Shared helpers ════════════════════════════════════════════════


def _get_token(request: Request) -> Optional[str]:
    return request.cookies.get("token") or request.headers.get("Authorization", "").removeprefix("Bearer ").strip()


def _redirect_to_login(client_id, redirect_uri, response_type, scope, state):
    """302 到 /auth 登录页, 登录后回跳 /oauth/authorize"""
    params = urlencode(
        {k: v for k, v in [
            ("client_id", client_id), ("redirect_uri", redirect_uri),
            ("response_type", response_type), ("scope", scope), ("state", state or ""),
        ] if v}
    )
    redirect_target = f"/oauth/authorize?{params}"
    from urllib.parse import quote
    redirect_url = f"/auth?redirect={quote(redirect_target, safe='')}"
    return RedirectResponse(redirect_url, status_code=302)


def _authenticate(request: Request):
    """从 cookie 验证当前用户，返回 UserModel 或 None"""
    from open_webui.utils.auth import decode_token

    token = _get_token(request)
    if not token:
        return None
    data = decode_token(token)
    if not data or "id" not in data:
        return None
    user = Users.get_user_by_id(data["id"])
    if user is None or user.is_guest:
        return None
    return user


def _validate_oauth_request(client_id: str, redirect_uri: str):
    """校验 client 和 redirect_uri, 返回 (error_response, client)。error_response 为 None 表示通过。"""
    client = OAuthClients.get_client_by_id(client_id)
    if client is None or client.status != "active":
        return JSONResponse({"detail": "Invalid client_id"}, status_code=400), None
    if not OAuthClients.check_redirect_uri(client_id, redirect_uri):
        return JSONResponse({"detail": "Invalid redirect_uri"}, status_code=400), None
    return None, client


# ═══ GET /oauth/authorize ══════════════════════════════════════════


@router.get("/authorize")
async def authorize(
    request: Request,
    client_id: Optional[str] = None,
    redirect_uri: Optional[str] = None,
    response_type: str = "code",
    scope: str = "openid profile",
    state: Optional[str] = None,
):
    if not client_id or not redirect_uri:
        return JSONResponse({"detail": "Missing client_id or redirect_uri"}, status_code=400)
    if response_type != "code":
        return RedirectResponse(f"{redirect_uri}?error=unsupported_response_type&state={state or ''}")

    err, client = _validate_oauth_request(client_id, redirect_uri)
    if err:
        return err

    user = _authenticate(request)
    if user is None:
        resp = _redirect_to_login(client_id, redirect_uri, response_type, scope, state)
        if _get_token(request):
            resp.delete_cookie("token")
        return resp

    consent_url = f"{request.base_url.scheme}://{request.base_url.netloc}/oauth/authorize/consent"
    html = _build_consent_html(
        app_name=client.client_name or client_id,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state or "",
        response_type=response_type,
        consent_url=consent_url,
        username=user.name or user.email,
    )
    return HTMLResponse(html)


# ═══ POST /oauth/authorize/consent ═════════════════════════════════


@router.post("/authorize/consent")
async def authorize_consent(
    request: Request,
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: str = Form("openid profile"),
    state: Optional[str] = Form(None),
    response_type: str = Form("code"),
):
    err, _ = _validate_oauth_request(client_id, redirect_uri)
    if err:
        return err

    user = _authenticate(request)
    if user is None:
        resp = _redirect_to_login(client_id, redirect_uri, response_type, scope, state)
        if _get_token(request):
            resp.delete_cookie("token")
        return resp

    code = OAuthCodes.create_code(client_id=client_id, user_id=user.id,
                                   redirect_uri=redirect_uri, scope=scope, state=state)
    if code is None:
        return JSONResponse({"detail": "Failed to create authorization code"}, status_code=500)

    params = {"code": code}
    if state:
        params["state"] = state
    return RedirectResponse(f"{redirect_uri}?{urlencode(params)}", status_code=302)


# ─── POST /oauth/token ───────────────────────────────────────────


class TokenRequest(BaseModel):
    grant_type: str
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    code: Optional[str] = None
    redirect_uri: Optional[str] = None
    refresh_token: Optional[str] = None


@router.post("/token")
async def token(request: Request, body: TokenRequest):
    # 支持 client 凭证在 body 或 Authorization header(Basic)
    client_id = body.client_id
    client_secret = body.client_secret

    if (not client_id or not client_secret) and request.headers.get("Authorization", "").startswith("Basic "):
        import base64
        auth_val = request.headers["Authorization"][len("Basic "):]
        try:
            decoded = base64.b64decode(auth_val).decode("utf-8")
            client_id, client_secret = decoded.split(":", 1)
        except Exception:
            return JSONResponse({"error": "invalid_client"}, status_code=401)

    if not client_id or not client_secret:
        return JSONResponse({"error": "invalid_client"}, status_code=401)

    client = OAuthClients.verify_client(client_id, client_secret)
    if client is None:
        return JSONResponse({"error": "invalid_client"}, status_code=401)

    issuer = _build_issuer(request)

    if body.grant_type == "authorization_code":
        if not body.code or not body.redirect_uri:
            return JSONResponse({"error": "invalid_request"}, status_code=400)

        code_data = OAuthCodes.consume_code(body.code, body.redirect_uri)
        if code_data is None:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)

        if code_data.client_id != client_id:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)

        user = Users.get_user_by_id(code_data.user_id)
        if user is None:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)

        access_token = generate_access_token(
            user_id=user.id,
            username=user.name,
            nickname=user.name,
            email=user.email,
            client_id=client_id,
            scope=code_data.scope,
            issuer=issuer,
        )
        refresh_token = OAuthTokens.create_token(
            client_id=client_id,
            user_id=user.id,
            scope=code_data.scope,
        )
        id_token = generate_id_token(
            user_id=user.id,
            username=user.name,
            nickname=user.name,
            email=user.email,
            client_id=client_id,
            scope=code_data.scope,
            issuer=issuer,
        )

        # 记录登录日志
        UserLogins.record_login(
            user_id=user.id,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent", ""),
            login_method="oauth",
            success=True,
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRES,
            "token_type": "Bearer",
            "id_token": id_token,
        }

    elif body.grant_type == "refresh_token":
        if not body.refresh_token:
            return JSONResponse({"error": "invalid_request"}, status_code=400)

        old_rt = OAuthTokens.get_valid_token(body.refresh_token)
        if old_rt is None:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)

        if old_rt.client_id != client_id:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)

        # 轮换:撤销旧 token
        OAuthTokens.revoke_token(body.refresh_token)

        user = Users.get_user_by_id(old_rt.user_id)
        if user is None:
            return JSONResponse({"error": "invalid_grant"}, status_code=400)

        access_token = generate_access_token(
            user_id=user.id,
            username=user.name,
            nickname=user.name,
            email=user.email,
            client_id=client_id,
            scope=old_rt.scope,
            issuer=issuer,
        )
        new_refresh_token = OAuthTokens.create_token(
            client_id=client_id,
            user_id=user.id,
            scope=old_rt.scope,
        )

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_in": ACCESS_TOKEN_EXPIRES,
            "token_type": "Bearer",
        }

    else:
        return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)


# ─── GET /oauth/userinfo ─────────────────────────────────────────


@router.get("/userinfo")
@router.post("/userinfo")
async def userinfo(request: Request):
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse({"error": "invalid_token"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})

    token = auth_header[len("Bearer "):]
    data = verify_access_token(token)
    if data is None:
        return JSONResponse({"error": "invalid_token"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})

    user = Users.get_user_by_id(data["sub"])
    if user is None:
        return JSONResponse({"error": "invalid_token"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})

    return {
        "sub": user.id,
        "username": user.name,
        "nickname": user.name,
        "email": user.email,
        "picture": user.profile_image_url or "",
    }


# ─── POST /oauth/introspect ─────────────────────────────────────


@router.post("/introspect")
async def introspect(request: Request):
    # 校验 client 凭证
    client_id, client_secret = None, None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Basic "):
        import base64
        auth_val = auth_header[len("Basic "):]
        try:
            decoded = base64.b64decode(auth_val).decode("utf-8")
            client_id, client_secret = decoded.split(":", 1)
        except Exception:
            pass

    # 也支持 body 中传
    try:
        body = await request.json()
        if not client_id:
            client_id = body.get("client_id")
        if not client_secret:
            client_secret = body.get("client_secret")
        token = body.get("token")
    except Exception:
        return {"active": False}

    if not client_id or not client_secret or not token:
        return {"active": False}

    client = OAuthClients.verify_client(client_id, client_secret)
    if client is None:
        return {"active": False}

    data = verify_access_token(token)
    if data is None:
        return {"active": False}

    return {
        "active": True,
        "sub": data["sub"],
        "scope": data.get("scope", ""),
        "client_id": data.get("client_id", ""),
        "exp": data.get("exp"),
        "username": data.get("username", ""),
    }


# ─── GET /.well-known/openid-configuration ──────────────────────


@router.get("/.well-known/openid-configuration")
async def openid_configuration(request: Request):
    issuer = _build_issuer(request)
    base = f"{issuer}/oauth"
    return {
        "issuer": issuer,
        "authorization_endpoint": f"{base}/authorize",
        "token_endpoint": f"{base}/token",
        "userinfo_endpoint": f"{base}/userinfo",
        "introspection_endpoint": f"{base}/introspect",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "token_endpoint_auth_methods_supported": ["client_secret_basic", "client_secret_post"],
        "scopes_supported": ["openid", "profile", "email"],
    }


# ─── GET /oauth/jwks.json ─────────────────────────────────────────
# HS256 不提供 JWKS,返回空 keys。


@router.get("/jwks.json")
async def jwks():
    return {"keys": []}


# ─── GET /oauth/client-info/{client_id} ──────────────────────────


@router.get("/client-info/{client_id}")
async def client_info(client_id: str):
    """返回客户端名称(给consent页展示用),不暴露 secret。"""
    client = OAuthClients.get_client_by_id(client_id)
    if client is None:
        return JSONResponse({"detail": "Client not found"}, status_code=404)
    return {
        "client_id": client.client_id,
        "client_name": client.client_name,
        "scope": client.scope,
    }
