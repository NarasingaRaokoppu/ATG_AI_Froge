"""NL-to-pandas chain for spreadsheet querying."""

from __future__ import annotations

import json
from pathlib import Path
import time
from typing import Any

import numpy as np
import pandas as pd
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.ai.llm import llm

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
_PANDAS_PROMPT = (_PROMPT_DIR / "pandas_prompt.txt").read_text(encoding="utf-8")

_parser = StrOutputParser()
_pandas_code_chain = ChatPromptTemplate.from_template(_PANDAS_PROMPT) | llm | _parser
_pandas_answer_chain = (
    ChatPromptTemplate.from_template(
        "Question:\n{question}\n\nComputed result (JSON):\n{computed_result_json}\n\n"
        "Write a short explanation in 1 to 3 sentences. "
        "Do not hedge or say the answer cannot be determined if the computed result is present."
    )
    | llm
    | _parser
)


def _strip_code_fence(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.replace("python", "", 1).strip()
    return text


def _validate_code_safety(code: str) -> None:
    banned = [
        "import ",
        "open(",
        "exec(",
        "eval(",
        "__import__",
        "os.",
        "subprocess",
        "sys.",
    ]
    lower = code.lower()
    for token in banned:
        if token in lower:
            raise ValueError(f"Unsafe pandas code detected: {token}")


def _to_records(result: Any) -> list[dict[str, Any]]:
    if isinstance(result, pd.DataFrame):
        return result.head(1000).replace({np.nan: None}).to_dict(orient="records")
    if isinstance(result, pd.Series):
        return result.head(1000).to_frame(name=result.name or "value").to_dict(
            orient="records"
        )
    if isinstance(result, list):
        if result and isinstance(result[0], dict):
            return result[:1000]
        return [{"value": str(x)} for x in result[:1000]]
    if isinstance(result, dict):
        return [result]
    return [{"value": str(result)}]


def _serialize_result(result: Any) -> Any:
    if isinstance(result, pd.DataFrame):
        return result.head(1000).replace({np.nan: None}).to_dict(orient="records")
    if isinstance(result, pd.Series):
        if result.index.nlevels == 1:
            return result.replace({np.nan: None}).to_dict()
        return result.head(1000).replace({np.nan: None}).to_dict()
    if isinstance(result, np.generic):
        return result.item()
    if isinstance(result, list):
        return [item.item() if isinstance(item, np.generic) else item for item in result[:1000]]
    if isinstance(result, dict):
        return {
            key: value.item() if isinstance(value, np.generic) else value
            for key, value in result.items()
        }
    return result


def _execute_generated_code(df: pd.DataFrame, code: str) -> tuple[Any, list[dict[str, Any]], list[str]]:
    _validate_code_safety(code)
    local_vars: dict[str, Any] = {"df": df.copy(), "result": None}
    safe_globals = {"pd": pd, "np": np, "__builtins__": {"len": len, "min": min, "max": max, "sum": sum, "abs": abs, "round": round, "sorted": sorted, "str": str, "int": int, "float": float}}
    exec(code, safe_globals, local_vars)  # noqa: S102
    result = local_vars.get("result")
    rows = _to_records(result)
    if isinstance(result, pd.DataFrame):
        columns = list(result.columns)
    elif isinstance(result, pd.Series):
        columns = [result.name or "value"]
    elif rows:
        columns = list(rows[0].keys())
    else:
        columns = []
    return _serialize_result(result), rows, columns


class PandasChain:
    """Generate pandas code and run it against an in-memory dataframe."""

    async def run_query(
        self,
        *,
        dataframe: pd.DataFrame,
        question: str,
        history_text: str,
        user_email: str,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        schema = {
            "columns": list(dataframe.columns),
            "dtypes": {k: str(v) for k, v in dataframe.dtypes.items()},
            "sample_rows": dataframe.head(5).to_dict(orient="records"),
        }

        generated_code = await _pandas_code_chain.ainvoke(
            {
                "question": question,
                "history": history_text,
                "dataframe_schema_json": json.dumps(schema, ensure_ascii=False),
            },
            config={"metadata": {"user_email": user_email}},
        )
        generated_code = _strip_code_fence(str(generated_code))

        computed_result, rows, columns = _execute_generated_code(dataframe, generated_code)

        explanation = await _pandas_answer_chain.ainvoke(
            {
                "question": question,
                "computed_result_json": json.dumps(computed_result, ensure_ascii=False, default=str),
            },
            config={"metadata": {"user_email": user_email}},
        )

        return {
            "generated_code": generated_code,
            "computed_result": computed_result,
            "rows": rows,
            "columns": columns,
            "answer": str(explanation),
            "explanation": str(explanation),
            "intermediate_steps": [generated_code],
            "return_intermediate_steps": True,
            "execution_ms": int((time.perf_counter() - started) * 1000),
        }

    async def stream_answer(
        self,
        *,
        question: str,
        rows: list[dict[str, Any]],
        user_email: str,
    ):
        async for token in _pandas_answer_chain.astream(
            {
                "question": question,
                "computed_result_json": json.dumps(rows[:20], ensure_ascii=False),
            },
            config={"metadata": {"user_email": user_email}},
        ):
            if token:
                yield token


pandas_chain = PandasChain()
