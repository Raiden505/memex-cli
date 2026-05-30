import os
from dataclasses import dataclass

from dotenv import load_dotenv

_REQUIRED = ["SUPABASE_URL", "SUPABASE_KEY", "GEMINI_API_KEY", "CHAT_MODEL", "EMBED_MODEL"]


class ConfigError(Exception):
    pass


@dataclass
class Config:
    supabase_url: str
    supabase_key: str
    gemini_api_key: str
    chat_model: str
    embed_model: str
    embed_dim: int = 768
    top_k: int = 5
    user_id: str = "00000000-0000-0000-0000-000000000001"


def load_config() -> Config:
    load_dotenv()
    missing = [v for v in _REQUIRED if not os.getenv(v)]
    if missing:
        lines = "\n".join(f"  {v}" for v in missing)
        raise ConfigError(
            f"Missing required environment variables:\n{lines}\n\n"
            "Copy .env.example to .env and fill in the values.\n"
            "See README.md for setup instructions."
        )
    return Config(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_KEY"],
        gemini_api_key=os.environ["GEMINI_API_KEY"],
        chat_model=os.environ["CHAT_MODEL"],
        embed_model=os.environ["EMBED_MODEL"],
        embed_dim=int(os.getenv("EMBED_DIM", "768")),
        top_k=int(os.getenv("TOP_K", "5")),
        user_id=os.getenv("RECALL_USER_ID", "00000000-0000-0000-0000-000000000001"),
    )
