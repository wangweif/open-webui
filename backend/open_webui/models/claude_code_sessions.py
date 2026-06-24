import logging
import time
from typing import Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy import BigInteger, Column, Integer, String, Text, UniqueConstraint

from open_webui.env import SRC_LOG_LEVELS
from open_webui.internal.db import Base, get_db


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


class ClaudeCodeSession(Base):
    __tablename__ = "claude_code_session"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, nullable=False)
    chat_id = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    claude_session_id = Column(String, nullable=False)
    workspace_path = Column(Text, nullable=False)
    status = Column(String, nullable=False, default="active")
    title = Column(Text, nullable=True)
    created_at = Column(BigInteger)
    updated_at = Column(BigInteger)

    __table_args__ = (
        UniqueConstraint("user_id", "chat_id", "model_id", name="unique_claude_session_binding"),
    )


class ClaudeCodeSessionModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: str
    chat_id: str
    model_id: str
    claude_session_id: str
    workspace_path: str
    status: str
    title: Optional[str] = None
    created_at: int
    updated_at: int


class ClaudeCodeSessionsTable:
    def get_by_user_chat_model(
        self, user_id: str, chat_id: str, model_id: str
    ) -> Optional[ClaudeCodeSessionModel]:
        with get_db() as db:
            session = (
                db.query(ClaudeCodeSession)
                .filter_by(user_id=user_id, chat_id=chat_id, model_id=model_id)
                .first()
            )
            return ClaudeCodeSessionModel.model_validate(session) if session else None

    def insert_new_session(
        self,
        user_id: str,
        chat_id: str,
        model_id: str,
        claude_session_id: str,
        workspace_path: str,
        title: Optional[str] = None,
    ) -> Optional[ClaudeCodeSessionModel]:
        now = int(time.time())
        with get_db() as db:
            try:
                session = ClaudeCodeSession(
                    user_id=user_id,
                    chat_id=chat_id,
                    model_id=model_id,
                    claude_session_id=claude_session_id,
                    workspace_path=workspace_path,
                    status="active",
                    title=title,
                    created_at=now,
                    updated_at=now,
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                return ClaudeCodeSessionModel.model_validate(session)
            except Exception as e:
                log.exception(f"Error inserting Claude Code session: {e}")
                return None

    def touch_session(self, id: int, title: Optional[str] = None) -> Optional[ClaudeCodeSessionModel]:
        with get_db() as db:
            session = db.get(ClaudeCodeSession, id)
            if not session:
                return None

            session.updated_at = int(time.time())
            session.status = "active"
            if title and not session.title:
                session.title = title

            db.commit()
            db.refresh(session)
            return ClaudeCodeSessionModel.model_validate(session)

    def close_by_chat_id(self, user_id: str, chat_id: str) -> bool:
        with get_db() as db:
            try:
                db.query(ClaudeCodeSession).filter_by(user_id=user_id, chat_id=chat_id).update(
                    {"status": "closed", "updated_at": int(time.time())}
                )
                db.commit()
                return True
            except Exception as e:
                log.exception(f"Error closing Claude Code sessions for chat {chat_id}: {e}")
                return False


ClaudeCodeSessions = ClaudeCodeSessionsTable()
