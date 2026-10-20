import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseModel):
    # App info
    APP_NAME: str = "TraceBench"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("TRACEBENCH_DEBUG", "false").lower() == "true"
    
    # Storage
    WORKSPACE_DIR: Path = Path(os.getenv("TRACEBENCH_WORKSPACE_DIR", str(BASE_DIR / "data" / "workspaces")))
    SAMPLE_REPOS_DIR: Path = Path(os.getenv("TRACEBENCH_SAMPLE_DIR", str(BASE_DIR / "data" / "sample_repos")))
    BENCHMARKS_DIR: Path = Path(os.getenv("TRACEBENCH_BENCHMARKS_DIR", str(BASE_DIR / "data" / "benchmarks")))
    
    # Ingestion limits
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("TRACEBENCH_MAX_UPLOAD_SIZE_MB", "50")) * 1024 * 1024
    MAX_EXTRACTED_SIZE_BYTES: int = int(os.getenv("TRACEBENCH_MAX_EXTRACTED_SIZE_MB", "150")) * 1024 * 1024
    MAX_FILE_COUNT: int = int(os.getenv("TRACEBENCH_MAX_FILE_COUNT", "2000"))
    MAX_FILE_SIZE_BYTES: int = int(os.getenv("TRACEBENCH_MAX_FILE_SIZE_BYTES", "1048576"))  # 1MB per file text index
    
    # CORS
    CORS_ORIGINS: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "TRACEBENCH_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
        ).split(",")
        if origin.strip()
    ]
    
    # AI
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()

settings = Settings()
settings.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
settings.SAMPLE_REPOS_DIR.mkdir(parents=True, exist_ok=True)
settings.BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)
