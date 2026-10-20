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

const API_BASE = (import.meta as any).env?.VITE_API_URL || '/api';

async function handleResponseError(res: Response, defaultMessage: string): Promise<never> {
  let message = defaultMessage;
  try {
    const errorData = await res.json();
    if (errorData && typeof errorData.detail === 'string') {
      message = errorData.detail;
    } else if (errorData && typeof errorData.message === 'string') {
      message = errorData.message;
    }
  } catch {
    // If response is not JSON (e.g. 502 from proxy or 500 HTML)
    if (res.status === 502) {
      message = 'Backend server is unreachable (502 Bad Gateway). Please verify that the FastAPI backend is running on http://127.0.0.1:8000.';
    } else if (res.status === 503) {
      message = 'Backend service temporarily unavailable (503).';
    } else if (res.status === 504) {
      message = 'Gateway timeout (504). The repository download or indexing took too long.';
    } else if (res.status === 413) {
      message = 'Upload payload too large (413). File exceeds maximum upload limit.';
    } else if (res.statusText) {
      message = `${defaultMessage} (HTTP ${res.status}: ${res.statusText})`;
    } else {
      message = `${defaultMessage} (HTTP ${res.status})`;
    }
  }
  throw new Error(message);
}

export async function fetchHealth(): Promise<HealthResponse> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) await handleResponseError(res, 'Failed to fetch system health');
    return res.json();
  } catch (err: any) {
    if (err.message && err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to TraceBench backend. Please ensure the server is running on http://127.0.0.1:8000.');
    }
    throw err;
  }
}

export async function fetchRepositories(): Promise<RepositoryMetadata[]> {
  try {
    const res = await fetch(`${API_BASE}/repositories`);
    if (!res.ok) await handleResponseError(res, 'Failed to list repositories');
    return res.json();
  } catch (err: any) {
    if (err.message && err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to TraceBench backend. Please ensure the server is running on http://127.0.0.1:8000.');
    }
    throw err;
  }
}

export async function importGitHubRepo(url: string, branch?: string): Promise<RepositoryMetadata> {
  try {
    const res = await fetch(`${API_BASE}/repositories/github`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, branch: branch || undefined }),
    });
    if (!res.ok) await handleResponseError(res, 'GitHub repository import failed');
    return res.json();
  } catch (err: any) {
    if (err.message && err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to TraceBench backend. Please ensure the server is running on http://127.0.0.1:8000.');
    }
    throw err;
  }
}

export async function uploadZipRepo(file: File): Promise<RepositoryMetadata> {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/repositories/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) await handleResponseError(res, 'ZIP archive upload failed');
    return res.json();
  } catch (err: any) {
    if (err.message && err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to TraceBench backend. Please ensure the server is running on http://127.0.0.1:8000.');
    }
    throw err;
  }
}

export async function loadSampleRepo(): Promise<RepositoryMetadata> {
  try {
    const res = await fetch(`${API_BASE}/repositories/sample`, {
      method: 'POST',
    });
    if (!res.ok) await handleResponseError(res, 'Failed to load sample repository');
    return res.json();
  } catch (err: any) {
    if (err.message && err.message.includes('Failed to fetch')) {
      throw new Error('Unable to connect to TraceBench backend. Please ensure the server is running on http://127.0.0.1:8000.');
    }
    throw err;
  }
}

export async function fetchRepository(repoId: string): Promise<RepositoryMetadata> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}`);
  if (!res.ok) await handleResponseError(res, `Repository ${repoId} not found`);
  return res.json();
}

export async function fetchRepositoryFiles(repoId: string): Promise<IndexedFile[]> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/files`);
  if (!res.ok) await handleResponseError(res, 'Failed to fetch repository files');
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
  if (!res.ok) await handleResponseError(res, `Failed to fetch file content for ${path}`);
  return res.json();
}

export async function fetchRepositoryLanguages(repoId: string): Promise<Record<string, LanguageCapability>> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/languages`);
  if (!res.ok) await handleResponseError(res, 'Failed to fetch language capabilities');
  return res.json();
}

export async function fetchRepositorySymbols(repoId: string, language?: string, filePath?: string): Promise<CodeSymbol[]> {
  let url = `${API_BASE}/repositories/${repoId}/symbols?`;
  if (language) url += `language=${encodeURIComponent(language)}&`;
  if (filePath) url += `file_path=${encodeURIComponent(filePath)}&`;
  const res = await fetch(url);
  if (!res.ok) await handleResponseError(res, 'Failed to fetch symbols');
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
  if (!res.ok) await handleResponseError(res, 'Failed to fetch repository graph');
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
  if (!res.ok) await handleResponseError(res, 'Search request failed');
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
  if (!res.ok) await handleResponseError(res, 'Ask AI request failed');
  return res.json();
}

export async function evaluateRepository(repoId: string): Promise<EvaluationResult> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/evaluate`, {
    method: 'POST',
  });
  if (!res.ok) await handleResponseError(res, 'Evaluation execution failed');
  return res.json();
}

export async function fetchEvaluation(repoId: string): Promise<EvaluationResult> {
  const res = await fetch(`${API_BASE}/repositories/${repoId}/evaluation`);
  if (!res.ok) await handleResponseError(res, 'Failed to retrieve evaluation results');
  return res.json();
}
