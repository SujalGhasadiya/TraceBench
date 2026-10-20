import React, { useState } from 'react';
import {
  FolderGit2,
  UploadCloud,
  FolderArchive,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  FileCode,
  ArrowRight,
  Boxes
} from 'lucide-react';
import { RepositoryMetadata } from '../types';
import { importGitHubRepo, uploadZipRepo, loadSampleRepo } from '../api/client';

interface HomeProps {
  repositories: RepositoryMetadata[];
  currentRepo: RepositoryMetadata | null;
  onSelectRepo: (repoId: string) => void;
  onRepoImported: (repo: RepositoryMetadata) => void;
}

export const Home: React.FC<HomeProps> = ({
  repositories,
  currentRepo,
  onSelectRepo,
  onRepoImported,
}) => {
  const [githubUrl, setGithubUrl] = useState('');
  const [githubBranch, setGithubBranch] = useState('');
  const [isImporting, setIsImporting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleGitHubImport = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl.trim()) return;
    setIsImporting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const repo = await importGitHubRepo(githubUrl, githubBranch);
      onRepoImported(repo);
      setSuccessMsg(`Successfully imported and indexed ${repo.name} (${repo.file_count} files)`);
      setGithubUrl('');
      setGithubBranch('');
    } catch (err: any) {
      setErrorMsg(err.message || 'GitHub import failed');
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsImporting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const repo = await uploadZipRepo(file);
      onRepoImported(repo);
      setSuccessMsg(`Successfully uploaded and indexed ${repo.name} (${repo.file_count} files)`);
    } catch (err: any) {
      setErrorMsg(err.message || 'ZIP upload failed');
    } finally {
      setIsImporting(false);
      e.target.value = '';
    }
  };

  const handleLoadSample = async () => {
    setIsImporting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      const repo = await loadSampleRepo();
      onRepoImported(repo);
      setSuccessMsg(`Sample multi-language repository loaded (${repo.file_count} files)`);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load sample repository');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-12">
      {/* Hero Banner */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-8 shadow-sm">
        <div className="max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-xs font-semibold mb-3">
            <Sparkles className="w-3.5 h-3.5" />
            Evidence-Grounded Code Intelligence
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
            Investigate any software codebase with verifiable evidence.
          </h2>
          <p className="mt-2 text-sm text-slate-600 leading-relaxed">
            TraceBench analyzes multi-language source repositories, extracts syntax structures and relationship graphs, searches code with lexical and graph ranking, and answers architecture questions with exact file and line citations.
          </p>
        </div>

        {/* Quick Launch Sample Repo Card */}
        <div className="mt-6 p-4 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-600/10 text-blue-600 flex items-center justify-center font-bold">
              <Boxes className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-slate-900">
                Explore Sample Multi-Language E-Commerce Repository
              </h4>
              <p className="text-xs text-slate-500">
                Includes verified Python, JavaScript, TypeScript, Java, C, C++, Go, Rust, and PHP microservices.
              </p>
            </div>
          </div>
          <button
            onClick={handleLoadSample}
            disabled={isImporting}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium rounded-lg shadow-sm transition flex items-center gap-2"
          >
            {isImporting ? 'Indexing...' : 'Analyze Sample Repo'}
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Alert Notices */}
      {errorMsg && (
        <div className="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2.5">
          <AlertCircle className="w-4 h-4 flex-shrink-0 text-red-500" />
          <span>{errorMsg}</span>
        </div>
      )}
      {successMsg && (
        <div className="p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs flex items-center gap-2.5">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-500" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Import Methods Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* GitHub Ingestion */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-slate-900 font-semibold text-base mb-1">
              <FolderGit2 className="w-5 h-5 text-slate-700" />
              Import Public GitHub Repository
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Enter any public GitHub repository URL. The codebase will be downloaded safely as a ZIP archive and indexed without executing any code.
            </p>

            <form onSubmit={handleGitHubImport} className="space-y-3">
              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1">
                  GitHub Repository URL
                </label>
                <input
                  type="text"
                  placeholder="https://github.com/owner/repository"
                  value={githubUrl}
                  onChange={(e) => setGithubUrl(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-slate-700 block mb-1">
                  Branch (Optional)
                </label>
                <input
                  type="text"
                  placeholder="main or master (default)"
                  value={githubBranch}
                  onChange={(e) => setGithubBranch(e.target.value)}
                  className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={isImporting || !githubUrl.trim()}
                className="w-full mt-2 py-2.5 px-4 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold rounded-md shadow-sm transition flex items-center justify-center gap-2"
              >
                {isImporting ? 'Ingesting Repository...' : 'Clone & Analyze Repository'}
              </button>
            </form>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Code is never executed on the host system.
          </div>
        </div>

        {/* Local ZIP Ingestion */}
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-slate-900 font-semibold text-base mb-1">
              <FolderArchive className="w-5 h-5 text-blue-600" />
              Upload Local Project Archive (ZIP)
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Upload any local repository as a `.zip` file. TraceBench extracts and indexes source files while enforcing strict path traversal safeguards.
            </p>

            <div className="border-2 border-dashed border-slate-300 hover:border-blue-400 rounded-lg p-6 text-center transition-colors bg-slate-50/50">
              <UploadCloud className="w-8 h-8 text-slate-400 mx-auto mb-2" />
              <p className="text-xs font-medium text-slate-700 mb-1">
                Drag and drop your project ZIP, or browse
              </p>
              <p className="text-[11px] text-slate-400 mb-3">
                Max 50MB archive size • Up to 2,000 files
              </p>
              <label className="inline-block px-3 py-1.5 bg-white border border-slate-300 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-50 cursor-pointer shadow-sm">
                Select .zip File
                <input
                  type="file"
                  accept=".zip"
                  onChange={handleFileUpload}
                  disabled={isImporting}
                  className="hidden"
                />
              </label>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400 flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
            Automatic Zip-Slip traversal defense and sensitive file exclusion.
          </div>
        </div>
      </div>

      {/* Indexed Repositories List */}
      {repositories.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
          <h3 className="text-sm font-bold text-slate-900 mb-3">Indexed Repositories ({repositories.length})</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {repositories.map((repo) => (
              <div
                key={repo.id}
                onClick={() => onSelectRepo(repo.id)}
                className={`p-3.5 rounded-lg border text-left cursor-pointer transition ${
                  currentRepo?.id === repo.id
                    ? 'border-blue-500 bg-blue-50/40 shadow-xs'
                    : 'border-slate-200 hover:border-slate-300 bg-slate-50/30'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <h4 className="font-semibold text-xs text-slate-900 truncate max-w-[180px]">{repo.name}</h4>
                  <span className="text-[10px] uppercase font-semibold px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                    {repo.source_type}
                  </span>
                </div>
                <div className="flex items-center gap-3 text-[11px] text-slate-500">
                  <span>{repo.file_count} files</span>
                  <span>•</span>
                  <span>{repo.symbol_count} symbols</span>
                  <span>•</span>
                  <span>{repo.edge_count} edges</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Security & System Boundaries */}
      <div className="p-5 rounded-xl bg-slate-100/70 border border-slate-200/80 text-xs text-slate-600 space-y-2">
        <h4 className="font-bold text-slate-800 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-blue-600" />
          TraceBench Security & Processing Model
        </h4>
        <p>
          <strong>Untrusted Code Boundary:</strong> All imported source code, docstrings, and comments are treated as untrusted data. TraceBench performs purely static parsing using Tree-sitter and AST; no imported code is executed.
        </p>
        <p>
          <strong>Sensitive File Filtering:</strong> TraceBench automatically skips <code className="bg-slate-200 px-1 py-0.5 rounded">.git</code>, <code className="bg-slate-200 px-1 py-0.5 rounded">node_modules</code>, virtual environments, <code className="bg-slate-200 px-1 py-0.5 rounded">.env</code> files, and private keys (<code className="bg-slate-200 px-1 py-0.5 rounded">.pem</code>, <code className="bg-slate-200 px-1 py-0.5 rounded">.key</code>, <code className="bg-slate-200 px-1 py-0.5 rounded">id_rsa</code>).
        </p>
        <p>
          <strong>Local vs External Processing:</strong> Repository indexing, text search, and graph operations occur 100% locally on your machine. Only bounded retrieved snippets are transmitted to Google Gemini when an API key is configured.
        </p>
      </div>
    </div>
  );
};
