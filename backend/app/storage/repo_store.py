from pathlib import Path
from typing import Dict, List, Optional
import shutil

from ..config import settings
from ..models.schemas import RepositoryMetadata, IndexedFile, CodeSymbol, Relationship, EvaluationResult
from ..analysis.analyzer import RepositoryAnalyzer
from ..graph.graph_builder import RepositoryGraph
from ..retrieval.tfidf_retriever import TFIDFRetriever
from ..retrieval.graph_retriever import GraphAssistedRetriever
from ..evaluation.evaluator import BenchmarkEvaluator

class RepositorySession:
    def __init__(
        self,
        metadata: RepositoryMetadata,
        files: Dict[str, IndexedFile],
        raw_contents: Dict[str, str],
        symbols: List[CodeSymbol],
        relationships: List[Relationship],
        graph: RepositoryGraph,
        tfidf_retriever: TFIDFRetriever,
        graph_retriever: GraphAssistedRetriever
    ):
        self.metadata = metadata
        self.files = files
        self.raw_contents = raw_contents
        self.symbols = symbols
        self.relationships = relationships
        self.graph = graph
        self.tfidf_retriever = tfidf_retriever
        self.graph_retriever = graph_retriever
        self.last_evaluation: Optional[EvaluationResult] = None

class RepositoryStore:
    """Thread-safe in-memory registry of indexed repositories."""
    def __init__(self):
        self._repos: Dict[str, RepositorySession] = {}
        self.analyzer = RepositoryAnalyzer()
        self.evaluator = BenchmarkEvaluator()

    def index_workspace(
        self,
        repo_id: str,
        repo_name: str,
        workspace_dir: Path,
        source_type: str,
        source_url: Optional[str] = None,
        initial_skipped: Optional[List[str]] = None
    ) -> RepositorySession:
        metadata, files, raw_contents, symbols, relationships = self.analyzer.analyze_workspace(
            repo_id=repo_id,
            repo_name=repo_name,
            workspace_dir=workspace_dir,
            source_type=source_type,
            source_url=source_url,
            initial_skipped=initial_skipped
        )

        # Build Graph
        graph = RepositoryGraph(repo_id)
        graph.build(files, symbols, relationships)

        # Build TF-IDF
        tfidf = TFIDFRetriever()
        tfidf.build_index(files, raw_contents, symbols, repo_id)

        # Build Graph-Assisted Retriever
        graph_retriever = GraphAssistedRetriever(tfidf, graph)

        session = RepositorySession(
            metadata=metadata,
            files=files,
            raw_contents=raw_contents,
            symbols=symbols,
            relationships=relationships,
            graph=graph,
            tfidf_retriever=tfidf,
            graph_retriever=graph_retriever
        )
        self._repos[repo_id] = session
        return session

    def get_repo(self, repo_id: str) -> Optional[RepositorySession]:
        return self._repos.get(repo_id)

    def list_repos(self) -> List[RepositoryMetadata]:
        return [session.metadata for session in self._repos.values()]

    def delete_repo(self, repo_id: str) -> bool:
        if repo_id in self._repos:
            del self._repos[repo_id]
            # Clean disk workspace
            repo_dir = settings.WORKSPACE_DIR / repo_id
            if repo_dir.exists():
                shutil.rmtree(repo_dir, ignore_errors=True)
            return True
        return False

# Global instance
repo_store = RepositoryStore()
