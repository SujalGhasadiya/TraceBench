import React from 'react';
import {
  Home,
  FolderGit2,
  FileCode,
  Network,
  Sparkles,
  BarChart3,
  Settings,
  Cpu,
  CheckCircle2,
  AlertTriangle
} from 'lucide-react';
import { RepositoryMetadata, HealthResponse } from '../types';

interface SidebarProps {
  currentTab: string;
  setCurrentTab: (tab: string) => void;
  currentRepo: RepositoryMetadata | null;
  repositories: RepositoryMetadata[];
  onSelectRepo: (repoId: string) => void;
  health: HealthResponse | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  currentTab,
  setCurrentTab,
  currentRepo,
  repositories,
  onSelectRepo,
  health
}) => {
  const navItems = [
    { id: 'home', label: 'Home & Import', icon: Home },
    { id: 'overview', label: 'Repository', icon: FolderGit2, disabled: !currentRepo },
    { id: 'explorer', label: 'Source Explorer', icon: FileCode, disabled: !currentRepo },
    { id: 'graph', label: 'Code Graph', icon: Network, disabled: !currentRepo },
    { id: 'ask', label: 'Ask AI', icon: Sparkles, disabled: !currentRepo },
    { id: 'evaluation', label: 'Evaluation', icon: BarChart3, disabled: !currentRepo },
    { id: 'settings', label: 'Settings & About', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-navy-950 text-slate-300 flex flex-col h-screen border-r border-navy-850 select-none flex-shrink-0">
      {/* Brand Header */}
      <div className="p-5 border-b border-navy-850/80">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white shadow-md shadow-blue-500/20">
            <Cpu className="w-4 h-4" />
          </div>
          <div>
            <h1 className="font-bold text-base text-white tracking-tight flex items-center gap-1.5">
              TraceBench
              <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 border border-blue-500/30">
                v1.0
              </span>
            </h1>
            <p className="text-[11px] text-slate-400 font-medium">Understand any codebase with evidence</p>
          </div>
        </div>

        {/* Active Repository Selector */}
        <div className="mt-4">
          <label className="text-[10px] font-semibold uppercase tracking-wider text-slate-400 block mb-1.5">
            Active Repository
          </label>
          <select
            value={currentRepo?.id || ''}
            onChange={(e) => onSelectRepo(e.target.value)}
            className="w-full bg-navy-900 border border-navy-700/60 rounded-md text-xs py-1.5 px-2 text-white focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors"
          >
            {repositories.length === 0 && (
              <option value="">No repository loaded</option>
            )}
            {repositories.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name} ({r.file_count} files)
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          const isDisabled = item.disabled;

          return (
            <button
              key={item.id}
              disabled={isDisabled}
              onClick={() => setCurrentTab(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2 rounded-md text-xs font-medium transition-all ${
                isActive
                  ? 'bg-blue-600 text-white font-semibold shadow-sm shadow-blue-600/30'
                  : isDisabled
                  ? 'text-slate-600 cursor-not-allowed opacity-60'
                  : 'text-slate-300 hover:bg-navy-850 hover:text-white'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* Footer System Status */}
      <div className="p-3.5 border-t border-navy-850 bg-navy-900/60 text-[11px]">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-slate-400">Engine Health:</span>
          <span className="inline-flex items-center gap-1 text-emerald-400 font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Healthy
          </span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-slate-400">AI Mode:</span>
          {health?.gemini_configured ? (
            <span className="inline-flex items-center gap-1 text-blue-400 font-medium">
              <CheckCircle2 className="w-3 h-3" />
              Live Gemini
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-amber-400 font-medium" title="API key not provided; operating in deterministic evidence summary mode">
              <AlertTriangle className="w-3 h-3" />
              Demo Mode
            </span>
          )}
        </div>
      </div>
    </aside>
  );
};
