"""
Utilities to fetch public repositories (GitHub) to a local temporary directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple
import tempfile
import requests
import zipfile
import io
import re


GITHUB_REPO_RE = re.compile(r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/#?]+)(?:/tree/(?P<ref>[^/#?]+))?/?$")


def parse_github_url(url: str) -> Optional[Tuple[str, str, Optional[str]]]:
    """Parse a GitHub repository URL and return (owner, repo, ref).

    Supports URLs like:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/
    - https://github.com/owner/repo/tree/branch
    """
    match = GITHUB_REPO_RE.match(url.strip())
    if not match:
        return None
    owner = match.group("owner")
    repo = match.group("repo")
    ref = match.group("ref")
    return owner, repo, ref


def _get_github_default_branch(owner: str, repo: str) -> str:
    """Get default branch for a public GitHub repo (unauthenticated)."""
    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    resp = requests.get(api_url, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("default_branch", "main")


def fetch_github_repo_to_dir(url: str, dest_dir: Optional[Path] = None) -> Path:
    """Download and extract a public GitHub repository to a directory.

    Args:
        url: GitHub repo URL
        dest_dir: Optional directory to extract into; if None, create a temp dir

    Returns:
        Path to the extracted repository root directory
    """
    parsed = parse_github_url(url)
    if not parsed:
        raise ValueError("Unsupported repository URL. Only GitHub public URLs are supported, e.g., https://github.com/owner/repo or /tree/branch")
    owner, repo, ref = parsed
    if not ref:
        ref = _get_github_default_branch(owner, repo)

    archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{ref}"
    r = requests.get(archive_url, timeout=60)
    if r.status_code != 200:
        # Fallback to master if main/default failed
        if ref != "master":
            alt_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/master"
            r = requests.get(alt_url, timeout=60)
        if r.status_code != 200:
            raise RuntimeError(f"Failed to download repository archive: HTTP {r.status_code}")

    zf = zipfile.ZipFile(io.BytesIO(r.content))

    extract_root = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp(prefix="repo_"))
    zf.extractall(extract_root)

    # The archive extracts into a single top-level folder like repo-ref/
    # Find the first directory inside extract_root
    subdirs = [p for p in extract_root.iterdir() if p.is_dir()]
    if len(subdirs) == 1:
        return subdirs[0]
    return extract_root



