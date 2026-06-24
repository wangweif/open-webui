import asyncio
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, AsyncGenerator, Optional
from uuid import uuid4

from fastapi import HTTPException, status
from fastapi.responses import StreamingResponse

from open_webui.config import (
    CLAUDE_CODE_DANGEROUSLY_SKIP_PERMISSIONS,
    CLAUDE_CODE_DEFAULT_SYSTEM_PROMPT,
    CLAUDE_CODE_PATH,
    CLAUDE_CODE_WORKSPACE_ROOT,
)
from open_webui.env import SRC_LOG_LEVELS
from open_webui.models.claude_code_sessions import ClaudeCodeSessions
from open_webui.models.models import Models


log = logging.getLogger(__name__)
log.setLevel(SRC_LOG_LEVELS["MODELS"])


def _persistent_value(value: Any) -> Any:
    return getattr(value, "value", value)


def _safe_path_part(value: str) -> str:
    value = value or "default"
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value)[:120]


def _get_text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif "text" in item:
                    parts.append(item.get("text", ""))
        return "\n".join([part for part in parts if part])

    return str(content) if content is not None else ""


def _get_last_user_message(messages: list[dict]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return _get_text_from_content(message.get("content"))
    return ""


def _get_model_params(model_id: str) -> dict:
    model_info = Models.get_model_by_id(model_id)
    if model_info:
        return model_info.params.model_dump()
    return {}


def _get_system_prompt(model_id: str) -> str:
    params = _get_model_params(model_id)
    system_prompt = params.get("system") or _persistent_value(
        CLAUDE_CODE_DEFAULT_SYSTEM_PROMPT
    )
    return (system_prompt or "").strip()


def _write_claude_md(workspace_path: Path, system_prompt: str) -> None:
    workspace_path.mkdir(parents=True, exist_ok=True)
    claude_md_path = workspace_path / "CLAUDE.md"
    content = "# System Prompt\n\n"
    if system_prompt:
        content += "The following rules are system-level instructions for this session and must be followed first:\n\n"
        content += system_prompt.strip()
        content += "\n"
    else:
        content += "No model-specific system prompt is configured for this session.\n"

    existing = claude_md_path.read_text(encoding="utf-8") if claude_md_path.exists() else None
    if existing != content:
        claude_md_path.write_text(content, encoding="utf-8")


def _get_or_create_binding(user: Any, metadata: dict, model_id: str, user_message: str):
    chat_id = metadata.get("chat_id") or metadata.get("session_id") or str(uuid4())
    binding = ClaudeCodeSessions.get_by_user_chat_model(user.id, chat_id, model_id)

    if binding:
        title = user_message[:50] if user_message else None
        ClaudeCodeSessions.touch_session(binding.id, title=title)
        return binding, True

    claude_session_id = str(uuid4())
    workspace_root = Path(str(_persistent_value(CLAUDE_CODE_WORKSPACE_ROOT)))
    workspace_path = (
        workspace_root
        / _safe_path_part(user.id)
        / _safe_path_part(chat_id)
        / _safe_path_part(model_id)
    )
    title = user_message[:50] if user_message else None
    binding = ClaudeCodeSessions.insert_new_session(
        user_id=user.id,
        chat_id=chat_id,
        model_id=model_id,
        claude_session_id=claude_session_id,
        workspace_path=str(workspace_path),
        title=title,
    )
    if not binding:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Claude Code session binding",
        )
    return binding, False


