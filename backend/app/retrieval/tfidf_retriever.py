from typing import Dict, List, Optional, Tuple
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from .units import SearchableUnit
from ..models.schemas import IndexedFile, CodeSymbol, SearchResultItem

class TFIDFRetriever:
    """
    Method A: TF-IDF lexical retrieval baseline.
    Indexes files, functions, classes, and documentation units using scikit-learn.
    """
    
    def __init__(self):
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self.units: List[SearchableUnit] = []
        self.doc_id_to_index: Dict[str, int] = {}
        self.node_id_to_unit_index: Dict[str, int] = {}

    def build_index(
        self,
        files: Dict[str, IndexedFile],
        raw_contents: Dict[str, str],
        symbols: List[CodeSymbol],
        repo_id: str
    ):
        self.units.clear()
        self.doc_id_to_index.clear()
        self.node_id_to_unit_index.clear()

        # 1. Index symbols (functions, methods, classes, etc.)
        for sym in symbols:
            file_code = raw_contents.get(sym.file_path, "")
            lines = file_code.splitlines()
            
            # Slice line range (1-indexed)
            start_idx = max(0, sym.start_line - 1)
            end_idx = min(len(lines), sym.end_line)
            body_lines = lines[start_idx:end_idx]
            
            # Formulate rich searchable text
            text_parts = [
                f"file: {sym.file_path}",
                f"language: {sym.language}",
                f"symbol: {sym.name}",
                f"type: {sym.symbol_type.value}",
                f"signature: {sym.signature or ''}",
                f"docstring: {sym.docstring or ''}",
                "\n".join(body_lines[:40])  # limit body slice to 40 lines
            ]
            content = " ".join(text_parts)
            
            # Snippet for display
            snippet = "\n".join(body_lines[:25])
            if len(body_lines) > 25:
                snippet += f"\n... [{len(body_lines) - 25} more lines]"

            unit = SearchableUnit(
                document_id=sym.id,
                file_path=sym.file_path,
                language=sym.language,
                line_range=(sym.start_line, sym.end_line),
                content=content,
                snippet=snippet,
                symbol_name=sym.name,
                symbol_type=sym.symbol_type.value,
                node_id=sym.id
            )
            idx = len(self.units)
            self.units.append(unit)
            self.doc_id_to_index[sym.id] = idx
            self.node_id_to_unit_index[sym.id] = idx

        # 2. Index whole files (especially useful for files without symbols or text docs)
        for file_path, file_info in files.items():
            file_code = raw_contents.get(file_path, "")
            lines = file_code.splitlines()
            file_node_id = f"{repo_id}:{file_path}"
            
            text_parts = [
                f"file: {file_path}",
                f"language: {file_info.language}",
                f"imports: {' '.join(file_info.imports)}",
                "\n".join(lines[:60])
            ]
            content = " ".join(text_parts)
            
            snippet = "\n".join(lines[:30])
            if len(lines) > 30:
                snippet += f"\n... [{len(lines) - 30} more lines]"

            unit = SearchableUnit(
                document_id=file_node_id,
                file_path=file_path,
                language=file_info.language,
                line_range=(1, min(len(lines), 30)),
                content=content,
                snippet=snippet,
                symbol_name=None,
                symbol_type="file",
                node_id=file_node_id
            )
            idx = len(self.units)
            self.units.append(unit)
            self.doc_id_to_index[file_node_id] = idx
            self.node_id_to_unit_index[file_node_id] = idx

        # Build TF-IDF vector space
        if self.units:
            corpus = [u.content for u in self.units]
            self.vectorizer = TfidfVectorizer(
                token_pattern=r"(?u)\b[a-zA-Z_][a-zA-Z0-9_]*\b",
                lowercase=True,
                stop_words="english",
                max_features=15000
            )
            try:
                self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
            except ValueError:
                # E.g. empty corpus or only stopwords
                self.vectorizer = None
                self.tfidf_matrix = None
        else:
            self.vectorizer = None
            self.tfidf_matrix = None

    def search(
        self,
        query: str,
        top_k: int = 10,
        language_filter: Optional[str] = None
    ) -> List[SearchResultItem]:
        if not query.strip() or not self.units or self.vectorizer is None or self.tfidf_matrix is None:
            return []

        try:
            query_vec = self.vectorizer.transform([query])
        except Exception:
            return []

        # Cosine similarity against all documents
        similarities = cosine_similarity(query_vec, self.tfidf_matrix).flatten()
        
        # Rank by score descending
        ranked_indices = np.argsort(similarities)[::-1]
        
        results: List[SearchResultItem] = []
        for idx in ranked_indices:
            score = float(similarities[idx])
            if score <= 0.001:
                break
                
            unit = self.units[idx]
            if language_filter and unit.language.lower() != language_filter.lower():
                continue

            results.append(
                SearchResultItem(
                    document_id=unit.document_id,
                    file_path=unit.file_path,
                    language=unit.language,
                    line_range=unit.line_range,
                    score=round(score, 4),
                    snippet=unit.snippet,
                    symbol_name=unit.symbol_name,
                    symbol_type=unit.symbol_type,
                    graph_signals={"lexical_tfidf_score": round(score, 4)}
                )
            )
            if len(results) >= top_k:
                break

        return results
