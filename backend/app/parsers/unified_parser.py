from typing import Optional
from .base import BaseParser, ParseResult
from .python_ast_parser import PythonASTParser
from .tree_sitter_parser import TreeSitterParser

class UnifiedParser:
    """
    Coordinates language-specific parsing engines.
    Ensures safe fallback to text indexing when grammar parsing is unavailable or fails.
    """
    
    def __init__(self):
        self.python_ast_parser = PythonASTParser()
        self.tree_sitter_parser = TreeSitterParser()

    def parse_file(
        self,
        file_path: str,
        source_code: str,
        repo_id: str,
        language: Optional[str] = None
    ) -> ParseResult:
        if not language or language == "text":
            return ParseResult(
                file_path=file_path,
                language=language or "text",
                is_parsed=False,
                symbols=[],
                imports=[],
                calls=[],
                relationships=[],
                errors=[]
            )

        # Python: try AST parser first for rich docstrings and decorators
        if language == "python":
            ast_res = self.python_ast_parser.parse(file_path, source_code, repo_id)
            if ast_res.is_parsed:
                return ast_res
            # If AST encountered syntax error (e.g. newer syntax or partial snippet), try Tree-sitter
            ts_res = self.tree_sitter_parser.parse(file_path, source_code, repo_id, language="python")
            if ts_res.is_parsed:
                return ts_res
            # If both failed, preserve errors
            return ast_res

        # All other supported Tree-sitter languages
        if language in self.tree_sitter_parser.LANG_GRAMMAR_MAP:
            return self.tree_sitter_parser.parse(file_path, source_code, repo_id, language=language)

        # Fallback for unrecognized or non-code files
        return ParseResult(
            file_path=file_path,
            language=language,
            is_parsed=False,
            symbols=[],
            imports=[],
            calls=[],
            relationships=[],
            errors=[f"Structural parsing not supported for language: {language}"]
        )
