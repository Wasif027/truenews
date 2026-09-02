from __future__ import annotations

from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://truenews:truenews@localhost:5432/truenews"

    @field_validator("database_url")
    @classmethod
    def _normalise_db_url(cls, v: str) -> str:
        # Managed Postgres (Neon, Render, Heroku, ...) hand out plain
        # `postgres://` / `postgresql://` URLs. SQLAlchemy needs the driver
        # named and this project uses psycopg 3, so coerce the scheme rather
        # than making every deploy get the prefix exactly right.
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                v = "postgresql+psycopg://" + v[len(prefix) :]
                break
        # Neon and most managed Postgres require TLS; add it if the URL omits it.
        if "neon.tech" in v and "sslmode=" not in v:
            v += ("&" if "?" in v else "?") + "sslmode=require"
        return v
    # Countries to ingest and serve, comma-separated. The first is the default.
    countries: str = "bd,in"

    @property
    def country_list(self) -> list[str]:
        return [c.strip() for c in self.countries.split(",") if c.strip()]

    @property
    def default_country(self) -> str:
        return self.country_list[0]

    cluster_window_hours: int = 72
    # Cosine similarity (headline embeddings) to link two articles into one story.
    # 0.80 tuned on real Bangladeshi feeds; lower = more merging.
    cluster_sim_threshold: float = 0.80

    # LLM providers, tried in order. Fill the numbered slots (LLM_1_*, LLM_2_*,
    # LLM_3_*) with any OpenAI-compatible endpoint; a slot is active once its
    # KEY, BASE, and MODEL are all set. Within a slot, MODEL may be a
    # comma-separated list. With no slot filled, the offline heuristic is used.
    llm_1_key: str = ""
    llm_1_base: str = ""
    llm_1_model: str = ""
    llm_2_key: str = ""
    llm_2_base: str = ""
    llm_2_model: str = ""
    llm_3_key: str = ""
    llm_3_base: str = ""
    llm_3_model: str = ""

    @property
    def llm_providers(self) -> list[tuple[str, str, str]]:
        """(base_url, api_key, model_csv) for each configured provider, in order."""
        slots = [
            (self.llm_1_base, self.llm_1_key, self.llm_1_model),
            (self.llm_2_base, self.llm_2_key, self.llm_2_model),
            (self.llm_3_base, self.llm_3_key, self.llm_3_model),
        ]
        return [s for s in slots if all(s)]

    summary_budget_per_run: int = 40

    frontend_origin: str = "http://localhost:3000"

    # Auth. Generate a real secret for anything deployed:
    #   python -c "import secrets; print(secrets.token_hex(32))"
    secret_key: str = "dev-insecure-secret-change-me-before-you-deploy-anything"
    token_ttl_days: int = 30
    cookie_secure: bool = False  # True when the site is served over https

    # Run ingestion inside the API process every N minutes (0 = off; use the
    # GitHub Actions cron for the deployed version instead).
    ingest_interval_min: int = 0

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    embedding_dim: int = 384


@lru_cache
def get_settings() -> Settings:
    return Settings()
