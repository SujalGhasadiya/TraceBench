import React, { useState, useEffect, useCallback } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Network,
  Search,
  Filter,
  Maximize2,
  FileCode,
  Layers,
  ArrowRight,
  Info,
  Compass
} from 'lucide-react';
import { GraphResponse, GraphNode as ApiGraphNode, GraphEdge as ApiGraphEdge } from '../types';
import { fetchRepositoryGraph } from '../api/client';

interface CodeGraphProps {
  repoId: string;
  onNavigateToSource: (filePath: string, lineRange?: [number, number]) => void;
}

export const CodeGraph: React.FC<CodeGraphProps> = ({
  repoId,
  onNavigateToSource,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedNode, setSelectedNode] = useState<ApiGraphNode | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(false);
  const [graphMeta, setGraphMeta] = useState<{ totalNodes: number; totalEdges: number; truncated: boolean }>({
    totalNodes: 0,
    totalEdges: 0,
    truncated: false
  });

  // Layout helper: arrange nodes in concentric hierarchical rings
  const transformToFlow = (apiNodes: ApiGraphNode[], apiEdges: ApiGraphEdge[]) => {
    const nodeCount = apiNodes.length;
    const flowNodes: Node[] = apiNodes.map((n, idx) => {
      // Simple radial/grid layout
      const angle = (idx / (nodeCount || 1)) * 2 * Math.PI;
      const radius = 220 + (idx % 3) * 120;
      const x = 500 + radius * Math.cos(angle);
      const y = 350 + radius * Math.sin(angle);

      // Node styling based on type
      let bgColor = '#f8fafc';
      let borderColor = '#94a3b8';
      let textColor = '#1e293b';

      if (n.node_type === 'file') {
        bgColor = '#eff6ff';
        borderColor = '#3b82f6';
        textColor = '#1d4ed8';
      } else if (n.node_type === 'class' || n.node_type === 'struct') {
        bgColor = '#faf5ff';
        borderColor = '#a855f7';
        textColor = '#7e22ce';
      } else if (n.node_type === 'function' || n.node_type === 'method') {
        bgColor = '#ecfdf5';
        borderColor = '#10b981';
        textColor = '#047857';
      } else if (n.node_type === 'interface') {
        bgColor = '#fffbeb';
        borderColor = '#f59e0b';
        textColor = '#b45309';
      }

      return {
        id: n.id,
        position: { x, y },
        data: {
          label: (
            <div className="text-left font-mono text-[11px]">
              <div className="text-[9px] uppercase font-bold text-slate-400">{n.node_type}</div>
              <div className="font-semibold truncate max-w-[140px]">{n.label}</div>
            </div>
          ),
          rawNode: n
        },
        style: {
          background: bgColor,
          borderColor: borderColor,
          color: textColor,
          borderWidth: '1.5px',
          borderRadius: '8px',
          padding: '6px 10px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)'
        }
      };
    });

    const flowEdges: Edge[] = apiEdges.map((e) => {
      const isInferred = e.is_inferred;
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        animated: isInferred,
        label: e.relationship_type,
        labelStyle: { fill: '#64748b', fontSize: 9, fontFamily: 'monospace' },
        style: {
          stroke: isInferred ? '#f59e0b' : '#3b82f6',
          strokeWidth: 1.5,
          strokeDasharray: isInferred ? '4 3' : undefined
        },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: isInferred ? '#f59e0b' : '#3b82f6',
          width: 14,
          height: 14
        }
      };
    });

    return { flowNodes, flowEdges };
  };

  const loadGraph = useCallback(
    (centerNodeId?: string) => {
      setIsLoading(true);
      fetchRepositoryGraph(repoId, centerNodeId, 45)
        .then((data) => {
          setGraphMeta({
            totalNodes: data.total_nodes,
            totalEdges: data.total_edges,
            truncated: data.truncated
          });
          const { flowNodes, flowEdges } = transformToFlow(data.nodes, data.edges);
          setNodes(flowNodes);
          setEdges(flowEdges);
        })
        .catch((err) => console.error('Failed to load graph:', err))
        .finally(() => setIsLoading(false));
    },
    [repoId, setNodes, setEdges]
  );

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  const onNodeClick = (_: any, node: Node) => {
    const raw = node.data.rawNode as ApiGraphNode;
    if (raw) setSelectedNode(raw);
  };

  const handleExpandNeighborhood = () => {
    if (selectedNode) {
      loadGraph(selectedNode.id);
    }
  };

  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col -m-6 relative">
      {/* Graph Control Bar */}
      <div className="bg-white border-b border-slate-200 px-6 py-3 flex flex-wrap items-center justify-between gap-3 z-10 shadow-xs">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Network className="w-4 h-4 text-blue-600" />
            <h3 className="text-sm font-bold text-slate-900">Code Architecture Graph</h3>
          </div>
          <span className="text-xs text-slate-400 font-mono">
            Showing {nodes.length} nodes • {edges.length} edges
          </span>
          {graphMeta.truncated && (
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-amber-100 text-amber-800">
              Bounded Subgraph View (Total nodes in repo: {graphMeta.totalNodes})
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => loadGraph()}
            className="px-2.5 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md transition font-medium"
          >
            Reset Overview
          </button>
        </div>
      </div>

      {/* Main Flow Canvas & Details Drawer */}
      <div className="flex-1 relative flex">
        <div className="flex-1 h-full bg-slate-50">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
          >
            <Background color="#cbd5e1" gap={16} />
            <Controls />
            <MiniMap
              nodeColor={(n: any) => {
                if (n.data?.rawNode?.node_type === 'file') return '#3b82f6';
                if (n.data?.rawNode?.node_type === 'class') return '#a855f7';
                return '#10b981';
              }}
              style={{ height: 100, width: 140 }}
            />
          </ReactFlow>
        </div>

        {/* Selected Node Details Drawer */}
        {selectedNode && (
          <div className="w-80 bg-white border-l border-slate-200 p-5 shadow-lg flex flex-col justify-between z-20 overflow-y-auto">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                  {selectedNode.node_type}
                </span>
                <span className="text-xs font-mono text-slate-400">{selectedNode.language}</span>
              </div>

              <h4 className="text-base font-bold text-slate-900 font-mono break-all mb-2">
                {selectedNode.label}
              </h4>

              <div className="space-y-2 text-xs text-slate-600 mb-4">
                <div>
                  <span className="text-slate-400 block text-[11px]">File Path:</span>
                  <span className="font-mono text-slate-800 break-all">{selectedNode.file_path}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[11px]">Line Range:</span>
                  <span className="font-mono text-slate-800">
                    L{selectedNode.line_range[0]} - L{selectedNode.line_range[1]}
                  </span>
                </div>
                {selectedNode.metadata?.signature && (
                  <div>
                    <span className="text-slate-400 block text-[11px]">Signature:</span>
                    <span className="font-mono text-slate-800 text-[11px] bg-slate-100 px-1.5 py-0.5 rounded block">
                      {selectedNode.metadata.signature}
                    </span>
                  </div>
                )}
                {selectedNode.metadata?.docstring && (
                  <div>
                    <span className="text-slate-400 block text-[11px]">Docstring:</span>
                    <p className="text-slate-700 italic bg-slate-50 p-2 rounded border border-slate-200">
                      "{selectedNode.metadata.docstring}"
                    </p>
                  </div>
                )}
              </div>

              <div className="space-y-2 pt-3 border-t border-slate-200">
                <button
                  onClick={handleExpandNeighborhood}
                  className="w-full py-2 px-3 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-md text-xs font-medium transition flex items-center justify-center gap-1.5"
                >
                  <Compass className="w-3.5 h-3.5 text-blue-600" />
                  Expand 2-Hop Neighborhood
                </button>
                <button
                  onClick={() => onNavigateToSource(selectedNode.file_path, selectedNode.line_range)}
                  className="w-full py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded-md text-xs font-medium shadow-sm transition flex items-center justify-center gap-1.5"
                >
                  <FileCode className="w-3.5 h-3.5" />
                  Open in Source Explorer
                </button>
              </div>
            </div>

            <button
              onClick={() => setSelectedNode(null)}
              className="mt-4 text-xs text-slate-400 hover:text-slate-600 text-center"
            >
              Close Details
            </button>
          </div>
        )}


      </div>
    </div>
  );
};
