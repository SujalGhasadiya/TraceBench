import io
import zipfile
import pytest
from pathlib import Path
from backend.app.ingestion.zip_ingestion import safe_extract_zip, ZipSecurityError
from backend.app.ingestion.github_ingestion import parse_github_url, GitHubIngestionError
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

def test_github_url_parser():
    owner, repo = parse_github_url("https://github.com/facebook/react")
    assert owner == "facebook"
    assert repo == "react"

    owner, repo = parse_github_url("https://github.com/tiangolo/fastapi.git")
    assert owner == "tiangolo"
    assert repo == "fastapi"

    with pytest.raises(GitHubIngestionError):
        parse_github_url("https://notgithub.com/user/repo")

    with pytest.raises(GitHubIngestionError):
        parse_github_url("invalid-url")
