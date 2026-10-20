import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.storage.repo_store import repo_store
from backend.app.config import settings

@pytest.fixture(autouse=True)
def setup_sample_repo():
    sample_dir = settings.SAMPLE_REPOS_DIR / "sample_ecommerce"
    if sample_dir.exists():
        repo_store.index_workspace(
            repo_id="sample-ecommerce",
            repo_name="Sample Multi-Language E-Commerce",
            workspace_dir=sample_dir,
            source_type="sample",
            source_url="local://sample_ecommerce"
        )

@pytest.mark.anyio
async def test_health_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["app"] == "TraceBench"
        assert len(data["supported_languages"]) == 9

@pytest.mark.anyio
async def test_get_repositories():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/repositories")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert any(r["id"] == "sample-ecommerce" for r in data)

@pytest.mark.anyio
async def test_get_repository_metadata():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/repositories/sample-ecommerce")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "sample-ecommerce"
        assert data["file_count"] >= 10
        assert data["symbol_count"] >= 10
        assert "python" in data["language_breakdown"]
        assert "javascript" in data["language_breakdown"]
        assert "go" in data["language_breakdown"]
        assert "rust" in data["language_breakdown"]

@pytest.mark.anyio
async def test_get_files_and_content():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/repositories/sample-ecommerce/files")
        assert resp.status_code == 200
        files = resp.json()
        assert len(files) >= 10

        content_resp = await client.get(
            "/api/repositories/sample-ecommerce/files/content",
            params={"path": "services/tax_calculator.py"}
        )
        assert content_resp.status_code == 200
        content_data = content_resp.json()
        assert "calculate_tax" in content_data["content"]
        assert content_data["language"] == "python"

@pytest.mark.anyio
async def test_get_symbols():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/repositories/sample-ecommerce/symbols")
        assert resp.status_code == 200
        symbols = resp.json()
        sym_names = [s["name"] for s in symbols]
        assert "calculate_tax" in sym_names
        assert "verifyToken" in sym_names
        assert "UserProfile" in sym_names

@pytest.mark.anyio
async def test_get_graph():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/repositories/sample-ecommerce/graph")
        assert resp.status_code == 200
        graph = resp.json()
        assert graph["total_nodes"] > 0
        assert graph["total_edges"] > 0
        assert any(e["relationship_type"] == "contains" for e in graph["edges"])

@pytest.mark.anyio
async def test_search_methods():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test TF-IDF method
        resp1 = await client.post(
            "/api/repositories/sample-ecommerce/search",
            json={"query": "calculate sales tax", "method": "tfidf", "top_k": 5}
        )
        assert resp1.status_code == 200
        res1 = resp1.json()
        assert len(res1["results"]) > 0
        assert "tax" in res1["results"][0]["snippet"].lower()

        # Test Graph-assisted method
        resp2 = await client.post(
            "/api/repositories/sample-ecommerce/search",
            json={"query": "calculate sales tax", "method": "graph_assisted", "top_k": 5}
        )
        assert resp2.status_code == 200
        res2 = resp2.json()
        assert len(res2["results"]) > 0
        assert "graph_signals" in res2["results"][0]

@pytest.mark.anyio
async def test_ask_ai_demo_mode():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/repositories/sample-ecommerce/ask",
            json={"question": "Where is tax calculation handled?", "retrieval_method": "tfidf"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert len(data["retrieved_evidence"]) > 0
        assert len(data["citations"]) > 0
        assert data["citations"][0]["is_valid"] is True
        assert "tax_calculator.py" in data["citations"][0]["file_path"]

@pytest.mark.anyio
async def test_evaluation_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/repositories/sample-ecommerce/evaluate")
        assert resp.status_code == 200
        eval_data = resp.json()
        assert eval_data["benchmark_size"] >= 10
        assert "tfidf" in eval_data["methods"]
        assert "graph_assisted" in eval_data["methods"]
        
        tfidf_res = eval_data["methods"]["tfidf"]
        assert tfidf_res["recall_at_5"] > 0.5  # Real measured recall on benchmark
        assert tfidf_res["mrr"] > 0.5
        assert tfidf_res["avg_latency_ms"] >= 0.0

@pytest.mark.anyio
async def test_not_found_handling():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/repositories/non-existent-id")
        assert resp.status_code == 404

@pytest.mark.anyio
async def test_api_upload_zip_success():
    import io, zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("calc.py", "def add(a, b):\n    return a + b\n")
        zf.writestr("README.md", "# Test Project")
    
    files = {"file": ("test_project.zip", buf.getvalue(), "application/zip")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/repositories/upload", files=files)
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "test_project"
        assert data["source_type"] == "zip"
        assert data["file_count"] == 2
        assert data["parsed_file_count"] == 1

@pytest.mark.anyio
async def test_api_upload_non_zip_rejected():
    files = {"file": ("test.txt", b"plain text", "text/plain")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/repositories/upload", files=files)
        assert resp.status_code == 400
        assert "Only .zip" in resp.json()["detail"]

@pytest.mark.anyio
async def test_api_upload_empty_zip_rejected():
    files = {"file": ("empty.zip", b"", "application/zip")}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/repositories/upload", files=files)
        assert resp.status_code == 400

@pytest.mark.anyio
async def test_api_github_import_invalid_url():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/repositories/github", json={"url": "not-a-url"})
        assert resp.status_code == 400
        assert "Invalid GitHub repository URL" in resp.json()["detail"]

@pytest.mark.anyio
async def test_api_github_import_not_found():
    from unittest.mock import patch, AsyncMock, MagicMock
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.content = b"Not Found"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/repositories/github", json={"url": "https://github.com/fake/nonexistent"})
            assert resp.status_code == 400
            assert "not found" in resp.json()["detail"].lower()

@pytest.mark.anyio
async def test_api_github_import_success_mocked():
    import io, zipfile
    from unittest.mock import patch, AsyncMock, MagicMock
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("app.py", "def run():\n    print('hello')\n")
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = buf.getvalue()

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_resp
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/repositories/github", json={"url": "https://github.com/testuser/mockrepo"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["name"] == "testuser/mockrepo"
            assert data["source_type"] == "github"
            assert data["file_count"] == 1

