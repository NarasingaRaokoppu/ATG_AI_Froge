"""Simple chatbot LCEL chain.

Pipeline: ChatPromptTemplate | ChatOpenAI (LiteLLM) | StrOutputParser
"""

from pathlib import Path

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core import settings

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
_SYSTEM_PROMPT = (_PROMPT_DIR / "chat_system.txt").read_text(encoding="utf-8")

# Prompt: simple system + human turn
# NOTE: attachment instructions are embedded in the human turn so that they are
# always active regardless of the system-prompt file contents.
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        (
            "human",
            "Previous conversation:\n{history}\n\n"
            "--- Attached files ---\n"
            "{attachments}\n"
            "--- End of attached files ---\n\n"
            "ATTACHMENT RULES (follow strictly):\n"
            "- If any image or video is listed above, acknowledge it explicitly.\n"
            "- Do NOT say 'I don't see an image', 'no attachment was provided', "
            "or 'I cannot access the file'.\n"
            "- You cannot view image/video content directly; instead tell the user "
            "you can see they uploaded the file and offer to help if they describe it.\n"
            "- For code or table attachments, analyze the content provided and give specific feedback.\n\n"
            "User: {message}",
        ),
    ]
)

# LLM: routed exclusively through the Amzur LiteLLM proxy
chat_llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    base_url=settings.LITELLM_PROXY_URL,
    api_key=settings.LITELLM_API_KEY,
    timeout=30,
    max_retries=2,
    streaming=True,
)

# LCEL chain
chat_chain = chat_prompt | chat_llm | StrOutputParser()
