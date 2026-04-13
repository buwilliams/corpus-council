from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class AppConfig:
    llm_provider: str
    llm_model: str
    embedding_provider: str
    embedding_model: str
    data_dir: Path
    chunk_max_size: int
    retrieval_top_k: int
    chroma_collection: str = "corpus"
    deliberation_mode: str = "parallel"

    @property
    def corpus_dir(self) -> Path:
        return self.data_dir / "corpus"

    @property
    def council_dir(self) -> Path:
        return self.data_dir / "council"

    @property
    def goals_dir(self) -> Path:
        return self.data_dir / "goals"

    @property
    def personas_dir(self) -> Path:
        return self.data_dir / "council"

    @property
    def goals_manifest_path(self) -> Path:
        return self.data_dir / "goals_manifest.json"

    @property
    def chunks_dir(self) -> Path:
        return self.data_dir / "chunks"

    @property
    def embeddings_dir(self) -> Path:
        return self.data_dir / "embeddings"

    @property
    def users_dir(self) -> Path:
        return self.data_dir / "users"


def _resolve_path(config_dir: Path, value: Any) -> Path:
    """Resolve a path value relative to the config file directory."""
    if not isinstance(value, str):
        raise ValueError(
            f"Expected a string path value, got {type(value).__name__!r}: {value!r}"
        )
    return (config_dir / value).resolve()


def _require_str(data: dict[str, Any], key: str) -> str:
    """Extract a required string value from a dict."""
    if key not in data:
        raise KeyError(f"Required key {key!r} is missing from config")
    val = data[key]
    if not isinstance(val, str):
        raise ValueError(
            f"Config key {key!r} must be a string, got {type(val).__name__!r}"
        )
    return val


def _require_int(data: dict[str, Any], key: str) -> int:
    """Extract a required int value from a dict."""
    if key not in data:
        raise KeyError(f"Required key {key!r} is missing from config")
    val = data[key]
    if not isinstance(val, int):
        raise ValueError(
            f"Config key {key!r} must be an int, got {type(val).__name__!r}"
        )
    return val


def _require_dict(data: dict[str, Any], key: str) -> dict[str, Any]:
    """Extract a required dict section from a dict."""
    if key not in data:
        raise KeyError(f"Required section {key!r} is missing from config")
    val = data[key]
    if not isinstance(val, dict):
        raise ValueError(
            f"Config section {key!r} must be a mapping, got {type(val).__name__!r}"
        )
    return val


_REMOVED_KEYS = (
    "corpus_dir",
    "council_dir",
    "goals_dir",
    "personas_dir",
    "goals_manifest_path",
)

_REMOVED_KEY_MESSAGES: dict[str, str] = {
    "corpus_dir": "the path is now derived as data_dir/corpus/ by convention.",
    "council_dir": "the path is now derived as data_dir/council/ by convention.",
    "goals_dir": "the path is now derived as data_dir/goals/ by convention.",
    "personas_dir": "the path is now derived as data_dir/council/ by convention.",
    "goals_manifest_path": (
        "the path is now derived as data_dir/goals_manifest.json by convention."
    ),
}


def load_config(path: str | Path) -> AppConfig:
    """Load and parse config.yaml, returning a fully typed AppConfig.

    Raises:
        FileNotFoundError: if the config file does not exist.
        KeyError: if a required key is absent.
        ValueError: if a value has the wrong type or a removed key is present.
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as fh:
        raw: Any = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(
            f"Config file must contain a YAML mapping, got {type(raw).__name__!r}"
        )

    data: dict[str, Any] = raw
    config_dir = config_path.parent.resolve()

    for removed_key in _REMOVED_KEYS:
        if removed_key in data:
            raise ValueError(
                f"Config key {removed_key!r} is no longer supported. "
                f"Remove it from your config file; "
                f"{_REMOVED_KEY_MESSAGES[removed_key]}"
            )

    llm_section = _require_dict(data, "llm")
    llm_provider = _require_str(llm_section, "provider")
    llm_model = _require_str(llm_section, "model")

    embedding_section = _require_dict(data, "embedding")
    embedding_provider = _require_str(embedding_section, "provider")
    embedding_model = _require_str(embedding_section, "model")

    chunking_section = _require_dict(data, "chunking")
    chunk_max_size = _require_int(chunking_section, "max_size")

    retrieval_section = _require_dict(data, "retrieval")
    retrieval_top_k = _require_int(retrieval_section, "top_k")

    chroma_collection_raw = data.get("chroma_collection", "corpus")
    if not isinstance(chroma_collection_raw, str):
        raw_type = type(chroma_collection_raw).__name__
        raise ValueError(
            f"Config key 'chroma_collection' must be a string, got {raw_type!r}"
        )
    chroma_collection: str = chroma_collection_raw

    deliberation_mode_raw = data.get("deliberation_mode", "parallel")
    if not isinstance(deliberation_mode_raw, str):
        raw_dm_type = type(deliberation_mode_raw).__name__
        raise ValueError(
            f"Config key 'deliberation_mode' must be a string, got {raw_dm_type!r}"
        )
    if deliberation_mode_raw not in {"parallel", "consolidated"}:
        raise ValueError(
            f"Config key 'deliberation_mode' must be 'parallel' or 'consolidated', "
            f"got {deliberation_mode_raw!r}"
        )
    deliberation_mode: str = deliberation_mode_raw

    return AppConfig(
        llm_provider=llm_provider,
        llm_model=llm_model,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        data_dir=_resolve_path(config_dir, data.get("data_dir", "data")),
        chunk_max_size=chunk_max_size,
        retrieval_top_k=retrieval_top_k,
        chroma_collection=chroma_collection,
        deliberation_mode=deliberation_mode,
    )


__all__ = ["AppConfig", "load_config"]
