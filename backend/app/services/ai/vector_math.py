from __future__ import annotations

import json
import math
from typing import Iterable, Optional


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def parse_embedding_json(raw: str) -> Optional[list[float]]:
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [float(x) for x in data]
    except (json.JSONDecodeError, TypeError, ValueError):
        return None
    return None


def average_vectors(vectors: Iterable[list[float]]) -> Optional[list[float]]:
    rows = [v for v in vectors if v]
    if not rows:
        return None
    dim = len(rows[0])
    acc = [0.0] * dim
    for v in rows:
        if len(v) != dim:
            continue
        for i, x in enumerate(v):
            acc[i] += x
    n = len(rows)
    return [x / n for x in acc]
