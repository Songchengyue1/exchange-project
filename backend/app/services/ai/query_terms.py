"""从用户自然语言问题中提取商品检索词，并做同义词扩展。"""
from __future__ import annotations

import re
from typing import Literal

# 问句尾部/语气词，去掉后便于关键词命中标题
_STOP_PHRASES = (
    "有货吗",
    "有货么",
    "还有货吗",
    "有没有货",
    "有没有",
    "在售吗",
    "多少钱",
    "什么价",
    "价格多少",
    "请问",
    "能不能",
    "可以吗",
    "想要",
    "想买",
)

_PUNCT_RE = re.compile(r"[\s\?？!！。，,.、；;：:\"'‘’“”\[\]【】()（）]+")
_TOKEN_RE = re.compile(r"[a-zA-Z0-9]+|[\u4e00-\u9fff]{2,}")

# 同义词组：命中任一词则展开整组用于检索
_SYNONYM_GROUPS: tuple[tuple[str, ...], ...] = (
    ("iPhone", "苹果手机", "苹果", "apple", "iPone", "iPhon", "爱疯"),
    ("mac", "macbook", "苹果电脑", "苹果笔记本"),
    ("switch", "任天堂", "ns"),
    ("宜家", "ikea"),
)

_HINT_TOKENS = (
    "iPhone",
    "mac",
    "macbook",
    "switch",
    "ikea",
    "电脑",
    "手机",
    "笔记本",
    "平板",
    "耳机",
    "鞋",
    "桌",
    "书",
)

_BROWSE_ALL_HINTS = ("上架", "有什么", "有哪些", "看看", "浏览", "全部商品", "卖什么", "有什么卖")


def normalize_query(text: str) -> str:
    t = text.strip()
    for phrase in _STOP_PHRASES:
        t = t.replace(phrase, " ")
    t = _PUNCT_RE.sub(" ", t)
    return " ".join(t.split())


def _contains(haystack: str, needle: str) -> bool:
    return needle.lower() in haystack.lower()


def expand_search_terms(query: str) -> list[str]:
    """按优先级返回去重后的检索词（英文不强制小写，交给 SQL ilike）。"""
    raw = query.strip()
    if not raw:
        return []

    terms: list[str] = []
    seen: set[str] = set()
    low = f"{raw.lower()} {normalize_query(raw).lower()}"

    def add(term: str) -> None:
        term = term.strip()
        for phrase in _STOP_PHRASES:
            term = term.replace(phrase, " ").strip()
        if not term or len(term) == 1:
            return
        if any(phrase in term for phrase in _STOP_PHRASES if len(phrase) > 1):
            return
        key = term.lower()
        if key in seen:
            return
        seen.add(key)
        terms.append(term)

    for group in _SYNONYM_GROUPS:
        if any(_contains(low, alias) or alias in raw for alias in group):
            for alias in group:
                add(alias)

    normalized = normalize_query(raw)
    for part in _TOKEN_RE.findall(f"{raw} {normalized}"):
        add(part)

    for token in _HINT_TOKENS:
        if token in low:
            add(token)

    if not terms:
        compact = normalized or raw
        if len(compact) >= 2:
            add(compact)

    return terms[:10]


def is_browse_all_intent(query: str) -> bool:
    """宽泛浏览类问题才回退到「最新上架」列表。"""
    q = query.strip()
    if not q:
        return True
    return any(h in q for h in _BROWSE_ALL_HINTS)


_GENERIC_TERMS = frozenset(
    {"手机", "电脑", "书", "桌", "鞋", "平板", "笔记本", "耳机", "数码"},
)


def product_links_kind(query: str) -> Literal["target", "recommend"]:
    """区分用户是否在找具体商品（目标）还是泛推荐。"""
    if is_browse_all_intent(query):
        return "recommend"
    terms = expand_search_terms(query)
    specific = [t for t in terms if t.lower() not in _GENERIC_TERMS]
    return "target" if specific else "recommend"
