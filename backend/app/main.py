from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import settings
from .api.routes import router as api_router
from .storage.repo_store import repo_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Pre-index sample ecommerce repository if present
    sample_dir = settings.SAMPLE_REPOS_DIR / "sample_ecommerce"
    if sample_dir.exists():
        try:
            repo_store.index_workspace(
                repo_id="sample-ecommerce",
                repo_name="Sample Multi-Language E-Commerce",
                workspace_dir=sample_dir,
                source_type="sample",
                source_url="local://sample_ecommerce"
            )
            print("[TraceBench] Sample ecommerce repository successfully indexed on startup.")
        except Exception as e:
            print(f"[TraceBench] Failed to pre-index sample repository: {e}")
    yield
    # Shutdown logic if any

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Multi-language AI code repository investigator with evidence-grounded question answering and retrieval evaluation.",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Safe Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log securely without exposing stack traces to clients
    print(f"[TraceBench Error] {request.method} {request.url.path}: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify your request or consult backend logs."}
    )

# Mount API
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
