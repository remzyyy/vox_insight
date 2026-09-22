"""Central configuration loaded from environment (.env)."""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # dotenv optional
    pass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "").strip()
    openai_chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    openai_embed_model: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

    vapi_webhook_secret: str = os.getenv("VAPI_WEBHOOK_SECRET", "change-me")
    deepgram_api_key: str = os.getenv("DEEPGRAM_API_KEY", "").strip()

    kb_store_path: str = os.getenv("KB_STORE_PATH", "data/kb_store.sqlite")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    @property
    def has_openai(self) -> bool:
        return bool(self.openai_api_key)


settings = Settings()
