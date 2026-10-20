import React from 'react';
import {
  FileCode,
  Layers,
  Network,
  Cpu,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  CheckCircle2,
  FileText
} from 'lucide-react';
import { RepositoryMetadata } from '../types';

interface RepositoryOverviewProps {
  repo: RepositoryMetadata;
  onNavigateTab: (tab: string) => void;
}

export const RepositoryOverview: React.FC<RepositoryOverviewProps> = ({
  repo,
  onNavigateTab,
}) => {
  const languageList = Object.entries(repo.language_breakdown).sort((a, b) => b[1] - a[1]);
  const totalFiles = repo.file_count || 1;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      {/* Header Banner */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-100 text-blue-700">
              {repo.source_type} repository
            </span>
            <span className="text-xs text-slate-400">ID: {repo.id}</span>
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">{repo.name}</h2>
          {repo.source_url && (
            <p className="text-xs text-slate-500 mt-1 font-mono">{repo.source_url}</p>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => onNavigateTab('explorer')}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5"
          >
            <FileCode className="w-4 h-4 text-slate-500" />
            Explore Source
          </button>
          <button
            onClick={() => onNavigateTab('graph')}
            className="px-3.5 py-2 bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5"
          >
            <Network className="w-4 h-4 text-blue-600" />
            View Graph
          </button>
          <button
            onClick={() => onNavigateTab('ask')}
            className="px-3.5 py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-1.5"
          >
            <Sparkles className="w-4 h-4" />
            Ask AI
          </button>
        </div>
      </div>

      {/* Metrics Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Indexed Files</span>
            <FileCode className="w-4 h-4 text-blue-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{repo.file_count}</div>
          <div className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            100% searchable text index
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Structurally Parsed</span>
            <Cpu className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{repo.parsed_file_count}</div>
          <div className="text-[11px] text-slate-400 mt-1">
            {Math.round((repo.parsed_file_count / totalFiles) * 100)}% structural grammar parsed
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Extracted Symbols</span>
            <Layers className="w-4 h-4 text-indigo-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{repo.symbol_count}</div>
          <div className="text-[11px] text-slate-400 mt-1">
            Functions, methods & classes
          </div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-semibold">Graph Relationships</span>
            <Network className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{repo.edge_count}</div>
          <div className="text-[11px] text-slate-400 mt-1">
            Contains, imports & calls
          </div>
        </div>
      </div>

      {/* Multi-Language Breakdown */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-1">Programming Languages Detected</h3>
        <p className="text-xs text-slate-500 mb-4">
          TraceBench supports mixed-language repositories without assuming a single language architecture.
        </p>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
          {languageList.map(([lang, count]) => {
            const percent = Math.round((count / totalFiles) * 100);
            const isText = lang.toLowerCase() === 'text';

            return (
              <div key={lang} className="p-3.5 rounded-lg border border-slate-200/70 bg-slate-50/50">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-xs text-slate-800 capitalize">{lang}</span>
                  <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    isText ? 'bg-slate-200 text-slate-700' : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {isText ? 'Text-Indexed' : 'Structural AST'}
                  </span>
                </div>
                <div className="flex items-baseline justify-between text-xs text-slate-600 mb-1.5">
                  <span>{count} {count === 1 ? 'file' : 'files'}</span>
                  <span className="font-medium text-slate-700">{percent}%</span>
                </div>
                <div className="w-full h-1.5 bg-slate-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${isText ? 'bg-slate-400' : 'bg-blue-600'}`}
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Skipped / Secret Files Notice */}
      {repo.skipped_files && repo.skipped_files.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
          <div className="flex items-center gap-2 text-slate-900 font-semibold text-sm mb-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            Filtered / Skipped Files ({repo.skipped_files.length})
          </div>
          <p className="text-xs text-slate-500 mb-3">
            These files were automatically excluded during ingestion to prevent secret leaks and ignore build noise.
          </p>
          <div className="max-h-36 overflow-y-auto p-2.5 rounded-md bg-slate-50 border border-slate-200 font-mono text-[11px] text-slate-600 space-y-1">
            {repo.skipped_files.map((f, i) => (
              <div key={i} className="truncate">• {f}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
