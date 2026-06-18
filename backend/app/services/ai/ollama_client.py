from __future__ import annotations

import json
import logging
from typing import AsyncIterator, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_async_client: httpx.AsyncClient | None = None
_ollama_available_cache: bool | None = None


class OllamaError(Exception):
    pass


def _async_client_for(base_url: str, timeout: float) -> httpx.AsyncClient:
    global _async_client
    url = base_url.rstrip("/")
    if _async_client is None:
        _async_client = httpx.AsyncClient(base_url=url, timeout=timeout)
    return _async_client


class OllamaClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> None:
        self.base_url = (base_url or settings.ollama_base_url).rstrip("/")
        self.timeout = timeout or settings.ai_request_timeout_seconds

    def is_available(self) -> bool:
        global _ollama_available_cache
        if _ollama_available_cache is not None:
            return _ollama_available_cache
        try:
            with httpx.Client(base_url=self.base_url, timeout=2.0) as client:
                _ollama_available_cache = client.get("/api/tags").status_code == 200
        except Exception:
            _ollama_available_cache = False
        return _ollama_available_cache

    def _client(self, *, timeout: Optional[float] = None) -> httpx.Client:
        """同步 httpx 客户端（调用方负责 with 上下文关闭）。"""
        return httpx.Client(base_url=self.base_url, timeout=timeout or self.timeout)

    def vision_describe(
        self,
        image_b64: str,
        prompt: str,
        *,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> str:
        """用多模态模型识别图片，返回模型生成的文本。

        image_b64 为不含 data URI 前缀的纯 base64 字符串。
        """
        model = model or settings.ollama_vision_model
        payload: dict = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt, "images": [image_b64]},
            ],
            "stream": False,
            "keep_alive": settings.ollama_keep_alive,
            "options": {"temperature": 0.1, "num_predict": 256},
        }
        if "qwen3" in model.lower():
            payload["think"] = False
        t = timeout or settings.ai_vision_timeout_seconds
        try:
            with self._client(timeout=t) as client:
                r = client.post("/api/chat", json=payload)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as exc:
            global _ollama_available_cache
            _ollama_available_cache = None
            raise OllamaError(f"Ollama 图片识别失败: {exc}") from exc
        content = (data.get("message") or {}).get("content") or ""
        return content.strip()

    def embed(self, text: str, *, model: Optional[str] = None, timeout: Optional[float] = None) -> list[float]:
        model = model or settings.ollama_embed_model
        payload = {"model": model, "input": text}
        t = timeout or min(8.0, self.timeout)
        try:
            with httpx.Client(base_url=self.base_url, timeout=t) as client:
                r = client.post("/api/embed", json=payload)
                if r.status_code == 404:
                    r = client.post("/api/embeddings", json=payload)
                r.raise_for_status()
                data = r.json()
        except httpx.HTTPError as exc:
            raise OllamaError(f"Ollama embedding 失败: {exc}") from exc

        emb = data.get("embedding")
        if not emb and "embeddings" in data:
            embeddings = data["embeddings"]
            if embeddings:
                emb = embeddings[0]
                if emb and isinstance(emb[0], list):
                    emb = emb[0]
        if not emb:
            raise OllamaError("Ollama 未返回 embedding 向量")
        return [float(x) for x in emb]

    async def achat_stream(
        self,
        messages: list[dict[str, str]],
        *,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        model = model or settings.ollama_chat_model
        payload: dict = {
            "model": model,
            "messages": messages,
            "stream": True,
            "keep_alive": settings.ollama_keep_alive,
            "options": {
                "num_predict": settings.ai_chat_num_predict,
                "temperature": 0.35,
                "top_p": 0.9,
            },
        }
        if "qwen3" in model.lower():
            payload["think"] = False

        client = _async_client_for(self.base_url, self.timeout)
        try:
            async with client.stream("POST", "/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.strip():
                        continue
                    try:
                        chunk = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if chunk.get("done"):
                        break
                    msg = chunk.get("message") or {}
                    content = msg.get("content")
                    if content:
                        yield content
        except httpx.HTTPError as exc:
            global _ollama_available_cache
            _ollama_available_cache = None
            raise OllamaError(f"Ollama 对话流失败: {exc}") from exc
