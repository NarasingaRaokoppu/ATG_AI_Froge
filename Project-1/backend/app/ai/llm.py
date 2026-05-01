"""LiteLLM client singletons — import from here."""
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from openai import OpenAI

from app.core import settings

# LangChain LLM client
llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    base_url=settings.LITELLM_PROXY_URL,
    api_key=settings.LITELLM_API_KEY,
    timeout=30,
    max_retries=2,
)

# OpenAI SDK client for direct calls (image generation, embeddings, etc.)
client = OpenAI(
    api_key=settings.LITELLM_API_KEY,
    base_url=settings.LITELLM_PROXY_URL,
)

# Embeddings client
embeddings = OpenAIEmbeddings(
    model=settings.LITELLM_EMBEDDING_MODEL,
    base_url=settings.LITELLM_PROXY_URL,
    api_key=settings.LITELLM_API_KEY,
)

__all__ = ["llm", "client", "embeddings"]
