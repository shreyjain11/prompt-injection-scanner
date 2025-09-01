"""
Repository indexer for building a lightweight index of repository files.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import hashlib
import time

from .file_processor import FileProcessor
from ..utils.file_utils import get_scannable_files, get_relative_path


@dataclass
class IndexedFile:
    """Represents a single indexed file with metadata."""
    path: str
    relative_path: str
    size_bytes: int
    modified_time: float
    extension: str
    language: Optional[str]
    sha256: Optional[str]


class RepositoryIndexer:
    """Indexes a repository by collecting metadata for scannable files."""

    def __init__(
        self,
        exclude_patterns: Optional[List[str]] = None,
        include_patterns: Optional[List[str]] = None,
        max_file_size_bytes: Optional[int] = None,
        verbose: bool = False
    ) -> None:
        self.exclude_patterns = exclude_patterns or []
        self.include_patterns = include_patterns or []
        self.max_file_size_bytes = max_file_size_bytes
        self.verbose = verbose
        self.file_processor = FileProcessor()

        # Override file processor max size if provided
        if self.max_file_size_bytes is not None:
            self.file_processor.max_file_size = self.max_file_size_bytes

    def index(self, root_path: Path) -> Dict[str, Any]:
        """
        Build an index of scannable files within root_path.

        Returns a dictionary with files and summary statistics suitable for JSON serialization.
        """
        start_time = time.time()

        files = get_scannable_files(
            root_path,
            exclude_patterns=self.exclude_patterns,
            include_patterns=self.include_patterns
        )

        indexed_files: List[IndexedFile] = []
        language_counts: Dict[str, int] = {}
        total_size = 0

        for file_path in files:
            try:
                stat = file_path.stat()
                size_bytes = stat.st_size
                if self.max_file_size_bytes is not None and size_bytes > self.max_file_size_bytes:
                    # Respect max size if set explicitly
                    continue

                content = self.file_processor.read_file(file_path)
                # Even if content is None (e.g., skipped due to binary/size), still index basic metadata
                language = None
                if content is not None:
                    language = self.file_processor.detect_language(file_path, content)

                # Compute a fast sha256 hash (over full content when available)
                sha256_hash = None
                try:
                    hasher = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        for chunk in iter(lambda: f.read(1024 * 1024), b""):
                            hasher.update(chunk)
                    sha256_hash = hasher.hexdigest()
                except Exception:
                    sha256_hash = None

                rel = get_relative_path(file_path, root_path)
                indexed = IndexedFile(
                    path=str(file_path.resolve()),
                    relative_path=rel,
                    size_bytes=size_bytes,
                    modified_time=stat.st_mtime,
                    extension=file_path.suffix.lower(),
                    language=language,
                    sha256=sha256_hash
                )
                indexed_files.append(indexed)

                if language:
                    language_counts[language] = language_counts.get(language, 0) + 1
                total_size += size_bytes
            except Exception:
                # Skip files that cannot be accessed
                continue

        duration = time.time() - start_time

        return {
            "root_path": str(root_path.resolve()),
            "generated_at": time.time(),
            "duration_seconds": duration,
            "total_files": len(indexed_files),
            "total_bytes": total_size,
            "languages": language_counts,
            "files": [
                {
                    "path": f.path,
                    "relative_path": f.relative_path,
                    "size_bytes": f.size_bytes,
                    "modified_time": f.modified_time,
                    "extension": f.extension,
                    "language": f.language,
                    "sha256": f.sha256,
                }
                for f in indexed_files
            ],
        }



