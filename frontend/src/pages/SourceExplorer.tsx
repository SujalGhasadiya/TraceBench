import React, { useState, useEffect, useRef } from 'react';
import {
  FileText,
  Search,
  Code2,
  Layers,
  ChevronRight,
  Info,
  CheckCircle2,
  Folder
} from 'lucide-react';
import { IndexedFile, CodeSymbol } from '../types';
import { fetchRepositoryFiles, fetchFileContent } from '../api/client';

interface SourceExplorerProps {
  repoId: string;
  initialFilePath?: string;
  initialLineRange?: [number, number];
}

export const SourceExplorer: React.FC<SourceExplorerProps> = ({
  repoId,
  initialFilePath,
  initialLineRange,
}) => {
  const [files, setFiles] = useState<IndexedFile[]>([]);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileDetails, setFileDetails] = useState<{
    file_path: string;
    language: string;
    line_count: number;
    is_parsed: boolean;
    content: string;
    symbols: CodeSymbol[];
  } | null>(null);
  const [highlightRange, setHighlightRange] = useState<[number, number] | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const codeContainerRef = useRef<HTMLDivElement>(null);

  // Load files
  useEffect(() => {
    fetchRepositoryFiles(repoId)
      .then((data) => {
        setFiles(data);
        if (initialFilePath && data.some((f) => f.file_path === initialFilePath)) {
          setSelectedFile(initialFilePath);
          if (initialLineRange) setHighlightRange(initialLineRange);
        } else if (data.length > 0 && !selectedFile) {
          setSelectedFile(data[0].file_path);
        }
      })
      .catch((err) => console.error('Failed to load files:', err));
  }, [repoId, initialFilePath]);

  // Load content when selected file changes
  useEffect(() => {
    if (!selectedFile) return;
    setIsLoading(true);
    fetchFileContent(repoId, selectedFile)
      .then((data) => {
        setFileDetails(data);
      })
      .catch((err) => console.error('Failed to load file content:', err))
      .finally(() => setIsLoading(false));
  }, [repoId, selectedFile]);

  // Scroll to highlight range if provided
  useEffect(() => {
    if (highlightRange && codeContainerRef.current) {
      const lineEl = document.getElementById(`line-${highlightRange[0]}`);
      if (lineEl) {
        lineEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [highlightRange, fileDetails]);

  const filteredFiles = files.filter((f) =>
    f.file_path.toLowerCase().includes(searchFilter.toLowerCase())
  );

  const handleSelectSymbol = (sym: CodeSymbol) => {
    setHighlightRange([sym.start_line, sym.end_line]);
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col -m-6">
      {/* Explorer Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Side: Searchable File Tree */}
        <div className="w-72 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
          <div className="p-3 border-b border-slate-200">
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search files..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                className="w-full text-xs pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
            {filteredFiles.map((file) => {
              const isSelected = selectedFile === file.file_path;
              return (
                <button
                  key={file.file_path}
                  onClick={() => {
                    setSelectedFile(file.file_path);
                    setHighlightRange(null);
                  }}
                  className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition ${
                    isSelected
                      ? 'bg-blue-50 text-blue-700 font-semibold border border-blue-200/60'
                      : 'text-slate-700 hover:bg-slate-100'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <FileText className={`w-3.5 h-3.5 flex-shrink-0 ${isSelected ? 'text-blue-600' : 'text-slate-400'}`} />
                    <span className="truncate">{file.file_path}</span>
                  </div>
                  <span className="text-[10px] text-slate-400 uppercase font-mono ml-1">
                    {file.language}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right Side: Code Viewer & Symbol Navigation */}
        <div className="flex-1 flex flex-col bg-slate-50 overflow-hidden">
          {fileDetails ? (
            <>
              {/* File Meta Header */}
              <div className="bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap items-center justify-between gap-3 shadow-xs">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-slate-900 font-mono">
                      {fileDetails.file_path}
                    </h3>
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                      {fileDetails.language}
                    </span>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                        fileDetails.is_parsed
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {fileDetails.is_parsed ? 'Structural AST Parsed' : 'Text-Indexed Only'}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-400 mt-0.5">
                    {fileDetails.line_count} lines • {fileDetails.symbols.length} extracted symbols
                  </div>
                </div>

                {/* Symbol Navigation Pills */}
                {fileDetails.symbols.length > 0 && (
                  <div className="flex items-center gap-1.5 overflow-x-auto max-w-lg py-1">
                    <span className="text-[11px] font-medium text-slate-400 flex items-center gap-1">
                      <Layers className="w-3 h-3" /> Jump:
                    </span>
                    {fileDetails.symbols.map((sym) => (
                      <button
                        key={sym.id}
                        onClick={() => handleSelectSymbol(sym)}
                        className="text-[11px] px-2 py-0.5 bg-slate-100 hover:bg-blue-50 hover:text-blue-700 border border-slate-200 rounded text-slate-700 whitespace-nowrap transition"
                        title={`${sym.symbol_type}: lines ${sym.start_line}-${sym.end_line}`}
                      >
                        {sym.name.split('.').pop()}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Code Viewer */}
              <div
                ref={codeContainerRef}
                className="flex-1 overflow-auto p-4 font-mono text-xs leading-relaxed bg-white text-slate-900"
              >
                {isLoading ? (
                  <div className="p-8 text-center text-slate-400 text-xs">Loading source...</div>
                ) : (
                  <table className="w-full border-collapse">
                    <tbody>
                      {fileDetails.content.split('\n').map((line, idx) => {
                        const lineNum = idx + 1;
                        const isHighlighted =
                          highlightRange &&
                          lineNum >= highlightRange[0] &&
                          lineNum <= highlightRange[1];

                        return (
                          <tr
                            key={lineNum}
                            id={`line-${lineNum}`}
                            className={`group ${
                              isHighlighted
                                ? 'bg-amber-100/70 border-l-4 border-amber-500'
                                : 'hover:bg-slate-50'
                            }`}
                          >
                            <td className="w-12 select-none text-right pr-4 py-0.5 text-slate-400 text-[11px] group-hover:text-slate-600">
                              {lineNum}
                            </td>
                            <td className="py-0.5 pl-2 whitespace-pre overflow-x-auto">
                              {line || ' '}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
              Select a file on the left to view its source code.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
