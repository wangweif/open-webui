import logging
import time
from typing import Optional

from open_webui.internal.db import Base, get_db
from open_webui.env import SRC_LOG_LEVELS

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Integer, String, UniqueConstraint

log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])

####################
# AppSessions DB Schema
####################


class AppSession(Base):
    __tablename__ = "app_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_id = Column(Integer, nullable=False)  # App ID (corresponds to different models)
    user_id = Column(String, nullable=False)  # User ID
    assistant_id = Column(String, nullable=False)  # Assistant ID

    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

    __table_args__ = (UniqueConstraint("app_id", "user_id", name="unique_app_user"),)


class AppSessionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    app_id: int
    user_id: str
    assistant_id: str
    created_at: int
    updated_at: int


class AppSessionForm(BaseModel):
    app_id: int
    user_id: str
    assistant_id: str


class AppSessionResponse(BaseModel):
    id: int
    app_id: int
    user_id: str
    assistant_id: str
    created_at: int
    updated_at: int


####################
# Forms
####################


class AppSessionTable:
    def __init__(self, db):
        self.db = db

    def insert_new_app_session(
        self, app_id: int, user_id: str, assistant_id: str
    ) -> Optional[AppSessionModel]:
        with get_db() as db:
            try:
                app_session = AppSession(
                    **{
                        "app_id": app_id,
                        "user_id": user_id,
                        "assistant_id": assistant_id,
                        "created_at": int(time.time()),
                        "updated_at": int(time.time()),
                    }
                )
                db.add(app_session)
                db.commit()
                db.refresh(app_session)
                return AppSessionModel.model_validate(app_session)
            except Exception as e:
                log.error(f"Error inserting app session: {e}")
                return None

    def get_app_session_by_app_user(
        self, app_id: int, user_id: str
    ) -> Optional[AppSessionModel]:
        with get_db() as db:
            try:
                app_session = (
                    db.query(AppSession)
                    .filter_by(app_id=app_id, user_id=user_id)
                    .first()
                )
                return (
                    AppSessionModel.model_validate(app_session) if app_session else None
                )
            except Exception as e:
                log.error(f"Error getting app session: {e}")
                return None

    def update_app_session_assistant_id(
        self, app_id: int, user_id: str, assistant_id: str
    ) -> Optional[AppSessionModel]:
        with get_db() as db:
            try:
                app_session = (
                    db.query(AppSession)
                    .filter_by(app_id=app_id, user_id=user_id)
                    .first()
                )
                if app_session:
                    app_session.assistant_id = assistant_id
                    app_session.updated_at = int(time.time())
                    db.commit()
                    db.refresh(app_session)
                    return AppSessionModel.model_validate(app_session)
                return None
            except Exception as e:
                log.error(f"Error updating app session: {e}")
                return None

    def get_or_create_app_session(
        self, app_id: int, user_id: str, assistant_id: str
    ) -> Optional[AppSessionModel]:
        """Get or create app session"""
        existing_session = self.get_app_session_by_app_user(app_id, user_id)
        if existing_session:
            return existing_session
        else:
            return self.insert_new_app_session(app_id, user_id, assistant_id)


AppSessions = AppSessionTable(get_db())
