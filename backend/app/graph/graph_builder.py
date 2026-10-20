from typing import Dict, List, Optional, Set, Tuple
import networkx as nx
from ..models.schemas import (
    CodeSymbol, Relationship, RelationshipType,
    GraphNode, GraphEdge, GraphResponse, IndexedFile
)

class RepositoryGraph:
    """
    Unified relationship graph backed by NetworkX.
    Maintains code hierarchy, import dependencies, and inferred call references.
    """
    
    def __init__(self, repo_id: str):
        self.repo_id = repo_id
        self.graph = nx.DiGraph()
        self.symbol_lookup: Dict[str, CodeSymbol] = {}
        self.name_to_symbols: Dict[str, List[CodeSymbol]] = {}
        self.file_to_symbols: Dict[str, List[CodeSymbol]] = {}

    def build(
        self,
        files: Dict[str, IndexedFile],
        symbols: List[CodeSymbol],
        relationships: List[Relationship]
    ):
        self.graph.clear()
        self.symbol_lookup.clear()
        self.name_to_symbols.clear()
        self.file_to_symbols.clear()

        # Index symbols for resolution
        for sym in symbols:
            self.symbol_lookup[sym.id] = sym
            self.name_to_symbols.setdefault(sym.name, []).append(sym)
            # Index base name without class prefix (e.g. 'connect' for 'DatabaseConnection.connect')
            base_name = sym.name.split(".")[-1]
            if base_name != sym.name:
                self.name_to_symbols.setdefault(base_name, []).append(sym)
            self.file_to_symbols.setdefault(sym.file_path, []).append(sym)

        # 1. Add File Nodes
        for file_path, file_info in files.items():
            file_node_id = f"{self.repo_id}:{file_path}"
            self.graph.add_node(
                file_node_id,
                label=file_path.split("/")[-1],
                node_type="file",
                file_path=file_path,
                language=file_info.language,
                line_range=(1, file_info.line_count),
                metadata={
                    "is_parsed": file_info.is_parsed,
                    "byte_size": file_info.byte_size,
                    "symbol_count": len(file_info.symbols)
                }
            )

        # 2. Add Symbol Nodes
        for sym in symbols:
            self.graph.add_node(
                sym.id,
                label=sym.name,
                node_type=sym.symbol_type.value,
                file_path=sym.file_path,
                language=sym.language,
                line_range=(sym.start_line, sym.end_line),
                metadata={
                    "signature": sym.signature,
                    "parent_id": sym.parent_id,
                    "docstring": sym.docstring
                }
            )

        # 3. Add Explicit Containment and Import Edges
        for rel in relationships:
            # Handle contains relationships
            if rel.relationship_type == RelationshipType.CONTAINS:
                if self.graph.has_node(rel.source_id) and self.graph.has_node(rel.target_id):
                    self.graph.add_edge(
                        rel.source_id,
                        rel.target_id,
                        relationship_type=rel.relationship_type.value,
                        provenance=rel.provenance,
                        confidence=rel.confidence,
                        is_inferred=rel.is_inferred
                    )

            # Handle imports relationships
            elif rel.relationship_type == RelationshipType.IMPORTS:
                # Find matching target file node if import string refers to a local file
                import_target = rel.target_id
                target_file_node = None
                
                # Try matching by file path or extension
                clean_target = import_target.replace("'", "").replace('"', "").replace(";", "").strip()
                for fp in files.keys():
                    if clean_target.endswith(fp) or fp.startswith(clean_target) or clean_target in fp:
                        target_file_node = f"{self.repo_id}:{fp}"
                        break
                        
                if target_file_node and self.graph.has_node(target_file_node):
                    self.graph.add_edge(
                        rel.source_id,
                        target_file_node,
                        relationship_type=RelationshipType.IMPORTS.value,
                        provenance=rel.provenance,
                        confidence=0.95,
                        is_inferred=False
                    )

            # Handle calls relationships
            elif rel.relationship_type in {RelationshipType.CALLS, RelationshipType.INFERRED_CALLS}:
                caller_node_id = rel.source_id
                callee_name = rel.target_id

                if not self.graph.has_node(caller_node_id):
                    continue

                caller_file = self.graph.nodes[caller_node_id].get("file_path", "")

                # Resolution strategy:
                # 1. Match symbol in the same file
                matched_target_id = None
                same_file_candidates = [
                    s for s in self.file_to_symbols.get(caller_file, [])
                    if s.name == callee_name or s.name.endswith(f".{callee_name}")
                ]
                if same_file_candidates:
                    matched_target_id = same_file_candidates[0].id
                    confidence = 0.9
                else:
                    # 2. Match unique symbol in the entire repository
                    global_candidates = self.name_to_symbols.get(callee_name, [])
                    if len(global_candidates) == 1:
                        matched_target_id = global_candidates[0].id
                        confidence = 0.75
                    elif len(global_candidates) > 1:
                        # Pick first matching candidate with lower confidence
                        matched_target_id = global_candidates[0].id
                        confidence = 0.55

                if matched_target_id and self.graph.has_node(matched_target_id):
                    self.graph.add_edge(
                        caller_node_id,
                        matched_target_id,
                        relationship_type=RelationshipType.CALLS.value,
                        provenance=rel.provenance,
                        confidence=confidence,
                        is_inferred=True
                    )

    def get_subgraph(
        self,
        center_node_id: Optional[str] = None,
        max_nodes: int = 50,
        node_types: Optional[List[str]] = None,
        relationship_types: Optional[List[str]] = None
    ) -> GraphResponse:
        """
        Returns a bounded subgraph centered around a selected node,
        or a representative top-level graph if no center node is specified.
        Avoids huge DOM layouts and fits cleanly in React Flow.
        """
        if self.graph.number_of_nodes() == 0:
            return GraphResponse(nodes=[], edges=[], total_nodes=0, total_edges=0, truncated=False)

        selected_nodes: Set[str] = set()

        if center_node_id and self.graph.has_node(center_node_id):
            selected_nodes.add(center_node_id)
            # Add 1-hop successors and predecessors
            for succ in self.graph.successors(center_node_id):
                selected_nodes.add(succ)
            for pred in self.graph.predecessors(center_node_id):
                selected_nodes.add(pred)

            # If still within limit, add 2-hop neighbors
            if len(selected_nodes) < max_nodes:
                two_hop: Set[str] = set()
                for n in list(selected_nodes):
                    for succ in self.graph.successors(n):
                        two_hop.add(succ)
                    for pred in self.graph.predecessors(n):
                        two_hop.add(pred)
                selected_nodes.update(two_hop)
        else:
            # Default overview: select all file nodes first, then high-level classes/functions
            file_nodes = [n for n, d in self.graph.nodes(data=True) if d.get("node_type") == "file"]
            selected_nodes.update(file_nodes[:max_nodes // 2])
            
            non_file_nodes = [
                n for n, d in self.graph.nodes(data=True)
                if d.get("node_type") in {"class", "function", "interface", "struct"}
            ]
            selected_nodes.update(non_file_nodes[:max_nodes - len(selected_nodes)])

        # Apply node type filters if provided
        if node_types:
            type_set = set(node_types)
            selected_nodes = {n for n in selected_nodes if self.graph.nodes[n].get("node_type") in type_set}

        # Cap at max_nodes
        bounded_node_ids = list(selected_nodes)[:max_nodes]
        truncated = len(selected_nodes) > max_nodes or len(bounded_node_ids) < self.graph.number_of_nodes()

        nodes: List[GraphNode] = []
        for n_id in bounded_node_ids:
            data = self.graph.nodes[n_id]
            nodes.append(
                GraphNode(
                    id=n_id,
                    label=data.get("label", n_id),
                    node_type=data.get("node_type", "unknown"),
                    file_path=data.get("file_path", ""),
                    language=data.get("language", ""),
                    line_range=data.get("line_range", (1, 1)),
                    metadata=data.get("metadata", {})
                )
            )

        edges: List[GraphEdge] = []
        subgraph = self.graph.subgraph(bounded_node_ids)
        for u, v, data in subgraph.edges(data=True):
            rel_type = data.get("relationship_type", "references")
            if relationship_types and rel_type not in relationship_types:
                continue

            edges.append(
                GraphEdge(
                    id=f"{u}->{v}:{rel_type}",
                    source=u,
                    target=v,
                    relationship_type=rel_type,
                    provenance=data.get("provenance", "unknown"),
                    confidence=data.get("confidence", 1.0),
                    is_inferred=data.get("is_inferred", False)
                )
            )

        return GraphResponse(
            nodes=nodes,
            edges=edges,
            total_nodes=self.graph.number_of_nodes(),
            total_edges=self.graph.number_of_edges(),
            truncated=truncated
        )

    def get_neighbors(self, node_id: str) -> List[str]:
        """Returns 1-hop successors and predecessors for graph-assisted retrieval."""
        if not self.graph.has_node(node_id):
            return []
        neighbors = set(self.graph.successors(node_id)) | set(self.graph.predecessors(node_id))
        return list(neighbors)
