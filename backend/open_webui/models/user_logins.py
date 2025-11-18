import time
from typing import Optional

from open_webui.internal.db import Base, get_db

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, String, Text, Index

####################
# User Login DB Schema
####################


class UserLogin(Base):
    __tablename__ = "user_login"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    ip_address = Column(String(45), nullable=False)  # 支持IPv6
    user_agent = Column(Text, nullable=True)
    login_method = Column(String(50), nullable=True)  # 'password', 'ldap', 'oauth', 'trusted_header'
    success = Column(String(10), default='true')  # 'true' or 'false'
    created_at = Column(BigInteger, nullable=False)
    
    # 创建索引以提高查询性能
    __table_args__ = (
        Index('idx_user_login_user_id', 'user_id'),
        Index('idx_user_login_created_at', 'created_at'),
        Index('idx_user_login_user_id_created_at', 'user_id', 'created_at'),
    )


####################
# Pydantic Models
####################


class UserLoginModel(BaseModel):
    id: str
    user_id: str
    ip_address: str
    user_agent: Optional[str] = None
    login_method: Optional[str] = None
    success: str = 'true'
    created_at: int

    model_config = ConfigDict(from_attributes=True)


####################
# Database Operations
####################


class UserLoginsTable:
    def record_login(
        self,
        user_id: str,
        ip_address: str,
        user_agent: Optional[str] = None,
        login_method: Optional[str] = None,
        success: bool = True,
    ) -> Optional[UserLoginModel]:
        """记录用户登录"""
        import uuid
        with get_db() as db:
            current_time = int(time.time())
            
            login_record = UserLogin(
                id=str(uuid.uuid4()),
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                login_method=login_method,
                success='true' if success else 'false',
                created_at=current_time
            )
            
            db.add(login_record)
            db.commit()
            db.refresh(login_record)
            
            return UserLoginModel.model_validate(login_record)

    def get_logins_by_user_id(
        self, 
        user_id: str, 
        skip: int = 0, 
        limit: int = 100
    ) -> list[UserLoginModel]:
        """获取用户的登录记录"""
        with get_db() as db:
            logins = (
                db.query(UserLogin)
                .filter_by(user_id=user_id)
                .order_by(UserLogin.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [UserLoginModel.model_validate(login) for login in logins]

    def get_all_logins(
        self, 
        skip: int = 0, 
        limit: int = 1000,
        user_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> list[UserLoginModel]:
        """获取所有登录记录"""
        with get_db() as db:
            query = db.query(UserLogin)
            
            if user_id:
                query = query.filter(UserLogin.user_id == user_id)
            if start_time:
                query = query.filter(UserLogin.created_at >= start_time)
            if end_time:
                query = query.filter(UserLogin.created_at <= end_time)
            
            logins = (
                query
                .order_by(UserLogin.created_at.desc())
                .offset(skip)
                .limit(limit)
                .all()
            )
            return [UserLoginModel.model_validate(login) for login in logins]

    def count_logins(
        self,
        user_id: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> int:
        """获取登录记录总数"""
        from sqlalchemy import func
        with get_db() as db:
            query = db.query(func.count(UserLogin.id))
            
            if user_id:
                query = query.filter(UserLogin.user_id == user_id)
            if start_time:
                query = query.filter(UserLogin.created_at >= start_time)
            if end_time:
                query = query.filter(UserLogin.created_at <= end_time)
            
            return query.scalar() or 0


# 创建全局实例
UserLogins = UserLoginsTable()

