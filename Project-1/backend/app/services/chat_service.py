"""Chat orchestration — invokes the LCEL chain and persists messages."""

from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chains.chat_chain import chat_chain, chat_llm, _SYSTEM_PROMPT
from app.core import settings
from app.models import User
from app.schemas.chat import ChatAttachment
from app.services import thread_service

_str_parser = StrOutputParser()


def _url_to_b64_data_uri(url: str | None) -> str | None:
    """Read an uploaded image from disk and return a base64 data URI.

    The remote LiteLLM proxy cannot reach http://localhost, so we embed the
    image bytes directly in the request payload instead of passing a URL.
    """
    if not url:
        return None

    # Strip any leading slash and derive a filename
    relative = url.lstrip("/")
    # stored as /uploads/<filename>  or  uploads/<filename>
    if relative.startswith("uploads/"):
        filename = relative[len("uploads/"):]
    else:
        # last segment as fallback
        filename = Path(relative).name

    file_path = Path(settings.UPLOAD_DIR) / filename
    if not file_path.is_file():
        return None

    import base64
    import mimetypes
    mime = mimetypes.guess_type(str(file_path))[0] or "image/png"
    b64 = base64.b64encode(file_path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def _build_multimodal_messages(
    history: str,
    message: str,
    attachments: list[ChatAttachment],
) -> list:
    """Build LangChain message objects with image_url content blocks.

    Uses the same system prompt and history context as the text chain but
    constructs a multimodal HumanMessage so Gemini can actually analyse images.
    """
    # System turn
    system = SystemMessage(content=_SYSTEM_PROMPT)

    # Build the human content list
    content: list[dict] = []

    # Memory context as first text block
    content.append(
        {
            "type": "text",
            "text": (
                f"Previous conversation:\n{history}\n\n"
                "Now answer the user's message below. "
                "Analyse any images provided and describe them in detail.\n\n"
                f"User: {message}"
            ),
        }
    )

    # Attachment blocks — images as image_url (base64), others as text
    for att in attachments:
        if att.attachment_type == "image":
            data_uri = _url_to_b64_data_uri(att.attachment_url)
            if data_uri:
                content.append(
                    {"type": "image_url", "image_url": {"url": data_uri}}
                )
            else:
                name = att.name or att.attachment_url or "uploaded image"
                content.append({"type": "text", "text": f"\n[Image attached: {name} — file not found on disk]"})

        elif att.attachment_type == "video":
            name = att.name or att.attachment_url or "uploaded video"
            content.append(
                {
                    "type": "text",
                    "text": (
                        f"\n[Video attached: {name}. "
                        "You cannot play video, so acknowledge it and offer help "
                        "if the user describes what is in it.]"
                    ),
                }
            )
        elif att.attachment_type == "code":
            lang = (Path(att.name or "").suffix.lstrip(".")) if att.name else ""
            content.append(
                {
                    "type": "text",
                    "text": f"\n[Code file: {att.name or 'snippet'}]\n```{lang}\n{att.content or ''}\n```",
                }
            )
        elif att.attachment_type in {"table", "formula"}:
            content.append(
                {
                    "type": "text",
                    "text": f"\n[{att.attachment_type.capitalize()}: {att.name or ''}]\n{att.content or ''}",
                }
            )

    return [system, HumanMessage(content=content)]


def _format_memory_context(messages: list) -> str:
    """Format up to the last 10 messages as prompt memory context."""
    if not messages:
        return "(no previous conversation)"

    lines: list[str] = []
    for msg in messages:
        role = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{role}: {msg.content}")
    return "\n".join(lines)


def _format_attachments_context(attachments: list[ChatAttachment]) -> str:
    """Format multimodal attachments into a compact text block for the LLM."""
    if not attachments:
        return "(none)"

    lines: list[str] = []
    for attachment in attachments:
        label = attachment.attachment_type.capitalize()
        # Prefer the original filename, fall back to URL or a generic label
        name = attachment.name or attachment.attachment_url or "uploaded file"
        if attachment.attachment_type == "image":
            lines.append(
                f"- Image file attached: {name}\n"
                f"  (You cannot view this image directly. Acknowledge its presence "
                f"and offer to help if the user describes the contents.)"
            )
        elif attachment.attachment_type == "video":
            lines.append(
                f"- Video file attached: {name}\n"
                f"  (You cannot play this video directly. Acknowledge its presence "
                f"and offer to help if the user describes what is in the video.)"
            )
        elif attachment.attachment_type == "code":
            body = attachment.content or ""
            lang_hint = name.rsplit(".", 1)[-1] if "." in name else ""
            lines.append(f"- Code file ({name}):\n```{lang_hint}\n{body}\n```")
        elif attachment.attachment_type == "table":
            body = attachment.content or ""
            lines.append(f"- Table data ({name}):\n{body}")
        elif attachment.attachment_type == "formula":
            body = attachment.content or ""
            lines.append(f"- Formula:\n{body}")
        else:
            lines.append(f"- {label} ({name}): {attachment.content or ''}")

    import logging
    logging.getLogger(__name__).debug("ATTACHMENTS SENT TO LLM:\n%s", "\n".join(lines))
    return "\n".join(lines)


async def stream_chat_response(
    db: AsyncSession,
    *,
    current_user: User,
    message: str,
    thread_id: UUID | None,
    attachments: list[ChatAttachment] | None = None,
) -> AsyncGenerator[dict, None]:
    """Stream tokens, persisting both the user prompt and assistant reply.

    Yields events shaped as:
        {"event": "thread", "thread_id": "..."}
        {"event": "token", "data": "..."}
        {"event": "done"}
    """
    attachments = attachments or []

    # 1. Resolve thread (create if needed)
    if thread_id is None:
        thread = await thread_service.create_thread(db, user_id=current_user.id)
    else:
        thread = await thread_service.get_thread_for_user(
            db, thread_id, current_user.id
        )

    # 1b. Load thread-scoped memory (last 10 messages = last 5 turns)
    recent_messages = await thread_service.get_recent_thread_messages_for_context(
        db,
        thread_id=thread.id,
        user_id=current_user.id,
        limit=10,
    )
    history = _format_memory_context(recent_messages)
    attachment_context = _format_attachments_context(attachments)

    attachment_metadata: dict[str, Any] | None = None
    primary_attachment_type: str | None = None
    primary_attachment_url: str | None = None
    if attachments:
        primary = attachments[0]
        primary_attachment_type = primary.attachment_type
        primary_attachment_url = primary.attachment_url
        attachment_metadata = {
            "attachments": [a.model_dump(exclude_none=True) for a in attachments]
        }

    # 2. Persist the user message + auto-title
    await thread_service.save_message(
        db,
        thread_id=thread.id,
        role="user",
        content=message,
        attachment_type=primary_attachment_type,
        attachment_url=primary_attachment_url,
        attachment_metadata=attachment_metadata,
    )
    await thread_service.maybe_set_title(
        db, thread, fallback_text=message, user_email=current_user.email
    )

    yield {"event": "thread", "thread_id": str(thread.id)}

    # 3. Stream LLM tokens — every AI call carries user_email metadata
    config = {
        "metadata": {
            "user_email": current_user.email,
            "application": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
        }
    }

    has_images = any(a.attachment_type == "image" for a in attachments)

    chunks: list[str] = []

    if has_images:
        # Multimodal path — build messages with image_url content blocks so
        # Gemini can actually analyse the uploaded image(s).
        lc_messages = _build_multimodal_messages(history, message, attachments)
        async for chunk in chat_llm.astream(lc_messages, config=config):
            token = _str_parser.invoke(chunk) if not isinstance(chunk, str) else chunk
            if not token:
                continue
            chunks.append(token)
            yield {"event": "token", "data": token}
    else:
        # Text-only path — use the standard LCEL chain
        async for token in chat_chain.astream(
            {
                "history": history,
                "attachments": attachment_context,
                "message": message,
            },
            config=config,
        ):
            if not token:
                continue
            chunks.append(token)
            yield {"event": "token", "data": token}

    # 4. Persist the assembled assistant reply
    full_reply = "".join(chunks)
    if full_reply:
        await thread_service.save_message(
            db, thread_id=thread.id, role="assistant", content=full_reply
        )

    yield {"event": "done"}
