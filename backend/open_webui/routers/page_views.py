import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from open_webui.models.page_views import (
    PageViews,
    PageViewModel,
    PageViewStatsModel,
    PageViewCreateForm,
    PageViewStatsResponse,
)
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.models.users import Users

log = logging.getLogger(__name__)

router = APIRouter()


####################
# Helper Functions
####################

def get_client_ip(request: Request) -> str:
    """获取客户端真实IP地址"""
    # 检查代理头
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For 可能包含多个IP，取第一个
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # 回退到远程地址
    return request.client.host if request.client else "unknown"


####################
# API Endpoints
####################

@router.post("/record")
async def record_page_view(
    form_data: PageViewCreateForm,
    request: Request,
    user=Depends(get_verified_user)
):
    """
    记录页面访问
    需要用户验证
    """
    try:
        print("--------------------------record_page_view--------------------------")
        # 从请求中获取额外信息
        ip_address = get_client_ip(request)
        user_agent = request.headers.get("User-Agent")
        referer = request.headers.get("Referer")
        
        # 记录页面访问
        page_view = PageViews.record_page_view(
            url=form_data.url,
            ip_address=ip_address,
            user_id=user.id,
            user_agent=user_agent,
            referer=referer,
            access_type=form_data.access_type,
        )
        
        if page_view:
            return {"message": "页面访问已记录", "id": page_view.id}
        else:
            raise HTTPException(status_code=500, detail="记录页面访问失败")
            
    except Exception as e:
        log.error(f"记录页面访问时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/{url}")
async def get_page_stats(
    url: str,
    user=Depends(get_verified_user)
):
    """
    获取特定页面的访问统计
    """
    try:
        # URL解码
        from urllib.parse import unquote
        decoded_url = unquote(url)
        
        # 获取页面统计
        stats = PageViews.get_page_view_stats(decoded_url)
        
        if stats:
            return PageViewStatsResponse(
                url=stats.url,
                view_count=stats.view_count,
                first_view_at=stats.first_view_at,
                last_view_at=stats.last_view_at
            )
        else:
            return PageViewStatsResponse(
                url=decoded_url,
                view_count=0,
                first_view_at=0,
                last_view_at=0
            )
    except Exception as e:
        log.error(f"获取页面统计时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_page_view_stats(
    skip: int = 0,
    limit: int = 100,
    order_by: str = "view_count",
    user=Depends(get_admin_user)
):
    """
    获取所有页面的访问统计
    需要管理员权限
    """
    try:
        stats = PageViews.get_all_page_stats(skip=skip, limit=limit, order_by=order_by)
        
        return [
            PageViewStatsResponse(
                url=stat.url,
                view_count=stat.view_count,
                first_view_at=stat.first_view_at,
                last_view_at=stat.last_view_at
            )
            for stat in stats
        ]
    except Exception as e:
        log.error(f"获取页面统计时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/summary")
async def get_analytics_summary(
    user=Depends(get_admin_user)
):
    """
    获取分析摘要
    需要管理员权限
    """
    try:
        total_views = PageViews.get_total_views_count()
        unique_pages = PageViews.get_unique_pages_count()
        top_pages = PageViews.get_top_pages(limit=10)
        access_type_statistics = PageViews.get_access_type_statistics()
        
        return {
            "total_views": total_views,
            "unique_pages": unique_pages,
            "top_pages": [
                PageViewStatsResponse(
                    url=page.url,
                    view_count=page.view_count,
                    first_view_at=page.first_view_at,
                    last_view_at=page.last_view_at
                )
                for page in top_pages
            ],
            "access_type_statistics": access_type_statistics
        }
    except Exception as e:
        log.error(f"获取分析摘要时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics/access-types")
async def get_access_type_statistics(
    user=Depends(get_admin_user)
):
    """
    获取访问类型统计
    需要管理员权限
    """
    try:
        statistics = PageViews.get_access_type_statistics()
        return statistics
    except Exception as e:
        log.error(f"获取访问类型统计时出错: {e}")
        raise HTTPException(status_code=500, detail=str(e))