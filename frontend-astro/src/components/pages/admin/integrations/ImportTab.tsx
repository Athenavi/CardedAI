'use client';

import React, {useState, useRef} from 'react';
import {useQuery, useMutation, useQueryClient} from '@tanstack/react-query';
import {SectionTitle} from '@/components/admin/shared-ui';
import {ArrowRight, Check, Database, FileText, FileUp, Globe, Loader, Upload, X} from 'lucide-react';
import {apiClient} from '@/lib/api/base-client';
import {ActionButton, Ghost} from './shared';


export default function ImportTab({showToast}: {
  showToast: (msg: string, type?: 'success' | 'error' | 'info') => void
}) {
  const __qc = useQueryClient();
  const wpFileRef = useRef<HTMLInputElement>(null);
  const [importing, setImporting] = useState(false);
  const [parseResult, setParseResult] = useState<any>(null);
  const [showImportConfirm, setShowImportConfirm] = useState(false);
  const [downloadMedia, setDownloadMedia] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const {data: _wpTemplate} = useQuery({
    queryKey: ['integ-wp-template'],
    queryFn: async () => {
      const r = await apiClient.get('/integrations/wordpress/template');
      return r.success && r.data ? r.data : null;
    },
  });

  const parseMut = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return apiClient.request('/integrations/wordpress/parse', {method: 'POST', body: formData});
    },
    onSuccess: (r) => {
      if (r.success) {
        setParseResult(r);
        setShowImportConfirm(true);
        showToast('文件解析成功，请确认导入');
      } else {
        showToast(r.error || '解析失败', 'error');
      }
      setImporting(false);
    },
    onError: () => {
      showToast('解析失败', 'error');
      setImporting(false);
    },
  });

  const importMut = useMutation({
    mutationFn: async ({file, downloadMedia}: { file: File; downloadMedia: boolean }) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('download_media', String(downloadMedia));
      return apiClient.request('/integrations/wordpress/import', {method: 'POST', body: formData});
    },
    onSuccess: (r) => {
      if (r.success) {
        showToast('WordPress 数据导入成功！');
        setParseResult(null);
        setShowImportConfirm(false);
      } else {
        showToast(r.error || '导入失败', 'error');
      }
      setImporting(false);
    },
    onError: () => {
      showToast('导入失败', 'error');
      setImporting(false);
    },
  });

  const handleWPFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setSelectedFile(file);
    setImporting(true);
    parseMut.mutate(file);
    e.target.value = '';
  };

  const handleWPImport = () => {
    if (!selectedFile) {
      showToast('请先选择文件', 'error');
      return;
    }
    setImporting(true);
    importMut.mutate({file: selectedFile, downloadMedia});
  };

  const importSources = [
    {name: 'Halo', desc: '从 Halo 博客导入文章和数据', icon: Globe, status: 'available'},
    {name: 'Jekyll', desc: '从 Jekyll 站点导入 Markdown 文章', icon: FileText, status: 'available'},
    {name: 'Hexo', desc: '从 Hexo 博客导入文章和配置', icon: FileText, status: 'available'},
    {name: 'Ghost', desc: '从 Ghost 平台导入内容和用户', icon: Ghost, status: 'coming'},
    {name: 'Medium', desc: '从 Medium 导出文章', icon: FileText, status: 'coming'},
    {name: 'JSON / CSV', desc: '通用 JSON/CSV 格式批量导入', icon: Database, status: 'available'},
  ];

  return (
    <div className="space-y-6">
      {/* WordPress Import - Primary */}
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="p-5 border-b border-gray-100 dark:border-gray-800">
          <SectionTitle icon={Upload} title="WordPress 导入" subtitle="从 WordPress WXR 导出文件迁移数据"/>
        </div>
        <div className="p-5">
          <div className="grid lg:grid-cols-2 gap-6">
            {/* Upload Area */}
            <div>
              <div
                className="border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl p-8 text-center hover:border-blue-400 transition-colors cursor-pointer"
                onClick={() => wpFileRef.current?.click()}>
                {importing ? (
                  <div className="flex flex-col items-center">
                    <Loader className="w-8 h-8 text-blue-500 animate-spin mb-2"/>
                    <p
                      className="text-sm text-gray-500 dark:text-gray-400">{parseResult ? '正在导入...' : '正在解析...'}</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <FileUp className="w-10 h-10 text-gray-300 mb-2"/>
                    <p className="text-sm text-gray-500 dark:text-gray-400">选择 WordPress 导出文件 (.xml)</p>
                    <p className="text-xs text-gray-400 mt-1">在 WordPress 后台 → 工具 → 导出 获取</p>
                  </div>
                )}
              </div>
              <input ref={wpFileRef} type="file" accept=".xml,.wxr" className="hidden" onChange={handleWPFileSelect}/>

              {/* Import Options */}
              {showImportConfirm && parseResult && (
                <div
                  className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/10 rounded-xl border border-blue-100 dark:border-blue-800/30">
                  <p className="text-sm font-medium text-blue-800 dark:text-blue-300 mb-3">确认导入</p>
                  {parseResult.stats && (
                    <div className="grid grid-cols-2 gap-2 mb-3">
                      {Object.entries(parseResult.stats).map(([key, val]) => (
                        <div key={key} className="flex justify-between text-xs">
                          <span className="text-blue-600 dark:text-blue-400">{key}</span>
                          <span className="font-medium text-blue-800 dark:text-blue-200">{String(val)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="flex items-center gap-2 mb-3">
                    <input type="checkbox" id="downloadMedia" checked={downloadMedia}
                           onChange={e => setDownloadMedia(e.target.checked)}
                           className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"/>
                    <label htmlFor="downloadMedia"
                           className="text-xs text-blue-700 dark:text-blue-300">同时下载媒体文件</label>
                  </div>
                  <div className="flex gap-2">
                    <ActionButton onClick={() => {
                      setShowImportConfirm(false);
                      setParseResult(null);
                      setSelectedFile(null);
                    }} icon={X} label="取消" variant="ghost" size="sm"/>
                    <ActionButton onClick={handleWPImport} icon={ArrowRight} label="开始导入" loading={importing}
                                  size="sm"/>
                  </div>
                </div>
              )}
            </div>

            {/* Instructions */}
            <div className="space-y-4">
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-3">导入步骤</p>
                <ol className="space-y-2.5">
                  {[
                    '在 WordPress 后台进入 工具 → 导出',
                    '选择"所有内容"并下载导出文件 (.xml)',
                    '点击左侧区域上传文件',
                    '预览解析结果并确认导入',
                    '等待导入完成',
                  ].map((step, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-xs text-gray-600 dark:text-gray-400">
                      <span
                        className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center shrink-0 text-[10px] font-bold">{i + 1}</span>
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-xl">
                <p className="text-sm font-medium text-gray-900 dark:text-white mb-2">支持的内容</p>
                <div className="flex flex-wrap gap-1.5">
                  {['文章', '页面', '分类', '标签', '评论', '媒体引用'].map(item => (
                    <span key={item}
                          className="inline-flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400 rounded-full">
                      <Check className="w-2.5 h-2.5"/>{item}
                    </span>
                  ))}
                </div>
              </div>
              <div
                className="p-3 bg-amber-50 dark:bg-amber-900/10 rounded-xl border border-amber-100 dark:border-amber-800/30">
                <p className="text-xs text-amber-700 dark:text-amber-300">
                  <strong>注意：</strong>媒体文件默认不会自动下载，仅保留引用链接。勾选"同时下载媒体文件"可迁移媒体资源。
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Other Import Sources */}
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        <div className="p-5 border-b border-gray-100 dark:border-gray-800">
          <SectionTitle icon={Upload} title="其他导入源" subtitle="从其他平台迁移数据"/>
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 divide-x divide-y divide-gray-100 dark:divide-gray-800">
          {importSources.map((src, i) => {
            const Icon = src.icon;
            return (
              <div key={i} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="w-8 h-8 rounded-lg bg-gradient-to-br from-gray-100 to-gray-200 dark:from-gray-700 dark:to-gray-800 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-gray-500 dark:text-gray-400"/>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{src.name}</p>
                    {src.status === 'coming' &&
                      <span className="text-[10px] text-amber-500 font-medium">即将推出</span>}
                  </div>
                </div>
                <p className="text-xs text-gray-400">{src.desc}</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
