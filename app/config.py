from dataclasses import dataclass
import os


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime configuration.

    The system is designed to run fully offline with deterministic components.
    An optional local LLM (Ollama) can be enabled for richer reply drafts, but
    it is OFF by default so the service never depends on an external process.
    """

    # Optional local LLM (Ollama). Disabled by default for reliability.
    use_ollama: bool = _env_bool("USE_OLLAMA", False)
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "mistral")
    ollama_timeout_s: float = float(os.getenv("OLLAMA_TIMEOUT_S", "15"))

    # Retrieval
    retrieval_top_k: int = int(os.getenv("RETRIEVAL_TOP_K", "4"))
    low_confidence_threshold: float = float(os.getenv("LOW_CONFIDENCE_THRESHOLD", "0.12"))

    # Cost model (used only for $/100 tickets estimate in evaluation)
    cost_per_1k_input_tokens: float = float(os.getenv("COST_PER_1K_INPUT", "0.0"))
    cost_per_1k_output_tokens: float = float(os.getenv("COST_PER_1K_OUTPUT", "0.0"))

    # Paths
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ticket_triage.db")
    data_dir: str = os.getenv("DATA_DIR", "./data")

    # CORS origins allowed to call the API (the Next.js dev server by default).
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:3000")


settings = Settings()


