'use client';

import React, {useState, useRef, useCallback, useEffect, useMemo} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {motion, AnimatePresence} from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  Bot,
  CheckCircle,
  ChevronRight,
  Clock,
  Copy,
  Database,
  Eye,
  FileText,
  GitBranch,
  Loader2,
  Mail,
  MoreHorizontal,
  Play,
  Plus,
  RefreshCw,
  Save,
  Search,
  Settings,
  Square,
  StopCircle,
  Trash2,
  X,
  Zap,
  Workflow
} from 'lucide-react';

// ═══ Types ═══
interface WorkflowDef {
  id: number;
  name: string;
  description?: string;
  graph: any;
  trigger_config?: any;
  is_active: boolean;
  version: number;
  created_at: string;
}

interface WorkflowExec {
  id: number;
  workflow_id: number;
  status: string;
  trigger_type: string;
  input_data?: any;
  output_data?: any;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  created_at: string;
  node_executions?: NodeExec[];
}

interface NodeExec {
  id: number;
  node_id: string;
  node_type: string;
  status: string;
  input_data?: any;
  output_data?: any;
  error_message?: string;
  duration_ms?: number;
}

interface WFNode {
  id: string;
  type: string;
  label: string;
  config: Record<string, any>;
  x: number;
  y: number;
}

interface WFEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

// ═══ Node type definitions ═══
const NODE_TYPES: Record<string, { label: string; color: string; icon: React.FC<any>; bg: string }> = {
  llm: {label: 'LLM 调用', color: '#6366f1', icon: Bot, bg: 'bg-indigo-50 dark:bg-indigo-900/20'},
  collector: {label: '数据采集', color: '#10b981', icon: Database, bg: 'bg-emerald-50 dark:bg-emerald-900/20'},
  rag: {label: 'RAG 检索', color: '#8b5cf6', icon: Search, bg: 'bg-purple-50 dark:bg-purple-900/20'},
  condition: {label: '条件判断', color: '#f59e0b', icon: GitBranch, bg: 'bg-amber-50 dark:bg-amber-900/20'},
  notify: {label: '通知推送', color: '#ef4444', icon: Mail, bg: 'bg-red-50 dark:bg-red-900/20'},
};

const STATUS_CONFIG: Record<string, { color: string; icon: React.FC<any>; label: string }> = {
  running: {color: 'text-blue-500', icon: Loader2, label: '运行中'},
  completed: {color: 'text-emerald-500', icon: CheckCircle, label: '已完成'},
  failed: {color: 'text-red-500', icon: AlertTriangle, label: '失败'},
  pending: {color: 'text-gray-500', icon: Clock, label: '等待中'},
  cancelled: {color: 'text-gray-400', icon: StopCircle, label: '已取消'},
};

const NODE_W = 180;
const NODE_H = 60;

