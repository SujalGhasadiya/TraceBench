from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
from pydantic import BaseModel, Field

class LanguageSupportLevel(str, Enum):
    FILE_RECOGNITION = "file_recognition"
    TEXT_INDEXED = "text_indexed"
    STRUCTURAL_PARSING = "structural_parsing"
    RELATIONSHIP_ANALYSIS = "relationship_analysis"

class LanguageCapability(BaseModel):
    language: str
    extensions: List[str]
    support_level: LanguageSupportLevel
    parser: str
    ast_supported: bool
    relationships_supported: bool
    notes: str

class SymbolType(str, Enum):
    FUNCTION = "function"
    ASYNC_FUNCTION = "async_function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    STRUCT = "struct"
    MODULE = "module"
    VARIABLE = "variable"
    CONSTANT = "constant"
    IMPORT = "import"
    NAMESPACE = "namespace"

class CodeSymbol(BaseModel):
    id: str = Field(..., description="Stable unique identifier: repo_id:file_path:name:line")
    repo_id: str
    file_path: str
    language: str
    name: str
    symbol_type: SymbolType
    start_line: int
    end_line: int
    parent_id: Optional[str] = None
    docstring: Optional[str] = None
    signature: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RelationshipType(str, Enum):
    CONTAINS = "contains"
    IMPORTS = "imports"
    INCLUDES = "includes"
    CALLS = "calls"
    INFERRED_CALLS = "inferred_calls"
    REFERENCES = "references"

class Relationship(BaseModel):
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    provenance: str = Field(..., description="Source parser or inference rule (e.g. tree_sitter, python_ast, lexical_import)")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    is_inferred: bool = False
    source_location: Optional[Dict[str, Any]] = None

class IndexedFile(BaseModel):
    file_path: str
    language: str
    is_parsed: bool
    is_text_indexed: bool
    parse_error: Optional[str] = None
    line_count: int
    byte_size: int
    symbols: List[CodeSymbol] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)

class RepositoryMetadata(BaseModel):
    id: str
    name: str
    source_type: str  # 'github' | 'zip' | 'sample'
    source_url: Optional[str] = None
    created_at: str
    file_count: int
    parsed_file_count: int
    text_indexed_count: int
    language_breakdown: Dict[str, int]
    symbol_count: int
    edge_count: int
    parsing_errors: List[Dict[str, Any]] = Field(default_factory=list)
    skipped_files: List[str] = Field(default_factory=list)

class GraphNode(BaseModel):
    id: str
    label: str
    node_type: str  # 'file', 'function', 'class', etc.
    file_path: str
    language: str
    line_range: Tuple[int, int]
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str
    provenance: str
    confidence: float
    is_inferred: bool

class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    total_nodes: int
    total_edges: int
    truncated: bool = False

class SearchQuery(BaseModel):
    query: str
    method: str = Field(default="tfidf", description="'tfidf' or 'graph_assisted'")
    top_k: int = 10
    language_filter: Optional[str] = None

class SearchResultItem(BaseModel):
    document_id: str
    file_path: str
    language: str
    line_range: Tuple[int, int]
    score: float
    snippet: str
    symbol_name: Optional[str] = None
    symbol_type: Optional[str] = None
    graph_signals: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    query: str
    method: str
    latency_ms: float
    total_results: int
    results: List[SearchResultItem]

class Citation(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    symbol_name: Optional[str] = None
    snippet: Optional[str] = None
    is_valid: bool = True
    validation_notes: Optional[str] = None

class AskRequest(BaseModel):
    question: str
    retrieval_method: str = Field(default="tfidf", description="'tfidf' or 'graph_assisted'")
    top_k: int = 8

class AskResponse(BaseModel):
    question: str
    answer: str
    citations: List[Citation]
    retrieved_evidence: List[SearchResultItem]
    retrieval_method: str
    mode: str = Field(..., description="'gemini' or 'demo'")
    languages_represented: List[str]
    uncertainty_notes: Optional[str] = None
    latency_ms: float

class BenchmarkItem(BaseModel):
    id: str
    question: str
    repo_name: str
    language: str
    expected_files: List[str]
    expected_symbols: List[str] = Field(default_factory=list)
    expected_line_ranges: Optional[List[Tuple[int, int]]] = None
    explanation: str

class EvaluationMethodResult(BaseModel):
    recall_at_5: float
    mrr: float
    avg_latency_ms: float
    citation_correctness: Optional[float] = None
    total_queries: int
    successful_queries: int
    per_language: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    per_question: List[Dict[str, Any]] = Field(default_factory=list)
    failed_cases: List[Dict[str, Any]] = Field(default_factory=list)

class EvaluationResult(BaseModel):
    benchmark_id: str
    benchmark_size: int
    evaluated_at: str
    methods: Dict[str, EvaluationMethodResult]
    metric_definitions: Dict[str, str]

class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    gemini_configured: bool
    gemini_model: str
    supported_languages: List[str]
