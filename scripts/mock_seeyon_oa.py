#!/usr/bin/env python3
"""Mock 致远OA ticket 校验接口 —— 无 OA 环境时本地模拟联调 SSO。

用法:
    python3 scripts/mock_seeyon_oa.py           # 默认 0.0.0.0:18080
    python3 scripts/mock_seeyon_oa.py 18081     # 指定端口

测试时把根目录 .env 里的 SEEYON_SSO_VALIDATE_URL 指向本 mock:
    SEEYON_SSO_VALIDATE_URL=http://127.0.0.1:18080/seeyon/thirdpartyController.do

然后浏览器访问(用你自己的后端地址):
    http://127.0.0.1:8081/api/v1/auths/sso/seeyon/login?ticket=test1
    -> 应 307 跳转到 /auth#token=... 即登录成功

模拟规则:
    ticket=test1 / test2        -> 正常返回 LoginName/MemberId/MemberName
    ticket=任意其它值           -> 返回默认用户 bjzhangzm/张三
    ticket=bad...               -> 返回 403(模拟非200失败)
    ticket=logout...            -> 返回 SSOLogoutError 头(模拟校验失败)
"""

import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

# ticket -> (LoginName, MemberName, MemberId)
# 注意: HTTP 响应头只支持 latin-1, MemberName 用 ASCII 避免中文乱码/报错
#       (真实 OA 若回中文姓名, 展示名可能乱码, 仅展示用, 不影响登录)
USERS = {
    "test1": ("bjzhangzm", "Zhang San", "1854279181896270886"),
    "test2": ("lisi@bjny.org.cn", "Li Si", "1854279181896270887"),
}
DEFAULT_USER = ("bjzhangzm", "Zhang San", "1854279181896270886")

HOST = "0.0.0.0"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 18080


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/seeyon/thirdpartyController.do":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"not found: " + parsed.path.encode())
            return
        qs = parse_qs(parsed.query)
        ticket = (qs.get("ticket") or [""])[0]
        self._handle_ticket(ticket)

    def _handle_ticket(self, ticket):
        print(f"[mock-oa] ticket={ticket!r}")

        # 场景1: 非200 (模拟 ticket 无效/服务异常)
        if ticket.startswith("bad"):
            self.send_response(403)
            self.end_headers()
            self.wfile.write(b"forbidden")
            return
        # 场景2: SSOLogoutError 头 (官方文档的失败表达之一)
        if ticket.startswith("logout"):
            self.send_response(200)
            self.send_header("SSOLogoutError", "1")
            self.end_headers()
            self.wfile.write(b"")
            return
        # 场景3: 缺 ticket
        if not ticket:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"ticket required")
            return

        login, name, member_id = USERS.get(ticket, DEFAULT_USER)
        body = login.encode("utf-8")
        self.send_response(200)
        self.send_header("LoginName", login)
        self.send_header("MemberId", member_id)
        self.send_header("MemberName", name)
        self.send_header("Content-Type", "text/plain;charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[mock-oa] {self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    print(f"[mock-oa] listening on {HOST}:{PORT}")
    print(f"[mock-oa] 测试: curl -i 'http://127.0.0.1:{PORT}/seeyon/thirdpartyController.do?ticket=test1'")
    HTTPServer((HOST, PORT), Handler).serve_forever()