def _openai_chunk(chat_id: str, model_id: str, delta: dict, finish_reason: Optional[str] = None) -> str:
    payload = {
        "id": chat_id,
        "object": "chat.completion.chunk",
        "created": 0,
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _extract_delta(event: dict) -> Optional[str]:
    event_type = event.get("type")
    inner = event.get("event") if event_type == "stream_event" else event
    if not isinstance(inner, dict):
        return None

    if inner.get("type") == "content_block_delta":
        delta = inner.get("delta") or {}
        return delta.get("text")

    return None


async def _stream_claude_code(
    *,
    model_id: str,
    claude_session_id: str,
    workspace_path: str,
    prompt: str,
    resume: bool,
) -> AsyncGenerator[str, None]:
    chat_completion_id = f"chatcmpl-{uuid4()}"
    yield _openai_chunk(chat_completion_id, model_id, {"role": "assistant"})

    command = str(_persistent_value(CLAUDE_CODE_PATH))
    args = [
        command,
        "--print",
        "--output-format",
        "stream-json",
        "--input-format",
        "stream-json",
        "--include-partial-messages",
        "--replay-user-messages",
        "--verbose",
        "--resume" if resume else "--session-id",
        claude_session_id,
    ]
    if _persistent_value(CLAUDE_CODE_DANGEROUSLY_SKIP_PERMISSIONS):
        args.append("--dangerously-skip-permissions")

    env = {
        **os.environ,
        "TERM": "dumb",
        "NO_COLOR": "1",
        "CLICOLOR": "0",
        "FORCE_COLOR": "0",
    }

    try:
        if sys.platform == "win32":
            quoted_args = " ".join(json.dumps(arg) for arg in args)
            proc = await asyncio.create_subprocess_shell(
                quoted_args,
                cwd=workspace_path,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        else:
            proc = await asyncio.create_subprocess_exec(
                *args,
                cwd=workspace_path,
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Claude Code CLI not found: {command}",
        )

    input_message = {
        "type": "user",
        "message": {
            "role": "user",
            "content": [{"type": "text", "text": prompt}],
        },
    }
    assert proc.stdin is not None
    proc.stdin.write((json.dumps(input_message, ensure_ascii=False) + "\n").encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()

    stderr_chunks: list[str] = []

    async def read_stderr():
        if proc.stderr is None:
            return
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            stderr_chunks.append(line.decode("utf-8", errors="ignore").strip())

    stderr_task = asyncio.create_task(read_stderr())

    try:
        assert proc.stdout is not None
        while True:
            line = await proc.stdout.readline()
            if not line:
                break

            text = line.decode("utf-8", errors="ignore").strip()
            if not text:
                continue

            try:
                event = json.loads(text)
            except json.JSONDecodeError:
                log.debug(f"Ignoring non-JSON Claude output: {text}")
                continue

            delta = _extract_delta(event)
            if delta:
                yield _openai_chunk(chat_completion_id, model_id, {"content": delta})

            if event.get("type") == "error":
                message = event.get("message") or event.get("error") or "Claude Code error"
                yield _openai_chunk(chat_completion_id, model_id, {"content": f"\n\nError: {message}"})

        return_code = await proc.wait()
        await stderr_task
    finally:
        if not stderr_task.done():
            stderr_task.cancel()

    if return_code != 0:
        stderr = "\n".join(chunk for chunk in stderr_chunks if chunk)
        message = stderr or f"Claude Code exited with status {return_code}"
        yield _openai_chunk(chat_completion_id, model_id, {"content": f"\n\nError: {message}"})

    yield _openai_chunk(chat_completion_id, model_id, {}, finish_reason="stop")
    yield "data: [DONE]\n\n"


async def generate_claude_code_chat_completion(request, form_data: dict, user: Any):
    model_id = form_data["model"]
    metadata = form_data.get("metadata") or getattr(request.state, "metadata", {})
    messages = form_data.get("messages") or []
    user_message = _get_last_user_message(messages)

    if not user_message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claude Code requires a user message",
        )

    binding, resume = _get_or_create_binding(user, metadata, model_id, user_message)
    system_prompt = _get_system_prompt(model_id)
    workspace_path = Path(binding.workspace_path)
    _write_claude_md(workspace_path, system_prompt)

    stream = _stream_claude_code(
        model_id=model_id,
        claude_session_id=binding.claude_session_id,
        workspace_path=binding.workspace_path,
        prompt=user_message,
        resume=resume,
    )

    if not form_data.get("stream", False):
        content = ""
        async for chunk in stream:
            if not chunk.startswith("data: "):
                continue

            data = chunk.removeprefix("data: ").strip()
            if not data or data == "[DONE]":
                continue

            try:
                payload = json.loads(data)
            except json.JSONDecodeError:
                continue

            choice = (payload.get("choices") or [{}])[0]
            delta = choice.get("delta") or {}
            content += delta.get("content") or ""

        return {
            "id": f"chatcmpl-{uuid4()}",
            "object": "chat.completion",
            "created": 0,
            "model": model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }
            ],
        }

    return StreamingResponse(stream, media_type="text/event-stream")
