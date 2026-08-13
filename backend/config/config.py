import os
import yaml

from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Self

load_dotenv(encoding="utf-8")

def _default_config_candidates() -> tuple[Path, ...]:
    backend_dir = Path(__file__).resolve().parents[2]
    repo_root = backend_dir.parent
    return backend_dir / "config.yaml", repo_root / "config.yaml"

class AgentConfig(BaseModel):
    """Config for the Code generate agent"""

    log_level: str = Field(default="info", description="Logging level for code generate agent (debug/info/warning/error)")
    temperature: float = Field(default=0.5, description="The temperature of the model")
    max_tokens: int = Field(default=1024, description="The max tokens of the model")
    timeout: int = Field(default=300, description="The timeout of the model")
    max_retries: int = Field(default=3, description="The max retries of the model")
    summarization_trigger_messages: int = Field(default=10, description="The messages count when summarization is triggered")
    summarization_trigger_tokens: int = Field(default=100, description="The tokens count when summarization is triggered")
    model_type: str = Field(default="deepseek", description="Model type for agent (openai/xiaomi/deepseek/qwen/glm)")
    embedding_model_type: str = Field(default="qwen_embedding", description="Model type for embedding (qwen_embedding)")
    print_thinking_process: bool = Field(default=True, description="Whether print the thinking process")
    user_memory: bool = Field(default=True, description="Whether use user memory or not")
    debounce_seconds: int = Field(default=10, ge=1, le=30, description="Seconds to wait before processing queued updates (debounce)")
    fact_confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold for storing facts")
    max_facts: int = Field(default=50, ge=10, le=100, description="Maximum number of facts to store")
    max_injection_tokens: int = Field(
        default=1000,
        ge=100,
        le=4000,
        description="Maximum tokens to use for memory injection",
    )
    model_cycle_max: int = Field(default=10,description="Maximum model cycle for one request")
    rerank_score_min: float = Field(default=0.8, ge=0, le=1, description="Minimum score for rerank score")
    es_index: str = Field(default="rag_chunk_index", description="The index of es")
    es_address: str = Field(default="http://localhost:9200", description="The address of es")
    open_tool_call_trace: bool = Field(default=False, description="Where open tool call trace, true/false")


    @classmethod
    def resolve_config_path(cls, config_path: str | None = None) -> Path:
        """Resolve the config file path.

        Priority:
        1. If provided `config_path` argument, use it.
        2. If provided `CODE_GENERATE_AGENT_CONFIG_PATH` environment variable, use it.
        3. Otherwise, search deterministic backend/repository-root defaults from `_default_config_candidates()`.
        """
        if config_path:
            path = Path(config_path)
            if not Path.exists(path):
                raise FileNotFoundError(f"Config file specified by param `config_path` not found at {path}")
            return path
        elif os.getenv("ASSISTANT_AGENT_CONFIG_PATH"):
            path = Path(os.getenv("ASSISTANT_AGENT_CONFIG_PATH"))
            if not Path.exists(path):
                raise FileNotFoundError(
                    f"Config file specified by environment variable `ASSISTANT_AGENT_CONFIG_PATH` not found at {path}")
            return path
        else:
            for path in _default_config_candidates():
                if path.exists():
                    return path
            raise FileNotFoundError("`config.yaml` file not found at the default backend or repository root locations")

    @classmethod
    def from_file(cls, config_path: str | None = None) -> Self:
        """Load config from YAML file.

        See `resolve_config_path` for more details.

        Args:
            config_path: Path to the config file.

        Returns:
            AgentConfig: The loaded config.
        """
        resolved_path = cls.resolve_config_path(config_path)
        with open(resolved_path, encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

        return cls.model_validate(config_data)

_app_config: AgentConfig | None = None

def get_app_config() -> AgentConfig:
    """Get the Code generate agent config instance."""
    global _app_config

    if _app_config is not None:
        return _app_config


    resolved_path = AgentConfig.resolve_config_path()
    _app_config = AgentConfig.from_file(str(resolved_path))

    return _app_config

if __name__ == "__main__":
    print(get_app_config())