// ═══ SVG DAG Canvas ═══
const DagCanvas: React.FC<{
  nodes: WFNode[];
  edges: WFEdge[];
  selectedNode: string | null;
  onSelectNode: (id: string | null) => void;
  onMoveNode: (id: string, x: number, y: number) => void;
  onConnect: (source: string, target: string) => void;
  onDeleteNode: (id: string) => void;
  onDeleteEdge: (id: string) => void;
  readOnly?: boolean;
  executionStatus?: Record<string, string>;
}> = ({nodes, edges, selectedNode, onSelectNode, onMoveNode, onConnect, onDeleteNode, onDeleteEdge, readOnly, executionStatus}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [dragging, setDragging] = useState<{ nodeId: string; offsetX: number; offsetY: number } | null>(null);
  const [connecting, setConnecting] = useState<{ source: string; mouseX: number; mouseY: number } | null>(null);
  const [viewBox, setViewBox] = useState({x: -50, y: -50, w: 1000, h: 600});
  const [panning, setPanning] = useState<{ startX: number; startY: number; vx: number; vy: number } | null>(null);

  const getSVGPoint = useCallback((e: React.MouseEvent) => {
    if (!svgRef.current) return {x: 0, y: 0};
    const rect = svgRef.current.getBoundingClientRect();
    const scaleX = viewBox.w / rect.width;
    const scaleY = viewBox.h / rect.height;
    return {
      x: (e.clientX - rect.left) * scaleX + viewBox.x,
      y: (e.clientY - rect.top) * scaleY + viewBox.y,
    };
  }, [viewBox]);

  const handleMouseDown = useCallback((e: React.MouseEvent, nodeId: string) => {
    if (readOnly) return;
    e.stopPropagation();
    const pt = getSVGPoint(e);
    const node = nodes.find(n => n.id === nodeId);
    if (!node) return;
    onSelectNode(nodeId);
    setDragging({nodeId, offsetX: pt.x - node.x, offsetY: pt.y - node.y});
  }, [getSVGPoint, nodes, onSelectNode, readOnly]);

  const handleSVGMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 1 || (e.button === 0 && e.altKey)) {
      setPanning({startX: e.clientX, startY: e.clientY, vx: viewBox.x, vy: viewBox.y});
    } else {
      onSelectNode(null);
    }
  }, [viewBox, onSelectNode]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const pt = getSVGPoint(e);
    if (dragging) {
      onMoveNode(dragging.nodeId, pt.x - dragging.offsetX, pt.y - dragging.offsetY);
    } else if (connecting) {
      setConnecting(prev => prev ? {...prev, mouseX: pt.x, mouseY: pt.y} : null);
    } else if (panning) {
      const svgEl = svgRef.current;
      if (!svgEl) return;
      const rect = svgEl.getBoundingClientRect();
      const scaleX = viewBox.w / rect.width;
      const scaleY = viewBox.h / rect.height;
      setViewBox(prev => ({
        ...prev,
        x: panning.vx - (e.clientX - panning.startX) * scaleX,
        y: panning.vy - (e.clientY - panning.startY) * scaleY,
      }));
    }
  }, [dragging, connecting, panning, getSVGPoint, onMoveNode, viewBox]);

  const handleMouseUp = useCallback(() => {
    setDragging(null);
    setConnecting(null);
    setPanning(null);
  }, []);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY > 0 ? 1.1 : 0.9;
    setViewBox(prev => {
      const cx = prev.x + prev.w / 2;
      const cy = prev.y + prev.h / 2;
      const nw = prev.w * factor;
      const nh = prev.h * factor;
      return {x: cx - nw / 2, y: cy - nh / 2, w: nw, h: nh};
    });
  }, []);

  const startConnect = useCallback((e: React.MouseEvent, sourceId: string) => {
    if (readOnly) return;
    e.stopPropagation();
    const pt = getSVGPoint(e);
    setConnecting({source: sourceId, mouseX: pt.x, mouseY: pt.y});
  }, [readOnly, getSVGPoint]);

  const endConnect = useCallback((e: React.MouseEvent, targetId: string) => {
    if (connecting && connecting.source !== targetId) {
      onConnect(connecting.source, targetId);
    }
    setConnecting(null);
  }, [connecting, onConnect]);

  // Auto-layout: simple left-to-right layout
  const renderEdge = useCallback((edge: WFEdge) => {
    const src = nodes.find(n => n.id === edge.source);
    const tgt = nodes.find(n => n.id === edge.target);
    if (!src || !tgt) return null;
    const sx = src.x + NODE_W;
    const sy = src.y + NODE_H / 2;
    const tx = tgt.x;
    const ty = tgt.y + NODE_H / 2;
    const mx = (sx + tx) / 2;
    const d = `M ${sx} ${sy} C ${mx} ${sy}, ${mx} ${ty}, ${tx} ${ty}`;
    return (
      <g key={edge.id}>
        <path d={d} fill="none" stroke="#94a3b8" strokeWidth="2" strokeDasharray={edge.label === 'false' ? '6 3' : undefined}/>
        <path d={d} fill="none" stroke="transparent" strokeWidth="12" className="cursor-pointer"
          onClick={(e) => { e.stopPropagation(); onDeleteEdge(edge.id); }}/>
        {edge.label && (
          <text x={mx} y={(sy + ty) / 2 - 8} textAnchor="middle" className="text-[10px] fill-gray-500">
            {edge.label}
          </text>
        )}
      </g>
    );
  }, [nodes, onDeleteEdge]);

  const renderNode = useCallback((node: WFNode) => {
    const nt = NODE_TYPES[node.type] || {label: node.type, color: '#6b7280', icon: Zap, bg: 'bg-gray-50'};
    const Icon = nt.icon;
    const isSelected = selectedNode === node.id;
    const execStatus = executionStatus?.[node.id];
    const statusConf = execStatus ? STATUS_CONFIG[execStatus] : null;
    const StatusIcon = statusConf?.icon;

    return (
      <g key={node.id}
        onMouseDown={e => handleMouseDown(e, node.id)}
        onMouseUp={e => endConnect(e, node.id)}
        className="cursor-pointer"
      >
        {/* Shadow */}
        <rect x={node.x + 2} y={node.y + 2} width={NODE_W} height={NODE_H} rx={12} fill="rgba(0,0,0,0.06)"/>
        {/* Node body */}
        <rect x={node.x} y={node.y} width={NODE_W} height={NODE_H} rx={12}
          fill="white" stroke={isSelected ? '#3b82f6' : nt.color} strokeWidth={isSelected ? 2.5 : 1.5}/>
        {/* Type indicator bar */}
        <rect x={node.x} y={node.y} width={6} height={NODE_H} rx={3} fill={nt.color}/>
        {/* Icon */}
        <foreignObject x={node.x + 14} y={node.y + 14} width={28} height={28}>
          <div className="w-7 h-7 rounded-lg flex items-center justify-center" style={{backgroundColor: nt.color + '20'}}>
            <Icon className="w-4 h-4" style={{color: nt.color}}/>
          </div>
        </foreignObject>
        {/* Label */}
        <text x={node.x + 48} y={node.y + 26} className="text-[13px] font-medium fill-gray-900" style={{fontFamily: 'inherit'}}>
          {node.label || nt.label}
        </text>
        <text x={node.x + 48} y={node.y + 44} className="text-[10px] fill-gray-500" style={{fontFamily: 'inherit'}}>
          {nt.label}
        </text>
        {/* Status indicator */}
        {statusConf && (
          <foreignObject x={node.x + NODE_W - 28} y={node.y + 8} width={20} height={20}>
            <StatusIcon className={`w-4 h-4 ${statusConf.color} ${execStatus === 'running' ? 'animate-spin' : ''}`}/>
          </foreignObject>
        )}
        {/* Connection ports */}
        {!readOnly && (
          <>
            {/* Input port */}
            <circle cx={node.x} cy={node.y + NODE_H / 2} r={6} fill="white" stroke="#94a3b8" strokeWidth={1.5}
              className="cursor-crosshair hover:stroke-blue-500"/>
            {/* Output port */}
            <circle cx={node.x + NODE_W} cy={node.y + NODE_H / 2} r={6} fill="white" stroke="#94a3b8" strokeWidth={1.5}
              className="cursor-crosshair hover:stroke-blue-500"
              onMouseDown={e => startConnect(e, node.id)}/>
          </>
        )}
      </g>
    );
  }, [selectedNode, executionStatus, readOnly, handleMouseDown, endConnect, startConnect]);

  return (
    <svg ref={svgRef} className="w-full h-full bg-gray-50 dark:bg-gray-950 rounded-xl"
      viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.w} ${viewBox.h}`}
      onMouseDown={handleSVGMouseDown} onMouseMove={handleMouseMove} onMouseUp={handleMouseUp}
      onWheel={handleWheel}
      style={{cursor: panning ? 'grabbing' : dragging ? 'move' : 'default'}}
    >
      {/* Grid pattern */}
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="0.5" opacity="0.5"/>
        </pattern>
      </defs>
      <rect x={viewBox.x - 1000} y={viewBox.y - 1000} width={viewBox.w + 2000} height={viewBox.h + 2000} fill="url(#grid)"/>

      {/* Edges */}
      {edges.map(e => renderEdge(e))}

      {/* Connecting line preview */}
      {connecting && (() => {
        const src = nodes.find(n => n.id === connecting.source);
        if (!src) return null;
        const sx = src.x + NODE_W;
        const sy = src.y + NODE_H / 2;
        const mx = (sx + connecting.mouseX) / 2;
        return <path d={`M ${sx} ${sy} C ${mx} ${sy}, ${mx} ${connecting.mouseY}, ${connecting.mouseX} ${connecting.mouseY}`}
          fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="6 3"/>;
      })()}

      {/* Nodes */}
      {nodes.map(n => renderNode(n))}
    </svg>
  );
};

// ═══ Node Config Panel ═══
const NodeConfigPanel: React.FC<{
  node: WFNode | null;
  onUpdate: (id: string, updates: Partial<WFNode>) => void;
  onDelete: (id: string) => void;
  onClose: () => void;
}> = ({node, onUpdate, onDelete, onClose}) => {
  if (!node) return null;
  const nt = NODE_TYPES[node.type];

  const configFields: Record<string, { key: string; label: string; type: string; placeholder?: string }[]> = {
    llm: [
      {key: 'model', label: '模型', type: 'text', placeholder: 'gpt-4o-mini'},
      {key: 'prompt', label: '提示词', type: 'textarea', placeholder: '你是一个专业的...'},
      {key: 'temperature', label: '温度', type: 'number', placeholder: '0.7'},
      {key: 'max_tokens', label: '最大 Token', type: 'number', placeholder: '2000'},
    ],
    collector: [
      {key: 'source_type', label: '采集类型', type: 'select', placeholder: 'rss'},
      {key: 'url', label: 'URL', type: 'text', placeholder: 'https://...'},
      {key: 'max_items', label: '最大条数', type: 'number', placeholder: '100'},
    ],
    rag: [
      {key: 'knowledge_base_id', label: '知识库 ID', type: 'number', placeholder: '1'},
      {key: 'top_k', label: 'Top K', type: 'number', placeholder: '5'},
      {key: 'query_template', label: '查询模板', type: 'textarea', placeholder: '{input} 的相关信息'},
    ],
    condition: [
      {key: 'field', label: '字段路径', type: 'text', placeholder: 'result.score'},
      {key: 'operator', label: '运算符', type: 'select', placeholder: '>'},
      {key: 'value', label: '比较值', type: 'text', placeholder: '0.8'},
    ],
    notify: [
      {key: 'channel', label: '通道', type: 'select', placeholder: 'email'},
      {key: 'recipients', label: '接收人', type: 'text', placeholder: 'admin@example.com'},
      {key: 'template', label: '消息模板', type: 'textarea', placeholder: '工作流已完成: {result}'},
    ],
  };

  const fields = configFields[node.type] || [];

  return (
    <motion.div initial={{x: 20, opacity: 0}} animate={{x: 0, opacity: 1}} exit={{x: 20, opacity: 0}}
      className="w-80 border-l border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-y-auto">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md flex items-center justify-center" style={{backgroundColor: (nt?.color || '#6b7280') + '20'}}>
            {nt && <nt.icon className="w-3.5 h-3.5" style={{color: nt.color}}/>}
          </div>
          <span className="font-medium text-sm text-gray-900 dark:text-white">节点配置</span>
        </div>
        <button onClick={onClose}><X className="w-4 h-4 text-gray-500"/></button>
      </div>
      <div className="p-4 space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">节点名称</label>
          <input value={node.label} onChange={e => onUpdate(node.id, {label: e.target.value})}
            className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
        </div>
        {fields.map(f => (
          <div key={f.key}>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">{f.label}</label>
            {f.type === 'textarea' ? (
              <textarea value={node.config[f.key] || ''} rows={3}
                onChange={e => onUpdate(node.id, {config: {...node.config, [f.key]: e.target.value}})}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-mono"/>
            ) : f.type === 'select' ? (
              <select value={node.config[f.key] || ''}
                onChange={e => onUpdate(node.id, {config: {...node.config, [f.key]: e.target.value}})}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
                {f.key === 'source_type' && (<><option value="rss">RSS</option><option value="web">网页</option><option value="api">API</option></>)}
                {f.key === 'operator' && (<><option value=">">></option><option value="<"><</option><option value=">=">>=</option><option value="<="><=</option><option value="==">==</option><option value="!=">!=</option><option value="contains">包含</option></>)}
                {f.key === 'channel' && (<><option value="email">邮件</option><option value="webhook">Webhook</option><option value="log">日志</option></>)}
              </select>
            ) : f.type === 'number' ? (
              <input type="number" value={node.config[f.key] || ''} placeholder={f.placeholder}
                onChange={e => onUpdate(node.id, {config: {...node.config, [f.key]: parseFloat(e.target.value) || 0}})}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
            ) : (
              <input value={node.config[f.key] || ''} placeholder={f.placeholder}
                onChange={e => onUpdate(node.id, {config: {...node.config, [f.key]: e.target.value}})}
                className="w-full px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
            )}
          </div>
        ))}
        <button onClick={() => onDelete(node.id)}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-red-300 dark:border-red-700 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 text-sm transition-colors">
          <Trash2 className="w-4 h-4"/> 删除节点
        </button>
      </div>
    </motion.div>
  );
};

// ═══ Workflow Editor Inner ═══
type TabKey = 'list' | 'editor' | 'executions';

function WorkflowEditorInner() {
  const qc = useQueryClient();
  const [activeTab, setActiveTab] = useState<TabKey>('list');
  const [currentDefId, setCurrentDefId] = useState<number | null>(null);
  const [nodes, setNodes] = useState<WFNode[]>([]);
  const [edges, setEdges] = useState<WFEdge[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [wfName, setWfName] = useState('');
  const [wfDesc, setWfDesc] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [newDefName, setNewDefName] = useState('');
  const [newDefDesc, setNewDefDesc] = useState('');
  const [execDetail, setExecDetail] = useState<WorkflowExec | null>(null);

  const {data: definitions, isLoading: defsLoading} = useQuery({
    queryKey: ['wf-definitions'],
    queryFn: async () => {
      const res = await apiClient.get('/workflow/definitions');
      return res.data?.items || res.data || [];
    }
  });

  const {data: executions, isLoading: execsLoading} = useQuery({
    queryKey: ['wf-executions'],
    queryFn: async () => {
      const res = await apiClient.get('/workflow/executions');
      return res.data?.items || res.data || [];
    },
    enabled: activeTab === 'executions',
    refetchInterval: activeTab === 'executions' ? 5000 : false,
  });

  const createMutation = useMutation({
    mutationFn: async () => {
      return apiClient.post('/workflow/definitions', {
        name: newDefName, description: newDefDesc,
        graph: JSON.stringify({nodes: [], edges: []}),
      });
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['wf-definitions']});
      setShowCreate(false);
      setNewDefName('');
      setNewDefDesc('');
    }
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!currentDefId) return;
      return apiClient.put(`/workflow/definitions/${currentDefId}`, {
        name: wfName, description: wfDesc,
        graph: JSON.stringify({nodes, edges}),
      });
    },
    onSuccess: () => qc.invalidateQueries({queryKey: ['wf-definitions']})
  });

  const executeMutation = useMutation({
    mutationFn: async (id: number) => {
      return apiClient.post(`/workflow/definitions/${id}/execute`, {input_data: '{}'});
    },
    onSuccess: () => {
      setActiveTab('executions');
      qc.invalidateQueries({queryKey: ['wf-executions']});
    }
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: number) => apiClient.delete(`/workflow/definitions/${id}`),
    onSuccess: () => qc.invalidateQueries({queryKey: ['wf-definitions']})
  });

  const toggleActiveMutation = useMutation({
    mutationFn: async ({id, active}: {id: number; active: boolean}) => {
      return apiClient.post(`/workflow/definitions/${id}/${active ? 'activate' : 'deactivate'}`);
    },
    onSuccess: () => qc.invalidateQueries({queryKey: ['wf-definitions']})
  });

  const loadDefinition = useCallback((def: WorkflowDef) => {
    setCurrentDefId(def.id);
    setWfName(def.name);
    setWfDesc(def.description || '');
    try {
      const graph = typeof def.graph === 'string' ? JSON.parse(def.graph) : def.graph;
      setNodes(graph?.nodes || []);
      setEdges(graph?.edges || []);
    } catch {
      setNodes([]);
      setEdges([]);
    }
    setActiveTab('editor');
  }, []);

  const addNode = useCallback((type: string) => {
    const id = `node_${Date.now()}`;
    const nt = NODE_TYPES[type];
    const newNode: WFNode = {
      id, type,
      label: nt?.label || type,
      config: {},
      x: 100 + Math.random() * 400,
      y: 100 + Math.random() * 300,
    };
    setNodes(prev => [...prev, newNode]);
    setSelectedNode(id);
  }, []);

  const updateNode = useCallback((id: string, updates: Partial<WFNode>) => {
    setNodes(prev => prev.map(n => n.id === id ? {...n, ...updates} : n));
  }, []);

  const deleteNode = useCallback((id: string) => {
    setNodes(prev => prev.filter(n => n.id !== id));
    setEdges(prev => prev.filter(e => e.source !== id && e.target !== id));
    if (selectedNode === id) setSelectedNode(null);
  }, [selectedNode]);

  const addEdge = useCallback((source: string, target: string) => {
    const exists = edges.some(e => e.source === source && e.target === target);
    if (exists) return;
    setEdges(prev => [...prev, {id: `edge_${source}_${target}`, source, target}]);
  }, [edges]);

  const deleteEdge = useCallback((id: string) => {
    setEdges(prev => prev.filter(e => e.id !== id));
  }, []);

  const selectedNodeData = useMemo(() => nodes.find(n => n.id === selectedNode) || null, [nodes, selectedNode]);

  // Execution status map for DAG canvas
  const execStatusMap = useMemo(() => {
    if (!execDetail?.node_executions) return {};
    const map: Record<string, string> = {};
    execDetail.node_executions.forEach(ne => { map[ne.node_id] = ne.status; });
    return map;
  }, [execDetail]);

  const fetchExecDetail = async (execId: number) => {
    try {
      const res = await apiClient.get(`/workflow/executions/${execId}`);
      setExecDetail(res.data);
    } catch {}
  };

  return (
    <div className="flex flex-col h-[calc(100vh-160px)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
            <Workflow className="w-7 h-7 text-indigo-500"/>
            工作流编辑器
          </h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">可视化 DAG 工作流编排与执行监控</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl w-fit mb-4">
        {([
          {key: 'list' as TabKey, label: '工作流列表', icon: FileText},
          {key: 'editor' as TabKey, label: '编辑器', icon: GitBranch},
          {key: 'executions' as TabKey, label: '执行记录', icon: Activity},
        ]).map(({key, label, icon: Icon}) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === key
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}>
            <Icon className="w-4 h-4"/> {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 min-h-0">
        {/* === List Tab === */}
        {activeTab === 'list' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">工作流定义</h3>
              <button onClick={() => setShowCreate(!showCreate)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium">
                <Plus className="w-4 h-4"/> 新建工作流
              </button>
            </div>

            <AnimatePresence>
              {showCreate && (
                <motion.div initial={{opacity: 0, height: 0}} animate={{opacity: 1, height: 'auto'}} exit={{opacity: 0, height: 0}}
                  className="overflow-hidden">
                  <div className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <input value={newDefName} onChange={e => setNewDefName(e.target.value)}
                        className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
                        placeholder="工作流名称"/>
                      <input value={newDefDesc} onChange={e => setNewDefDesc(e.target.value)}
                        className="px-3 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
                        placeholder="描述（可选）"/>
                    </div>
                    <div className="flex gap-2 justify-end">
                      <button onClick={() => setShowCreate(false)} className="px-3 py-1.5 text-sm text-gray-500">取消</button>
                      <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !newDefName.trim()}
                        className="px-4 py-1.5 bg-blue-600 text-white rounded-lg text-sm disabled:opacity-50">
                        {createMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin inline mr-1"/> : null}创建
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {defsLoading ? (
              <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
            ) : definitions?.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Workflow className="w-12 h-12 mx-auto mb-3 opacity-50"/>
                <p>暂无工作流</p>
              </div>
            ) : (
              <div className="grid gap-3">
                {definitions?.map((def: WorkflowDef) => (
                  <motion.div key={def.id} initial={{opacity: 0}} animate={{opacity: 1}}
                    className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-blue-300 dark:hover:border-blue-700 transition-colors group">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-indigo-50 dark:bg-indigo-900/20 flex items-center justify-center">
                        <Workflow className="w-5 h-5 text-indigo-500"/>
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">{def.name}</h4>
                        <p className="text-xs text-gray-500 flex items-center gap-2">
                          v{def.version}
                          {def.description && <span>- {def.description}</span>}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${def.is_active ? 'bg-emerald-500' : 'bg-gray-400'}`}/>
                      <button onClick={() => toggleActiveMutation.mutate({id: def.id, active: !def.is_active})}
                        className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
                          def.is_active ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
                        }`}>
                        {def.is_active ? '已激活' : '未激活'}
                      </button>
                      <button onClick={() => loadDefinition(def)}
                        className="px-3 py-1.5 rounded-lg bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs font-medium hover:bg-blue-100 dark:hover:bg-blue-900/40 transition-colors">
                        编辑
                      </button>
                      <button onClick={() => executeMutation.mutate(def.id)} disabled={executeMutation.isPending}
                        className="px-3 py-1.5 rounded-lg bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 text-xs font-medium hover:bg-emerald-100 dark:hover:bg-emerald-900/40 transition-colors disabled:opacity-50">
                        <Play className="w-3 h-3 inline mr-1"/> 执行
                      </button>
                      <button onClick={() => { if (confirm('确定删除？')) deleteMutation.mutate(def.id); }}
                        className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 transition-colors">
                        <Trash2 className="w-4 h-4"/>
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* === Editor Tab === */}
        {activeTab === 'editor' && (
          <div className="flex h-full gap-0 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden bg-white dark:bg-gray-900">
            {/* Toolbar */}
            <div className="w-56 border-r border-gray-200 dark:border-gray-700 p-4 space-y-4 overflow-y-auto bg-gray-50 dark:bg-gray-950">
              {/* Workflow info */}
              {currentDefId ? (
                <div className="space-y-2">
                  <input value={wfName} onChange={e => setWfName(e.target.value)}
                    className="w-full px-2 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm font-medium"
                    placeholder="工作流名称"/>
                  <input value={wfDesc} onChange={e => setWfDesc(e.target.value)}
                    className="w-full px-2 py-1 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-xs"
                    placeholder="描述"/>
                  <button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}
                    className="w-full flex items-center justify-center gap-1.5 px-3 py-2 bg-blue-600 text-white rounded-lg text-xs font-medium hover:bg-blue-700 disabled:opacity-50">
                    {saveMutation.isPending ? <Loader2 className="w-3.5 h-3.5 animate-spin"/> : <Save className="w-3.5 h-3.5"/>}
                    保存
                  </button>
                </div>
              ) : (
                <p className="text-xs text-gray-500 text-center py-4">请从列表中选择或新建工作流</p>
              )}

              {/* Node palette */}
              <div>
                <h4 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2">节点面板</h4>
                <div className="space-y-1.5">
                  {Object.entries(NODE_TYPES).map(([type, info]) => {
                    const Icon = info.icon;
                    return (
                      <button key={type} onClick={() => addNode(type)} disabled={!currentDefId}
                        className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-blue-300 dark:hover:border-blue-700 transition-colors disabled:opacity-50 text-left">
                        <div className="w-7 h-7 rounded-md flex items-center justify-center" style={{backgroundColor: info.color + '20'}}>
                          <Icon className="w-3.5 h-3.5" style={{color: info.color}}/>
                        </div>
                        <span className="text-xs font-medium text-gray-700 dark:text-gray-300">{info.label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Help */}
              <div className="p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
                <p className="text-[11px] text-blue-700 dark:text-blue-300 leading-relaxed">
                  <strong>操作提示：</strong><br/>
                  - 从左侧面板添加节点<br/>
                  - 拖拽节点移动位置<br/>
                  - 从输出端口拖拽到输入端口创建连线<br/>
                  - 点击节点查看/编辑配置<br/>
                  - Alt+拖拽 或 中键 画布平移<br/>
                  - 滚轮缩放
                </p>
              </div>
            </div>

            {/* Canvas */}
            <div className="flex-1 relative">
              <DagCanvas
                nodes={nodes} edges={edges}
                selectedNode={selectedNode}
                onSelectNode={setSelectedNode}
                onMoveNode={updateNode}
                onConnect={addEdge}
                onDeleteNode={deleteNode}
                onDeleteEdge={deleteEdge}
                executionStatus={execStatusMap}
              />
              {/* Node count badge */}
              <div className="absolute bottom-3 left-3 px-2.5 py-1 rounded-lg bg-white/90 dark:bg-gray-900/90 border border-gray-200 dark:border-gray-700 text-xs text-gray-600 dark:text-gray-400">
                {nodes.length} 节点 / {edges.length} 连线
              </div>
            </div>

            {/* Config Panel */}
            <AnimatePresence>
              {selectedNodeData && (
                <NodeConfigPanel node={selectedNodeData} onUpdate={updateNode} onDelete={deleteNode}
                  onClose={() => setSelectedNode(null)}/>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* === Executions Tab === */}
        {activeTab === 'executions' && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">执行记录</h3>
              <button onClick={() => qc.invalidateQueries({queryKey: ['wf-executions']})}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-gray-300 dark:border-gray-600 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white">
                <RefreshCw className="w-3.5 h-3.5"/> 刷新
              </button>
            </div>

            {execsLoading ? (
              <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
            ) : executions?.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <Activity className="w-12 h-12 mx-auto mb-3 opacity-50"/>
                <p>暂无执行记录</p>
              </div>
            ) : (
              <div className="space-y-2">
                {executions?.map((exec: WorkflowExec) => {
                  const sc = STATUS_CONFIG[exec.status] || STATUS_CONFIG.pending;
                  const StatusIcon = sc.icon;
                  return (
                    <motion.div key={exec.id} initial={{opacity: 0}} animate={{opacity: 1}}
                      className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-blue-300 dark:hover:border-blue-700 cursor-pointer transition-colors"
                      onClick={() => fetchExecDetail(exec.id)}>
                      <div className="flex items-center gap-3">
                        <StatusIcon className={`w-5 h-5 ${sc.color} ${exec.status === 'running' ? 'animate-spin' : ''}`}/>
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">执行 #{exec.id}</p>
                          <p className="text-xs text-gray-500">
                            工作流 #{exec.workflow_id} - {exec.trigger_type}
                            {exec.duration_ms && ` - ${(exec.duration_ms / 1000).toFixed(1)}s`}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                          exec.status === 'completed' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                          exec.status === 'running' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                          exec.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                          'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                        }`}>
                          {sc.label}
                        </span>
                        <span className="text-xs text-gray-500">{new Date(exec.created_at).toLocaleString('zh-CN')}</span>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            )}

            {/* Execution Detail Modal */}
            <AnimatePresence>
              {execDetail && (
                <motion.div initial={{opacity: 0}} animate={{opacity: 1}} exit={{opacity: 0}}
                  className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setExecDetail(null)}>
                  <motion.div initial={{scale: 0.9, y: 20}} animate={{scale: 1, y: 0}} exit={{scale: 0.9, y: 20}}
                    onClick={e => e.stopPropagation()}
                    className="max-w-2xl w-full mx-4 max-h-[80vh] overflow-y-auto rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700">
                    <div className="p-5 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                      <h3 className="font-semibold text-gray-900 dark:text-white">执行详情 #{execDetail.id}</h3>
                      <button onClick={() => setExecDetail(null)}><X className="w-5 h-5 text-gray-500"/></button>
                    </div>
                    <div className="p-5 space-y-4">
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div>
                          <span className="text-gray-500">状态</span>
                          <p className="font-medium mt-0.5">{STATUS_CONFIG[execDetail.status]?.label || execDetail.status}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">触发方式</span>
                          <p className="font-medium mt-0.5">{execDetail.trigger_type}</p>
                        </div>
                        <div>
                          <span className="text-gray-500">耗时</span>
                          <p className="font-medium mt-0.5">{execDetail.duration_ms ? `${(execDetail.duration_ms / 1000).toFixed(1)}s` : '-'}</p>
                        </div>
                      </div>
                      {execDetail.error_message && (
                        <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
                          <p className="text-sm text-red-700 dark:text-red-300">{execDetail.error_message}</p>
                        </div>
                      )}
                      {execDetail.node_executions && execDetail.node_executions.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">节点执行</h4>
                          <div className="space-y-2">
                            {execDetail.node_executions.map(ne => {
                              const nsc = STATUS_CONFIG[ne.status] || STATUS_CONFIG.pending;
                              const NIcon = nsc.icon;
                              return (
                                <div key={ne.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-gray-800">
                                  <div className="flex items-center gap-2">
                                    <NIcon className={`w-4 h-4 ${nsc.color}`}/>
                                    <span className="text-sm font-medium text-gray-900 dark:text-white">{ne.node_id}</span>
                                    <span className="text-xs text-gray-500">{ne.node_type}</span>
                                  </div>
                                  <div className="text-xs text-gray-500">
                                    {ne.duration_ms && `${(ne.duration_ms / 1000).toFixed(1)}s`}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                      {execDetail.output_data && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">输出数据</h4>
                          <pre className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800 text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">
                            {JSON.stringify(execDetail.output_data, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}

// ═══ Export with Providers ═══
export default function AdminWorkflowEditor() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminShell>
          <WorkflowEditorInner/>
        </AdminShell>
      </QueryProvider>
    </AuthGuard>
  );
}
