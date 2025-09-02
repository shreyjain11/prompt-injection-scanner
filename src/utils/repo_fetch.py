"""
Utilities to fetch public repositories (GitHub) to a local temporary directory.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple, List
import tempfile
import requests
import zipfile
import io
import re
import os


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


def _branch_exists_on_codeload(owner: str, repo: str, ref: str) -> bool:
    """Check if a branch exists by probing codeload (no API/rate-limit)."""
    url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{ref}"
    try:
        # HEAD is cheaper; GitHub codeload returns 200 when the ref exists
        resp = requests.head(url, timeout=15)
        return resp.status_code == 200
    except Exception:
        return False


def _choose_ref_without_api(owner: str, repo: str, explicit_ref: Optional[str]) -> str:
    """Resolve a reasonable branch ref without using the GitHub REST API.

    Strategy:
    - If an explicit ref was provided in the URL, use it first.
    - Otherwise probe a list of common default branch names on codeload.
    - If none are found, fall back to 'main'.
    """
    candidate_order: List[str] = []
    if explicit_ref:
        candidate_order.append(explicit_ref)

    # Common default branch names to try in order
    candidate_order.extend([
        "main",
        "master",
        "trunk",
        "dev",
        "develop",
        "release",
        "stable",
    ])

    # De-duplicate while keeping order
    seen = set()
    ordered_candidates = [c for c in candidate_order if not (c in seen or seen.add(c))]

    for ref in ordered_candidates:
        if _branch_exists_on_codeload(owner, repo, ref):
            return ref

    # Last resort: fall back to main if none detected
    return explicit_ref or "main"


def _get_github_default_branch_with_token(owner: str, repo: str) -> Optional[str]:
    """Use GitHub API to get default branch if a token is available.

    This avoids unauthenticated rate limits. Returns None on failure.
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        return None
    try:
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github+json",
        }
        resp = requests.get(api_url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("default_branch")
    except Exception:
        return None


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
    owner, repo, explicit_ref = parsed

    # Prefer codeload probing to avoid GitHub REST API rate limits
    ref = _choose_ref_without_api(owner, repo, explicit_ref)

    # If we still failed to find a working ref via codeload probing, and a token
    # exists, try the REST API once to discover the default branch.
    if not _branch_exists_on_codeload(owner, repo, ref):
        api_ref = _get_github_default_branch_with_token(owner, repo)
        if api_ref and _branch_exists_on_codeload(owner, repo, api_ref):
            ref = api_ref

    # Try to download the archive, iterating through reasonable fallbacks
    candidate_refs: List[str] = [ref]
    for fallback in ["main", "master", "trunk", "dev", "develop"]:
        if fallback not in candidate_refs:
            candidate_refs.append(fallback)

    r = None
    last_status = None
    for candidate in candidate_refs:
        archive_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{candidate}"
        resp = requests.get(archive_url, timeout=60)
        last_status = resp.status_code
        if resp.status_code == 200:
            r = resp
            ref = candidate
            break

    if r is None:
        tried = ", ".join(candidate_refs)
        raise RuntimeError(
            "Could not download repository archive from codeload. "
            f"Tried refs: {tried}. Provide an explicit branch in the URL "
            f"(e.g., https://github.com/{owner}/{repo}/tree/<branch>) or set a "
            "GITHUB_TOKEN on the API server to allow default-branch discovery. "
            f"Last HTTP status: {last_status}"
        )

    zf = zipfile.ZipFile(io.BytesIO(r.content))

    extract_root = Path(dest_dir) if dest_dir else Path(tempfile.mkdtemp(prefix="repo_"))
    zf.extractall(extract_root)

    # The archive extracts into a single top-level folder like repo-ref/
    # Find the first directory inside extract_root
    subdirs = [p for p in extract_root.iterdir() if p.is_dir()]
    if len(subdirs) == 1:
        return subdirs[0]
    return extract_root



