import io
import zipfile
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from backend.app.ingestion.zip_ingestion import safe_extract_zip, ZipSecurityError
from backend.app.ingestion.github_ingestion import (
    parse_github_url,
    download_and_extract_github_repo,
    GitHubIngestionError
)
from backend.app.config import settings

def create_in_memory_zip(file_dict: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in file_dict.items():
            zf.writestr(name, content)
    return buf.getvalue()

def test_safe_zip_extraction(tmp_path):
    files = {
        "src/main.py": "print('hello world')",
        "src/utils.js": "export function help() {}",
        "README.md": "# Documentation"
    }
    zip_bytes = create_in_memory_zip(files)
    count, total_bytes, skipped = safe_extract_zip(zip_bytes, tmp_path)
    
    assert count == 3
    assert (tmp_path / "src" / "main.py").exists()
    assert (tmp_path / "src" / "utils.js").exists()
    assert (tmp_path / "README.md").exists()
    assert len(skipped) == 0

def test_zip_with_windows_backslashes(tmp_path):
    files = {
        "myrepo\\src\\main.py": "print('windows')",
        "myrepo\\src\\helper.js": "export const x = 1;"
    }
    zip_bytes = create_in_memory_zip(files)
    count, total_bytes, skipped = safe_extract_zip(zip_bytes, tmp_path)
    assert count == 2
    assert (tmp_path / "src" / "main.py").exists() or (tmp_path / "myrepo" / "src" / "main.py").exists()

def test_zip_with_leading_slashes(tmp_path):
    files = {
        "/app/server.py": "def run(): pass\n",
        "/root.txt": "hello"
    }
    zip_bytes = create_in_memory_zip(files)
    count, total_bytes, skipped = safe_extract_zip(zip_bytes, tmp_path)
    assert count == 2
    assert (tmp_path / "app" / "server.py").exists()
    assert (tmp_path / "root.txt").exists()

def test_zip_empty_rejection(tmp_path):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        pass
    with pytest.raises(ZipSecurityError, match="empty"):
        safe_extract_zip(buf.getvalue(), tmp_path)

def test_zip_slip_rejection(tmp_path):
    # Construct a malicious zip entry trying to escape target_dir
    files = {
        "../../evil.py": "import os; os.system('echo pwned')",
        "safe.py": "print('safe')"
    }
    zip_bytes = create_in_memory_zip(files)
    with pytest.raises(ZipSecurityError, match="Malicious zip entry attempting path traversal"):
        safe_extract_zip(zip_bytes, tmp_path)

def test_skipped_secrets_and_ignored_directories(tmp_path):
    files = {
        ".git/HEAD": "ref: refs/heads/main",
        "node_modules/pkg/index.js": "module.exports = {}",
        ".env": "SECRET_KEY=12345",
        "cert.pem": "-----BEGIN CERTIFICATE-----",
        "app.py": "print('actual app')"
    }
    zip_bytes = create_in_memory_zip(files)
    count, total_bytes, skipped = safe_extract_zip(zip_bytes, tmp_path)
    
    assert count == 1
    assert (tmp_path / "app.py").exists()
    assert not (tmp_path / ".env").exists()
    assert not (tmp_path / "node_modules").exists()
    assert not (tmp_path / "cert.pem").exists()
    assert any(".env" in s for s in skipped)

def test_github_url_parser_extended():
    owner, repo, branch = parse_github_url("https://github.com/facebook/react")
    assert owner == "facebook"
    assert repo == "react"
    assert branch is None

    owner, repo, branch = parse_github_url("https://github.com/tiangolo/fastapi.git")
    assert owner == "tiangolo"
    assert repo == "fastapi"

    owner, repo, branch = parse_github_url("https://github.com/pallets/flask/tree/main")
    assert owner == "pallets"
    assert repo == "flask"
    assert branch == "main"

    owner, repo, branch = parse_github_url("https://github.com/expressjs/express/")
    assert owner == "expressjs"
    assert repo == "express"

    with pytest.raises(GitHubIngestionError):
        parse_github_url("https://notgithub.com/user/repo")

    with pytest.raises(GitHubIngestionError):
        parse_github_url("invalid-url")

@pytest.mark.anyio
async def test_download_and_extract_github_mocked(tmp_path):
    # Mock successful zipball response from GitHub
    valid_zip = create_in_memory_zip({"main.py": "print('ok')"})
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = valid_zip

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        repo_name, count, total_bytes, skipped = await download_and_extract_github_repo(
            "https://github.com/testuser/testrepo",
            tmp_path
        )
        assert repo_name == "testuser/testrepo"
        assert count == 1
        assert (tmp_path / "main.py").exists()

@pytest.mark.anyio
async def test_download_github_404(tmp_path):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b"Not Found"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(GitHubIngestionError, match="not found or is private"):
            await download_and_extract_github_repo(
                "https://github.com/testuser/nonexistent",
                tmp_path
            )

@pytest.mark.anyio
async def test_download_github_rate_limit(tmp_path):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.content = b"Rate limit"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        with pytest.raises(GitHubIngestionError, match="rate limit"):
            await download_and_extract_github_repo(
                "https://github.com/testuser/ratelimited",
                tmp_path
            )
