import React, { useState } from 'react';
import {
  Sparkles,
  Send,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Layers,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  HelpCircle,
  Clock
} from 'lucide-react';
import { AskResponse, Citation, SearchResultItem } from '../types';
import { askRepositoryAI } from '../api/client';

interface AskAIProps {
  repoId: string;
  onNavigateToSource: (filePath: string, lineRange?: [number, number]) => void;
}

export const AskAI: React.FC<AskAIProps> = ({ repoId, onNavigateToSource }) => {
  const [question, setQuestion] = useState('');
  const [retrievalMethod, setRetrievalMethod] = useState<'tfidf' | 'graph_assisted'>('graph_assisted');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<AskResponse | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [expandedSnippets, setExpandedSnippets] = useState<Record<number, boolean>>({});

  const sampleQuestions = [
    'Where is tax calculation handled?',
    'Which class handles order processing and invoices?',
    'Where is user JWT token validation implemented?',
    'Where is the UserProfile data interface defined?',
    'Which class executes credit card payments?',
    'Where is the network socket initialization implemented?',
    'Where is in-memory caching logic implemented?'
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    setIsLoading(true);
    setErrorMsg(null);
    setResponse(null);

    try {
      const data = await askRepositoryAI(repoId, question, retrievalMethod, 8);
      setResponse(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to generate answer');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSnippet = (idx: number) => {
    setExpandedSnippets((prev) => ({ ...prev, [idx]: !prev[idx] }));
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-16">
      {/* Ask Header */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">
              Evidence-Grounded Code Assistant
            </h2>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500 font-medium">Retrieval Engine:</span>
            <select
              value={retrievalMethod}
              onChange={(e) => setRetrievalMethod(e.target.value as any)}
              className="text-xs font-semibold bg-slate-50 border border-slate-300 rounded-md px-2.5 py-1 text-slate-700 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="graph_assisted">Method B: Graph-Assisted</option>
              <option value="tfidf">Method A: TF-IDF Baseline</option>
            </select>
          </div>
        </div>
        <p className="text-xs text-slate-500">
          TraceBench retrieves bounded source snippets and answers questions with verifiable file and line references.
        </p>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="mt-4">
          <div className="relative">
            <textarea
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask any architectural, functional, or implementation question about this repository..."
              className="w-full text-xs p-3 pr-24 bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white transition"
            />
            <button
              type="submit"
              disabled={isLoading || !question.trim()}
              className="absolute right-3 bottom-3.5 px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-semibold rounded-md shadow-sm transition flex items-center gap-1.5"
            >
              <Send className="w-3.5 h-3.5" />
              {isLoading ? 'Retrieving...' : 'Ask'}
            </button>
          </div>
        </form>

        {/* Suggested Queries */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] font-medium text-slate-400">Sample questions:</span>
          {sampleQuestions.map((sq, i) => (
            <button
              key={i}
              type="button"
              onClick={() => setQuestion(sq)}
              className="text-[11px] px-2 py-0.5 rounded bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
            >
              {sq}
            </button>
          ))}
        </div>
      </div>

      {/* Error state */}
      {errorMsg && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2.5">
          <AlertTriangle className="w-4 h-4 flex-shrink-0 text-red-500" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Response Display */}
      {response && (
        <div className="space-y-6">
          {/* Answer Card */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <span className="text-xs font-semibold text-slate-700">Synthesized Answer</span>
                <span
                  className={`text-[10px] font-semibold px-2 py-0.5 rounded-full ${
                    response.mode === 'gemini'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-purple-100 text-purple-800'
                  }`}
                >
                  {response.mode === 'gemini' ? 'Live Gemini Model' : 'Deterministic Evidence Mode'}
                </span>
              </div>
              <div className="flex items-center gap-3 text-[11px] text-slate-400 font-mono">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {response.latency_ms} ms
                </span>
                <span>•</span>
                <span>{response.retrieval_method.toUpperCase()}</span>
              </div>
            </div>

            {/* Answer Content */}
            <div className="prose prose-sm max-w-none text-xs text-slate-800 leading-relaxed space-y-2 whitespace-pre-wrap">
              {response.answer}
            </div>

            {/* Uncertainty Notice if present */}
            {response.uncertainty_notes && (
              <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-[11px] flex items-start gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600 flex-shrink-0 mt-0.5" />
                <span>{response.uncertainty_notes}</span>
              </div>
            )}

            {/* Validated Clickable Citations */}
            {response.citations.length > 0 && (
              <div className="pt-3 border-t border-slate-100">
                <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Verified Citations ({response.citations.length})
                </div>
                <div className="flex flex-wrap gap-2">
                  {response.citations.map((c, i) => (
                    <button
                      key={i}
                      onClick={() => onNavigateToSource(c.file_path, [c.start_line, c.end_line])}
                      className={`text-xs px-2.5 py-1 rounded-md border font-mono transition flex items-center gap-1.5 shadow-2xs ${
                        c.is_valid
                          ? 'bg-emerald-50 hover:bg-emerald-100 border-emerald-300 text-emerald-800'
                          : 'bg-red-50 border-red-300 text-red-800 line-through'
                      }`}
                      title={c.validation_notes || 'Click to view highlighted lines in Source Explorer'}
                    >
                      <FileText className="w-3 h-3 text-emerald-600" />
                      <span>{c.file_path}#L{c.start_line}-L{c.end_line}</span>
                      <ExternalLink className="w-2.5 h-2.5 opacity-60" />
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Retrieved Evidence Snippets List */}
          <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center justify-between">
              <span>Retrieved Ground-Truth Evidence ({response.retrieved_evidence.length})</span>
              <span className="text-xs font-normal text-slate-400">
                Languages: {response.languages_represented.join(', ')}
              </span>
            </h3>

            <div className="space-y-2.5">
              {response.retrieved_evidence.map((item, idx) => {
                const isExpanded = !!expandedSnippets[idx];

                return (
                  <div
                    key={item.document_id + idx}
                    className="p-3 rounded-lg border border-slate-200 bg-slate-50/60 hover:bg-slate-50 transition"
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <div className="flex items-center gap-2 truncate">
                        <button
                          onClick={() => onNavigateToSource(item.file_path, item.line_range)}
                          className="font-mono text-xs font-bold text-blue-700 hover:underline truncate"
                        >
                          {item.file_path}
                        </button>
                        <span className="text-[10px] font-mono text-slate-500">
                          L{item.line_range[0]}-L{item.line_range[1]}
                        </span>
                        {item.symbol_name && (
                          <span className="text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-mono">
                            {item.symbol_name}
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                          Score: {item.score}
                        </span>
                        <button
                          onClick={() => toggleSnippet(idx)}
                          className="text-slate-400 hover:text-slate-600 p-0.5"
                        >
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>

                    {/* Expandable Snippet Preview */}
                    {isExpanded && (
                      <div className="mt-2 p-2 rounded bg-slate-900 text-slate-100 font-mono text-[11px] overflow-x-auto leading-relaxed border border-slate-800">
                        <pre>{item.snippet}</pre>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
