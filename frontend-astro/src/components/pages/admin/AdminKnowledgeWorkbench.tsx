'use client';

import React, {useState, useRef, useEffect} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {motion, AnimatePresence} from 'framer-motion';
import {
  BookOpen,
  Database,
  FileText,
  FolderPlus,
  HelpCircle,
  Loader2,
  MessageSquare,
  Plus,
  Rss,
  Search,
  Send,
  Trash2,
  Upload,
  File,
  BarChart3,
  X,
  ChevronRight,
  Sparkles,
  Clock
} from 'lucide-react';

// ═══ Types ═══
interface KnowledgeBase {
  id: number;
  name: string;
  description?: string;
  embedding_model: string;
  chunk_size: number;
  chunk_overlap: number;
  document_count: number;
  chunk_count: number;
  is_active: boolean;
  created_at: string;
}

interface KDocument {
  id: number;
  filename: string;
  file_type: string;
  status: string;
  chunk_count: number;
  file_size?: number;
  created_at: string;
}

interface SearchResult {
  chunk_id: string;
  document_id: number;
  content: string;
  score: number;
  metadata?: any;
}

interface Report {
  id: number;
  title: string;
  content: string;
  report_type: string;
  status: string;
  created_at: string;
}

type TabKey = 'bases' | 'search' | 'reports';

const TABS: { key: TabKey; label: string; icon: React.FC<any> }[] = [
  {key: 'bases', label: '知识库', icon: Database},
  {key: 'search', label: 'RAG 问答', icon: MessageSquare},
  {key: 'reports', label: '研报中心', icon: FileText},
];

