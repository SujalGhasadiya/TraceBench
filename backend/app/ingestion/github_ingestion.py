import re
from pathlib import Path
from typing import Tuple, List, Optional
import httpx
from .zip_ingestion import safe_extract_zip, ZipSecurityError

GITHUB_URL_REGEX = re.compile(
    r"^https?://github\.com/(?P<owner>[a-zA-Z0-9_\-\.]+)/(?P<repo>[a-zA-Z0-9_\-\.]+?)(?:\.git)?(?:/)?$"
)

class GitHubIngestionError(Exception):
    pass

def parse_github_url(url: str) -> Tuple[str, str]:
    """Parse owner and repo name from GitHub URL, or raise GitHubIngestionError."""
    match = GITHUB_URL_REGEX.match(url.strip())
    if not match:
        raise GitHubIngestionError(
            "Invalid GitHub repository URL. Must be in format: https://github.com/owner/repository"
        )
    return match.group("owner"), match.group("repo")

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
    owner, repo = parse_github_url(github_url)
    repo_name = f"{owner}/{repo}"
    
    # Try archive download endpoints
    urls_to_try = []
    if branch:
        urls_to_try.append(f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip")
    urls_to_try.extend([
        f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip",
        f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip",
        f"https://api.github.com/repos/{owner}/{repo}/zipball"
    ])
    
    headers = {
        "User-Agent": "TraceBench-Code-Intelligence/1.0",
        "Accept": "application/vnd.github.v3+json"
    }

    zip_bytes: Optional[bytes] = None
    last_status = None
    
    async with httpx.AsyncClient(follow_redirects=True, timeout=30.0) as client:
        for archive_url in urls_to_try:
            try:
                resp = await client.get(archive_url, headers=headers)
                last_status = resp.status_code
                if resp.status_code == 200:
                    zip_bytes = resp.content
                    break
            except httpx.RequestError as e:
                raise GitHubIngestionError(f"Network error while connecting to GitHub: {str(e)}")

    if not zip_bytes:
        if last_status == 404:
            raise GitHubIngestionError(
                f"Repository not found or private: {github_url}. Ensure repository is public and default branch is accessible."
            )
        elif last_status == 403:
            raise GitHubIngestionError(
                "GitHub API rate limit exceeded. Please wait or upload repository directly as a ZIP file."
            )
        else:
            raise GitHubIngestionError(
                f"Failed to download repository from GitHub (HTTP status: {last_status})."
            )

    try:
        count, total_bytes, skipped = safe_extract_zip(zip_bytes, target_dir)
    except ZipSecurityError as e:
        raise GitHubIngestionError(str(e))
        
    return repo_name, count, total_bytes, skipped
