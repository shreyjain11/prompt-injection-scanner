"""
Caching system for scan results.
"""

import json
import hashlib
import time
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import asdict
import pickle


class ScanCache:
    """Cache for scan results to avoid re-scanning unchanged files."""
    
    def __init__(self, cache_dir: Optional[Path] = None, ttl: int = 3600):
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory to store cache files (default: ~/.prompt-scanner/cache)
            ttl: Time to live for cache entries in seconds (default: 1 hour)
        """
        if cache_dir is None:
            cache_dir = Path.home() / '.prompt-scanner' / 'cache'
        
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, file_path: Path) -> Optional[Any]:
        """
        Get cached result for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Cached result or None if not found/expired
        """
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        if not cache_file.exists():
            return None
        
        try:
            # Check if cache is expired
            if self._is_expired(cache_file):
                cache_file.unlink()
                return None
            
            # Check if file has been modified
            if self._file_modified(file_path, cache_file):
                cache_file.unlink()
                return None
            
            # Load cached result
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
            
            return cached_data['result']
            
        except (IOError, OSError, pickle.PickleError):
            # If there's any error reading the cache, remove it
            if cache_file.exists():
                cache_file.unlink()
            return None
    
    def set(self, file_path: Path, result: Any) -> None:
        """
        Cache a scan result.
        
        Args:
            file_path: Path to the file
            result: Scan result to cache
        """
        cache_key = self._get_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        try:
            # Get file metadata for change detection
            stat = file_path.stat()
            
            cached_data = {
                'result': result,
                'file_mtime': stat.st_mtime,
                'file_size': stat.st_size,
                'cached_at': time.time()
            }
            
            # Write to cache
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
                
        except (IOError, OSError):
            # If we can't write to cache, just continue
            pass
    
    def clear(self) -> None:
        """Clear all cached results."""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                cache_file.unlink()
        except (IOError, OSError):
            pass
    
    def clear_expired(self) -> None:
        """Clear expired cache entries."""
        try:
            for cache_file in self.cache_dir.glob("*.pkl"):
                if self._is_expired(cache_file):
                    cache_file.unlink()
        except (IOError, OSError):
            pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            cache_files = list(self.cache_dir.glob("*.pkl"))
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'total_entries': len(cache_files),
                'total_size_bytes': total_size,
                'cache_dir': str(self.cache_dir)
            }
        except (IOError, OSError):
            return {
                'total_entries': 0,
                'total_size_bytes': 0,
                'cache_dir': str(self.cache_dir)
            }
    
    def _get_cache_key(self, file_path: Path) -> str:
        """Generate a cache key for a file."""
        # Use absolute path and hash it
        abs_path = str(file_path.resolve())
        return hashlib.md5(abs_path.encode()).hexdigest()
    
    def _is_expired(self, cache_file: Path) -> bool:
        """Check if a cache file is expired."""
        try:
            stat = cache_file.stat()
            return (time.time() - stat.st_mtime) > self.ttl
        except (IOError, OSError):
            return True
    
    def _file_modified(self, file_path: Path, cache_file: Path) -> bool:
        """Check if the original file has been modified since caching."""
        try:
            # Load cached metadata
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
            
            # Get current file metadata
            current_stat = file_path.stat()
            
            # Compare modification time and size
            return (current_stat.st_mtime != cached_data['file_mtime'] or
                    current_stat.st_size != cached_data['file_size'])
                    
        except (IOError, OSError, pickle.PickleError):
            return True





