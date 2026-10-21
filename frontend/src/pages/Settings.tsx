import React, { useState, useEffect } from 'react';
import {
  Settings as SettingsIcon,
  Cpu,
  ShieldCheck,
  Layers,
  Database,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  FileCode,
  Network,
  Sparkles
} from 'lucide-react';
import { LanguageCapability } from '../types';
import { fetchRepositoryLanguages } from '../api/client';

interface SettingsProps {
  repoId?: string;
}

export const Settings: React.FC<SettingsProps> = ({ repoId }) => {
  const [capabilities, setCapabilities] = useState<Record<string, LanguageCapability>>({});

  useEffect(() => {
    if (repoId) {
      fetchRepositoryLanguages(repoId)
        .then((caps) => setCapabilities(caps))
        .catch((e) => console.error(e));
    }
  }, [repoId]);

  return (
    <div className="max-w-5xl mx-auto space-y-8 pb-16">
      {/* Header */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm">
        <div className="flex items-center gap-2 mb-2">
          <SettingsIcon className="w-5 h-5 text-blue-600" />
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            Settings, Architecture & Capabilities
          </h2>
        </div>
        <p className="text-xs text-slate-500">
          TraceBench is an open evidence-grounded code intelligence platform designed for deep codebase investigation and measurable retrieval evaluation.
        </p>
      </div>

      {/* System Pipeline Architecture */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-4">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-4 h-4 text-blue-600" />
          System Processing Pipeline
        </h3>
        <p className="text-xs text-slate-600">
          TraceBench processes software repositories through five discrete, verifiable architectural stages:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-2">
          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs">
            <span className="text-[10px] uppercase font-bold text-blue-600 block mb-1">Stage 1</span>
            <h4 className="font-bold text-slate-800 mb-1">Safe Ingestion</h4>
            <p className="text-[11px] text-slate-500 leading-normal">
              ZIP Slip defense, resource quotas, secret filtering (.git, node_modules, .env).
            </p>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs">
            <span className="text-[10px] uppercase font-bold text-blue-600 block mb-1">Stage 2</span>
            <h4 className="font-bold text-slate-800 mb-1">AST Parsing</h4>
            <p className="text-[11px] text-slate-500 leading-normal">
              Tree-sitter & Python AST extract functions, classes, methods, imports, and calls.
            </p>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs">
            <span className="text-[10px] uppercase font-bold text-blue-600 block mb-1">Stage 3</span>
            <h4 className="font-bold text-slate-800 mb-1">Unified Graph</h4>
            <p className="text-[11px] text-slate-500 leading-normal">
              NetworkX constructs containment, import dependencies, and inferred call references.
            </p>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs">
            <span className="text-[10px] uppercase font-bold text-blue-600 block mb-1">Stage 4</span>
            <h4 className="font-bold text-slate-800 mb-1">Dual Retrieval</h4>
            <p className="text-[11px] text-slate-500 leading-normal">
              TF-IDF lexical search baseline and Graph-Assisted neighbor re-ranking.
            </p>
          </div>

          <div className="p-3.5 rounded-lg border border-slate-200 bg-slate-50/70 text-xs">
            <span className="text-[10px] uppercase font-bold text-blue-600 block mb-1">Stage 5</span>
            <h4 className="font-bold text-slate-800 mb-1">Evidence Q&A</h4>
            <p className="text-[11px] text-slate-500 leading-normal">
              Google Gemini synthesis or Deterministic Demo Mode with 4-point citation validation.
            </p>
          </div>
        </div>
      </div>

      {/* Language Capability Matrix */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <FileCode className="w-4 h-4 text-emerald-600" />
          Multi-Language Capability Matrix
        </h3>
        <p className="text-xs text-slate-500">
          TraceBench reports exact language capabilities transparently rather than claiming unverified semantic resolution.
        </p>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 text-[11px] uppercase">
                <th className="py-2.5 px-3 font-semibold">Language</th>
                <th className="py-2.5 px-3 font-semibold">Extensions</th>
                <th className="py-2.5 px-3 font-semibold">Support Level</th>
                <th className="py-2.5 px-3 font-semibold">Parser Engine</th>
                <th className="py-2.5 px-3 font-semibold">Capabilities & Notes</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(capabilities).map(([key, cap]) => (
                <tr key={key} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-2.5 px-3 font-semibold text-slate-800 capitalize">{cap.language}</td>
                  <td className="py-2.5 px-3 font-mono text-slate-500 text-[11px]">
                    {cap.extensions.slice(0, 3).join(', ')}
                  </td>
                  <td className="py-2.5 px-3">
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">
                      {cap.support_level}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 font-mono text-slate-600 text-[11px]">{cap.parser}</td>
                  <td className="py-2.5 px-3 text-slate-600 text-[11px] max-w-xs">{cap.notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Security & Execution Boundaries */}
      <div className="bg-white rounded-xl border border-slate-200/80 p-6 shadow-sm space-y-3">
        <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-600" />
          Security & Execution Boundaries
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          TraceBench is strictly designed for local security:
        </p>
        <ul className="text-xs text-slate-600 space-y-2">
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span><strong>Zero Code Execution:</strong> Imported code is parsed only via AST grammars; it is never run or evaluated.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span><strong>ZIP Path Traversal Defense:</strong> Archives are validated to prevent Zip Slip file system escapes.</span>
          </li>
          <li className="flex items-start gap-2">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
            <span><strong>Local Storage:</strong> Code and graphs are stored in local temporary workspaces (<code className="bg-slate-100 px-1 py-0.5 rounded">data/workspaces</code>).</span>
          </li>
        </ul>
      </div>
    </div>
  );
};
