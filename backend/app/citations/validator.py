import re
from typing import List, Dict, Tuple, Optional
from ..models.schemas import Citation, IndexedFile, SearchResultItem

CITATION_REGEX = re.compile(
    r"\[(?P<file>[^#\]]+)#L(?P<start>\d+)(?:-L(?P<end>\d+))?\]"
)

class CitationValidator:
    """
    Validates that every source reference returned by the LLM or synthesis engine
    resolves to real, verified lines in the indexed codebase.
    """
    
    @staticmethod
    def extract_and_validate(
        text_or_citations: str | List[Citation],
        indexed_files: Dict[str, IndexedFile],
        raw_contents: Dict[str, str],
        retrieved_evidence: List[SearchResultItem]
    ) -> Tuple[List[Citation], str]:
        validated_citations: List[Citation] = []
        uncertainty_notes: List[str] = []

        # If already parsed citations passed
        if isinstance(text_or_citations, list):
            raw_citations = text_or_citations
        else:
            # Parse [file#L10-L20] patterns from text
            raw_citations = []
            for match in CITATION_REGEX.finditer(text_or_citations):
                f_path = match.group("file").strip()
                s_line = int(match.group("start"))
                e_line = int(match.group("end")) if match.group("end") else s_line
                raw_citations.append(
                    Citation(
                        file_path=f_path,
                        start_line=s_line,
                        end_line=e_line
                    )
                )

        # Build lookup of retrieved evidence line spans per file
        evidence_spans: Dict[str, List[Tuple[int, int]]] = {}
        for ev in retrieved_evidence:
            evidence_spans.setdefault(ev.file_path, []).append(ev.line_range)

        # Validate each citation
        for cit in raw_citations:
            file_path = cit.file_path
            start_line = cit.start_line
            end_line = cit.end_line

            # Check 1: File existence
            if file_path not in indexed_files:
                # Try finding case-insensitive or partial match
                matched_fp = None
                for real_fp in indexed_files.keys():
                    if real_fp.lower() == file_path.lower() or real_fp.endswith(file_path):
                        matched_fp = real_fp
                        break
                if not matched_fp:
                    validated_citations.append(
                        Citation(
                            file_path=file_path,
                            start_line=start_line,
                            end_line=end_line,
                            is_valid=False,
                            validation_notes=f"Referenced file '{file_path}' does not exist in indexed repository."
                        )
                    )
                    continue
                file_path = matched_fp

            file_info = indexed_files[file_path]
            file_code = raw_contents.get(file_path, "")
            lines = file_code.splitlines()
            total_lines = file_info.line_count

            # Check 2: Valid line ranges
            if start_line < 1 or end_line > total_lines or start_line > end_line:
                validated_citations.append(
                    Citation(
                        file_path=file_path,
                        start_line=start_line,
                        end_line=end_line,
                        is_valid=False,
                        validation_notes=f"Line range L{start_line}-L{end_line} is outside valid file lines (1-{total_lines})."
                    )
                )
                continue

            # Check 3: Extract snippet
            slice_start = max(0, start_line - 1)
            slice_end = min(total_lines, end_line)
            citation_snippet = "\n".join(lines[slice_start:slice_end])

            # Check 4: Overlap with retrieved evidence or indexed symbols
            spans = evidence_spans.get(file_path, [])
            in_evidence = any(
                not (end_line < s_start or start_line > s_end)
                for s_start, s_end in spans
            )

            # Match symbol if line falls within one
            matching_sym_name = None
            for sym in file_info.symbols:
                if sym.start_line <= start_line and end_line <= sym.end_line:
                    matching_sym_name = sym.name
                    break

            notes = None
            if not in_evidence:
                notes = "Citation verified against indexed file, but falls outside the top retrieved evidence snippets."

            validated_citations.append(
                Citation(
                    file_path=file_path,
                    start_line=start_line,
                    end_line=end_line,
                    symbol_name=matching_sym_name,
                    snippet=citation_snippet,
                    is_valid=True,
                    validation_notes=notes
                )
            )

        # De-duplicate citations
        unique_citations: List[Citation] = []
        seen = set()
        for c in validated_citations:
            key = (c.file_path, c.start_line, c.end_line, c.is_valid)
            if key not in seen:
                seen.add(key)
                unique_citations.append(c)

        invalid_count = sum(1 for c in unique_citations if not c.is_valid)
        uncertainty = ""
        if invalid_count > 0:
            uncertainty = f"Caution: {invalid_count} cited source references could not be verified against actual files."

        return unique_citations, uncertainty
