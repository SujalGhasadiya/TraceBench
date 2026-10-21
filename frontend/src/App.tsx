import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Home } from './pages/Home';
import { RepositoryOverview } from './pages/RepositoryOverview';
import { SourceExplorer } from './pages/SourceExplorer';
import { CodeGraph } from './pages/CodeGraph';
import { AskAI } from './pages/AskAI';
import { Evaluation } from './pages/Evaluation';
import { Settings } from './pages/Settings';
import { RepositoryMetadata, HealthResponse } from './types';
import { fetchHealth, fetchRepositories, fetchRepository } from './api/client';

export const App: React.FC = () => {
  const [currentTab, setCurrentTab] = useState<string>('home');
  const [repositories, setRepositories] = useState<RepositoryMetadata[]>([]);
  const [currentRepo, setCurrentRepo] = useState<RepositoryMetadata | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [sourceTarget, setSourceTarget] = useState<{
    filePath: string;
    lineRange?: [number, number];
  } | null>(null);

  // Initial load
  useEffect(() => {
    fetchHealth()
      .then((h) => setHealth(h))
      .catch((e) => console.error('Health fetch failed:', e));

    fetchRepositories()
      .then((repos) => {
        setRepositories(repos);
        if (repos.length > 0 && !currentRepo) {
          setCurrentRepo(repos[0]);
        }
      })
      .catch((e) => console.error('Repositories fetch failed:', e));
  }, []);

  const handleSelectRepo = (repoId: string) => {
    const target = repositories.find((r) => r.id === repoId);
    if (target) {
      setCurrentRepo(target);
    } else {
      fetchRepository(repoId)
        .then((r) => {
          setCurrentRepo(r);
          setRepositories((prev) => (prev.some((p) => p.id === r.id) ? prev : [...prev, r]));
        })
        .catch((e) => console.error(e));
    }
  };

  const handleRepoImported = (newRepo: RepositoryMetadata) => {
    setRepositories((prev) => [newRepo, ...prev.filter((r) => r.id !== newRepo.id)]);
    setCurrentRepo(newRepo);
    setCurrentTab('overview');
  };

  const handleNavigateToSource = (filePath: string, lineRange?: [number, number]) => {
    setSourceTarget({ filePath, lineRange });
    setCurrentTab('explorer');
  };

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* Dark Navy Sidebar */}
      <Sidebar
        currentTab={currentTab}
        setCurrentTab={setCurrentTab}
        currentRepo={currentRepo}
        repositories={repositories}
        onSelectRepo={handleSelectRepo}
        health={health}
      />

      {/* Main Workspace Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header Bar */}
        <header className="h-14 bg-white border-b border-slate-200 px-8 flex items-center justify-between flex-shrink-0 z-10 shadow-2xs">
          <div className="flex items-center gap-3">
            <span className="text-xs uppercase font-bold tracking-wider text-slate-400">
              {currentTab.replace('_', ' ')}
            </span>
            {currentRepo && (
              <>
                <span className="text-slate-300">•</span>
                <span className="text-xs font-semibold text-slate-800 font-mono">
                  {currentRepo.name}
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold border border-blue-200">
                  {currentRepo.file_count} files
                </span>
              </>
            )}
          </div>

          <div className="flex items-center gap-3 text-xs text-slate-500">
            <span>TraceBench Core</span>
          </div>
        </header>

        {/* Scrollable View Container */}
        <div className="flex-1 overflow-y-auto p-6">
          {currentTab === 'home' && (
            <Home
              repositories={repositories}
              currentRepo={currentRepo}
              onSelectRepo={handleSelectRepo}
              onRepoImported={handleRepoImported}
            />
          )}

          {currentTab === 'overview' && currentRepo && (
            <RepositoryOverview
              repo={currentRepo}
              onNavigateTab={(tab) => setCurrentTab(tab)}
            />
          )}

          {currentTab === 'explorer' && currentRepo && (
            <SourceExplorer
              repoId={currentRepo.id}
              initialFilePath={sourceTarget?.filePath}
              initialLineRange={sourceTarget?.lineRange}
            />
          )}

          {currentTab === 'graph' && currentRepo && (
            <CodeGraph
              repoId={currentRepo.id}
              onNavigateToSource={handleNavigateToSource}
            />
          )}

          {currentTab === 'ask' && currentRepo && (
            <AskAI
              repoId={currentRepo.id}
              onNavigateToSource={handleNavigateToSource}
            />
          )}

          {currentTab === 'evaluation' && currentRepo && (
            <Evaluation repoId={currentRepo.id} />
          )}

          {currentTab === 'settings' && (
            <Settings repoId={currentRepo?.id} />
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
