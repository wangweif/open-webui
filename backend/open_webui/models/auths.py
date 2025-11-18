import logging
import uuid
import time
from typing import Optional

from open_webui.internal.db import Base, get_db
from open_webui.models.users import UserModel, Users
from open_webui.env import SRC_LOG_LEVELS
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, String, Text, BigInteger, Integer
from open_webui.utils.auth import verify_password

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# DB MODEL
####################


class Auth(Base):
    __tablename__ = "auth"

    id = Column(String, primary_key=True)
    email = Column(String)
    password = Column(Text)
    active = Column(Boolean)
    password_changed_at = Column(BigInteger, nullable=True)  # 密码最后修改时间（时间戳）
    failed_login_count = Column(Integer, default=0)  # 登录失败次数
    locked_until = Column(BigInteger, nullable=True)  # 账户锁定到期时间（时间戳）


class AuthModel(BaseModel):
    id: str
    email: str
    password: str
    active: bool = True
    password_changed_at: Optional[int] = None
    failed_login_count: int = 0
    locked_until: Optional[int] = None


####################
# Forms
####################


class Token(BaseModel):
    token: str
    token_type: str


class ApiKey(BaseModel):
    api_key: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    profile_image_url: str
    assistant_id: Optional[str] = None


class SigninResponse(Token, UserResponse):
    pass


class SigninForm(BaseModel):
    email: str
    password: str


class LdapForm(BaseModel):
    user: str
    password: str


class ProfileImageUrlForm(BaseModel):
    profile_image_url: str


class UpdateProfileForm(BaseModel):
    profile_image_url: str
    name: str


class UpdatePasswordForm(BaseModel):
    password: str
    new_password: str


class SignupForm(BaseModel):
    name: str
    email: str
    password: str
    profile_image_url: Optional[str] = "/user.png"


class AddUserForm(SignupForm):
    role: Optional[str] = "pending"


class AuthsTable:
    def insert_new_auth(
        self,
        email: str,
        password: str,
        name: str,
        profile_image_url: str = "/user.png",
        role: str = "pending",
        oauth_sub: Optional[str] = None,
        assistant_id: Optional[str] = None,
        team_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Optional[UserModel]:
        with get_db() as db:
            log.info("insert_new_auth")

            id = str(uuid.uuid4())
            ragflow_user_id = id

            current_time = int(time.time())
            auth = AuthModel(
                **{
                    "id": id,
                    "email": email,
                    "password": password,
                    "active": True,
                    "password_changed_at": current_time,
                    "failed_login_count": 0,
                    "locked_until": None,
                }
            )
            result = Auth(**auth.model_dump())
            db.add(result)

            user = Users.insert_new_user(
                id, name, email, profile_image_url, role, oauth_sub, assistant_id, ragflow_user_id, team_id, tenant_id
            )

            db.commit()
            db.refresh(result)

            if result and user:
                return user
            else:
                return None

    def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        log.info(f"authenticate_user: {email}")
        try:
            with get_db() as db:
                auth = db.query(Auth).filter_by(email=email, active=True).first()
                if auth:
                    current_time = int(time.time())
                    
                    # 检查账户是否被锁定
                    if auth.locked_until and auth.locked_until > current_time:
                        # 账户仍被锁定
                        remaining_time = auth.locked_until - current_time
                        remaining_minutes = remaining_time // 60
                        log.warning(f"Account {email} is locked. Remaining time: {remaining_minutes} minutes")
                        return None
                    elif auth.locked_until and auth.locked_until <= current_time:
                        # 锁定时间已过，重置失败计数
                        auth.failed_login_count = 0
                        auth.locked_until = None
                    
                    if verify_password(password, auth.password):
                        # 登录成功，重置失败计数和锁定时间
                        auth.failed_login_count = 0
                        auth.locked_until = None
                        db.commit()
                        user = Users.get_user_by_id(auth.id)
                        return user
                    else:
                        # 登录失败，增加失败计数
                        auth.failed_login_count = (auth.failed_login_count or 0) + 1
                        
                        # 如果失败次数达到5次，锁定账户30分钟
                        if auth.failed_login_count >= 5:
                            auth.locked_until = current_time + (30 * 60)  # 30分钟 = 1800秒
                            log.warning(f"Account {email} locked due to 5 failed login attempts")
                        
                        db.commit()
                        return None
                else:
                    return None
        except Exception as e:
            log.error(f"authenticate_user error: {str(e)}")
            return None

    def authenticate_user_by_api_key(self, api_key: str) -> Optional[UserModel]:
        log.info(f"authenticate_user_by_api_key: {api_key}")
        # if no api_key, return None
        if not api_key:
            return None

        try:
            user = Users.get_user_by_api_key(api_key)
            return user if user else None
        except Exception:
            return False

    def authenticate_user_by_trusted_header(self, email: str) -> Optional[UserModel]:
        log.info(f"authenticate_user_by_trusted_header: {email}")
        try:
            with get_db() as db:
                auth = db.query(Auth).filter_by(email=email, active=True).first()
                if auth:
                    user = Users.get_user_by_id(auth.id)
                    return user
        except Exception:
            return None

    def update_user_password_by_id(self, id: str, new_password: str) -> bool:
        try:
            with get_db() as db:
                current_time = int(time.time())
                result = (
                    db.query(Auth)
                    .filter_by(id=id)
                    .update({
                        "password": new_password,
                        "password_changed_at": current_time,
                        "failed_login_count": 0,  # 重置失败计数
                        "locked_until": None,  # 解除锁定
                    })
                )
                db.commit()
                return True if result == 1 else False
        except Exception as e:
            log.error(f"update_user_password_by_id error: {str(e)}")
            return False

    def update_email_by_id(self, id: str, email: str) -> bool:
        try:
            with get_db() as db:
                result = db.query(Auth).filter_by(id=id).update({"email": email})
                db.commit()
                return True if result == 1 else False
        except Exception:
            return False

    def delete_auth_by_id(self, id: str) -> bool:
        try:
            with get_db() as db:
                # Delete User
                result = Users.delete_user_by_id(id)

                if result:
                    db.query(Auth).filter_by(id=id).delete()
                    db.commit()

                    return True
                else:
                    return False
        except Exception:
            return False


Auths = AuthsTable()
