"""Thread title auto-generation via LiteLLM."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from app.ai.llm import llm

_TITLE_TEMPLATE = PromptTemplate.from_template(
    "Generate an extremely short chat title (5 words max, no punctuation) for "
    "this user message. Reply ONLY with the title, nothing else.\n\nMessage: {message}"
)

title_chain = _TITLE_TEMPLATE | llm | StrOutputParser()
