import {
  HealthResponse,
  RepositoryMetadata,
  IndexedFile,
  CodeSymbol,
  GraphResponse,
  SearchResponse,
  AskResponse,
  EvaluationResult,
  LanguageCapability
} from '../types';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error('Failed to fetch system health');
  return res.json();
}

export async function fetchRepositories(): Promise<RepositoryMetadata[]> {
  const res = await fetch(`${API_BASE}/repositories`);
  if (!res.ok) throw new Error('Failed to list repositories');
  return res.json();
}

export async function importGitHubRepo(url: string, branch?: string): Promise<RepositoryMetadata> {
  const res = await fetch(`${API_BASE}/repositories/github`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url, branch: branch || undefined }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to import GitHub repo' }));
    throw new Error(errorData.detail || 'GitHub import failed');
  }
  return res.json();
}

export async function uploadZipRepo(file: File): Promise<RepositoryMetadata> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/repositories/upload`, {
    method: 'POST',
    body: formData,
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to upload ZIP' }));
    throw new Error(errorData.detail || 'ZIP upload failed');
  }
  return res.json();
}

export async function loadSampleRepo(): Promise<RepositoryMetadata> {
  const res = await fetch(`${API_BASE}/repositories/sample`, {
    method: 'POST',
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to load sample repo' }));
    throw new Error(errorData.detail || 'Failed to load sample repository');
  }
  return res.json();
}

export async function fetchRepository(repoId: string): Promise<RepositoryMetadata> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}`);
  if (!res.ok) throw new Error('Repository not found');
  return res.json();
}

export async function fetchRepositoryFiles(repoId: string): Promise<IndexedFile[]> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/files`);
  if (!res.ok) throw new Error('Failed to fetch repository files');
  return res.json();
}

export async function fetchFileContent(repoId: string, path: string): Promise<{
  file_path: string;
  language: string;
  line_count: number;
  is_parsed: boolean;
  content: string;
  symbols: CodeSymbol[];
}> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/files/content?path=${encodeURIComponent(path)}`);
  if (!res.ok) throw new Error(`Failed to fetch file content for ${path}`);
  return res.json();
}

export async function fetchRepositoryLanguages(repoId: string): Promise<Record<string, LanguageCapability>> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/languages`);
  if (!res.ok) throw new Error('Failed to fetch language capabilities');
  return res.json();
}

export async function fetchRepositorySymbols(repoId: string, language?: string, filePath?: string): Promise<CodeSymbol[]> {
  let url = `${API_BASE}/repositories/${repoId}/symbols?`;
  if (language) url += `language=${encodeURIComponent(language)}&`;
  if (filePath) url += `file_path=${encodeURIComponent(filePath)}&`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch symbols');
  return res.json();
}

export async function fetchRepositoryGraph(
  repoId: string,
  nodeId?: string,
  maxNodes: number = 50,
  nodeTypes?: string[],
  relationshipTypes?: string[]
): Promise<GraphResponse> {
  let url = `${API_BASE}/repositories/${repoId}/graph?max_nodes=${maxNodes}&`;
  if (nodeId) url += `node_id=${encodeURIComponent(nodeId)}&`;
  if (nodeTypes && nodeTypes.length > 0) url += `node_types=${encodeURIComponent(nodeTypes.join(','))}&`;
  if (relationshipTypes && relationshipTypes.length > 0) url += `relationship_types=${encodeURIComponent(relationshipTypes.join(','))}&`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch repository graph');
  return res.json();
}

export async function searchRepository(
  repoId: string,
  query: string,
  method: 'tfidf' | 'graph_assisted' = 'tfidf',
  topK: number = 10,
  languageFilter?: string
): Promise<SearchResponse> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      method,
      top_k: topK,
      language_filter: languageFilter || undefined,
    }),
  });
  if (!res.ok) throw new Error('Search failed');
  return res.json();
}

export async function askRepositoryAI(
  repoId: string,
  question: string,
  retrievalMethod: 'tfidf' | 'graph_assisted' = 'tfidf',
  topK: number = 8
): Promise<AskResponse> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question,
      retrieval_method: retrievalMethod,
      top_k: topK,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to ask AI' }));
    throw new Error(errorData.detail || 'Ask AI failed');
  }
  return res.json();
}

export async function evaluateRepository(repoId: string): Promise<EvaluationResult> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/evaluate`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Evaluation execution failed');
  return res.json();
}

export async function fetchEvaluation(repoId: string): Promise<EvaluationResult> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/evaluation`);
  if (!res.ok) throw new Error('Failed to retrieve evaluation results');
  return res.json();
}
