import time
from typing import Optional, List, Dict
from datetime import datetime

from open_webui.internal.db import Base, JSONField, get_db

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, Integer, DateTime, Index, func

####################
# Page View DB Schema
####################


class PageView(Base):
    __tablename__ = "page_view"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False)
    user_id = Column(String, nullable=True)  # 可选，用于记录登录用户
    ip_address = Column(String(45), nullable=False)  # 支持IPv6
    user_agent = Column(Text, nullable=True)
    referer = Column(Text, nullable=True)
    access_type = Column(String(50), nullable=True)  # 访问类型：询问、查看记录等
    
    created_at = Column(BigInteger, nullable=False)
    
    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_page_view_url', 'url'),
        Index('idx_page_view_created_at', 'created_at'),
        Index('idx_page_view_url_created_at', 'url', 'created_at'),
        Index('idx_page_view_access_type', 'access_type'),
        Index('idx_page_view_access_type_created_at', 'access_type', 'created_at'),
    )


class PageViewStats(Base):
    __tablename__ = "page_view_stats"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String(500), nullable=False, unique=True)
    view_count = Column(Integer, default=0, nullable=False)
    
    first_view_at = Column(BigInteger, nullable=False)
    last_view_at = Column(BigInteger, nullable=False)
    updated_at = Column(BigInteger, nullable=False)
    
    # 创建索引
    __table_args__ = (
        Index('idx_page_view_stats_url', 'url'),
        Index('idx_page_view_stats_view_count', 'view_count'),
    )


####################
# Pydantic Models
####################


class PageViewModel(BaseModel):
    id: int
    url: str
    user_id: Optional[str] = None
    ip_address: str
    user_agent: Optional[str] = None
    referer: Optional[str] = None
    access_type: Optional[str] = None
    created_at: int

    model_config = ConfigDict(from_attributes=True)


class PageViewStatsModel(BaseModel):
    id: int
    url: str
    view_count: int
    first_view_at: int
    last_view_at: int
    updated_at: int

    model_config = ConfigDict(from_attributes=True)


class PageViewCreateForm(BaseModel):
    url: str
    access_type: Optional[str] = None


class PageViewStatsResponse(BaseModel):
    url: str
    view_count: int
    first_view_at: int
    last_view_at: int


####################
# Database Operations
####################


class PageViewsTable:
    def record_page_view(
        self,
        url: str,
        ip_address: str,
        user_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        referer: Optional[str] = None,
        access_type: Optional[str] = None,
    ) -> Optional[PageViewModel]:
        """记录页面访问"""
        with get_db() as db:
            current_time = int(time.time())
            
            # 创建页面访问记录
            page_view = PageView(
                url=url,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                access_type=access_type,
                created_at=current_time
            )
            
            db.add(page_view)
            
            # 更新或创建页面统计
            stats = db.query(PageViewStats).filter_by(url=url).first()
            if stats:
                stats.view_count += 1
                stats.last_view_at = current_time
                stats.updated_at = current_time
            else:
                stats = PageViewStats(
                    url=url,
                    view_count=1,
                    first_view_at=current_time,
                    last_view_at=current_time,
                    updated_at=current_time
                )
                db.add(stats)
            
            db.commit()
            db.refresh(page_view)
            
            return PageViewModel.model_validate(page_view)

    def get_page_view_stats(self, url: str) -> Optional[PageViewStatsModel]:
        """获取特定页面的访问统计"""
        with get_db() as db:
            stats = db.query(PageViewStats).filter_by(url=url).first()
            if stats:
                return PageViewStatsModel.model_validate(stats)
            return None

    def get_all_page_stats(
        self, 
        skip: int = 0, 
        limit: int = 100,
        order_by: str = "view_count"
    ) -> List[PageViewStatsModel]:
        """获取所有页面的访问统计"""
        with get_db() as db:
            query = db.query(PageViewStats)
            
            if order_by == "view_count":
                query = query.order_by(PageViewStats.view_count.desc())
            elif order_by == "last_view_at":
                query = query.order_by(PageViewStats.last_view_at.desc())
            elif order_by == "url":
                query = query.order_by(PageViewStats.url)
            
            stats = query.offset(skip).limit(limit).all()
            return [PageViewStatsModel.model_validate(stat) for stat in stats]

    def get_page_views_by_url(
        self, 
        url: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[PageViewModel]:
        """获取特定页面的访问记录"""
        with get_db() as db:
            views = (
                db.query(PageView)
                .filter_by(url=url)
                .order_by(PageView.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [PageViewModel.model_validate(view) for view in views]

    def get_page_views_by_date_range(
        self, 
        start_time: int, 
        end_time: int,
        skip: int = 0,
        limit: int = 1000
    ) -> List[PageViewModel]:
        """获取时间范围内的访问记录"""
        with get_db() as db:
            views = (
                db.query(PageView)
                .filter(
                    PageView.created_at >= start_time,
                    PageView.created_at <= end_time
                )
                .order_by(PageView.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [PageViewModel.model_validate(view) for view in views]

    def get_total_views_count(self) -> int:
        """获取总访问次数"""
        with get_db() as db:
            return db.query(func.sum(PageViewStats.view_count)).scalar() or 0

    def get_unique_pages_count(self) -> int:
        """获取独特页面数量"""
        with get_db() as db:
            return db.query(PageViewStats).count()

    def get_top_pages(self, limit: int = 10) -> List[PageViewStatsModel]:
        """获取访问量最高的页面"""
        with get_db() as db:
            stats = (
                db.query(PageViewStats)
                .order_by(PageViewStats.view_count.desc())
                .limit(limit)
                .all()
            )
            return [PageViewStatsModel.model_validate(stat) for stat in stats]

    def get_page_views_by_access_type(
        self, 
        access_type: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[PageViewModel]:
        """获取特定访问类型的访问记录"""
        with get_db() as db:
            views = (
                db.query(PageView)
                .filter_by(access_type=access_type)
                .order_by(PageView.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [PageViewModel.model_validate(view) for view in views]

    def get_access_type_statistics(self) -> Dict[str, int]:
        """获取各访问类型的统计"""
        with get_db() as db:
            results = (
                db.query(PageView.access_type, func.count(PageView.id))
                .filter(PageView.access_type.isnot(None))
                .group_by(PageView.access_type)
                .all()
            )
            return {access_type: count for access_type, count in results}

    def get_page_views_by_url_and_type(
        self, 
        url: str, 
        access_type: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[PageViewModel]:
        """获取特定页面和访问类型的访问记录"""
        with get_db() as db:
            query = db.query(PageView).filter_by(url=url)
            
            if access_type:
                query = query.filter_by(access_type=access_type)
            
            views = (
                query
                .order_by(PageView.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [PageViewModel.model_validate(view) for view in views]


# 创建全局实例
PageViews = PageViewsTable() 