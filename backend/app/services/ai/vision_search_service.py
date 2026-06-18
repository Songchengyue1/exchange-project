from __future__ import annotations

import base64
import json
import logging
import re
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.schemas.ai import AISearchByImageOut
from app.services.ai.ollama_client import OllamaClient, OllamaError
from app.services.ai.search_service import AISearchService

logger = logging.getLogger(__name__)

# 让视觉模型输出结构化结果：物品名 + 若干搜索关键词
# keywords 强调「宽泛品类词」与「中英文品牌词」，提高与商品标题的命中率
_VISION_PROMPT = (
    "你是二手交易平台的看图识物助手。请观察图片中的主要物品，"
    "只输出一行 JSON，不要任何解释或多余文字，格式：\n"
    '{"item": "物品名称（简短，如 白色耐克运动鞋）", '
    '"keywords": ["关键词1", "关键词2", "关键词3", "关键词4"]}\n'
    "keywords 用于在商品库里逐词检索商品标题（标题多为英文），规则：\n"
    "1. 若能认出品牌，【务必给出英文名】，并可同时给中文名，如 Nike、耐克；iPhone、苹果；MacBook；\n"
    "2. 必须包含【最短的品类词】，如 鞋（而非只有 运动鞋）、手机、电脑、书；\n"
    "3. 再补充常见品类词，如 运动鞋、球鞋；\n"
    "4. 颜色、型号等细节词可选，放在最后；\n"
    "5. 共给 3~6 个词，英文品牌名优先，宁可宽泛也不要只给生僻的具体描述。"
)


class VisionSearchService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.client = OllamaClient()
        self.search_service = AISearchService(db)

    def _parse_vision_output(self, text: str) -> tuple[str, list[str]]:
        """从模型输出里抽取 item 与 keywords；失败时退化为纯文本关键词。"""
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                item = str(data.get("item") or "").strip()
                raw_kw = data.get("keywords")
                keywords: list[str] = []
                if isinstance(raw_kw, list):
                    for k in raw_kw:
                        s = str(k).strip()
                        if s:
                            keywords.append(s)
                if item or keywords:
                    return item, keywords
            except (json.JSONDecodeError, TypeError, ValueError):
                pass
        # 退化：把整段文本压成一行当作识别结果
        cleaned = re.sub(r"\s+", " ", text).strip()
        return cleaned[:60], []

    # 常见品类的「窄词 → 宽词」回退：模型常给 运动鞋/高帮鞋，
    # 而商品标题/描述里可能只出现 鞋；补上短词可提高 OR 命中率
    _CATEGORY_TAILS = ("运动鞋", "球鞋", "高帮鞋", "皮鞋", "板鞋")

    def _expand_keywords(self, keywords: list[str]) -> list[str]:
        expanded: list[str] = []
        seen: set[str] = set()

        def add(word: str) -> None:
            w = word.strip()
            if w and w.lower() not in seen:
                seen.add(w.lower())
                expanded.append(w)

        for kw in keywords:
            add(kw)
            # 鞋类：补一个「鞋」字宽词
            if kw in self._CATEGORY_TAILS or (len(kw) >= 2 and kw.endswith("鞋")):
                add("鞋")
        return expanded

    def search_by_image(
        self,
        image_bytes: bytes,
        *,
        page: int = 1,
        page_size: int = 12,
    ) -> AISearchByImageOut:
        if not settings.ai_enabled or not self.client.is_available():
            raise OllamaError("AI 服务当前不可用，请稍后再试或改用文字搜索")

        image_b64 = base64.b64encode(image_bytes).decode("ascii")
        raw = self.client.vision_describe(image_b64, _VISION_PROMPT)
        item, keywords = self._parse_vision_output(raw)

        # 拼装查询：物品名 + 关键词，去重保序
        parts: list[str] = []
        seen: set[str] = set()
        for token in ([item] if item else []) + keywords:
            t = token.strip()
            if t and t.lower() not in seen:
                seen.add(t.lower())
                parts.append(t)
        query = " ".join(parts).strip()

        if not query:
            return AISearchByImageOut(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                mode="keyword",
                used_llm=True,
                fallback=True,
                recognized_item=item or None,
                keywords=keywords,
                query=query,
            )

        # 把识别出的词逐个传给检索：关键词分支按「任一词命中」匹配，
        # 整串 query 仍用于向量语义检索与结果展示；窄词补宽词提高命中率
        kw_list = self._expand_keywords(parts) if parts else None
        result = self.search_service.search(
            query, page=page, page_size=page_size, keywords=kw_list
        )
        return AISearchByImageOut(
            items=result.items,
            total=result.total,
            page=result.page,
            page_size=result.page_size,
            mode=result.mode,
            used_llm=True,
            fallback=result.fallback,
            recognized_item=item or None,
            keywords=keywords,
            query=query,
        )
