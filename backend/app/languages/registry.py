from typing import Dict, List
from ..models.schemas import LanguageCapability, LanguageSupportLevel

CAPABILITIES: Dict[str, LanguageCapability] = {
    "python": LanguageCapability(
        language="Python",
        extensions=[".py", ".pyi"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter + Python built-in AST",
        ast_supported=True,
        relationships_supported=True,
        notes="Functions, async functions, classes, methods, docstrings, imports, and calls extracted with AST & Tree-sitter.",
    ),
    "javascript": LanguageCapability(
        language="JavaScript",
        extensions=[".js", ".jsx", ".mjs", ".cjs"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Functions, methods, arrow functions, classes, ES imports/requires, and calls extracted.",
    ),
    "typescript": LanguageCapability(
        language="TypeScript",
        extensions=[".ts", ".tsx", ".mts", ".cts"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Interfaces, classes, methods, functions, type declarations, imports, and calls extracted.",
    ),
    "java": LanguageCapability(
        language="Java",
        extensions=[".java"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Classes, interfaces, constructors, methods, package imports, and method invocations extracted.",
    ),
    "c": LanguageCapability(
        language="C",
        extensions=[".c", ".h"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Functions, struct specifiers, preprocessor includes, and function calls extracted.",
    ),
    "cpp": LanguageCapability(
        language="C++",
        extensions=[".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Classes, structs, functions, methods, include directives, and calls extracted.",
    ),
    "go": LanguageCapability(
        language="Go",
        extensions=[".go"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Package declarations, functions, methods with receivers, struct types, imports, and calls extracted.",
    ),
    "rust": LanguageCapability(
        language="Rust",
        extensions=[".rs"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Functions, structs, traits, impl blocks, use declarations, and function calls extracted.",
    ),
    "php": LanguageCapability(
        language="PHP",
        extensions=[".php", ".phtml"],
        support_level=LanguageSupportLevel.RELATIONSHIP_ANALYSIS,
        parser="Tree-sitter",
        ast_supported=True,
        relationships_supported=True,
        notes="Namespaces, classes, interfaces, methods, functions, use declarations, and method calls extracted.",
    ),
    "text": LanguageCapability(
        language="Plain Text / Docs",
        extensions=[".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".html", ".css", ".sql"],
        support_level=LanguageSupportLevel.TEXT_INDEXED,
        parser="Text Indexer",
        ast_supported=False,
        relationships_supported=False,
        notes="Text searchable via lexical TF-IDF. Structural AST and graph relationship analysis not applicable.",
    ),
}

def get_supported_languages() -> List[str]:
    return [k for k in CAPABILITIES.keys() if k != "text"]

def get_capability(language: str) -> LanguageCapability:
    lang_lower = language.lower()
    if lang_lower in CAPABILITIES:
        return CAPABILITIES[lang_lower]
    return LanguageCapability(
        language=language,
        extensions=[],
        support_level=LanguageSupportLevel.FILE_RECOGNITION,
        parser="None",
        ast_supported=False,
        relationships_supported=False,
        notes="Recognized as raw file. Text indexed only if readable UTF-8 text.",
    )

def get_all_capabilities() -> Dict[str, LanguageCapability]:
    return CAPABILITIES
