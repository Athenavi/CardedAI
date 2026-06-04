'use client';

import React, {useState, useCallback, useRef} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {EmptyState, Modal, SectionTitle, StatCard} from '@/components/admin/shared-ui';
import {
  CloudUpload,
  Copy,
  Database,
  Eye,
  FileText,
  FileUp,
  HardDrive,
  Loader,
  Pin,
  PinOff,
  Save,
  Trash2,
  X
} from 'lucide-react';
import {apiClient} from '@/lib/api/base-client';
import {useConfirm} from '@/components/ui/confirm-provider';
import {IPFSFile, InputField, ActionButton} from './shared';


export default function IPFSTab({showToast}: {
  showToast: (msg: string, type?: 'success' | 'error' | 'info') => void
}) {
  const confirm = useConfirm();
  const qc = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [showTextUpload, setShowTextUpload] = useState(false);
  const [textContent, setTextContent] = useState('');
  const [textFilename, setTextFilename] = useState('content.txt');
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [ipfsGateway, setIpfsGateway] = useState('');

  const {data: ipfsFiles, isLoading} = useQuery({
    queryKey: ['integ-ipfs-files'],
    queryFn: async () => {
      const r = await apiClient.get('/integrations/ipfs/files');
      const raw = r.success && r.data ? (r.data.files || r.data) : [];
      return (Array.isArray(raw) ? raw : []) as IPFSFile[];
    },
  });

  const uploadFileMut = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.request('/integrations/ipfs/upload/file', {method: 'POST', body: formData});
    },
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-ipfs-files']});
      showToast(r.message || '文件已上传到 IPFS');
      setUploading(false);
    },
    onError: () => {
      showToast('上传失败', 'error');
      setUploading(false);
    },
  });

  const uploadTextMut = useMutation({
    mutationFn: (data: { text: string; filename: string }) => apiClient.post('/integrations/ipfs/upload/text', data),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-ipfs-files']});
      setShowTextUpload(false);
      setTextContent('');
      showToast(r.message || '文本已上传到 IPFS');
    },
    onError: () => showToast('上传失败', 'error'),
  });

  const pinMut = useMutation({
    mutationFn: (cid: string) => apiClient.post(`/integrations/ipfs/pin/${cid}`),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-ipfs-files']});
      showToast(r.message || '已固定');
    },
    onError: () => showToast('操作失败', 'error'),
  });

  const unpinMut = useMutation({
    mutationFn: (cid: string) => apiClient.post(`/integrations/ipfs/unpin/${cid}`),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-ipfs-files']});
      showToast(r.message || '已取消固定');
    },
    onError: () => showToast('操作失败', 'error'),
  });

  const deleteMut = useMutation({
    mutationFn: (cid: string) => apiClient.delete(`/integrations/ipfs/file/${cid}`),
    onSuccess: (r) => {
      qc.invalidateQueries({queryKey: ['integ-ipfs-files']});
      showToast(r.message || '已删除');
    },
    onError: () => showToast('删除失败', 'error'),
  });

  const configureMut = useMutation({
    mutationFn: (config: any) => apiClient.post('/integrations/ipfs/configure', config),
    onSuccess: (r) => {
      setShowConfigModal(false);
      showToast(r.message || 'IPFS 配置已更新');
    },
    onError: () => showToast('配置失败', 'error'),
  });

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    uploadFileMut.mutate(file);
    e.target.value = '';
  };

  const handleDragDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      setUploading(true);
      uploadFileMut.mutate(file);
    }
  }, []);

  const files = Array.isArray(ipfsFiles) ? ipfsFiles : [];

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={HardDrive} label="总文件数" value={files.length} color="from-purple-500 to-violet-500"/>
        <StatCard icon={Pin} label="已固定" value={files.filter(f => f.pinned).length}
                  color="from-green-500 to-emerald-500"/>
        <StatCard icon={Database} label="总大小"
                  value={files.reduce((s, f) => s + (f.size || 0), 0) > 0 ? `${(files.reduce((s, f) => s + (f.size || 0), 0) / 1024).toFixed(1)} KB` : '0 KB'}
                  color="from-blue-500 to-indigo-500"/>
        <StatCard icon={CloudUpload} label="存储网关" value="IPFS" color="from-orange-500 to-amber-500"/>
      </div>

      {/* Upload Area */}
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="p-5 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
          <SectionTitle icon={Database} title="IPFS 文件管理" subtitle="上传、固定和管理去中心化存储的文件"/>
          <div className="flex gap-2">
            <ActionButton onClick={() => setShowTextUpload(true)} icon={FileText} label="上传文本" variant="ghost"/>
            <ActionButton onClick={() => fileInputRef.current?.click()} icon={FileUp} label="上传文件"
                          loading={uploading}/>
          </div>
        </div>

        {/* Drag & Drop Zone */}
        <div className="p-5">
          <div
            className="border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
            onDragOver={e => e.preventDefault()} onDrop={handleDragDrop} onClick={() => fileInputRef.current?.click()}>
            {uploading ? (
              <div className="flex flex-col items-center">
                <Loader className="w-8 h-8 text-blue-500 animate-spin mb-2"/>
                <p className="text-sm text-gray-500 dark:text-gray-400">正在上传到 IPFS...</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <CloudUpload className="w-10 h-10 text-gray-300 mb-2"/>
                <p className="text-sm text-gray-500 dark:text-gray-400">拖放文件到这里，或点击选择文件</p>
                <p className="text-xs text-gray-400 mt-1">支持任意类型文件</p>
              </div>
            )}
          </div>
          <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileSelect}/>
        </div>

        {/* Files List */}
        <div className="border-t border-gray-100 dark:border-gray-800">
          {isLoading ? (
            <div className="p-8 text-center"><Loader className="w-6 h-6 animate-spin mx-auto text-gray-400"/></div>
          ) : files.length > 0 ? (
            <div className="divide-y divide-gray-100 dark:divide-gray-800 max-h-[400px] overflow-y-auto">
              {files.map((f: IPFSFile, i: number) => (
                <div key={f.cid || i}
                     className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                  <div className="flex items-center gap-3 min-w-0 flex-1">
                    <div
                      className="w-9 h-9 rounded-xl bg-gradient-to-br from-purple-100 to-indigo-100 dark:from-purple-900/30 dark:to-indigo-900/30 flex items-center justify-center shrink-0">
                      <FileText className="w-4 h-4 text-purple-500"/>
                    </div>
                    <div className="min-w-0">
                      <p
                        className="text-sm font-medium text-gray-900 dark:text-white truncate">{f.name || f.filename || f.cid}</p>
                      <p className="text-xs text-gray-400 font-mono truncate">{f.cid}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    {f.size && <span className="text-xs text-gray-400">{(f.size / 1024).toFixed(1)} KB</span>}
                    {f.pinned ? (
                      <span
                        className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full">
                        <Pin className="w-2.5 h-2.5"/>已固定
                      </span>
                    ) : (
                      <span
                        className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium bg-gray-100 text-gray-500 dark:text-gray-400 dark:bg-gray-800 dark:text-gray-400 rounded-full">
                        未固定
                      </span>
                    )}
                    <div className="flex gap-1">
                      {f.pinned ? (
                        <button onClick={() => unpinMut.mutate(f.cid)}
                                className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                                title="取消固定">
                          <PinOff className="w-3.5 h-3.5 text-gray-400"/>
                        </button>
                      ) : (
                        <button onClick={() => pinMut.mutate(f.cid)}
                                className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                                title="固定">
                          <Pin className="w-3.5 h-3.5 text-gray-400"/>
                        </button>
                      )}
                      {f.gateway_url && (
                        <a href={f.gateway_url} target="_blank" rel="noopener noreferrer"
                           className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                           title="查看">
                          <Eye className="w-3.5 h-3.5 text-gray-400"/>
                        </a>
                      )}
                      <button onClick={() => {
                        navigator.clipboard.writeText(f.cid);
                        showToast('CID 已复制', 'info');
                      }} className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-colors"
                              title="复制 CID">
                        <Copy className="w-3.5 h-3.5 text-gray-400"/>
                      </button>
                      <button onClick={async () => {
                        if (await confirm({
                          message: `确定删除 ${f.name || f.cid}？\n注意：IPFS 上的文件无法真正删除，仅删除记录。`,
                          variant: 'danger'
                        })) deleteMut.mutate(f.cid);
                      }} className="p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                              title="删除">
                        <Trash2 className="w-3.5 h-3.5 text-red-400"/>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState icon={Database} title="暂无 IPFS 文件" desc="上传文件到去中心化存储网络"/>
          )}
        </div>
      </div>

      {/* Text Upload Modal */}
      <Modal open={showTextUpload} onClose={() => setShowTextUpload(false)} title="上传文本到 IPFS"
             subtitle="将文本内容存储到去中心化网络">
        <div className="space-y-4">
          <InputField label="文件名" value={textFilename} onChange={setTextFilename} placeholder="content.txt"/>
          <div>
            <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1.5">内容</label>
            <textarea value={textContent} onChange={e => setTextContent(e.target.value)} rows={8}
                      placeholder="输入要上传的文本内容..."
                      className="w-full px-3 py-2 text-sm border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder:text-gray-400 focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 outline-none transition-all resize-none"/>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <ActionButton onClick={() => setShowTextUpload(false)} icon={X} label="取消" variant="ghost"/>
            <ActionButton onClick={() => {
              if (!textContent.trim()) {
                showToast('请输入内容', 'error');
                return;
              }
              uploadTextMut.mutate({text: textContent, filename: textFilename});
            }} icon={CloudUpload} label="上传" loading={uploadTextMut.isPending}/>
          </div>
        </div>
      </Modal>

      {/* IPFS Config Modal */}
      <Modal open={showConfigModal} onClose={() => setShowConfigModal(false)} title="IPFS 服务配置"
             subtitle="配置 IPFS 网关和 API">
        <div className="space-y-4">
          <InputField label="IPFS API 端点" value={ipfsGateway} onChange={setIpfsGateway}
                      placeholder="http://localhost:5001" hint="IPFS 节点 API 地址"/>
          <div className="flex justify-end gap-2 pt-2">
            <ActionButton onClick={() => setShowConfigModal(false)} icon={X} label="取消" variant="ghost"/>
            <ActionButton onClick={() => configureMut.mutate({api_url: ipfsGateway})} icon={Save} label="保存"
                          loading={configureMut.isPending}/>
          </div>
        </div>
      </Modal>
    </div>
  );
}
