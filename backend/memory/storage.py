import abc
import json
import logging
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

def utc_now_iso_z() -> str:
    """Current UTC time as ISO-8601 with ``Z`` suffix (matches prior naive-UTC output)."""
    return datetime.now(UTC).isoformat().removesuffix("+00:00") + "Z"


def create_empty_memory() -> dict[str, Any]:
    """Create an empty memory structure."""
    return {
        "version": "1.0",
        "lastUpdated": utc_now_iso_z(),
        "user": {
            "workContext": {"summary": "", "updatedAt": ""},
            "personalContext": {"summary": "", "updatedAt": ""},
            "topOfMind": {"summary": "", "updatedAt": ""},
        },
        "history": {
            "recentMonths": {"summary": "", "updatedAt": ""},
            "earlierContext": {"summary": "", "updatedAt": ""},
            "longTermBackground": {"summary": "", "updatedAt": ""},
        },
        "facts": [],
    }


class MemoryStorage(abc.ABC):
    """Abstract base class for memory storage providers."""

    @abc.abstractmethod
    def load(self, user_id: str) -> dict[str, Any] | str:
        """Load memory data for the given user_id."""
        pass

    @abc.abstractmethod
    def reload(self, user_id: str) -> dict[str, Any]:
        """Force reload memory data for the given user_id."""
        pass

    @abc.abstractmethod
    def save(self, memory_data: dict[str, Any] | str, user_id: str) -> bool:
        """Save memory data for the given user_id."""
        pass

    @abc.abstractmethod
    def delete(self, user_id: str) -> bool:
        """Delete memory data for the given user_id."""
        pass


class FileMemoryStorage(MemoryStorage):
    """File-based memory storage provider."""

    def __init__(self):
        # user memory cache: key: user_id, Value: (memory_data, file_mtime)
        self._memory_cache: dict[str, tuple[dict[str, Any], float | None]] = {}
        # Guards all reads and writes to _memory_cache across concurrent callers.
        self._cache_lock = threading.Lock()
        """user memory: `{base_dir}/users/{user_id}/memory.json`."""
        self.repo_root = Path(__file__).parents[2]

    def get_memory_file_path(self, user_id: str) -> Path:
        """user memory: `{base_dir}/users/{user_id}/memory.json`."""
        return self.repo_root / "users" / user_id / "memory.json"

    def load_memory_from_file(self, user_id: str) -> dict[str, Any]:
        """Load memory data from file."""
        file_path = self.get_memory_file_path(user_id=user_id)

        if not file_path.exists():
            return create_empty_memory()

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            return data
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Failed to load memory file: %s", e)
            return create_empty_memory()

    @staticmethod
    def _cache_key(user_id: str) -> str:
        return user_id

    def load(self, user_id: str) -> dict[str, Any]:
        """Load memory data (cached with file modification time check)."""
        file_path = self.get_memory_file_path(user_id=user_id)
        cache_key = self._cache_key(user_id=user_id)

        try:
            current_mtime = file_path.stat().st_mtime if file_path.exists() else None
        except OSError:
            current_mtime = None

        with self._cache_lock:
            cached = self._memory_cache.get(cache_key)
            if cached is not None and cached[1] == current_mtime:
                return cached[0]

        memory_data = self.load_memory_from_file(user_id=user_id)

        with self._cache_lock:
            self._memory_cache[cache_key] = (memory_data, current_mtime)

        return memory_data

    def reload(self, user_id: str) -> dict[str, Any]:
        """Reload memory data from file, forcing cache invalidation."""
        file_path = self.get_memory_file_path(user_id=user_id)
        memory_data = self.load_memory_from_file(user_id=user_id)
        cache_key = self._cache_key(user_id=user_id)

        try:
            mtime = file_path.stat().st_mtime if file_path.exists() else None
        except OSError:
            mtime = None

        with self._cache_lock:
            self._memory_cache[cache_key] = (memory_data, mtime)
        return memory_data

    def save(self, memory_data: dict[str, Any], user_id: str) -> bool:
        """Save memory data to file and update cache."""
        file_path = self.get_memory_file_path(user_id=user_id)
        cache_key = self._cache_key(user_id=user_id)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Shallow-copy before adding lastUpdated so the caller's dict is not
            # mutated as a side-effect, and the cache reference is not silently
            # updated before the file write succeeds.
            memory_data = {**memory_data, "lastUpdated": utc_now_iso_z()}

            temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)

            temp_path.replace(file_path)

            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                mtime = None

            with self._cache_lock:
                self._memory_cache[cache_key] = (memory_data, mtime)
            logger.info("Memory saved to %s", file_path)
            return True
        except OSError as e:
            logger.error("Failed to save memory file: %s", e)
            return False

    def delete(self, user_id: str) -> bool:
        """Delete memory data to file to default value."""
        file_path = self.get_memory_file_path(user_id=user_id)
        cache_key = self._cache_key(user_id=user_id)

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            # Shallow-copy before adding lastUpdated so the caller's dict is not
            # mutated as a side-effect, and the cache reference is not silently
            # updated before the file write succeeds.
            memory_data = {**create_empty_memory(), "lastUpdated": utc_now_iso_z()}

            temp_path = file_path.with_suffix(f".{uuid.uuid4().hex}.tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(memory_data, f, indent=2, ensure_ascii=False)

            temp_path.replace(file_path)

            try:
                mtime = file_path.stat().st_mtime
            except OSError:
                mtime = None

            with self._cache_lock:
                self._memory_cache[cache_key] = (memory_data, mtime)
            logger.info("Memory delete from %s", file_path)
            return True
        except OSError as e:
            logger.error("Failed to delete memory file: %s", e)
            return False


_storage_instance: MemoryStorage | None = None
_storage_lock = threading.Lock()

def get_memory_storage() -> MemoryStorage:
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    _storage_instance = FileMemoryStorage()

    return _storage_instance
