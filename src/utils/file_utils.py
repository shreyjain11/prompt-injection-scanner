"""
File utilities for the scanner.
"""

import re
from pathlib import Path
from typing import List, Set
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern


def get_scannable_files(
    root_path: Path, 
    exclude_patterns: List[str] = None,
    include_patterns: List[str] = None
) -> List[Path]:
    """
    Get all scannable files in a directory.
    
    Args:
        root_path: Root directory to scan
        exclude_patterns: Patterns to exclude (e.g., ['node_modules', 'dist'])
        include_patterns: Patterns to include (if None, include all scannable files)
        
    Returns:
        List of file paths to scan
    """
    exclude_patterns = exclude_patterns or []
    include_patterns = include_patterns or []
    
    # Load .gitignore if present and merge into excludes
    gitignore_path = root_path / '.gitignore'
    if gitignore_path.exists():
        try:
            lines = gitignore_path.read_text().splitlines()
            # Keep non-empty, non-comment lines
            gitignore_patterns = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith('#')]
            # Convert gitignore entries to pathspec-friendly patterns (leave as-is; pathspec supports GitWildMatchPattern)
            exclude_patterns = list(exclude_patterns) + gitignore_patterns
        except Exception:
            pass
    
    # Build pathspec for exclusion
    exclude_spec = None
    if exclude_patterns:
        exclude_spec = PathSpec.from_lines(GitWildMatchPattern, exclude_patterns)
    
    # Build pathspec for inclusion
    include_spec = None
    if include_patterns:
        include_spec = PathSpec.from_lines(GitWildMatchPattern, include_patterns)
    
    scannable_files = []
    
    # Walk through all files
    for file_path in root_path.rglob('*'):
        if not file_path.is_file():
            continue
        
        # Skip if excluded
        if exclude_spec and exclude_spec.match_file(str(file_path)):
            continue
        
        # Skip if not included (when include patterns are specified)
        if include_spec and not include_spec.match_file(str(file_path)):
            continue
        
        # Check if file is scannable
        if is_scannable_file(file_path):
            scannable_files.append(file_path)
    
    return scannable_files


def is_scannable_file(file_path: Path) -> bool:
    """
    Check if a file should be scanned.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file should be scanned
    """
    # Skip hidden files and directories
    if any(part.startswith('.') for part in file_path.parts):
        return False
    
    # Skip common directories that shouldn't be scanned
    skip_dirs = {
        'node_modules', 'dist', 'build', 'target', '__pycache__', '.git',
        'vendor', 'bower_components', 'jspm_packages', 'coverage',
        '.pytest_cache', '.mypy_cache', '.tox', '.venv', 'venv', 'env'
    }
    
    if any(part in skip_dirs for part in file_path.parts):
        return False
    
    # Check file extension
    scannable_extensions = {
        # Programming languages
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.cs', '.php',
        '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.dart', '.r', '.m', '.mm',
        # Web technologies
        '.html', '.htm', '.css', '.scss', '.sass', '.less', '.vue', '.svelte',
        # Configuration files
        '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf', '.config',
        '.env', '.properties', '.xml', '.csv',
        # Documentation
        '.md', '.txt', '.rst', '.adoc',
        # Shell scripts
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
        # Other
        '.sql', '.graphql', '.gql', '.proto', '.thrift'
    }
    
    if file_path.suffix.lower() in scannable_extensions:
        return True
    
    # Check if it's a text file without extension
    if not file_path.suffix:
        return is_text_file(file_path)
    
    return False


def is_text_file(file_path: Path) -> bool:
    """
    Check if a file appears to be a text file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        True if file appears to be text
    """
    try:
        # Check file size (skip very large files)
        if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB
            return False
        
        # Read first 1024 bytes to check for binary content
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            
            # Check for null bytes (common in binary files)
            if b'\x00' in chunk:
                return False
            
            # Check if mostly printable ASCII
            printable = sum(1 for byte in chunk if 32 <= byte <= 126 or byte in (9, 10, 13))
            if len(chunk) > 0 and printable / len(chunk) < 0.7:
                return False
            
            return True
            
    except (IOError, OSError):
        return False


def get_file_size_mb(file_path: Path) -> float:
    """Get file size in megabytes."""
    try:
        return file_path.stat().st_size / (1024 * 1024)
    except (IOError, OSError):
        return 0.0


def get_relative_path(file_path: Path, root_path: Path) -> str:
    """Get relative path from root."""
    try:
        return str(file_path.relative_to(root_path))
    except ValueError:
        return str(file_path)


def validate_path(path: Path) -> bool:
    """Validate that a path exists and is accessible."""
    try:
        return path.exists() and path.is_dir()
    except (IOError, OSError):
        return False


def get_common_exclude_patterns() -> List[str]:
    """Get common patterns to exclude from scanning."""
    return [
        # Dependencies
        'node_modules/**',
        'vendor/**',
        'bower_components/**',
        'jspm_packages/**',
        
        # Build outputs
        'dist/**',
        'build/**',
        'target/**',
        'out/**',
        '*.min.js',
        '*.min.css',
        
        # Cache directories
        '__pycache__/**',
        '.pytest_cache/**',
        '.mypy_cache/**',
        '.tox/**',
        '.cache/**',
        
        # Virtual environments
        '.venv/**',
        'venv/**',
        'env/**',
        '.env/**',
        
        # Version control
        '.git/**',
        '.svn/**',
        '.hg/**',
        
        # IDE files
        '.vscode/**',
        '.idea/**',
        '*.swp',
        '*.swo',
        '*~',
        
        # OS files
        '.DS_Store',
        'Thumbs.db',
        
        # Logs
        '*.log',
        'logs/**',
        
        # Generated files
        '*.pyc',
        '*.pyo',
        '*.class',
        '*.o',
        '*.so',
        '*.dll',
        '*.dylib',
        
        # Archives
        '*.zip',
        '*.tar.gz',
        '*.rar',
        '*.7z',
        
        # Media files
        '*.jpg',
        '*.jpeg',
        '*.png',
        '*.gif',
        '*.bmp',
        '*.ico',
        '*.svg',
        '*.pdf',
        '*.mp3',
        '*.mp4',
        '*.avi',
        '*.mov',
    ]




