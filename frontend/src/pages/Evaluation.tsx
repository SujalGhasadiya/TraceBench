import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  RefreshCw,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Clock,
  Target,
  Award,
  Layers,
  Info,
  AlertTriangle
} from 'lucide-react';
import { EvaluationResult, EvaluationMethodResult } from '../types';
import { fetchEvaluation, evaluateRepository } from '../api/client';

interface EvaluationProps {
  repoId: string;
}

export const Evaluation: React.FC<EvaluationProps> = ({ repoId }) => {
  const [evaluation, setEvaluation] = useState<EvaluationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeMethod, setActiveMethod] = useState<'tfidf' | 'graph_assisted'>('graph_assisted');

  const loadEvaluation = () => {
    setIsLoading(true);
    fetchEvaluation(repoId)
      .then((data) => setEvaluation(data))
      .catch((err) => console.error('Failed to load evaluation:', err))
      .finally(() => setIsLoading(false));
  };

  const handleRerun = () => {
    setIsLoading(true);
    evaluateRepository(repoId)
      .then((data) => setEvaluation(data))
      .catch((err) => console.error('Failed to run evaluation:', err))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    loadEvaluation();
  }, [repoId]);

  const tfidfResult: EvaluationMethodResult | undefined = evaluation?.methods?.tfidf;
  const graphResult: EvaluationMethodResult | undefined = evaluation?.methods?.graph_assisted;
  const currentResult = activeMethod === 'graph_assisted' ? graphResult : tfidfResult;

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-16">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-[11px] font-semibold mb-2">
            <BarChart3 className="w-3.5 h-3.5" />
            Empirical Retrieval Evaluation
          </div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Benchmark Quality & Retrieval Metrics
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Evaluates retrieval effectiveness across multi-language questions against manually verified ground truth.
          </p>
        </div>

        <button
          onClick={handleRerun}
          disabled={isLoading}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold rounded-lg shadow-sm transition flex items-center gap-2"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          {isLoading ? 'Evaluating Benchmark...' : 'Rerun Benchmark Evaluation'}
        </button>
      </div>

      {evaluation ? (
        <>
          {/* Method Comparison Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Method A: TF-IDF */}
            <div
              onClick={() => setActiveMethod('tfidf')}
              className={`p-5 rounded-xl border text-left cursor-pointer transition ${
                activeMethod === 'tfidf'
                  ? 'border-blue-500 bg-white shadow-md ring-1 ring-blue-500/20'
                  : 'border-slate-200 bg-white/70 hover:bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-900">Method A: TF-IDF Lexical Baseline</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                  scikit-learn
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium">Recall@5</span>
                  <span className="text-xl font-bold text-slate-900">
                    {tfidfResult ? `${Math.round(tfidfResult.recall_at_5 * 100)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium">MRR</span>
                  <span className="text-xl font-bold text-slate-900">
                    {tfidfResult?.mrr ?? 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium">Latency</span>
                  <span className="text-xl font-bold text-slate-900">
                    {tfidfResult ? `${tfidfResult.avg_latency_ms}ms` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Method B: Graph-Assisted */}
            <div
              onClick={() => setActiveMethod('graph_assisted')}
              className={`p-5 rounded-xl border text-left cursor-pointer transition ${
                activeMethod === 'graph_assisted'
                  ? 'border-blue-500 bg-white shadow-md ring-1 ring-blue-500/20'
                  : 'border-slate-200 bg-white/70 hover:bg-white'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-bold text-slate-900">Method B: Graph-Assisted Retrieval</span>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                  TF-IDF + NetworkX
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium">Recall@5</span>
                  <span className="text-xl font-bold text-blue-700">
                    {graphResult ? `${Math.round(graphResult.recall_at_5 * 100)}%` : 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium">MRR</span>
                  <span className="text-xl font-bold text-blue-700">
                    {graphResult?.mrr ?? 'N/A'}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 block font-medium">Latency</span>
                  <span className="text-xl font-bold text-slate-900">
                    {graphResult ? `${graphResult.avg_latency_ms}ms` : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Metric Definitions & Transparency Note */}
          <div className="p-4 rounded-xl bg-slate-100/70 border border-slate-200/80 text-xs text-slate-600 space-y-1.5">
            <div className="font-bold text-slate-800 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-blue-600" />
              Verified Metric Definitions
            </div>
            {Object.entries(evaluation.metric_definitions).map(([name, desc]) => (
              <p key={name} className="text-[11px]">
                <strong>{name}:</strong> {desc}
              </p>
            ))}
          </div>

          {/* Per-Language Breakdown Table */}
          {currentResult?.per_language && (
            <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 mb-1">
                Per-Language Performance ({activeMethod === 'graph_assisted' ? 'Graph-Assisted' : 'TF-IDF'})
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Measures retrieval success broken down by programming language target.
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 text-[11px] uppercase">
                      <th className="py-2 px-3 font-semibold">Language</th>
                      <th className="py-2 px-3 font-semibold">Queries</th>
                      <th className="py-2 px-3 font-semibold">Recall@5</th>
                      <th className="py-2 px-3 font-semibold">MRR</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(currentResult.per_language).map(([lang, stat]) => (
                      <tr key={lang} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-2.5 px-3 font-semibold text-slate-800 capitalize">{lang}</td>
                        <td className="py-2.5 px-3 text-slate-600">{stat.queries_evaluated}</td>
                        <td className="py-2.5 px-3">
                          <span className="font-semibold text-emerald-700">
                            {Math.round(stat.recall_at_5 * 100)}%
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-700">{stat.mrr}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Per-Question Results Table */}
          {currentResult?.per_question && (
            <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
              <h3 className="text-sm font-bold text-slate-900 mb-3">
                Per-Question Evaluation Log ({currentResult.per_question.length} queries)
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-slate-200 text-slate-400 text-[11px] uppercase">
                      <th className="py-2 px-3 font-semibold">ID</th>
                      <th className="py-2 px-3 font-semibold">Question</th>
                      <th className="py-2 px-3 font-semibold">Language</th>
                      <th className="py-2 px-3 font-semibold">Result</th>
                      <th className="py-2 px-3 font-semibold">Rank</th>
                      <th className="py-2 px-3 font-semibold">Latency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {currentResult.per_question.map((q) => (
                      <tr key={q.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-2 px-3 font-mono text-slate-500 text-[11px]">{q.id}</td>
                        <td className="py-2 px-3 text-slate-800 font-medium">{q.question}</td>
                        <td className="py-2 px-3 text-slate-500 uppercase text-[10px]">{q.language}</td>
                        <td className="py-2 px-3">
                          {q.hit_at_5 ? (
                            <span className="inline-flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Hit@5
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 text-red-700 font-medium text-[11px]">
                              <XCircle className="w-3.5 h-3.5 text-red-500" /> Miss
                            </span>
                          )}
                        </td>
                        <td className="py-2 px-3 font-mono text-slate-600">
                          {q.first_rank > 0 ? `#${q.first_rank}` : 'None'}
                        </td>
                        <td className="py-2 px-3 font-mono text-slate-400 text-[11px]">{q.latency_ms}ms</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Failed Retrieval Cases */}
          {currentResult?.failed_cases && currentResult.failed_cases.length > 0 && (
            <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
              <div className="flex items-center gap-2 text-slate-900 font-bold text-sm mb-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Failed Retrieval Diagnostics ({currentResult.failed_cases.length})
              </div>
              <p className="text-xs text-slate-500 mb-4">
                Queries where none of the expected source files appeared in the top 5 candidates.
              </p>
              <div className="space-y-3">
                {currentResult.failed_cases.map((fc) => (
                  <div key={fc.id} className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 text-xs space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800">{fc.question}</span>
                      <span className="font-mono text-[10px] text-slate-400 uppercase">{fc.language}</span>
                    </div>
                    <div className="text-slate-600 text-[11px]">
                      <span className="text-slate-400">Expected files: </span>
                      <code className="bg-slate-200 px-1 py-0.5 rounded text-slate-800">
                        {fc.expected_files.join(', ') || 'None (Negative Case)'}
                      </code>
                    </div>
                    <div className="text-slate-500 text-[11px]">
                      <span className="text-slate-400">Explanation: </span>
                      {fc.explanation}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-slate-400 text-xs">
          {isLoading ? 'Computing benchmark evaluation...' : 'No evaluation data loaded.'}
        </div>
      )}
    </div>
  );
};