// ═══ Stat Card ═══
const StatCard: React.FC<{
  label: string; value: number | string;
  icon: React.FC<any>; color: string;
}> = ({label, value, icon: Icon, color}) => {
  const colorMap: Record<string, { bg: string; text: string; icon: string }> = {
    blue: {bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', icon: 'text-blue-500'},
    green: {bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400', icon: 'text-emerald-500'},
    purple: {bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400', icon: 'text-purple-500'},
    orange: {bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-600 dark:text-orange-400', icon: 'text-orange-500'},
  };
  const c = colorMap[color] || colorMap.blue;
  return (
    <motion.div initial={{opacity: 0, y: 20}} animate={{opacity: 1, y: 0}}
      className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 card-hover">
      <div className="flex items-center gap-3 mb-3">
        <div className={`w-10 h-10 rounded-xl ${c.bg} flex items-center justify-center`}>
          <Icon className={`w-5 h-5 ${c.icon}`}/>
        </div>
        <span className="text-sm text-gray-500 dark:text-gray-400">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white tabular-nums">{value}</p>
    </motion.div>
  );
};

// ═══ Knowledge Bases Panel ═══
const BasesPanel: React.FC = () => {
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [selectedBase, setSelectedBase] = useState<KnowledgeBase | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [newBase, setNewBase] = useState({name: '', description: '', embedding_model: 'text-embedding-3-small', chunk_size: 500, chunk_overlap: 50});

  const {data: bases, isLoading} = useQuery({
    queryKey: ['knowledge-bases'],
    queryFn: async () => {
      const res = await apiClient.get('/knowledge/bases');
      return res.data?.items || res.data || [];
    }
  });

  const {data: docs, isLoading: docsLoading} = useQuery({
    queryKey: ['knowledge-docs', selectedBase?.id],
    queryFn: async () => {
      if (!selectedBase) return [];
      const res = await apiClient.get(`/knowledge/bases/${selectedBase.id}/documents`);
      return res.data?.items || res.data || [];
    },
    enabled: !!selectedBase
  });

  const createMutation = useMutation({
    // Backend uses Form() annotation → must send form-encoded body
    mutationFn: async () => apiClient.postForm('/knowledge/bases', newBase),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['knowledge-bases']}); setShowCreate(false); }
  });

  const deleteBaseMutation = useMutation({
    mutationFn: async (id: number) => apiClient.delete(`/knowledge/bases/${id}`),
    onSuccess: () => { qc.invalidateQueries({queryKey: ['knowledge-bases']}); setSelectedBase(null); }
  });

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      if (!selectedBase) return;
      const formData = new FormData();
      formData.append('file', file);
      // FormData is auto-detected by base-client; no need for extra headers
      return apiClient.post(`/knowledge/bases/${selectedBase.id}/documents/upload`, formData);
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['knowledge-docs']});
      qc.invalidateQueries({queryKey: ['knowledge-bases']});
      setShowUpload(false);
    }
  });

  const deleteDocMutation = useMutation({
    mutationFn: async (docId: number) => {
      if (!selectedBase) return;
      return apiClient.delete(`/knowledge/bases/${selectedBase.id}/documents/${docId}`);
    },
    onSuccess: () => {
      qc.invalidateQueries({queryKey: ['knowledge-docs']});
      qc.invalidateQueries({queryKey: ['knowledge-bases']});
    }
  });

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {selectedBase ? (
            <span className="flex items-center gap-2">
              <button onClick={() => setSelectedBase(null)} className="text-blue-500 hover:text-blue-600">知识库</button>
              <ChevronRight className="w-4 h-4 text-gray-400"/>
              {selectedBase.name}
            </span>
          ) : '知识库管理'}
        </h3>
        {!selectedBase && (
          <button onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium">
            <Plus className="w-4 h-4"/> 创建知识库
          </button>
        )}
        {selectedBase && (
          <button onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium">
            <Upload className="w-4 h-4"/> 上传文档
          </button>
        )}
      </div>

      {/* Create Form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div initial={{opacity: 0, height: 0}} animate={{opacity: 1, height: 'auto'}} exit={{opacity: 0, height: 0}}
            className="overflow-hidden">
            <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">名称</label>
                  <input value={newBase.name} onChange={e => setNewBase({...newBase, name: e.target.value})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
                    placeholder="例：产品文档库"/>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Embedding 模型</label>
                  <select value={newBase.embedding_model} onChange={e => setNewBase({...newBase, embedding_model: e.target.value})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
                    <option value="text-embedding-3-small">OpenAI text-embedding-3-small</option>
                    <option value="all-MiniLM-L6-v2">Local all-MiniLM-L6-v2</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
                <input value={newBase.description} onChange={e => setNewBase({...newBase, description: e.target.value})}
                  className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">分块大小</label>
                  <input type="number" value={newBase.chunk_size} onChange={e => setNewBase({...newBase, chunk_size: parseInt(e.target.value) || 500})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">分块重叠</label>
                  <input type="number" value={newBase.chunk_overlap} onChange={e => setNewBase({...newBase, chunk_overlap: parseInt(e.target.value) || 50})}
                    className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"/>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button onClick={() => setShowCreate(false)} className="px-4 py-2 text-sm text-gray-600 dark:text-gray-400">取消</button>
                <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium disabled:opacity-50">
                  {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin"/>}
                  创建
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Upload Dialog */}
      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setShowUpload(false)}>
          <motion.div initial={{scale: 0.9, opacity: 0}} animate={{scale: 1, opacity: 1}}
            onClick={e => e.stopPropagation()}
            className="p-6 rounded-2xl bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 max-w-md w-full mx-4">
            <div className="flex items-center justify-between mb-4">
              <h4 className="font-semibold text-gray-900 dark:text-white">上传文档</h4>
              <button onClick={() => setShowUpload(false)}><X className="w-5 h-5 text-gray-500"/></button>
            </div>
            <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-8 text-center">
              <Upload className="w-10 h-10 mx-auto text-gray-400 mb-3"/>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">支持 PDF、DOCX、TXT、MD、HTML</p>
              <input ref={fileInputRef} type="file" accept=".pdf,.docx,.doc,.txt,.md,.html" onChange={handleFileChange} className="hidden"/>
              <button onClick={() => fileInputRef.current?.click()} disabled={uploadMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700 text-sm font-medium disabled:opacity-50">
                {uploadMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin inline mr-2"/> : null}
                选择文件
              </button>
            </div>
            {uploadMutation.isError && <p className="mt-2 text-sm text-red-500">上传失败</p>}
            {uploadMutation.isSuccess && <p className="mt-2 text-sm text-emerald-500">上传成功</p>}
          </motion.div>
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
      ) : !selectedBase ? (
        /* Bases List */
        bases?.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <Database className="w-12 h-12 mx-auto mb-3 opacity-50"/>
            <p>暂无知识库</p>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2">
            {bases?.map((base: KnowledgeBase) => (
              <motion.div key={base.id} initial={{opacity: 0}} animate={{opacity: 1}}
                onClick={() => setSelectedBase(base)}
                className="p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 hover:border-blue-300 dark:hover:border-blue-700 cursor-pointer transition-colors group">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center">
                      <BookOpen className="w-5 h-5 text-blue-500"/>
                    </div>
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">{base.name}</h4>
                      <p className="text-xs text-gray-500">{base.embedding_model}</p>
                    </div>
                  </div>
                  <button onClick={e => {e.stopPropagation(); if (confirm('确定删除？')) deleteBaseMutation.mutate(base.id);}}
                    className="p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-gray-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100">
                    <Trash2 className="w-4 h-4"/>
                  </button>
                </div>
                {base.description && <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">{base.description}</p>}
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span className="flex items-center gap-1"><File className="w-3.5 h-3.5"/> {base.document_count} 文档</span>
                  <span className="flex items-center gap-1"><Rss className="w-3.5 h-3.5"/> {base.chunk_count} 切片</span>
                </div>
              </motion.div>
            ))}
          </div>
        )
      ) : (
        /* Documents List */
        <div>
          {docsLoading ? (
            <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-blue-500"/></div>
          ) : docs?.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <FileText className="w-12 h-12 mx-auto mb-3 opacity-50"/>
              <p>暂无文档，点击上方按钮上传</p>
            </div>
          ) : (
            <div className="space-y-2">
              {docs?.map((doc: KDocument) => (
                <motion.div key={doc.id} initial={{opacity: 0}} animate={{opacity: 1}}
                  className="flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-purple-50 dark:bg-purple-900/20 flex items-center justify-center">
                      <FileText className="w-4 h-4 text-purple-500"/>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-gray-900 dark:text-white">{doc.filename}</h4>
                      <p className="text-xs text-gray-500">
                        {doc.file_type?.toUpperCase()} - {doc.chunk_count} 切片 - {doc.file_size ? `${(doc.file_size / 1024).toFixed(1)} KB` : ''}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      doc.status === 'completed' ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400' :
                      doc.status === 'processing' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
                      doc.status === 'failed' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                      'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400'
                    }`}>
                      {doc.status === 'completed' ? '已完成' : doc.status === 'processing' ? '处理中' : doc.status === 'failed' ? '失败' : doc.status}
                    </span>
                    <button onClick={() => { if (confirm('确定删除文档及所有切片？')) deleteDocMutation.mutate(doc.id); }}
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
    </div>
  );
};

// ═══ RAG Search / QA Panel ═══
const SearchPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const [selectedBaseId, setSelectedBaseId] = useState<number | null>(null);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [answer, setAnswer] = useState('');
  const [searching, setSearching] = useState(false);
  const [mode, setMode] = useState<'search' | 'qa'>('qa');

  const {data: bases} = useQuery({
    queryKey: ['knowledge-bases-select'],
    queryFn: async () => {
      const res = await apiClient.get('/knowledge/bases');
      return res.data?.items || res.data || [];
    }
  });

  const handleSearch = async () => {
    if (!query.trim() || !selectedBaseId) return;
    setSearching(true);
    setResults([]);
    setAnswer('');
    try {
      if (mode === 'search') {
        // Backend uses Form() annotation → must send form-encoded body
        const res = await apiClient.postForm(`/knowledge/bases/${selectedBaseId}/search`, {query, top_k: 5});
        setResults(res.data?.results || res.data || []);
      } else {
        // Backend uses Form() annotation → must send form-encoded body
        const res = await apiClient.postForm(`/knowledge/bases/${selectedBaseId}/qa`, {question: query, top_k: 5});
        setAnswer(res.data?.answer || '');
        setResults(res.data?.sources || []);
      }
    } catch (e: any) {
      setAnswer('查询失败：' + (e.message || '未知错误'));
    }
    setSearching(false);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">知识检索</h3>
        <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-lg">
          <button onClick={() => setMode('qa')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${mode === 'qa' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500'}`}>
            <MessageSquare className="w-3.5 h-3.5 inline mr-1"/> 问答
          </button>
          <button onClick={() => setMode('search')}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${mode === 'search' ? 'bg-white dark:bg-gray-700 shadow-sm text-gray-900 dark:text-white' : 'text-gray-500'}`}>
            <Search className="w-3.5 h-3.5 inline mr-1"/> 语义搜索
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="p-4 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <div className="flex gap-3">
          <select value={selectedBaseId || ''} onChange={e => setSelectedBaseId(Number(e.target.value) || null)}
            className="px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm shrink-0">
            <option value="">选择知识库</option>
            {bases?.map((b: KnowledgeBase) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
          <div className="flex-1 relative">
            <input value={query} onChange={e => setQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              className="w-full px-4 py-2 pr-10 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm focus:ring-2 focus:ring-blue-500 outline-none"
              placeholder={mode === 'qa' ? '输入问题，AI 将基于知识库回答...' : '输入搜索关键词...'}/>
            <button onClick={handleSearch} disabled={searching || !selectedBaseId}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg bg-blue-600 text-white disabled:opacity-50">
              {searching ? <Loader2 className="w-4 h-4 animate-spin"/> : <Send className="w-4 h-4"/>}
            </button>
          </div>
        </div>
      </div>

      {/* Answer */}
      {answer && (
        <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}}
          className="p-5 rounded-2xl border border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20">
          <div className="flex items-center gap-2 mb-3">
            <Sparkles className="w-5 h-5 text-blue-500"/>
            <h4 className="font-medium text-blue-900 dark:text-blue-300">AI 回答</h4>
          </div>
          <div className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">{answer}</div>
        </motion.div>
      )}

      {/* Results */}
      {results.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">相关文档片段 ({results.length})</h4>
          {results.map((r, i) => (
            <motion.div key={r.chunk_id || i} initial={{opacity: 0, x: -10}} animate={{opacity: 1, x: 0}}
              className="p-4 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-gray-500">文档 #{r.document_id}</span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                  相似度 {(r.score * 100).toFixed(1)}%
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">{r.content}</p>
            </motion.div>
          ))}
        </div>
      )}

      {!answer && results.length === 0 && !searching && (
        <div className="text-center py-12 text-gray-500">
          <Search className="w-12 h-12 mx-auto mb-3 opacity-50"/>
          <p>选择知识库后输入问题进行检索</p>
        </div>
      )}
    </div>
  );
};

// ═══ Reports Panel ═══
const ReportsPanel: React.FC = () => {
  const qc = useQueryClient();
  const [generating, setGenerating] = useState(false);
  const [selectedBaseId, setSelectedBaseId] = useState<number | null>(null);
  const [genConfig, setGenConfig] = useState({topic: '', template: 'default', max_sections: 6, detail_level: 'standard'});

  const {data: bases} = useQuery({
    queryKey: ['knowledge-bases-for-reports'],
    queryFn: async () => {
      const res = await apiClient.get('/knowledge/bases');
      return res.data?.items || res.data || [];
    }
  });

  const {data: reports, isLoading} = useQuery({
    queryKey: ['knowledge-reports'],
    queryFn: async () => {
      const res = await apiClient.get('/knowledge/reports');
      return res.data?.items || res.data || [];
    }
  });

  const generateMutation = useMutation({
    mutationFn: async () => {
      if (!selectedBaseId) throw new Error('请选择知识库');
      // Backend uses Form() annotation → must send form-encoded body
      return apiClient.postForm(`/knowledge/bases/${selectedBaseId}/reports/generate`, genConfig);
    },
    onSuccess: () => qc.invalidateQueries({queryKey: ['knowledge-reports']})
  });

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white">研报中心</h3>

      {/* Generate */}
      <div className="p-5 rounded-2xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
        <h4 className="font-medium text-gray-900 dark:text-white mb-4 flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-500"/> 生成研报
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">知识库</label>
            <select value={selectedBaseId || ''} onChange={e => setSelectedBaseId(Number(e.target.value) || null)}
              className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
              <option value="">选择知识库</option>
              {bases?.map((b: KnowledgeBase) => <option key={b.id} value={b.id}>{b.name}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">报告模板</label>
            <select value={genConfig.template} onChange={e => setGenConfig({...genConfig, template: e.target.value})}
              className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm">
              <option value="default">默认模板</option>
              <option value="research">研究报告</option>
              <option value="summary">摘要报告</option>
              <option value="comparison">对比分析</option>
              <option value="trend">趋势分析</option>
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-600 dark:text-gray-400 mb-1">主题</label>
            <input value={genConfig.topic} onChange={e => setGenConfig({...genConfig, topic: e.target.value})}
              className="w-full px-3 py-2 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm"
              placeholder="例：大语言模型发展趋势"/>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button onClick={() => generateMutation.mutate()} disabled={generateMutation.isPending || !selectedBaseId}
            className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-xl hover:bg-purple-700 text-sm font-medium disabled:opacity-50">
            {generateMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin"/> : <Sparkles className="w-4 h-4"/>}
            生成研报
          </button>
        </div>
        {generateMutation.isError && (
          <p className="mt-2 text-sm text-red-500">{(generateMutation.error as any)?.message || '生成失败'}</p>
        )}
      </div>

      {/* Reports List */}
      {isLoading ? (
        <div className="flex items-center justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-purple-500"/></div>
      ) : reports?.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <FileText className="w-12 h-12 mx-auto mb-3 opacity-50"/>
          <p>暂无研报</p>
        </div>
      ) : (
        <div className="space-y-3">
          {reports?.map((r: Report) => (
            <motion.div key={r.id} initial={{opacity: 0}} animate={{opacity: 1}}
              className="p-5 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">{r.title}</h4>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="px-2 py-0.5 rounded-full text-xs bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                      {r.report_type}
                    </span>
                    <span className="text-xs text-gray-500 flex items-center gap-1">
                      <Clock className="w-3 h-3"/>{new Date(r.created_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                </div>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none text-gray-600 dark:text-gray-400 line-clamp-4 whitespace-pre-wrap">
                {r.content}
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
};

// ═══ Main Component ═══
function KnowledgeWorkbenchInner() {
  const [activeTab, setActiveTab] = useState<TabKey>('bases');

  // Stats
  const {data: stats} = useQuery({
    queryKey: ['knowledge-stats'],
    queryFn: async () => {
      const res = await apiClient.get('/knowledge/stats');
      return res.data || {};
    },
    staleTime: 60_000,
  });

  const renderTab = () => {
    switch (activeTab) {
      case 'bases': return <BasesPanel/>;
      case 'search': return <SearchPanel/>;
      case 'reports': return <ReportsPanel/>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
          <BookOpen className="w-7 h-7 text-purple-500"/>
          知识工作台
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">知识库管理、RAG 智能问答与研报生成</p>
      </div>

      {/* Stats Dashboard */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="知识库" value={stats?.total_bases ?? stats?.bases ?? '-'} icon={Database} color="blue"/>
        <StatCard label="文档" value={stats?.total_documents ?? stats?.documents ?? '-'} icon={FileText} color="green"/>
        <StatCard label="文档切片" value={stats?.total_chunks ?? stats?.chunks ?? '-'} icon={BarChart3} color="purple"/>
        <StatCard label="报告" value={stats?.total_reports ?? stats?.reports ?? '-'} icon={Rss} color="orange"/>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 p-1 bg-gray-100 dark:bg-gray-800 rounded-xl w-fit">
        {TABS.map(({key, label, icon: Icon}) => (
          <button key={key} onClick={() => setActiveTab(key)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === key
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
            }`}>
            <Icon className="w-4 h-4"/>
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      <AnimatePresence mode="wait">
        <motion.div key={activeTab} initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} exit={{opacity: 0, y: -10}}>
          {renderTab()}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

// ═══ Export with Providers ═══
export default function AdminKnowledgeWorkbench() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminShell title="知识工作台">
          <KnowledgeWorkbenchInner/>
        </AdminShell>
      </QueryProvider>
    </AuthGuard>
  );
}
