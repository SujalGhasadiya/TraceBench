from pathlib import Path
from typing import Optional, Set

LANGUAGE_EXTENSIONS = {
    "python": {".py", ".pyi"},
    "javascript": {".js", ".jsx", ".mjs", ".cjs"},
    "typescript": {".ts", ".tsx", ".mts", ".cts"},
    "java": {".java"},
    "c": {".c", ".h"},
    "cpp": {".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"},
    "go": {".go"},
    "rust": {".rs"},
    "php": {".php", ".phtml", ".php3", ".php4", ".php5", ".phps"},
}

# Reverse lookup
EXTENSION_TO_LANGUAGE = {
    ext: lang for lang, exts in LANGUAGE_EXTENSIONS.items() for ext in exts
}

# General text files indexed for search but not structurally parsed into code graphs
TEXT_EXTENSIONS = {
    ".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".toml", ".xml",
    ".html", ".css", ".scss", ".sql", ".sh", ".bash", ".zsh", ".bat", ".ps1",
    ".dockerfile", ".rst", ".csv"
}

# Directory names that should never be indexed or traversed
IGNORED_DIRECTORIES: Set[str] = {
    ".git", ".svn", ".hg", "node_modules", "__pycache__", ".venv", "venv",
    "env", ".env", ".tox", ".idea", ".vscode", "target", "build", "dist",
    "bin", "obj", ".next", ".nuxt", "vendor"
}

# File names / patterns that should be strictly skipped for security / secrets
IGNORED_FILENAMES: Set[str] = {
    ".env", ".env.local", ".env.production", ".env.development",
    "id_rsa", "id_rsa.pub", "id_ecdsa", "id_ed25519",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "Cargo.lock"
}

IGNORED_EXTENSIONS: Set[str] = {
    ".pem", ".key", ".pkcs12", ".pfx", ".cer", ".crt",
    ".exe", ".dll", ".so", ".dylib", ".class", ".pyc", ".o", ".a",
    ".zip", ".tar", ".gz", ".7z", ".rar", ".iso",
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".webp",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx"
}

def is_ignored_path(relative_path: str) -> bool:
    """Check if a path should be skipped during repository indexing."""
    path_obj = Path(relative_path)
    
    # Check directory components
    for part in path_obj.parts[:-1]:
        if part in IGNORED_DIRECTORIES:
            return True
            
    filename = path_obj.name.lower()
    
    # Check sensitive filename
    if filename in IGNORED_FILENAMES or filename.startswith(".env"):
        return True
        
    # Check extension
    suffix = path_obj.suffix.lower()
    if suffix in IGNORED_EXTENSIONS:
        return True
        
    return False

def detect_language(file_path: str) -> Optional[str]:
    """
    Detect the programming or text language of a given file path.
    Returns:
      - 'python', 'javascript', 'typescript', 'java', 'c', 'cpp', 'go', 'rust', 'php' for target languages
      - 'text' for non-code text files (markdown, json, etc.)
      - None for unsupported or binary files
    """
    path_obj = Path(file_path)
    suffix = path_obj.suffix.lower()
    
    # Check target code languages
    if suffix in EXTENSION_TO_LANGUAGE:
        return EXTENSION_TO_LANGUAGE[suffix]
        
    # Check special filenames
    name = path_obj.name.lower()
    if name in {"dockerfile", "makefile", "cmakelists.txt"}:
        return "text"
        
    # Check non-code text documents
    if suffix in TEXT_EXTENSIONS:
        return "text"
        
    return None
