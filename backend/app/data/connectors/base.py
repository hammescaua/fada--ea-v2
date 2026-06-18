"""Fonte HTTP base: cache em disco + retry com backoff exponencial.

O cache torna a ingestão reprodutível e re-executável offline (uma vez populado
o ``data/raw/cache``). Em produção o cache migra para Redis sem mudar a interface.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

import httpx

from app.core.config import settings


class HttpDataSource:
    """Cliente HTTP com cache JSON em arquivo e tentativas com backoff."""

    def __init__(
        self,
        cache_dir: Path | None = None,
        timeout: float = 60.0,
        max_retries: int = 4,
        use_cache: bool = True,
    ) -> None:
        self.cache_dir = cache_dir or settings.cache_dir
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_cache = use_cache

    def _cache_key(self, url: str, params: dict[str, Any] | None) -> Path:
        raw = url + "?" + json.dumps(params or {}, sort_keys=True)
        digest = hashlib.sha256(raw.encode()).hexdigest()[:24]
        return self.cache_dir / f"{digest}.json"

    def get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        cache_file = self._cache_key(url, params)
        if self.use_cache and cache_file.exists():
            return json.loads(cache_file.read_text())

        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                resp = httpx.get(url, params=params, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()
                if self.use_cache:
                    cache_file.parent.mkdir(parents=True, exist_ok=True)
                    cache_file.write_text(json.dumps(data))
                return data
            except Exception as exc:  # noqa: BLE001 — retry em qualquer falha de rede
                last_exc = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
        raise RuntimeError(f"Falha ao obter {url} após {self.max_retries} tentativas") from last_exc
