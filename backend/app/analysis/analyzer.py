import os
from pathlib import Path
from typing import Dict, List, Tuple, Any
from ..config import settings
from ..languages.detector import detect_language, is_ignored_path
from ..parsers.unified_parser import UnifiedParser
from ..models.schemas import IndexedFile, CodeSymbol, Relationship, RepositoryMetadata

class RepositoryAnalyzer:
    """
    Coordinates repository file discovery, language identification,
    source extraction, and multi-language AST parsing.
    """
    def __init__(self):
        self.parser = UnifiedParser()

    def analyze_workspace(
        self,
        repo_id: str,
        repo_name: str,
        workspace_dir: Path,
        source_type: str,
        source_url: str | None = None,
        initial_skipped: List[str] | None = None
    ) -> Tuple[RepositoryMetadata, Dict[str, IndexedFile], Dict[str, str], List[CodeSymbol], List[Relationship]]:
        indexed_files: Dict[str, IndexedFile] = {}
        raw_contents: Dict[str, str] = {}
        all_symbols: List[CodeSymbol] = []
        all_relationships: List[Relationship] = []
        parsing_errors: List[Dict[str, Any]] = []
        skipped_files: List[str] = list(initial_skipped or [])
        language_counts: Dict[str, int] = {}

        workspace_dir = workspace_dir.resolve()

        for root, dirs, files in os.walk(workspace_dir):
            rel_dir = os.path.relpath(root, workspace_dir).replace("\\", "/")
            if rel_dir != "." and is_ignored_path(rel_dir):
                dirs[:] = []
                continue

            for file_name in files:
                rel_path = (Path(rel_dir) / file_name).as_posix() if rel_dir != "." else file_name
                
                if is_ignored_path(rel_path):
                    skipped_files.append(rel_path)
                    continue

                full_path = workspace_dir / rel_path
                file_size = full_path.stat().st_size

                # Detect language
                lang = detect_language(rel_path)
                if not lang:
                    skipped_files.append(rel_path)
                    continue

                # Read source text safely
                try:
                    with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                        source_code = f.read(settings.MAX_FILE_SIZE_BYTES + 1)
                except Exception as e:
                    parsing_errors.append({"file": rel_path, "error": f"Read error: {str(e)}"})
                    skipped_files.append(rel_path)
                    continue

                line_count = source_code.count("\n") + 1
                raw_contents[rel_path] = source_code
                language_counts[lang] = language_counts.get(lang, 0) + 1

                # Parse file
                parse_res = self.parser.parse_file(rel_path, source_code, repo_id, language=lang)
                
                if parse_res.errors:
                    for err in parse_res.errors:
                        parsing_errors.append({"file": rel_path, "error": err})

                indexed_file = IndexedFile(
                    file_path=rel_path,
                    language=lang,
                    is_parsed=parse_res.is_parsed,
                    is_text_indexed=True,
                    parse_error="; ".join(parse_res.errors) if parse_res.errors else None,
                    line_count=line_count,
                    byte_size=file_size,
                    symbols=parse_res.symbols,
                    imports=parse_res.imports
                )
                indexed_files[rel_path] = indexed_file

                all_symbols.extend(parse_res.symbols)
                all_relationships.extend(parse_res.relationships)

        parsed_count = sum(1 for f in indexed_files.values() if f.is_parsed)
        text_indexed_count = len(indexed_files)

        from datetime import datetime, timezone
        created_at = datetime.now(timezone.utc).isoformat()

        metadata = RepositoryMetadata(
            id=repo_id,
            name=repo_name,
            source_type=source_type,
            source_url=source_url,
            created_at=created_at,
            file_count=len(indexed_files),
            parsed_file_count=parsed_count,
            text_indexed_count=text_indexed_count,
            language_breakdown=language_counts,
            symbol_count=len(all_symbols),
            edge_count=len(all_relationships),
            parsing_errors=parsing_errors,
            skipped_files=skipped_files
        )

        return metadata, indexed_files, raw_contents, all_symbols, all_relationships
