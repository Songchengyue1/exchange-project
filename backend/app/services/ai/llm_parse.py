from __future__ import annotations

import json
import logging
import re
from typing import Optional

from pydantic import BaseModel, Field

from app.config import settings
from app.services.ai.ollama_client import OllamaClient, OllamaError

logger = logging.getLogger(__name__)


class SearchSlots(BaseModel):
    q: Optional[str] = Field(default=None, description="关键词")
    category_id: Optional[int] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    sort: Optional[str] = Field(default=None, description="created_at_desc|price_asc|price_desc")


_PARSE_PROMPT = """你是酱菜交易平台的搜索助手。根据用户自然语言，输出 JSON，字段：
q(关键词，可空)、category_id(整数，不确定则 null)、price_min、price_max、sort(仅 created_at_desc|price_asc|price_desc 或 null)。
只输出一行 JSON，不要解释。用户输入：{query}"""


def parse_search_query(query: str, *, client: Optional[OllamaClient] = None) -> Optional[SearchSlots]:
    if not settings.ai_search_use_llm:
        return None
    client = client or OllamaClient()
    try:
        from langchain_core.output_parsers import PydanticOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_ollama import ChatOllama
    except ImportError:
        logger.warning("LangChain 未安装，跳过 LLM 抽槽位")
        return _parse_search_fallback(query, client)

    try:
        llm = ChatOllama(
            model=settings.ollama_chat_model,
            base_url=settings.ollama_base_url,
            temperature=0,
        )
        parser = PydanticOutputParser(pydantic_object=SearchSlots)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "只返回合法 JSON。"),
                ("human", _PARSE_PROMPT + "\n{format_instructions}"),
            ]
        ).partial(format_instructions=parser.get_format_instructions())
        chain = prompt | llm | parser
        return chain.invoke({"query": query})
    except Exception as exc:
        logger.warning("LangChain 抽槽位失败: %s", exc)
        return _parse_search_fallback(query, client)


def _parse_search_fallback(query: str, client: OllamaClient) -> Optional[SearchSlots]:
    try:
        with client._client(timeout=settings.ai_search_timeout_seconds) as http:
            r = http.post(
                "/api/chat",
                json={
                    "model": settings.ollama_chat_model,
                    "messages": [{"role": "user", "content": _PARSE_PROMPT.format(query=query)}],
                    "stream": False,
                },
            )
            r.raise_for_status()
            text = (r.json().get("message") or {}).get("content") or ""
    except (OllamaError, Exception):
        return None

    match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group())
        return SearchSlots.model_validate(data)
    except Exception:
        return None
