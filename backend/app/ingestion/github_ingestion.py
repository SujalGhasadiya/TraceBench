import re
from pathlib import Path
from typing import Tuple, List, Optional
import httpx
from .zip_ingestion import safe_extract_zip, ZipSecurityError

# Supports:
# https://github.com/owner/repo
# https://github.com/owner/repo/
# https://github.com/owner/repo.git
# https://github.com/owner/repo/tree/branch_name
GITHUB_URL_REGEX = re.compile(
    r"^https?://github\.com/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+?)(?:\.git)?(?:/tree/(?P<url_branch>[^/]+))?(?:/.*)?$"
)

class GitHubIngestionError(Exception):
    pass

def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
    """
    Parse owner, repo name, and optional embedded branch from a GitHub URL.
    Returns: (owner, repo, embedded_branch)
    """
    cleaned = url.strip()
    match = GITHUB_URL_REGEX.match(cleaned)
    if not match:
        raise GitHubIngestionError(
            "Invalid GitHub repository URL. Expected format: https://github.com/owner/repository"
        )
    owner = match.group("owner")
    repo = match.group("repo")
    url_branch = match.group("url_branch")
    return owner, repo, url_branch

async def download_and_extract_github_repo(
    github_url: str,
    target_dir: Path,
    branch: Optional[str] = None
) -> Tuple[str, int, int, List[str]]:
    """
    Downloads a public GitHub repository as a ZIP archive and extracts it safely.
    Returns:
      (repo_name, extracted_count, total_bytes, skipped_paths)
    """
    owner, repo, embedded_branch = parse_github_url(github_url)
    effective_branch = branch or embedded_branch
    repo_name = f"{owner}/{repo}"
    
    # Construct archive download endpoints in order of priority
    urls_to_try = []
    if effective_branch:
        urls_to_try.extend([
            f"https://github.com/{owner}/{repo}/archive/refs/heads/{effective_branch}.zip",
            f"https://github.com/{owner}/{repo}/archive/refs/tags/{effective_branch}.zip",
            f"https://github.com/{owner}/{repo}/archive/{effective_branch}.zip",
        ])
    else:
        urls_to_try.extend([
            # Direct default branch web archive (does not consume API rate limit)
            f"https://github.com/{owner}/{repo}/archive/HEAD.zip",
            f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
            f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
            f"https://api.github.com/repos/{owner}/{repo}/zipball"
        ])
    
    headers = {
        "User-Agent": "TraceBench-Code-Intelligence/1.0",
        "Accept": "application/vnd.github.v3+json, application/zip, application/octet-stream, */*"
    }

    zip_bytes: Optional[bytes] = None
    last_status = None
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=60.0) as client:
        for archive_url in urls_to_try:
            try:
                resp = await client.get(archive_url, headers=headers)
                last_status = resp.status_code
                # Verify HTTP 200 and standard ZIP magic bytes (PK..)
                if resp.status_code == 200 and len(resp.content) >= 4 and resp.content[:2] == b"PK":
                    zip_bytes = resp.content
                    break
            except httpx.TimeoutException:
                raise GitHubIngestionError(f"Connection timed out while downloading {github_url}. The repository may be too large or the network is slow.")
            except httpx.RequestError as e:
                raise GitHubIngestionError(f"Network error while connecting to GitHub: {str(e)}")

    if not zip_bytes:
        if last_status == 404:
            branch_msg = f" (branch '{effective_branch}')" if effective_branch else ""
            raise GitHubIngestionError(
                f"Repository{branch_msg} not found or is private on GitHub: {github_url}. Ensure the repository is public."
            )
        elif last_status == 403:
            raise GitHubIngestionError(
                "GitHub rate limit reached for this IP. Please wait a few minutes or upload the repository as a ZIP archive."
            )
        else:
            raise GitHubIngestionError(
                f"Failed to download repository archive from GitHub (HTTP {last_status})."
            )

    try:
        count, total_bytes, skipped = safe_extract_zip(zip_bytes, target_dir)
    except ZipSecurityError as e:
        raise GitHubIngestionError(str(e))
        
    return repo_name, count, total_bytes, skipped
