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
chat_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", _SYSTEM_PROMPT),
        ("human", "{message}"),
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
