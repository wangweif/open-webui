"""Peewee migrations -- 021_add_claude_code_sessions.py."""

from contextlib import suppress

import peewee as pw
from peewee_migrate import Migrator


with suppress(ImportError):
    import playhouse.postgres_ext as pw_pext


def migrate(migrator: Migrator, database: pw.Database, *, fake=False):
    """Create bindings between Open WebUI chats and Claude Code sessions."""

    @migrator.create_model
    class ClaudeCodeSession(pw.Model):
        id = pw.AutoField()
        user_id = pw.CharField()
        chat_id = pw.CharField()
        model_id = pw.CharField()
        claude_session_id = pw.CharField()
        workspace_path = pw.TextField()
        status = pw.CharField(default="active")
        title = pw.TextField(null=True)
        created_at = pw.BigIntegerField()
        updated_at = pw.BigIntegerField()

        class Meta:
            table_name = "claude_code_session"
            indexes = (
                (("user_id", "chat_id", "model_id"), True),
                (("claude_session_id",), False),
            )


def rollback(migrator: Migrator, database: pw.Database, *, fake=False):
    """Drop Claude Code session bindings."""

    migrator.remove_model("claude_code_session")
