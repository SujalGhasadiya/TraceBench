from typing import List, Optional, Dict, Set
from .tfidf_retriever import TFIDFRetriever
from ..graph.graph_builder import RepositoryGraph
from ..models.schemas import SearchResultItem

class GraphAssistedRetriever:
    """
    Method B: Graph-assisted code retrieval.
    Combines TF-IDF lexical matching with relationship graph neighborhood signals.
    """
    
    def __init__(self, tfidf_retriever: TFIDFRetriever, graph: RepositoryGraph):
        self.tfidf = tfidf_retriever
        self.graph = graph

    def search(
        self,
        query: str,
        top_k: int = 10,
        language_filter: Optional[str] = None
    ) -> List[SearchResultItem]:
        # 1. Fetch initial lexical candidate pool
        initial_candidates = self.tfidf.search(query, top_k=30, language_filter=language_filter)
        if not initial_candidates:
            return []

        # Map candidate doc_ids to their lexical score
        lexical_scores: Dict[str, float] = {item.document_id: item.score for item in initial_candidates}
        candidate_map: Dict[str, SearchResultItem] = {item.document_id: item for item in initial_candidates}

        # 2. Compute Graph Neighborhood Connectivity
        # For each candidate, find connected neighbors within the candidate set
        graph_boosts: Dict[str, float] = {}
        connected_info: Dict[str, List[str]] = {}

        candidate_ids = set(candidate_map.keys())

        for doc_id, item in candidate_map.items():
            neighbors = self.graph.get_neighbors(doc_id)
            # Find neighbors that are also candidates
            in_set_neighbors = [n for n in neighbors if n in candidate_ids and n != doc_id]
            
            # Boost proportional to the lexical strength of connected neighbors
            boost = 0.0
            neighbor_labels = []
            for n_id in in_set_neighbors:
                neighbor_score = lexical_scores.get(n_id, 0.0)
                boost += neighbor_score * 0.4
                n_data = self.graph.graph.nodes.get(n_id, {})
                neighbor_labels.append(n_data.get("label", n_id.split(":")[-1]))

            graph_boosts[doc_id] = min(boost, 1.0)
            connected_info[doc_id] = neighbor_labels

        # 3. Combine scores using calibrated weights (70% lexical, 30% graph connectivity)
        scored_items: List[SearchResultItem] = []
        for doc_id, item in candidate_map.items():
            lex_score = lexical_scores[doc_id]
            g_boost = graph_boosts.get(doc_id, 0.0)
            combined_score = (0.70 * lex_score) + (0.30 * g_boost)

            scored_item = SearchResultItem(
                document_id=item.document_id,
                file_path=item.file_path,
                language=item.language,
                line_range=item.line_range,
                score=round(combined_score, 4),
                snippet=item.snippet,
                symbol_name=item.symbol_name,
                symbol_type=item.symbol_type,
                graph_signals={
                    "lexical_score": round(lex_score, 4),
                    "graph_boost": round(g_boost, 4),
                    "connected_neighbors": connected_info.get(doc_id, [])
                }
            )
            scored_items.append(scored_item)

        # 4. Sort by combined score descending
        scored_items.sort(key=lambda x: x.score, reverse=True)
        return scored_items[:top_k]
