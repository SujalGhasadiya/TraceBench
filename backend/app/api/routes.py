import uuid
import time
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from pydantic import BaseModel

from ..config import settings
from ..models.schemas import (
    HealthResponse, RepositoryMetadata, IndexedFile, CodeSymbol,
    GraphResponse, SearchQuery, SearchResponse, AskRequest, AskResponse,
    EvaluationResult, LanguageCapability
)
from ..languages.registry import get_supported_languages, get_all_capabilities
from ..ingestion.zip_ingestion import safe_extract_zip, ZipSecurityError
from ..ingestion.github_ingestion import download_and_extract_github_repo, GitHubIngestionError
from ..storage.repo_store import repo_store
from ..ai.gemini_service import GeminiService

router = APIRouter()
gemini_service = GeminiService()

class GitHubImportRequest(BaseModel):
    url: str
    branch: Optional[str] = None

@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="healthy",
        app=settings.APP_NAME,
        version=settings.APP_VERSION,
        gemini_configured=gemini_service.is_live_configured,
        gemini_model=settings.GEMINI_MODEL,
        supported_languages=get_supported_languages()
    )

@router.get("/repositories", response_model=List[RepositoryMetadata])
def list_repositories():
    return repo_store.list_repos()

@router.post("/repositories/github", response_model=RepositoryMetadata)
async def import_github_repo(request: GitHubImportRequest):
    repo_id = str(uuid.uuid4())[:8]
    workspace_dir = settings.WORKSPACE_DIR / repo_id

    try:
        repo_name, count, total_bytes, skipped = await download_and_extract_github_repo(
            request.url, workspace_dir, request.branch
        )
        if count == 0:
            shutil.rmtree(workspace_dir, ignore_errors=True)
            raise HTTPException(
                status_code=400,
                detail="The repository was downloaded but contains no supported code files to index."
            )

        session = repo_store.index_workspace(
            repo_id=repo_id,
            repo_name=repo_name,
            workspace_dir=workspace_dir,
            source_type="github",
            source_url=request.url,
            initial_skipped=skipped
        )
        return session.metadata
    except HTTPException:
        shutil.rmtree(workspace_dir, ignore_errors=True)
        raise
    except GitHubIngestionError as e:
        shutil.rmtree(workspace_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        shutil.rmtree(workspace_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Unexpected ingestion failure: {str(e)}")

@router.post("/repositories/upload", response_model=RepositoryMetadata)
async def upload_zip_repo(file: UploadFile = File(...)):
    filename = (file.filename or "").strip()
    if not filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archive files are supported.")

    repo_id = str(uuid.uuid4())[:8]
    workspace_dir = settings.WORKSPACE_DIR / repo_id
    repo_name = Path(filename).stem or "uploaded_repo"

    try:
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="The uploaded ZIP file is empty (0 bytes).")
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded ZIP exceeds limit of {settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
            )
        count, total_bytes, skipped = safe_extract_zip(content, workspace_dir)
        if count == 0:
            shutil.rmtree(workspace_dir, ignore_errors=True)
            raise HTTPException(
                status_code=400,
                detail="The archive was extracted but contains no readable source files."
            )

        session = repo_store.index_workspace(
            repo_id=repo_id,
            repo_name=repo_name,
            workspace_dir=workspace_dir,
            source_type="zip",
            source_url=None,
            initial_skipped=skipped
        )
        return session.metadata
    except HTTPException:
        shutil.rmtree(workspace_dir, ignore_errors=True)
        raise
    except ZipSecurityError as e:
        shutil.rmtree(workspace_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        shutil.rmtree(workspace_dir, ignore_errors=True)
        raise HTTPException(status_code=500, detail=f"Failed to process ZIP: {str(e)}")

@router.post("/repositories/sample", response_model=RepositoryMetadata)
def load_sample_repo():
    sample_dir = settings.SAMPLE_REPOS_DIR / "sample_ecommerce"
    if not sample_dir.exists():
        raise HTTPException(status_code=404, detail="Sample repository directory not found.")

    repo_id = "sample-ecommerce"
    # Re-index fresh copy
    session = repo_store.index_workspace(
        repo_id=repo_id,
        repo_name="Sample Multi-Language E-Commerce",
        workspace_dir=sample_dir,
        source_type="sample",
        source_url="local://sample_ecommerce"
    )
    return session.metadata

@router.get("/repositories/{repository_id}", response_model=RepositoryMetadata)
def get_repository(repository_id: str):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return session.metadata

@router.get("/repositories/{repository_id}/files", response_model=List[IndexedFile])
def get_repository_files(repository_id: str):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return list(session.files.values())

@router.get("/repositories/{repository_id}/files/content")
def get_file_content(repository_id: str, path: str = Query(...)):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")
    if path not in session.raw_contents:
        raise HTTPException(status_code=404, detail=f"File '{path}' not found in indexed repository.")
    
    file_info = session.files.get(path)
    return {
        "file_path": path,
        "language": file_info.language if file_info else "text",
        "line_count": file_info.line_count if file_info else 0,
        "is_parsed": file_info.is_parsed if file_info else False,
        "content": session.raw_contents[path],
        "symbols": file_info.symbols if file_info else []
    }

@router.get("/repositories/{repository_id}/languages", response_model=dict[str, LanguageCapability])
def get_repository_languages(repository_id: str):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")
    return get_all_capabilities()

@router.get("/repositories/{repository_id}/symbols", response_model=List[CodeSymbol])
def get_repository_symbols(
    repository_id: str,
    language: Optional[str] = None,
    file_path: Optional[str] = None
):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")
    
    results = session.symbols
    if language:
        results = [s for s in results if s.language.lower() == language.lower()]
    if file_path:
        results = [s for s in results if s.file_path == file_path]
    return results

@router.get("/repositories/{repository_id}/graph", response_model=GraphResponse)
def get_repository_graph(
    repository_id: str,
    node_id: Optional[str] = None,
    max_nodes: int = Query(50, ge=5, le=200),
    node_types: Optional[str] = None,
    relationship_types: Optional[str] = None
):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")

    nt_filter = node_types.split(",") if node_types else None
    rt_filter = relationship_types.split(",") if relationship_types else None

    return session.graph.get_subgraph(
        center_node_id=node_id,
        max_nodes=max_nodes,
        node_types=nt_filter,
        relationship_types=rt_filter
    )

@router.post("/repositories/{repository_id}/search", response_model=SearchResponse)
def search_repository(repository_id: str, query: SearchQuery):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")

    t0 = time.perf_counter()
    if query.method == "graph_assisted":
        results = session.graph_retriever.search(
            query=query.query,
            top_k=query.top_k,
            language_filter=query.language_filter
        )
    else:
        results = session.tfidf_retriever.search(
            query=query.query,
            top_k=query.top_k,
            language_filter=query.language_filter
        )
    latency = (time.perf_counter() - t0) * 1000

    return SearchResponse(
        query=query.query,
        method=query.method,
        latency_ms=round(latency, 2),
        total_results=len(results),
        results=results
    )

@router.post("/repositories/{repository_id}/ask", response_model=AskResponse)
async def ask_repository_ai(repository_id: str, request: AskRequest):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")

    # Retrieve relevant snippets
    if request.retrieval_method == "graph_assisted":
        evidence = session.graph_retriever.search(request.question, top_k=request.top_k)
    else:
        evidence = session.tfidf_retriever.search(request.question, top_k=request.top_k)

    return await gemini_service.answer_question(
        question=request.question,
        evidence=evidence,
        indexed_files=session.files,
        raw_contents=session.raw_contents,
        retrieval_method=request.retrieval_method
    )

@router.post("/repositories/{repository_id}/evaluate", response_model=EvaluationResult)
def evaluate_repository(repository_id: str):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")

    evaluator = repo_store.evaluator
    eval_result = evaluator.evaluate(
        tfidf_retriever=session.tfidf_retriever,
        graph_retriever=session.graph_retriever,
        indexed_files=session.files
    )
    session.last_evaluation = eval_result
    return eval_result

@router.get("/repositories/{repository_id}/evaluation", response_model=EvaluationResult)
def get_repository_evaluation(repository_id: str):
    session = repo_store.get_repo(repository_id)
    if not session:
        raise HTTPException(status_code=404, detail="Repository not found.")

    if not session.last_evaluation:
        # Run on the fly if not cached
        evaluator = repo_store.evaluator
        eval_result = evaluator.evaluate(
            tfidf_retriever=session.tfidf_retriever,
            graph_retriever=session.graph_retriever,
            indexed_files=session.files
        )
        session.last_evaluation = eval_result
        return eval_result

    return session.last_evaluation
