import logging
from typing import List, Optional, Tuple
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from open_webui.models.page_views import PageViews, PageViewModel
from open_webui.utils.auth import get_audit_user
from open_webui.models.users import Users
from open_webui.models.user_logins import UserLogins, UserLoginModel

log = logging.getLogger(__name__)

router = APIRouter()


####################
# Pydantic Models
####################

class UserLogEntry(BaseModel):
    """统一的用户操作日志条目"""
    id: str
    type: str  # 'login', 'page_view'
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    action: str  # 操作描述
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: int


class UserLogsResponse(BaseModel):
    """日志列表响应"""
    logs: List[UserLogEntry]
    total: int
    page: int
    limit: int


####################
# Helper Functions
####################

def get_user_info(user_id: Optional[str]) -> dict:
    """获取用户信息"""
    if not user_id:
        return {"name": None, "email": None}
    
    try:
        user = Users.get_user_by_id(user_id)
        if user:
            return {"name": user.name, "email": user.email}
    except Exception as e:
        log.error(f"获取用户信息失败: {e}")
    
    return {"name": None, "email": None}


def convert_page_view_to_log(page_view: PageViewModel) -> UserLogEntry:
    """将页面访问记录转换为日志条目"""
    user_info = get_user_info(page_view.user_id)
    
    # 根据URL和access_type确定操作类型
    action = "页面访问"
    if page_view.access_type:
        action = f"{page_view.access_type} - {page_view.url}"
    else:
        action = f"访问 {page_view.url}"
    
    return UserLogEntry(
        id=f"page_view_{page_view.id}",
        type="page_view",
        user_id=page_view.user_id,
        user_name=user_info.get("name"),
        user_email=user_info.get("email"),
        action=action,
        details={
            "url": page_view.url,
            "access_type": page_view.access_type,
            "referer": page_view.referer
        },
        ip_address=page_view.ip_address,
        user_agent=page_view.user_agent,
        created_at=page_view.created_at
    )




def convert_login_to_log(login: UserLoginModel) -> UserLogEntry:
    """将登录记录转换为日志条目"""
    user_info = get_user_info(login.user_id)
    
    login_method_map = {
        'password': '密码登录',
        'ldap': 'LDAP登录',
        'oauth': 'OAuth登录',
        'trusted_header': '信任头登录'
    }
    method_label = login_method_map.get(login.login_method, login.login_method or '未知方式')
    
    return UserLogEntry(
        id=f"login_{login.id}",
        type="login",
        user_id=login.user_id,
        user_name=user_info.get("name"),
        user_email=user_info.get("email"),
        action=f"用户登录 ({method_label})" + (" - 成功" if login.success == 'true' else " - 失败"),
        details={
            "login_method": login.login_method,
            "success": login.success
        },
        ip_address=login.ip_address,
        user_agent=login.user_agent,
        created_at=login.created_at
    )


####################
# API Endpoints
####################

@router.get("/all", response_model=UserLogsResponse)
async def get_all_user_logs(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    log_type: str = Query("login", description="日志类型: login, page_view"),
    user_id: Optional[str] = Query(None, description="用户ID"),
    start_time: Optional[int] = Query(None, description="开始时间戳"),
    end_time: Optional[int] = Query(None, description="结束时间戳"),
    user=Depends(get_audit_user)
):
    """
    获取用户操作日志（审计用户）
    支持登录记录和页面访问记录，严格分页查询
    """
    try:
        # 验证 log_type 参数
        if log_type not in ["login", "page_view"]:
            raise HTTPException(status_code=400, detail="log_type 必须是 'login' 或 'page_view'")
        
        # 计算分页参数
        skip = (page - 1) * limit
        
        # 如果没有提供时间范围，使用默认值（从0到当前时间）
        if not start_time:
            start_time = 0
        if not end_time:
            end_time = int(datetime.now().timestamp())
        
        logs: List[UserLogEntry] = []
        total = 0
        
        # 根据类型分别查询
        if log_type == "login":
            # 获取登录记录总数
            total = UserLogins.count_logins(
                user_id=user_id,
                start_time=start_time,
                end_time=end_time
            )
            
            # 获取登录记录（严格分页）
            login_records = UserLogins.get_all_logins(
                skip=skip,
                limit=limit,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time
            )
            
            # 转换为日志条目
            for login in login_records:
                logs.append(convert_login_to_log(login))
                
        elif log_type == "page_view":
            # 获取页面访问记录总数
            total = PageViews.count_page_views(
                user_id=user_id,
                start_time=start_time,
                end_time=end_time
            )
            
            # 获取页面访问记录（严格分页）
            page_views = PageViews.get_page_views_by_date_range(
                start_time=start_time,
                end_time=end_time,
                user_id=user_id,
                skip=skip,
                limit=limit
            )
            
            # 转换为日志条目
            for pv in page_views:
                logs.append(convert_page_view_to_log(pv))
        
        return UserLogsResponse(
            logs=logs,
            total=total,
            page=page,
            limit=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"获取用户操作日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))