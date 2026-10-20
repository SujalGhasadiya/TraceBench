export type LanguageSupportLevel =
  | 'file_recognition'
  | 'text_indexed'
  | 'structural_parsing'
  | 'relationship_analysis';

export interface LanguageCapability {
  language: string;
  extensions: string[];
  support_level: LanguageSupportLevel;
  parser: string;
  ast_supported: boolean;
  relationships_supported: boolean;
  notes: string;
}

export interface CodeSymbol {
  id: string;
  repo_id: string;
  file_path: string;
  language: string;
  name: string;
  symbol_type: string;
  start_line: number;
  end_line: number;
  parent_id?: string;
  docstring?: string;
  signature?: string;
  metadata?: Record<string, any>;
}

export interface IndexedFile {
  file_path: string;
  language: string;
  is_parsed: boolean;
  is_text_indexed: boolean;
  parse_error?: string;
  line_count: number;
  byte_size: number;
  symbols: CodeSymbol[];
  imports: string[];
}

export interface RepositoryMetadata {
  id: string;
  name: string;
  source_type: 'github' | 'zip' | 'sample';
  source_url?: string;
  created_at: string;
  file_count: number;
  parsed_file_count: number;
  text_indexed_count: number;
  language_breakdown: Record<string, number>;
  symbol_count: number;
  edge_count: number;
  parsing_errors: Array<{ file: string; error: string }>;
  skipped_files: string[];
}

export interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  file_path: string;
  language: string;
  line_range: [number, number];
  metadata: Record<string, any>;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relationship_type: string;
  provenance: string;
  confidence: number;
  is_inferred: boolean;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  total_edges: number;
  truncated: boolean;
}

export interface SearchResultItem {
  document_id: string;
  file_path: string;
  language: string;
  line_range: [number, number];
  score: number;
  snippet: string;
  symbol_name?: string;
  symbol_type?: string;
  graph_signals?: Record<string, any>;
}

export interface SearchResponse {
  query: string;
  method: string;
  latency_ms: number;
  total_results: number;
  results: SearchResultItem[];
}

export interface Citation {
  file_path: string;
  start_line: number;
  end_line: number;
  symbol_name?: string;
  snippet?: string;
  is_valid: boolean;
  validation_notes?: string;
}

export interface AskResponse {
  question: string;
  answer: string;
  citations: Citation[];
  retrieved_evidence: SearchResultItem[];
  retrieval_method: string;
  mode: 'gemini' | 'demo';
  languages_represented: string[];
  uncertainty_notes?: string;
  latency_ms: number;
}

export interface EvaluationMethodResult {
  recall_at_5: number;
  mrr: number;
  avg_latency_ms: number;
  citation_correctness?: number;
  total_queries: number;
  successful_queries: number;
  per_language: Record<string, { recall_at_5: number; mrr: number; queries_evaluated: number }>;
  per_question: Array<{
    id: string;
    question: string;
    language: string;
    expected_files: string[];
    hit_at_5: boolean;
    first_rank: number;
    reciprocal_rank: number;
    retrieved_top_files: string[];
    latency_ms: number;
  }>;
  failed_cases: Array<{
    id: string;
    question: string;
    language: string;
    expected_files: string[];
    retrieved: string[];
    explanation: string;
  }>;
}

export interface EvaluationResult {
  benchmark_id: string;
  benchmark_size: number;
  evaluated_at: string;
  methods: Record<string, EvaluationMethodResult>;
  metric_definitions: Record<string, string>;
}

export interface HealthResponse {
  status: string;
  app: string;
  version: string;
  gemini_configured: boolean;
  gemini_model: string;
  supported_languages: string[];
}
