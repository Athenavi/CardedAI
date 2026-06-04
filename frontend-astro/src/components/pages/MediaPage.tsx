'use client';

import React, {useCallback, useEffect, useRef, useState} from 'react';
import type {MediaFile} from '@/lib/api';
import {MediaService} from '@/lib/api';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {motion} from 'framer-motion';
import {
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  FileText,
  Filter,
  FolderClosed,
  FolderOpen,
  Grid3X3,
  Image as ImageIcon,
  List,
  Music,
  Plus,
  Tag,
  Trash2,
  Upload,
  Video,
  X
} from 'lucide-react';
import {getConfig} from '@/lib/config';
import DesktopLyrics from '@/components/audio/DesktopLyrics';
import {apiClient} from "@/lib/api/base-client";
import {getFullMediaUrl} from '@/lib/utils';
import {useConfirm} from '@/components/ui/confirm-provider';

/* ---------- Shared icons ---------- */
const _Minus: React.FC<{ className?: string }> = p => <svg className={p.className} fill="none" viewBox="0 0 24 24"
                                                           stroke="currentColor">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4"/>
</svg>;
const _File: React.FC<{ className?: string }> = p => <svg className={p.className} fill="none" viewBox="0 0 24 24"
                                                          stroke="currentColor">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"/>
</svg>;

/* ---------- FolderTree ---------- */
interface FolderNode {
  id: number; name: string; children?: FolderNode[];
}

const FolderTree: React.FC<{
  folders: FolderNode[]; selectedId: number | null; onSelect: (f: FolderNode | null) => void;
  onCreate: () => void; onDelete: (id: number) => void; loading: boolean;
}> = ({folders, selectedId, onSelect, onCreate, onDelete, loading}) => {
  const [expanded, setExpanded] = useState<Set<number>>(new Set());

  const toggle = (id: number) => {
    const s = new Set(expanded);
    s.has(id) ? s.delete(id) : s.add(id);
    setExpanded(s);
  };

  const renderNode = (node: FolderNode, depth: number = 0) => (
    <div key={node.id}>
      <div className={`group flex items-center gap-1 px-2 py-1.5 rounded-lg cursor-pointer text-sm transition-colors ${
        selectedId === node.id ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
      }`} style={{paddingLeft: `${12 + depth * 16}px`}}>
        <button onClick={() => toggle(node.id)} className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded">
          {node.children?.length ? (expanded.has(node.id) ? <ChevronDown className="w-3.5 h-3.5"/> : <ChevronRight className="w-3.5 h-3.5"/>) : <span className="w-3.5"/>}
        </button>
        <div className="flex-1 flex items-center gap-1.5" onClick={() => onSelect(node)}>
          {expanded.has(node.id) ? <FolderOpen className="w-4 h-4 text-yellow-500"/> : <FolderClosed className="w-4 h-4 text-yellow-600"/>}
          <span className="truncate">{node.name}</span>
        </div>
        <button onClick={e => {e.stopPropagation(); onDelete(node.id);}} className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-red-100 dark:hover:bg-red-900/30 rounded text-gray-400 hover:text-red-500"><X className="w-3 h-3"/></button>
      </div>
      {expanded.has(node.id) && node.children?.map(child => renderNode(child, depth + 1))}
    </div>
  );

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">文件夹</h3>
        <button onClick={onCreate} className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded text-gray-400 hover:text-blue-600"><Plus className="w-4 h-4"/></button>
      </div>
      {loading ? (
        <div className="space-y-2">{[1,2,3].map(i => <div key={i} className="h-8 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
      ) : (
        <div className="space-y-0.5">
          <div onClick={() => onSelect(null)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg cursor-pointer text-sm transition-colors ${selectedId === null ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>
            <Grid3X3 className="w-4 h-4"/><span>全部文件</span>
          </div>
          {folders.map(n => renderNode(n))}
        </div>
      )}
    </div>
  );
};

/* ---------- StorageStats ---------- */
const StorageStats: React.FC<{ stats: any; loading: boolean }> = ({stats, loading}) => {
  const items = [
    {label: '图片', count: stats.image_count || 0, color: 'from-blue-500 to-cyan-500', icon: ImageIcon},
    {label: '视频', count: stats.video_count || 0, color: 'from-purple-500 to-pink-500', icon: Video},
    {label: '已用空间', count: stats.storage_used || '0 MB', color: 'from-green-500 to-emerald-500', icon: Upload},
  ];
  return (<div className="space-y-3">
    <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">存储</h3>
    {items.map(item => {const Icon = item.icon; return (
      <div key={item.label} className={`p-4 rounded-xl bg-gradient-to-br ${item.color} text-white`}>
        <div className="flex items-center gap-2 text-sm opacity-80"><Icon className="w-4 h-4"/>{item.label}</div>
        <p className="text-xl font-bold mt-1">{loading ? '...' : item.count}</p>
      </div>
    );})}
    {!loading && stats.storage_percentage !== undefined && (<div>
      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
        <span>存储</span><span>{stats.storage_percentage}%</span></div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2"><div className="bg-blue-600 h-2 rounded-full" style={{width: `${stats.storage_percentage}%`}}/></div></div>)}
  </div>);
};

/* ---------- UploadArea ---------- */
const UploadArea: React.FC<{onUpload: (files: File[]) => void; uploading: boolean; progress: number; status: string; collapsed: boolean; onToggle: () => void}> = ({onUpload, uploading, progress, status, collapsed, onToggle}) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  return (<div className="mb-6">
    <button onClick={onToggle} className="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400 mb-3">
      {collapsed ? <ChevronRight className="w-4 h-4"/> : <ChevronDown className="w-4 h-4"/>} 上传文件
    </button>
    {!collapsed && (<div onDragOver={e => {e.preventDefault(); setDragOver(true);}} onDragLeave={() => setDragOver(false)} onDrop={e => {e.preventDefault(); setDragOver(false); if (e.dataTransfer.files.length) onUpload(Array.from(e.dataTransfer.files));}}
      className={`border-2 border-dashed rounded-2xl p-8 text-center transition-colors cursor-pointer ${dragOver ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-300 dark:border-gray-700 hover:border-blue-400'}`}
      onClick={() => inputRef.current?.click()}>
      <Upload className="w-10 h-10 text-gray-400 mx-auto mb-3"/>
      <p className="text-gray-600 dark:text-gray-400 font-medium">{uploading ? '上传中...' : '拖拽文件到此处或点击上传'}</p>
      <input ref={inputRef} type="file" multiple onChange={e => {if (e.target.files?.length) onUpload(Array.from(e.target.files));}} className="hidden"/>
      {uploading && <div className="mt-4">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div className="bg-blue-600 h-2 rounded-full transition-all" style={{width: `${progress}%`}}/>
        </div>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{status}</p></div>}
    </div>)}
  </div>);
};

/* ---------- MediaGrid ---------- */
/** 按分类分组：返回 Map<分类名, MediaFile[]> */
function groupByCategory(files: MediaFile[]): Map<string, MediaFile[]> {
  const groups = new Map<string, MediaFile[]>();
  for (const f of files) {
    const key = (f as any).category || '\u0000未分类'; // \u0000 排序到最前
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key)!.push(f);
  }
  // 排序: 未分类始终在最前，其余按名称
  return new Map([...groups.entries()].sort(([a], [b]) => {
    if (a.startsWith('\u0000')) return -1;
    if (b.startsWith('\u0000')) return 1;
    return a.localeCompare(b, 'zh-CN');
  }));
}

const MediaGrid: React.FC<{files: MediaFile[]; loading: boolean; viewMode: 'grid'|'list'; selected: number[]; onSelect: (id: number) => void; onPreview: (m: MediaFile) => void; onDelete: (m: MediaFile) => void; onEditTags?: (m: MediaFile) => void; onEditCategory?: (m: MediaFile) => void}> = ({files, loading, viewMode, selected, onSelect, onPreview, onDelete, onEditTags, onEditCategory}) => {
  const [groupCollapsed, setGroupCollapsed] = useState<Set<string>>(new Set());
  const [allExpanded, setAllExpanded] = useState(true); // true = 全部展开, false = 全部折叠

  if (loading) return <div className="p-12 text-center"><div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>;
  if (!files.length) return <div className="p-12 text-center text-gray-400"><ImageIcon className="w-12 h-12 mx-auto mb-3 opacity-50"/><p>暂无媒体文件</p></div>;

  const getIcon = (m: string) => m?.startsWith('video/') ? Video : m?.startsWith('audio/') ? Music : FileText;

  const groups = groupByCategory(files);

  const toggleGroup = (key: string) => {
    const s = new Set(groupCollapsed);
    s.has(key) ? s.delete(key) : s.add(key);
    setGroupCollapsed(s);
    setAllExpanded(s.size === 0); // 全展开时设为true
  };

  const expandAll = () => { setGroupCollapsed(new Set()); setAllExpanded(true); };
  const collapseAll = () => {
    const all = new Set(groups.keys());
    setGroupCollapsed(all);
    setAllExpanded(false);
  };

  const selectGroup = (items: MediaFile[]) => {
    const allSelected = items.every(f => selected.includes(f.id));
    if (allSelected) {
      // 取消全选：只取消当前选中的
      selected.filter(id => items.some(f => f.id === id)).forEach(id => onSelect(id));
    } else {
      // 全选：只选中未选中的
      items.filter(f => !selected.includes(f.id)).forEach(f => onSelect(f.id));
    }
  };

  // 公共的单个文件渲染（列表行 / 网格卡片）
  const renderListItem = (f: MediaFile) => {
    const isPDF = f.mime_type === 'application/pdf';
    const Icon = f.mime_type?.startsWith('image/') ? ImageIcon : getIcon(f.mime_type || '');
    return (
        <tr key={f.id} className={`hover:bg-gray-50 dark:hover:bg-gray-800 ${selected.includes(f.id)?'bg-blue-50 dark:bg-blue-900/20':''}`}>
          <td className="px-4"><input type="checkbox" checked={selected.includes(f.id)} onChange={() => onSelect(f.id)} className="h-4 w-4 text-blue-600 rounded"/></td>
          <td className="py-3 cursor-pointer" onClick={() => onPreview(f)}><div className="flex items-center gap-3">
            {f.mime_type?.startsWith('image/') && f.url ? (
                <img src={getFullMediaUrl(f.url)} alt={f.original_filename} className="w-10 h-10 rounded-lg object-cover" loading="lazy" decoding="async"/>
            ) : f.mime_type?.startsWith('video/') && f.url ? (
                    <div className="w-10 h-10 rounded-lg bg-gray-900 flex items-center justify-center relative">
                      <Video className="w-5 h-5 text-white"/>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-4 h-4 bg-white/80 rounded-full flex items-center justify-center"><div className="w-0 h-0 border-t-[3px] border-t-transparent border-l-[6px] border-l-black border-b-[3px] border-b-transparent ml-0.5"/></div>
                      </div>
                    </div>
            ) : isPDF ? (
                    <div className="w-10 h-10 rounded-lg bg-red-50 dark:bg-red-900/10 flex items-center justify-center"><FileText className="w-5 h-5 text-red-500"/></div>
                ) :
                <div className="w-10 h-10 rounded-lg bg-gray-100 dark:bg-gray-700 flex items-center justify-center"><Icon className="w-5 h-5 text-gray-400"/></div>}
            <div>
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate max-w-[200px]">{f.original_filename}</p>
              <p
                className="text-xs text-gray-500 dark:text-gray-400">{f.file_size ? `${(f.file_size / 1024).toFixed(1)} KB` : ''}</p>
              {f.tags && onEditTags && (
                  <p className="flex flex-wrap gap-1 mt-1 cursor-pointer hover:opacity-80" onClick={(e) => { e.stopPropagation(); onEditTags(f); }}>
                    {(f.tags as string).split(',').filter(Boolean).slice(0, 3).map((tag: string) => (
                        <span key={tag} className="text-[10px] px-1.5 py-0.5 rounded bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400">{tag.trim()}</span>
                    ))}
                    {(f.tags as string).split(',').filter(Boolean).length > 3 && (
                        <span className="text-[10px] text-gray-400">+{(f.tags as string).split(',').filter(Boolean).length - 3}</span>
                    )}
                  </p>
              )}
            </div>
          </div></td>
          <td className="text-sm text-gray-500 dark:text-gray-400 hidden sm:table-cell">
            <div className="flex items-center gap-2"><span>{f.mime_type?.split('/')[0] || '-'}</span></div>
          </td>
          <td className="pr-4 text-right"><button onClick={() => onDelete(f)} className="p-1 text-gray-400 hover:text-red-500"><Trash2 className="w-4 h-4"/></button></td>
        </tr>
    );
  };

  const renderGridItem = (f: MediaFile) => {
    const isVideo = f.mime_type?.startsWith('video/');
    const isImage = f.mime_type?.startsWith('image/');
    const isPDF = f.mime_type === 'application/pdf';
    const isAudio = f.mime_type?.startsWith('audio/');
    const Icon = getIcon(f.mime_type || '');
    return (
        <div key={f.id}
             className={`relative group aspect-square rounded-xl overflow-hidden border ${selected.includes(f.id) ? 'border-blue-500 ring-2 ring-blue-500' : 'border-gray-200 dark:border-gray-700'} bg-gray-50 dark:bg-gray-800`}>
          <input type="checkbox" checked={selected.includes(f.id)} onChange={() => onSelect(f.id)} className="absolute top-2 left-2 z-10 h-4 w-4 text-blue-600 rounded"/>
          {isImage && f.url ? (
              <img src={getFullMediaUrl(f.url)} alt={f.original_filename} className="w-full h-full object-cover cursor-pointer" onClick={() => onPreview(f)} loading="lazy" decoding="async"/>
          ) : isVideo && f.url ? (
            <div
              className="w-full h-full relative cursor-pointer bg-gray-900 overflow-hidden"
              onClick={() => onPreview(f)}>
              <video src={getFullMediaUrl(f.url)} preload="metadata" muted playsInline
                     style={{
                       position: 'absolute',
                       top: 0,
                       left: 0,
                       width: '100%',
                       height: '100%',
                       objectFit: 'cover',
                       objectPosition: 'center'
                     }}/>
              <div
                className="absolute inset-0 bg-black/30 flex items-center justify-center group-hover:bg-black/40 transition-colors">
                <div
                  className="w-12 h-12 bg-white/90 rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                  <div
                    className="w-0 h-0 border-t-[8px] border-t-transparent border-l-[14px] border-l-black border-b-[8px] border-b-transparent ml-1"/>
                </div>
              </div>
            </div>
          ) : isPDF ? (
                  <div className="w-full h-full flex flex-col items-center justify-center cursor-pointer bg-red-50 dark:bg-red-900/10" onClick={() => onPreview(f)}>
                    <FileText className="w-12 h-12 text-red-500 mb-2"/>
                    <span className="text-xs text-red-600 dark:text-red-400 font-medium">PDF</span>
                  </div>
          ) : isAudio ? (
                  <div className="w-full h-full flex flex-col items-center justify-center cursor-pointer bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/10 dark:to-pink-900/10" onClick={() => onPreview(f)}>
                    <Music className="w-12 h-12 text-purple-500 mb-2"/>
                    <span className="text-xs text-purple-600 dark:text-purple-400 font-medium">AUDIO</span>
                  </div>
              ) :
              <div className="w-full h-full flex items-center justify-center cursor-pointer" onClick={() => onPreview(f)}>{React.createElement(Icon, {className: 'w-10 h-10 text-gray-400'})}</div>}
          {onEditCategory && (
              <div className="absolute top-2 left-8 z-10">
                <span onClick={(e) => { e.stopPropagation(); onEditCategory(f); }} className="text-[9px] px-1.5 py-0.5 rounded cursor-pointer hover:opacity-80 transition-opacity" style={{background: f.category ? 'rgba(5,150,105,0.7)' : 'rgba(107,114,128,0.5)', color: '#fff'}}>
                  {f.category || '+分类'}
                </span>
              </div>
          )}
          <div className="absolute inset-x-0 bottom-0 p-2 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
            <p className="text-xs text-white truncate">{f.original_filename}</p>
            {(f.tags || (onEditTags && !f.tags)) && (
                <div className="flex flex-wrap gap-1 mt-1 cursor-pointer hover:opacity-80" onClick={(e) => { e.stopPropagation(); onEditTags && onEditTags(f); }}>
                  {f.tags ? (f.tags as string).split(',').filter(Boolean).slice(0, 2).map((tag: string) => (
                      <span key={tag} className="text-[9px] px-1 py-0.5 rounded bg-purple-600/60 text-white/90">{tag.trim()}</span>
                  )) : <span className="text-[9px] text-white/50 italic">+标签</span>}
                </div>
            )}
          </div>
          <button onClick={() => onDelete(f)} className="absolute top-2 right-2 z-10 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100"><X className="w-3 h-3"/></button>
        </div>
    );
  };

  /* ====== 分组头部 ====== */
  const renderGroupHeader = (key: string, label: string, items: MediaFile[]) => {
    const collapsed = groupCollapsed.has(key);
    const groupSelectedAll = items.every(f => selected.includes(f.id));
    const __groupSelectedSome = items.some(f => selected.includes(f.id));
    const cleanKey = key.replace('\u0000', '');
    return (
        <div key={`header-${key}`}
             className="flex items-center gap-2 px-3 py-2.5 bg-gray-100 dark:bg-gray-800/80 rounded-xl mb-3 select-none">
          {/* 展开/折叠 */}
          <button onClick={() => toggleGroup(key)}
                  className="p-0.5 rounded hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400 transition-colors">
            {collapsed ? <ChevronRight className="w-4 h-4"/> : <ChevronDown className="w-4 h-4"/>}
          </button>

          {/* 分类名 + 数量 */}
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-200 flex-1">
            {cleanKey || '未分类'}
            <span
              className="ml-2 text-xs font-normal text-gray-400 dark:text-gray-500 dark:text-gray-400">{items.length} 项</span>
          </span>

          {/* 全选按钮 */}
          <button onClick={() => selectGroup(items)}
                  className={`px-2 py-1 rounded-lg text-xs font-medium transition-colors ${
                      groupSelectedAll
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400'
                          : 'text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                  title={groupSelectedAll ? '取消全选' : '全选本组'}>
            {groupSelectedAll ? '取消全选' : '全选'}
          </button>
        </div>
    );
  };

  /* ====== 分组列表视图 ====== */
  if (viewMode === 'list') {
    return (
        <div>
          {/* 全部展开/折叠控制条 */}
          <div className="flex items-center justify-between mb-3 px-1">
            <span className="text-xs text-gray-400">共 {files.length} 个文件，{groups.size} 个分组</span>
            <div className="flex gap-2">
              <button onClick={expandAll}
                      className={`text-xs px-2 py-1 rounded-lg transition-colors ${allExpanded ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>全部展开
              </button>
              <button onClick={collapseAll}
                      className={`text-xs px-2 py-1 rounded-lg transition-colors ${!allExpanded ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>全部折叠
              </button>
            </div>
          </div>

          {[...groups.entries()].map(([key, items]) => (
              <div key={key} className="mb-4">
                {renderGroupHeader(key, key.replace('\u0000', ''), items)}
                {!groupCollapsed.has(key) && (
                    <div className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden">
                      <table className="w-full">
                        <tbody className="divide-y">
                        {items.map(f => renderListItem(f))}
                        </tbody>
                      </table>
                    </div>
                )}
              </div>
          ))}
        </div>
    );
  }

  /* ====== 分组网格视图 ====== */
  return (
      <div>
        {/* 全部展开/折叠控制条 */}
        <div className="flex items-center justify-between mb-3 px-1">
          <span className="text-xs text-gray-400">共 {files.length} 个文件，{groups.size} 个分组</span>
          <div className="flex gap-2">
            <button onClick={expandAll}
                    className={`text-xs px-2 py-1 rounded-lg transition-colors ${allExpanded ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>全部展开
            </button>
            <button onClick={collapseAll}
                    className={`text-xs px-2 py-1 rounded-lg transition-colors ${!allExpanded ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600' : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>全部折叠
            </button>
          </div>
        </div>

        {[...groups.entries()].map(([key, items]) => (
            <div key={key} className="mb-6">
              {renderGroupHeader(key, key.replace('\u0000', ''), items)}
              {!groupCollapsed.has(key) && (
                  <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {items.map(f => renderGridItem(f))}
                  </div>
              )}
            </div>
        ))}
      </div>
  );
};

/* ---------- Audio Player with Vinyl Animation & Karaoke Lyrics ---------- */

// 将歌词行拆分为逐字/逐词 token（中文按字，英文按单词）
function tokenizeText(text: string): string[] {
  const tokens: string[] = [];
  let buf = '';
  for (const ch of text) {
    const isCJK = /[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]/.test(ch);
    if (isCJK) {
      if (buf) { tokens.push(buf); buf = ''; }
      tokens.push(ch);
    } else if (ch === ' ') {
      if (buf) { tokens.push(buf); buf = ''; }
      tokens.push(' ');
    } else {
      buf += ch;
    }
  }
  if (buf) tokens.push(buf);
  return tokens;
}

// 计算当前行的逐字高亮进度 (0..1)
function calcKaraokeProgress(
  currentTime: number,
  lineStart: number,
  nextLineStart: number | null,
): number {
  const end = nextLineStart ?? lineStart + 3;
  const duration = end - lineStart;
  if (duration <= 0) return 1;
  return Math.max(0, Math.min(1, (currentTime - lineStart) / duration));
}

const AudioPlayer: React.FC<{
  media: MediaFile;
  fullUrl: string;
  onMinimize?: () => void;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  togglePlay: () => void;
  handleSeek: (t: number) => void;
}> = ({media, fullUrl, onMinimize, audioRef, isPlaying, currentTime, duration, togglePlay, handleSeek}) => {
  const [volume, setVolume] = useState(1);
  const [showLyrics, setShowLyrics] = useState(false);
  const lyricsContainerRef = useRef<HTMLDivElement>(null);
  const vinylRef = useRef<HTMLDivElement>(null);

  // 音频元数据
  const [coverImage, setCoverImage] = useState<string | null>(null);
  const [lyrics, setLyrics] = useState<Array<{ time: number; text: string }>>([]);
  const [loadingMetadata, setLoadingMetadata] = useState(true);

  // 当前高亮行索引
  const activeLineIndex = lyrics.findIndex((l, i) => {
    const next = lyrics[i + 1];
    return currentTime >= l.time && (!next || currentTime < next.time);
  });

  // 当前行的逐字进度
  const activeLine = activeLineIndex !== -1 ? lyrics[activeLineIndex] : null;
  const karaokeProgress = activeLine
    ? calcKaraokeProgress(
        currentTime,
        activeLine.time,
        lyrics[activeLineIndex + 1]?.time ?? null,
      )
    : 0;

  // 加载音频元数据
  useEffect(() => {
    const loadMetadata = async () => {
      try {
        setLoadingMetadata(true);
        const response = await fetch(`${getConfig().API_BASE_URL}/api/v2/media/${media.id}/metadata`, {
          credentials: 'include'
        });

        if (response.ok) {
          const result = await response.json();
          if (result.success && result.data) {
            if (result.data.cover_image) {
              setCoverImage(result.data.cover_image);
            }
            if (result.data.lyrics && result.data.lyrics.length > 0) {
              setLyrics(result.data.lyrics);
              setShowLyrics(true);
            }
          }
        }
      } catch (error) {
        console.error('加载音频元数据失败:', error);
      } finally {
        setLoadingMetadata(false);
      }
    };

    loadMetadata();
  }, [media.id]);

  // 歌词自动滚动
  useEffect(() => {
    if (!showLyrics || !lyricsContainerRef.current || activeLineIndex === -1) return;
    const container = lyricsContainerRef.current;
    const el = container.children[activeLineIndex] as HTMLElement | undefined;
    if (el) {
      const target = el.offsetTop - container.clientHeight / 2 + el.clientHeight / 2;
      container.scrollTo({top: target, behavior: 'smooth'});
    }
  }, [activeLineIndex, showLyrics]);

  // togglePlay 由父组件 AudioLayer 提供
  const handleSeekEvent = (e: React.ChangeEvent<HTMLInputElement>) => {
    handleSeek(parseFloat(e.target.value));
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current;
    if (!audio) return;
    const vol = parseFloat(e.target.value);
    audio.volume = vol;
    setVolume(vol);
  };

  const formatTime = (time: number) => {
    const minutes = Math.floor(time / 60);
    const seconds = Math.floor(time % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
  };

  // 扩展控制状态
  const [repeatMode, setRepeatMode] = useState<'off' | 'one' | 'all'>('off');
  const [isLiked, setIsLiked] = useState(false);
  const [showPlaylist, setShowPlaylist] = useState(false);
  const [showVolumeSlider, setShowVolumeSlider] = useState(false);

  return (
      <div className="flex flex-col h-full bg-black select-none">

        {/* ====== Main Content Area ====== */}
        <div className="flex-1 flex flex-col lg:flex-row min-h-0 overflow-hidden">
          {/* 最小化按钮 (桌面左上角) */}
          <button
              onClick={onMinimize}
              className="absolute top-4 left-4 z-20 w-8 h-8 rounded-full bg-white/5 hover:bg-white/15 backdrop-blur flex items-center justify-center transition-colors hidden lg:flex"
              aria-label="最小化播放"
              title="最小化 (Esc)"
          >
            <svg className="w-4 h-4 text-white/70" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"/>
            </svg>
          </button>

          {/* --- Left: Vinyl (hidden on mobile, shown lg+) --- */}
          <div className="hidden lg:flex w-[45%] items-center justify-center relative overflow-hidden">
            {/* Background glow */}
            <motion.div
                className="absolute inset-0"
                animate={{opacity: isPlaying ? 0.3 : 0.06}}
                transition={{duration: 1}}
            >
              <motion.div
                  className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] aspect-square rounded-full blur-3xl"
                  style={{background: 'radial-gradient(circle, rgba(147,51,234,0.5), rgba(236,72,153,0.2), transparent)'}}
                  animate={isPlaying ? {
                    scale: [1, 1.1, 1],
                    opacity: [0.3, 0.6, 0.3],
                  } : {scale: 1, opacity: 0.2}}
                  transition={isPlaying ? {
                    duration: 4,
                    repeat: Infinity,
                    ease: 'easeInOut',
                  } : {duration: 0.6}}
              />
            </motion.div>

            {/* Vinyl + Tone arm container — 点击唱片可最小化 */}
            <div className="relative cursor-pointer" onClick={onMinimize}>
              {/* 唱臂 */}
              <motion.div
                  className="absolute -top-8 -right-8 z-10"
                  style={{transformOrigin: '16px 100%'}}
                  animate={{rotate: isPlaying ? 18 : -35}}
                  transition={{type: 'spring', stiffness: 90, damping: 14}}
              >
                <svg width="110" height="48" viewBox="0 0 110 48" fill="none">
                  <rect x="16" y="10" width="94" height="4" rx="2" fill="url(#armGrad2)" />
                  <circle cx="16" cy="12" r="10" fill="#555" stroke="#333" strokeWidth="1.5" />
                  <circle cx="16" cy="12" r="4" fill="#222" />
                  <circle cx="16" cy="12" r="1.5" fill="#888" />
                  <rect x="92" y="2" width="18" height="20" rx="3" fill="#555" />
                  <circle cx="101" cy="12" r="3" fill="#777" />
                  <defs>
                    <linearGradient id="armGrad2" x1="0" y1="0" x2="1" y2="0">
                      <stop offset="0%" stopColor="#999" />
                      <stop offset="50%" stopColor="#666" />
                      <stop offset="100%" stopColor="#444" />
                    </linearGradient>
                  </defs>
                </svg>
              </motion.div>

              {/* 黑胶唱片 */}
              <motion.div
                  ref={vinylRef}
                  className="w-72 h-72 xl:w-80 xl:h-80 rounded-full bg-gradient-to-br from-gray-800 via-gray-900 to-black shadow-2xl flex items-center justify-center relative"
                  style={{
                    boxShadow: isPlaying
                      ? '0 0 100px rgba(147, 51, 234, 0.35), inset 0 0 80px rgba(0,0,0,0.6)'
                      : '0 0 50px rgba(147, 51, 234, 0.1), inset 0 0 80px rgba(0,0,0,0.6)',
                  }}
                  animate={{rotate: isPlaying ? 360 : 0}}
                  transition={isPlaying
                    ? {duration: 8, ease: 'linear', repeat: Infinity}
                    : {duration: 0.6, ease: 'easeOut'}
                  }
              >
                {/* 纹路 */}
                {[5, 10, 15, 20, 25, 30, 35].map(i => (
                    <div key={i}
                         className="absolute rounded-full border border-gray-700/20"
                         style={{inset: `${i * 4}px`}}
                    />
                ))}

                {/* 反光 */}
                <div className="absolute inset-2 rounded-full bg-gradient-to-br from-white/[0.06] via-transparent to-transparent pointer-events-none" />

                {/* 中心标签 */}
                <div className="w-28 h-28 xl:w-32 xl:h-32 rounded-full overflow-hidden shadow-lg relative z-10 ring-2 ring-white/10">
                  {coverImage ? (
                      <img
                          src={coverImage}
                          alt="cover"
                          className="w-full h-full object-cover"
                      />
                  ) : (
                      <div className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                        {loadingMetadata ? (
                            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"/>
                        ) : (
                            <Music className="w-7 h-7 text-white/80"/>
                        )}
                      </div>
                  )}
                </div>

                {/* 中心孔 */}
                <div className="absolute w-3 h-3 bg-black rounded-full z-20 border border-gray-700/50" />
              </motion.div>
            </div>
          </div>

          {/* --- Right: Lyrics Area (Apple Music style) --- */}
          <div className="flex-1 flex flex-col min-h-0 relative">
            {/* 手机版：顶部封面缩略 + 歌名 */}
            <div className="lg:hidden flex items-center gap-4 p-5 border-b border-white/10">
              <motion.button
                  className="shrink-0"
                  whileTap={{scale: 0.9}}
                  onClick={onMinimize}
                  aria-label="最小化"
              >
                <svg className="w-5 h-5 text-white/50" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7"/>
                </svg>
              </motion.button>
              <div className="w-14 h-14 rounded-xl overflow-hidden shadow-lg shrink-0">
                {coverImage ? (
                    <img src={coverImage} alt="cover" className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                      <Music className="w-6 h-6 text-white/80"/>
                    </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-white font-semibold truncate text-base">{media.original_filename}</p>
                <p className="text-white/50 text-xs truncate">FastBlog Audio</p>
              </div>
            </div>

            {/* 歌词标题 */}
            <div className="px-6 pt-5 pb-2 flex items-center justify-between">
              <button
                  onClick={() => setShowLyrics(!showLyrics)}
                  className="flex items-center gap-2 text-sm font-medium transition-colors"
                  style={{color: showLyrics ? '#a855f7' : 'rgba(255,255,255,0.4)'}}
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/>
                </svg>
                歌词
              </button>
              {showLyrics && lyrics.length > 0 && (
                  <span className="text-xs text-white/30">{lyrics.length} 行</span>
              )}
            </div>

            {/* 歌词内容 */}
            <div className="flex-1 overflow-hidden px-4">
              {showLyrics ? (
                  <div
                      ref={lyricsContainerRef}
                      className="h-full overflow-y-auto space-y-3 py-2 scrollbar-thin"
                      style={{scrollbarWidth: 'thin'}}
                  >
                    {lyrics.length > 0 ? (
                        lyrics.map((lyric, index) => {
                          const isActive = index === activeLineIndex;
                          const isPast = index < activeLineIndex;
                          const tokens = tokenizeText(lyric.text);
                          const highlightCount = isActive
                              ? Math.floor(tokens.length * karaokeProgress)
                              : (isPast ? tokens.length : 0);

                          return (
                              <div key={index} className="relative px-4 py-2 transition-all duration-300 min-h-[2.5rem]"
                                   style={{
                                     opacity: isPast ? 0.5 : (isActive ? 1 : 0.35),
                                     transform: isActive ? 'scale(1)' : 'scale(0.96)',
                                   }}
                              >
                                {/* 背景进度条 */}
                                {isActive && (
                                    <motion.div
                                        className="absolute inset-0 rounded-xl bg-gradient-to-r from-purple-500/8 via-pink-500/8 to-transparent pointer-events-none"
                                        animate={{width: `${karaokeProgress * 100}%`}}
                                        transition={{duration: 0.08, ease: 'linear'}}
                                    />
                                )}

                                <div className={`text-center leading-relaxed ${isActive ? 'text-xl font-bold tracking-wide' : 'text-sm'}`}>
                                  {tokens.map((token, ti) => {
                                    const isHighlighted = ti < highlightCount;
                                    const isTransitioning = isActive && ti === highlightCount - 1 && karaokeProgress < 1;
                                    const isNextToken = isActive && ti === highlightCount;
                                    const tokenClipProgress = isTransitioning
                                        ? (karaokeProgress * tokens.length - ti)
                                        : (isHighlighted ? 1 : 0);

                                    return token === ' ' ? (
                                        <span key={ti} className="inline-block" style={{width: '0.3em'}}>&nbsp;</span>
                                    ) : (
                                        <span key={ti} className="relative inline-block mx-[0.5px]">
                                      {/* 未高亮层 */}
                                      <span className={`transition-all duration-150 ${isHighlighted ? 'text-transparent' : 'text-white/50'}`}>
                                        {token}
                                      </span>
                                          {/* 高亮渐变层 */}
                                          {isHighlighted && (
                                              <span className="absolute inset-0 bg-gradient-to-r from-purple-400 via-fuchsia-300 to-pink-300 bg-clip-text text-transparent"
                                                    style={{
                                                      WebkitBackgroundClip: 'text',
                                                      filter: isActive ? 'drop-shadow(0 0 10px rgba(168,85,247,0.5))' : 'none',
                                                    }}
                                              >
                                            {token}
                                          </span>
                                          )}
                                          {/* 过渡 clipPath */}
                                          {isTransitioning && (
                                              <span className="absolute inset-0 overflow-hidden" style={{color: 'transparent'}}>
                                            <span className="absolute inset-0 bg-gradient-to-r from-purple-400 via-fuchsia-300 to-pink-300 bg-clip-text text-transparent"
                                                  style={{
                                                    WebkitBackgroundClip: 'text',
                                                    clipPath: `inset(0 ${(1 - tokenClipProgress) * 100}% 0 0)`,
                                                    filter: 'drop-shadow(0 0 12px rgba(168,85,247,0.7))',
                                                  }}
                                            >
                                              {token}
                                            </span>
                                          </span>
                                          )}
                                          {/* 下一个字脉冲 */}
                                          {isNextToken && (
                                              <motion.span
                                                  className="absolute inset-0 text-white/50"
                                                  animate={{opacity: [0.3, 0.7, 0.3]}}
                                                  transition={{duration: 1.2, repeat: Infinity, ease: 'easeInOut'}}
                                              >
                                                {token}
                                              </motion.span>
                                          )}
                                    </span>
                                    );
                                  })}
                                </div>
                              </div>
                          );
                        })
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-white/30">
                          <Music className="w-12 h-12 mb-4 opacity-40"/>
                          <p className="text-sm">暂无歌词</p>
                          <p className="text-xs mt-1">支持在音频文件同目录下放置 .lrc 文件</p>
                        </div>
                    )}
                  </div>
              ) : (
                  <div className="flex flex-col items-center justify-center h-full text-white/20">
                    <svg className="w-16 h-16 mb-4 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/>
                    </svg>
                    <p className="text-sm">点击上方「歌词」查看逐字高亮</p>
                  </div>
              )}
            </div>
          </div>
        </div>

        {/* ====== Bottom Controls Bar (Apple Music style) ====== */}
        <div className="flex-shrink-0 bg-black/90 backdrop-blur-2xl border-t border-white/10"
             style={{paddingBottom: 'env(safe-area-inset-bottom, 0px)'}}>
          {/* --- Progress Bar (touch-friendly, thin visual + large tap target) --- */}
          <div className="px-4 pt-3 pb-1">
            <div className="relative h-6 flex items-center -my-1">
              <input
                  type="range"
                  min="0"
                  max={duration || 100}
                  value={currentTime}
                  onChange={handleSeekEvent}
                  className="absolute inset-0 w-full h-full appearance-none bg-transparent cursor-pointer z-10 opacity-0"
                  style={{touchAction: 'none'}}
                  aria-label="播放进度"
              />
              {/* 视觉进度条 */}
              <div className="w-full h-1 rounded-full bg-white/15 overflow-hidden pointer-events-none">
                <div
                    className="h-full rounded-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-75"
                    style={{width: `${duration ? (currentTime / duration) * 100 : 0}%`}}
                />
              </div>
            </div>
            <div className="flex justify-between text-[11px] text-white/30 mt-0.5 px-0.5">
              <span>{formatTime(currentTime)}</span>
              <span>{formatTime(duration)}</span>
            </div>
          </div>

          {/* --- Controls Row --- */}
          <div className="flex items-center justify-between px-5 pb-3 gap-2">
            {/* Left: song info */}
            <div className="flex items-center gap-3 min-w-0 flex-1">
              <motion.div
                  className="w-10 h-10 rounded-lg overflow-hidden shadow shrink-0 cursor-pointer"
                  whileTap={{scale: 0.9}}
                  onClick={onMinimize}
                  title="最小化播放 (Esc)"
                  aria-label="最小化播放"
              >
                {coverImage ? (
                    <img src={coverImage} alt="" className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                      <Music className="w-5 h-5 text-white/70"/>
                    </div>
                )}
              </motion.div>
              <div className="min-w-0 max-w-[140px]">
                <p className="text-white text-sm font-medium truncate">{media.original_filename}</p>
                <p className="text-white/40 text-xs truncate">FastBlog</p>
              </div>
              {/* Like button */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => setIsLiked(!isLiked)}
                  className="shrink-0"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill={isLiked ? '#ec4899' : 'none'} stroke={isLiked ? '#ec4899' : 'rgba(255,255,255,0.4)'} strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
                </svg>
              </motion.button>
            </div>

            {/* Center: Playback controls — 标准三键布局 + 附加键 (桌面) */}
            <div className="flex items-center justify-center gap-1 sm:gap-3">
              {/* Rewind 10s (仅桌面) */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => handleSeek(Math.max(0, currentTime - 10))}
                  className="text-white/50 hover:text-white transition-colors p-2 min-w-[44px] min-h-[44px] items-center justify-center hidden sm:flex"
                  aria-label="后退10秒"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M11 18V6l-8.5 6 8.5 6zm.5-6l8.5 6V6l-8.5 6z"/></svg>
              </motion.button>

              {/* Prev (restart) */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => handleSeek(0)}
                  className="text-white/50 hover:text-white transition-colors p-2 min-w-[44px] min-h-[44px] flex items-center justify-center"
                  aria-label="重新播放"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>
              </motion.button>

              {/* Play/Pause (large) */}
              <motion.button
                  whileTap={{scale: 0.9}}
                  onClick={togglePlay}
                  className="w-12 h-12 sm:w-11 sm:h-11 bg-white rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all mx-1"
                  aria-label={isPlaying ? '暂停' : '播放'}
              >
                {isPlaying ? (
                    <svg className="w-5 h-5 text-black" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
                    </svg>
                ) : (
                    <svg className="w-5 h-5 text-black ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M8 5v14l11-7z"/>
                    </svg>
                )}
              </motion.button>

              {/* Next (skip 10s) */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => handleSeek(Math.min(duration, currentTime + 10))}
                  className="text-white/50 hover:text-white transition-colors p-2 min-w-[44px] min-h-[44px] flex items-center justify-center"
                  aria-label="前进10秒"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M4 18l8.5-6L4 6v12zm9-12v12l8.5-6L13 6z"/></svg>
              </motion.button>

              {/* Forward 10s (仅桌面) */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => handleSeek(Math.min(duration, currentTime + 10))}
                  className="text-white/50 hover:text-white transition-colors p-2 min-w-[44px] min-h-[44px] items-center justify-center hidden sm:flex"
                  aria-label="快进10秒"
              >
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M13 6v12l8.5-6L13 6zM4 18l8.5-6L4 6v12z"/></svg>
              </motion.button>
            </div>

            {/* Right: Volume & extras */}
            <div className="flex items-center justify-end gap-1 sm:gap-3 flex-1">
              {/* Repeat (hidden on mobile) */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => setRepeatMode(r => r === 'off' ? 'all' : r === 'all' ? 'one' : 'off')}
                  className="relative hidden sm:block p-2 min-w-[44px] min-h-[44px]"
                  aria-label={`循环模式: ${repeatMode === 'off' ? '关闭' : repeatMode === 'all' ? '全部循环' : '单曲循环'}`}
              >
                <svg className="w-4 h-4 mx-auto" viewBox="0 0 24 24" fill="none" stroke={repeatMode !== 'off' ? '#a855f7' : 'rgba(255,255,255,0.4)'} strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                </svg>
                {repeatMode === 'one' && (
                    <span className="absolute top-0 right-0 w-3 h-3 bg-purple-500 rounded-full flex items-center justify-center text-[8px] font-bold text-white">1</span>
                )}
              </motion.button>

              {/* Volume (hidden on mobile) */}
              <div className="relative hidden sm:flex items-center">
                <motion.button
                    whileTap={{scale: 0.85}}
                    onClick={() => setShowVolumeSlider(v => !v)}
                    className="p-2 min-w-[44px] min-h-[44px] flex items-center justify-center"
                    aria-label="音量"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"/>
                  </svg>
                </motion.button>
                {showVolumeSlider && (
                    <div className="absolute bottom-full right-0 mb-2 p-3 bg-neutral-900/95 backdrop-blur-xl rounded-xl border border-white/10 shadow-xl">
                      <input
                          type="range"
                          min="0"
                          max="1"
                          step="0.01"
                          value={volume}
                          onChange={handleVolumeChange}
                          className="w-24 h-1.5 bg-white/20 rounded-full appearance-none cursor-pointer accent-purple-500"
                          style={{
                            background: `linear-gradient(to right, #a855f7 ${volume * 100}%, rgba(255,255,255,0.15) ${volume * 100}%)`,
                          }}
                          aria-label="音量滑块"
                      />
                    </div>
                )}
              </div>

              {/* Mobile: 歌词快捷切换 */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => setShowLyrics(!showLyrics)}
                  className="sm:hidden p-2 min-w-[44px] min-h-[44px] flex items-center justify-center"
                  aria-label={showLyrics ? '隐藏歌词' : '显示歌词'}
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke={showLyrics ? '#a855f7' : 'rgba(255,255,255,0.4)'} strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/>
                </svg>
              </motion.button>

              {/* Playlist toggle (hidden on mobile) */}
              <motion.button
                  whileTap={{scale: 0.85}}
                  onClick={() => setShowPlaylist(!showPlaylist)}
                  className="hidden sm:block p-2 min-w-[44px] min-h-[44px]"
                  aria-label="播放列表"
              >
                <svg className="w-4 h-4 mx-auto" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.4)" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01"/>
                </svg>
              </motion.button>
            </div>
          </div>
        </div>
      </div>
  );
};

/* ========== MiniPlayer (最小化播放) ========== */
const MiniPlayer: React.FC<{
  media: MediaFile;
  fullUrl: string;
  isPlaying: boolean;
  onTogglePlay: () => void;
  onRestore: () => void;
  onClose: () => void;
  coverImage: string | null;
  currentTime: number;
  duration: number;
  formatTime: (t: number) => string;
  audioRef: React.RefObject<HTMLAudioElement | null>;
}> = ({media, fullUrl, isPlaying, onTogglePlay, onRestore, onClose, coverImage, currentTime, duration, formatTime, audioRef}) => {
  const [showMenu, setShowMenu] = useState(false);
  const longPressTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 长按处理（移动端）
  const handleTouchStart = () => {
    longPressTimer.current = setTimeout(() => setShowMenu(true), 500);
  };
  const handleTouchEnd = () => {
    if (longPressTimer.current) clearTimeout(longPressTimer.current);
  };

  // 点击外部关闭菜单
  useEffect(() => {
    if (!showMenu) return;
    const handler = () => setShowMenu(false);
    window.addEventListener('click', handler);
    return () => window.removeEventListener('click', handler);
  }, [showMenu]);

  return (
      <>
        {/* 桌面端：左下角迷你卡片 */}
        <motion.div
            initial={{x: -100, opacity: 0}}
            animate={{x: 0, opacity: 1}}
            exit={{x: -100, opacity: 0}}
            className="hidden sm:flex fixed bottom-4 left-4 z-[60] bg-black/90 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden"
            style={{paddingBottom: 'env(safe-area-inset-bottom, 0px)'}}
        >
          <div className="flex items-center gap-3 p-3 min-w-[260px] max-w-[320px]">
            {/* 封面 */}
            <motion.div
                className="w-12 h-12 rounded-xl overflow-hidden shrink-0 cursor-pointer"
                whileTap={{scale: 0.9}}
                onClick={onRestore}
                animate={isPlaying ? {rotate: 360} : {rotate: 0}}
                transition={isPlaying ? {duration: 8, ease: 'linear', repeat: Infinity} : {duration: 0.4}}
            >
              {coverImage ? (
                  <img src={coverImage} alt="" className="w-full h-full object-cover"/>
              ) : (
                  <div className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                    <Music className="w-6 h-6 text-white/70"/>
                  </div>
              )}
            </motion.div>

            {/* 歌名 + 进度条 */}
            <div className="flex-1 min-w-0">
              <p className="text-white text-sm font-medium truncate cursor-pointer" onClick={onRestore}>{media.original_filename}</p>
              <div className="w-full h-0.5 rounded-full bg-white/10 mt-1.5 overflow-hidden">
                <div className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-200"
                     style={{width: `${duration ? (currentTime / duration) * 100 : 0}%`}}
                />
              </div>
            </div>

            {/* 控制按钮 */}
            <div className="flex items-center gap-1">
              <motion.button whileTap={{scale: 0.85}} onClick={onTogglePlay}
                             className="w-9 h-9 bg-white/10 hover:bg-white/20 rounded-full flex items-center justify-center transition-colors"
                             aria-label={isPlaying ? '暂停' : '播放'}>
                {isPlaying ? (
                    <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
                ) : (
                    <svg className="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                )}
              </motion.button>
              <motion.button whileTap={{scale: 0.85}} onClick={onClose}
                             className="w-9 h-9 bg-white/5 hover:bg-white/15 rounded-full flex items-center justify-center transition-colors"
                             aria-label="关闭">
                <svg className="w-4 h-4 text-white/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </motion.button>
            </div>
          </div>
        </motion.div>

        {/* 移动端：右上角黑胶迷你播放器 */}
        <motion.div
            initial={{y: -80, opacity: 0}}
            animate={{y: 0, opacity: 1}}
            exit={{y: -80, opacity: 0}}
            className="sm:hidden fixed top-4 right-4 z-[60]"
            onTouchStart={handleTouchStart}
            onTouchEnd={handleTouchEnd}
            onClick={onTogglePlay}
        >
          <motion.div
              className="w-16 h-16 rounded-full overflow-hidden shadow-2xl border-2 border-white/20 cursor-pointer relative"
              animate={isPlaying ? {rotate: 360} : {rotate: 0}}
              transition={isPlaying ? {duration: 8, ease: 'linear', repeat: Infinity} : {duration: 0.4}}
          >
            {coverImage ? (
                <img src={coverImage} alt="" className="w-full h-full object-cover"/>
            ) : (
                <div className="w-full h-full bg-gradient-to-br from-purple-600 to-pink-600 flex items-center justify-center">
                  <Music className="w-8 h-8 text-white/80"/>
                </div>
            )}

            {/* 底部半透明条显示歌名 */}
            <div className="absolute inset-x-0 bottom-0 h-5 bg-black/50 backdrop-blur flex items-center justify-center px-1">
              <p className="text-[9px] text-white font-medium truncate leading-none">{media.original_filename}</p>
            </div>
          </motion.div>
        </motion.div>

        {/* 长按菜单 (移动端) */}
        {showMenu && (
            <div className="sm:hidden fixed z-[70] inset-0 bg-black/40 flex items-end justify-center pb-20"
                 onClick={() => setShowMenu(false)}>
              <motion.div
                  initial={{y: 100, opacity: 0}}
                  animate={{y: 0, opacity: 1}}
                  className="bg-neutral-900/95 backdrop-blur-2xl rounded-2xl w-64 p-4 border border-white/10 shadow-2xl"
                  onClick={e => e.stopPropagation()}
              >
                <p className="text-white font-semibold text-center mb-4 truncate">{media.original_filename}</p>
                <div className="space-y-2">
                  <button onClick={() => { setShowMenu(false); onRestore(); }}
                          className="w-full py-3 px-4 bg-white/10 hover:bg-white/20 rounded-xl text-white text-sm font-medium transition-colors flex items-center gap-3">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
                    </svg>
                    展开播放器
                  </button>
                  <button onClick={() => { setShowMenu(false); onClose(); }}
                          className="w-full py-3 px-4 bg-red-500/20 hover:bg-red-500/30 rounded-xl text-red-400 text-sm font-medium transition-colors flex items-center gap-3">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                    关闭播放
                  </button>
                </div>
              </motion.div>
            </div>
        )}

      </>
  );
};

/* ========== MiniPlayerWrapper (使用共享 audioRef) ========== */
const MiniPlayerWrapper: React.FC<{
  media: MediaFile;
  fullUrl: string;
  onRestore: () => void;
  onClose: () => void;
  audioRef: React.RefObject<HTMLAudioElement | null>;
  isPlaying: boolean;
  currentTime: number;
  duration: number;
  togglePlay: () => void;
  handleSeek?: (t: number) => void;
}> = ({media, fullUrl, onRestore, onClose, audioRef, isPlaying, currentTime, duration, togglePlay}) => {
  const [coverImage, setCoverImage] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${getConfig().API_BASE_URL}/api/v2/media/${media.id}/metadata`, {credentials: 'include'})
        .then(r => r.json())
        .then(result => {
          if (result.success && result.data?.cover_image) setCoverImage(result.data.cover_image);
        })
        .catch(() => {});
  }, [media.id]);

  const formatTime = (t: number) => {
    const m = Math.floor(t / 60);
    const s = Math.floor(t % 60);
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
      <MiniPlayer
          media={media}
          fullUrl={fullUrl}
          isPlaying={isPlaying}
          onTogglePlay={togglePlay}
          onRestore={onRestore}
          onClose={onClose}
          coverImage={coverImage}
          currentTime={currentTime}
          duration={duration}
          formatTime={formatTime}
          audioRef={audioRef}
      />
  );
};

/* ========== DesktopLyrics (桌面歌词浮动窗口) ========== */
/* ========== AudioLayer (持久音频层) ========== */
const AudioLayer: React.FC<{ media: MediaFile; onClose: () => void }> = ({media, onClose}) => {
  const fullUrl = getFullMediaUrl(media.url);
  const [minimized, setMinimized] = useState(false);

  // 共享 audio 元素 — 全程由 AudioLayer 持有
  const audioRef = useRef<HTMLAudioElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [lyrics, setLyrics] = useState<Array<{ time: number; text: string }>>([]);

  // 歌词高亮状态
  const [activeLineIndex, setActiveLineIndex] = useState(-1);
  const [karaokeProgress, setKaraokeProgress] = useState(0);

  // 桌面歌词设置
  const [showDesktopLyrics, setShowDesktopLyrics] = useState(false);

  // audio 事件监听
  useEffect(() => {
    const a = audioRef.current;
    if (!a) return;
    const onTime = () => setCurrentTime(a.currentTime);
    const onDur = () => setDuration(a.duration);
    const onPlay = () => setIsPlaying(true);
    const onPause = () => setIsPlaying(false);
    const onEnd = () => setIsPlaying(false);
    a.addEventListener('timeupdate', onTime);
    a.addEventListener('loadedmetadata', onDur);
    a.addEventListener('play', onPlay);
    a.addEventListener('pause', onPause);
    a.addEventListener('ended', onEnd);
    return () => { a.removeEventListener('timeupdate', onTime); a.removeEventListener('loadedmetadata', onDur); a.removeEventListener('play', onPlay); a.removeEventListener('pause', onPause); a.removeEventListener('ended', onEnd); };
  }, []);

  const togglePlay = () => {
    const a = audioRef.current;
    if (!a) return;
    if (isPlaying) a.pause(); else a.play();
  };

  const handleSeek = (time: number) => {
    const a = audioRef.current;
    if (a) a.currentTime = time;
  };

  // 加载元数据
  useEffect(() => {
    fetch(`${getConfig().API_BASE_URL}/api/v2/media/${media.id}/metadata`, {credentials: 'include'})
        .then(r => r.json())
        .then(result => {
          if (result.success && result.data) {
            if (result.data.lyrics?.length) setLyrics(result.data.lyrics);
          }
        })
        .catch(() => {});
  }, [media.id]);

  // 桌面歌词默认关闭，用户通过按钮开启
  useEffect(() => {
    // 不再从 localStorage 读取 visible 状态，由用户主动触发
  }, [lyrics]);

  // 更新歌词高亮
  useEffect(() => {
    if (!lyrics.length) return;
    const idx = lyrics.findIndex((l, i) => {
      const next = lyrics[i + 1];
      return currentTime >= l.time && (!next || currentTime < next.time);
    });
    setActiveLineIndex(idx);
    if (idx >= 0) {
      const line = lyrics[idx];
      const nextTime = lyrics[idx + 1]?.time ?? line.time + 3;
      const progress = Math.max(0, Math.min(1, (currentTime - line.time) / (nextTime - line.time)));
      setKaraokeProgress(progress);
    }
  }, [currentTime, lyrics]);

  // ESC 切换最小化
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMinimized(m => !m);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  // 共享给子组件
  const sharedAudioProps = {
    audioRef,
    isPlaying,
    currentTime,
    duration,
    togglePlay,
    handleSeek,
  };

  return (
      <>
        {/* audio 永远在这个位置，不被条件分支卸载 */}
        <audio ref={audioRef} src={fullUrl} preload="auto"/>

        {minimized ? (
            <>
              <DesktopLyrics
                  lyrics={lyrics}
                  activeLineIndex={activeLineIndex}
                  karaokeProgress={karaokeProgress}
                  visible={showDesktopLyrics}
                  onVisibilityChange={setShowDesktopLyrics}
              />
              {/* 桌面歌词开关（stopPropagation 防止误触 MiniPlayer 的 togglePlay） */}
              {lyrics.length > 0 && (
                  <button
                      onClick={(e) => { e.stopPropagation(); setShowDesktopLyrics(v => !v); }}
                      onPointerDown={(e) => e.stopPropagation()}
                      className="fixed bottom-24 right-4 z-[66] w-9 h-9 rounded-full bg-black/60 backdrop-blur border border-white/10 flex items-center justify-center hover:bg-white/10 transition-colors"
                      aria-label="桌面歌词"
                      title="桌面歌词"
                  >
                    <svg className="w-4 h-4 text-white/70" fill="none" viewBox="0 0 24 24" stroke={showDesktopLyrics ? '#a855f7' : 'currentColor'} strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/>
                    </svg>
                  </button>
              )}
              <MiniPlayerWrapper
                  media={media}
                  fullUrl={fullUrl}
                  onRestore={() => setMinimized(false)}
                  onClose={onClose}
                  {...sharedAudioProps}
              />
            </>
        ) : (
            <div className="fixed inset-0 z-50 flex flex-col bg-black">
              <AudioPlayer
                  media={media}
                  fullUrl={fullUrl}
                  onMinimize={() => setMinimized(true)}
                  {...sharedAudioProps}
              />
            </div>
        )}
      </>
  );
};

/* ---------- PreviewModal (仅非音频) ---------- */
const PreviewModal: React.FC<{media: MediaFile|null; onClose: ()=>void}> = ({media, onClose}) => {
  if(!media) return null;
  const fullUrl = getFullMediaUrl(media.url);

  // ESC 关闭
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [onClose]);

  return (<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80" onClick={onClose}>
    <div
        className="w-[90vw] max-w-7xl max-h-[95vh] bg-white dark:bg-gray-900 rounded-2xl overflow-hidden shadow-2xl flex flex-col"
        onClick={e => e.stopPropagation()}>
      {media.mime_type === 'application/pdf' && fullUrl ? (
          <div className="flex-1 bg-gray-100 dark:bg-gray-800 min-h-[80vh]">
            <embed src={fullUrl} type="application/pdf" className="w-full h-full" style={{minHeight: '80vh', maxHeight: '85vh'}}/>
          </div>
      ) : media.mime_type?.startsWith('video/') && fullUrl ? (
        <div className="bg-black flex-1 flex items-center justify-center">
          <video src={fullUrl} controls autoPlay preload="auto"
                 className="max-w-full max-h-[85vh] w-full h-full object-contain" playsInline>您的浏览器不支持视频播放
          </video>
        </div>
      ) : media.mime_type?.startsWith('image/') && fullUrl ? (
          <img src={fullUrl} alt={media.original_filename} className="max-w-full max-h-[70vh] object-contain" loading="eager" decoding="async"/>
      ) : (
          <div className="p-16 text-center"><FileText className="w-16 h-16 text-gray-400 mx-auto mb-4"/><p className="text-gray-600">{media.original_filename}</p></div>
      )}
      <div className="p-6 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
        <h3 className="font-bold text-gray-900 dark:text-white">{media.original_filename}</h3>
        <p
          className="text-sm text-gray-500 dark:text-gray-400 mt-1">{media.file_size ? `${(media.file_size / 1024).toFixed(1)} KB` : ''} · {media.mime_type}</p>
      </div>
    </div>
  </div>);
};

const DeleteConfirm: React.FC<{item: MediaFile; onCancel: ()=>void; onConfirm: ()=>void}> = ({item, onCancel, onConfirm}) => (
  <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onCancel}>
    <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 max-w-sm w-full shadow-xl" onClick={e=>e.stopPropagation()}>
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">确认删除</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">确定要删除 <span
        className="font-medium">{item.original_filename}</span> 吗？</p>
      <div className="flex justify-end gap-3"><button onClick={onCancel} className="px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm font-medium">取消</button><button onClick={onConfirm} className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700">删除</button></div>
    </div>
  </div>
);

const MoveDialog: React.FC<{open: boolean; onClose: ()=>void; folders: FolderNode[]; mediaCount: number; onMove: (folderPath: string|null)=>void}> = ({open, onClose, folders, mediaCount, onMove}) => {
  if(!open) return null;
  const renderNode = (node: FolderNode, depth=0) => (
    <button key={node.id} onClick={()=>onMove(node.name)} className="w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-500 transition-colors" style={{paddingLeft:`${16+depth*20}px`}}>
      <FolderClosed className="w-5 h-5 text-yellow-600"/> <span className="font-medium">{node.name}</span>
    </button>
  );
  return (<div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
    <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 max-w-md w-full shadow-xl" onClick={e=>e.stopPropagation()}>
      <h3 className="text-lg font-bold mb-2">移动文件</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">将选中的 {mediaCount} 个文件移动到：</p>
      <div className="space-y-2 max-h-64 overflow-y-auto mb-4">
        <button onClick={()=>onMove(null)} className="w-full flex items-center gap-3 px-4 py-3 text-left rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-blue-50 dark:hover:bg-blue-900/20 hover:border-blue-500 transition-colors">
          <Grid3X3 className="w-5 h-5 text-gray-500 dark:text-gray-400"/><span className="font-medium">根目录</span>
        </button>
        {folders.map(n=>renderNode(n))}
      </div>
      <div className="flex justify-end"><button onClick={onClose} className="px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm font-medium">取消</button></div>
    </div>
  </div>);
};

const CreateFolderDialog: React.FC<{open: boolean; onClose: ()=>void; onCreate: (name: string)=>void}> = ({open, onClose, onCreate}) => {
  const [name, setName] = useState('');
  if(!open) return null;
  return (<div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
    <div className="bg-white dark:bg-gray-900 rounded-2xl p-6 max-w-sm w-full shadow-xl" onClick={e=>e.stopPropagation()}>
      <h3 className="text-lg font-bold mb-4">新建文件夹</h3>
      <input type="text" value={name} onChange={e=>setName(e.target.value)} placeholder="文件夹名称" className="w-full px-4 py-3 border border-gray-200 dark:border-gray-700 rounded-xl bg-gray-50 dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white mb-4" autoFocus onKeyDown={e=>{if(e.key==='Enter' && name.trim()) {onCreate(name.trim()); setName('');}}}/>
      <div className="flex justify-end gap-3"><button onClick={onClose} className="px-4 py-2 bg-gray-100 dark:bg-gray-800 rounded-lg text-sm font-medium">取消</button><button onClick={()=>{if(name.trim()){onCreate(name.trim()); setName('');}}} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">创建</button></div>
    </div>
  </div>);
};

/* ---------- Upload hook ---------- */
const useMediaUpload = (onComplete?: () => void) => {
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState('');
  const uploadFiles = async (files: File[]) => {
    if (!files.length) return;
    setUploading(true); setUploadProgress(0); setUploadStatus(`开始上传 ${files.length} 个文件...`);
    try {
      for (let i = 0; i < files.length; i++) {
        await MediaService.uploadMediaFileWithProgress(files[i], (p) => { setUploadProgress(((i/files.length)*100)+(p/files.length)); });
        setUploadStatus(`已上传: ${files[i].name} (${i+1}/${files.length})`);
      }
      setUploadStatus('上传完成!'); if (onComplete) onComplete();
    } catch (e: any) { setUploadStatus(`上传失败: ${e.message}`); }
    finally { setTimeout(()=>{setUploading(false);setUploadProgress(0);setUploadStatus('');},2000); }
  };
  return {uploading, uploadProgress, uploadStatus, uploadFiles};
};

/* ========== Main MediaPage ========== */
const MediaPage: React.FC = () => {
  const confirm = useConfirm();
  const [files, setFiles] = useState<MediaFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filterType, setFilterType] = useState('');
  const [search, setSearch] = useState('');
  const [viewMode, setViewMode] = useState<'grid'|'list'>('grid');
  const [selected, setSelected] = useState<number[]>([]);
  const [previewMedia, setPreviewMedia] = useState<MediaFile|null>(null);
  const [nowPlaying, setNowPlaying] = useState<MediaFile|null>(null);
  const [deleteItem, setDeleteItem] = useState<MediaFile|null>(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [uploadCollapsed, setUploadCollapsed] = useState(true);
  const [stats, setStats] = useState<any>({});
  // Folder state
  const [folders, setFolders] = useState<FolderNode[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<number|null>(null);
  const [folderLoading, setFolderLoading] = useState(true);
  const [showCreateFolder, setShowCreateFolder] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);

  // Tags & Categories state
    const [allTags, setAllTags] = useState<{ id: string; name: string }[]>([]);
    const [allCategories, setAllCategories] = useState<{ id: string; name: string; count?: number }[]>([]);
    const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
    const [selectedCategoryId, setSelectedCategoryId] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Tag editor state (单文件 + 批量)
  const [tagEditorMedia, setTagEditorMedia] = useState<{id: number; tags: string; multiple?: boolean} | null>(null);

  const loadFolders = useCallback(async () => {
    setFolderLoading(true);
    try {
      const res = await apiClient.get('/media/folders/tree');
      if (res.success && res.data) setFolders((res.data as any).tree || []);
    } catch {} finally { setFolderLoading(false); }
  }, []);

  const loadTags = useCallback(async () => {
    try {
      const res = await apiClient.get('/media/tags');
      if (res.success && res.data) {
        const d = res.data as any;
        setAllTags((d.tags || []).map((t) => ({id: t.name, name: t.name, count: t.count})));
      }
    } catch {}
  }, []);

  const loadCategories = useCallback(async () => {
    try {
      const res = await apiClient.get('/media/categories');
      if (res.success && res.data) {
        const d = res.data as any;
        setAllCategories((d.categories || []).map((c) => ({id: c.name, name: c.name, count: c.count})));
      }
    } catch {}
  }, []);

  const loadFiles = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {page, per_page: 20, media_type: filterType||undefined, q: search||undefined};
      // Advanced filters
      if (selectedCategoryId) params.category = selectedCategoryId;
      // Get folder name from selected folder
      if (selectedFolder !== null) {
        const findName = (nodes: FolderNode[], id: number): string|null => {
          for (const n of nodes) { if (n.id===id) return n.name; if (n.children) {const r=findName(n.children,id); if(r) return r;}} return null;
        };
        const fn = findName(folders, selectedFolder);
        if (fn) params.folder_name = fn;
      }
      const res = await MediaService.getMediaFiles(params);
      if (res.success && res.data) {
        const d = res.data as any;
        setFiles(d.media_items || d.files || []);
        setTotalPages(d.pagination?.pages || d.total_pages || 1);
        if (d.stats) setStats(d.stats);
      } else {
        console.error('[MediaPage] loadFiles failed:', res.error || res.message);
      }
    } catch (e) {
      console.error('[MediaPage] loadFiles error:', e);
    } finally { setLoading(false); }
  }, [page, filterType, search, selectedFolder, folders, selectedCategoryId]);

  useEffect(() => { loadFiles(); }, [loadFiles]);
  useEffect(() => { loadFolders(); }, []);
  useEffect(() => { loadTags(); loadCategories(); }, []);

  const {uploading, uploadProgress, uploadStatus, uploadFiles} = useMediaUpload(() => loadFiles());

  const handleDelete = async (id: number) => {
    const res = await apiClient.delete('/media/?file-id-list=' + id);
    if (res.success) {
      setDeleteItem(null);
      await loadFiles();
    } else alert(res.error || '删除失败');
  };

  const handleCreateFolder = async (name: string) => {
    const res = await apiClient.post('/media/folders/', {name});
    if (res.success) {
      setShowCreateFolder(false);
      await loadFolders();
    }
    else alert(res.error||'创建失败');
  };

  const handleMoveToFolder = async (folderPath: string|null) => {
    if (!selected.length) return;
    const res = await apiClient.post('/media/folders/move-media', {media_ids: selected, folder_path: folderPath});
    if (res.success) {
      setSelected([]);
      setShowMoveDialog(false);
      await loadFiles();
    }
    else alert(res.error||'移动失败');
  };

  const handleDeleteFolder = async (id: number) => {
    if (!await confirm({message: '确定删除此文件夹？', variant: 'danger'})) return;
    const res = await apiClient.delete(`/media/folders/${id}`);
    if (res.success) {
      if (selectedFolder === id) setSelectedFolder(null);
      await loadFolders();
    }
    else alert(res.error||'删除失败');
  };

  const handleSaveTags = async (mediaId: number, tags: string[], mode: 'add' | 'replace') => {
    try {
      const res = await apiClient.post(`/media/${mediaId}/tags`, {tags, mode});
      if (res.success) {
        await loadFiles();
        loadTags();
        return true;
      }
      else { alert(res.error || '保存标签失败'); return false; }
    } catch { alert('保存标签失败'); return false; }
  };

  // 分类编辑
  const [categoryEditorMedia, setCategoryEditorMedia] = useState<{id: number; category: string | null; multiple?: boolean} | null>(null);

  const handleSaveCategory = async (mediaId: number, category: string | null) => {
    try {
      const res = await apiClient.put(`/media/detail/${mediaId}`, {category});
      if (res.success) {
        await loadFiles();
        loadCategories();
        return true;
      }
      else { alert(res.error || '保存分类失败'); return false; }
    } catch { alert('保存分类失败'); return false; }
  };

  const handleSaveBatchCategory = async (category: string) => {
    if (!selected.length) return;
    try {
      const res = await apiClient.post('/media/batch-categorize', {media_ids: selected, category});
      if (res.success) {
        await loadFiles();
        loadCategories();
      }
      else alert(res.error || '批量设置分类失败');
    } catch { alert('批量设置分类失败'); }
  };

  const handleSaveBatchTags = async (tag: string) => {
    if (!selected.length) return;
    try {
      const res = await apiClient.post('/media/batch-tags', {media_ids: selected, tags: [tag], mode: 'add'});
      if (res.success) {
        await loadFiles();
        loadTags();
      }
      else alert(res.error || '批量添加标签失败');
    } catch { alert('批量添加标签失败'); }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 pt-24 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">媒体库</h1>
          <div className="flex items-center gap-2">
            <button onClick={()=>setSidebarCollapsed(!sidebarCollapsed)} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800">{sidebarCollapsed?<ChevronRight className="w-5 h-5"/>:<ChevronLeft className="w-5 h-5"/>}</button>
            <button onClick={()=>setViewMode('grid')} className={`p-2 rounded-lg ${viewMode==='grid'?'bg-blue-100 text-blue-600':'hover:bg-gray-100 dark:hover:bg-gray-800'}`}><Grid3X3 className="w-5 h-5"/></button>
            <button onClick={()=>setViewMode('list')} className={`p-2 rounded-lg ${viewMode==='list'?'bg-blue-100 text-blue-600':'hover:bg-gray-100 dark:hover:bg-gray-800'}`}><List className="w-5 h-5"/></button>
          </div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          <aside className={`${sidebarCollapsed?'hidden':'lg:w-56'} flex-shrink-0 space-y-6`}>
            <StorageStats stats={stats} loading={loading}/>
            <FolderTree folders={folders} selectedId={selectedFolder} onSelect={f=>{setSelectedFolder(f?.id??null);setPage(1)}} onCreate={()=>setShowCreateFolder(true)} onDelete={handleDeleteFolder} loading={folderLoading}/>
          </aside>

          <main className="flex-1">
            <UploadArea onUpload={uploadFiles} uploading={uploading} progress={uploadProgress} status={uploadStatus} collapsed={uploadCollapsed} onToggle={()=>setUploadCollapsed(!uploadCollapsed)}/>

            <div className="flex flex-wrap items-center gap-3 mb-2">
              <input type="text" value={search} onChange={e=>{setSearch(e.target.value);setPage(1)}} placeholder="搜索文件..." className="flex-1 min-w-[200px] px-4 py-2.5 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/>
              <button onClick={() => setShowFilters(v => !v)}
                      className={`px-3 py-2.5 rounded-xl text-sm flex items-center gap-1.5 transition-colors ${showFilters || selectedTagIds.length || selectedCategoryId ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-800' : 'bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800'}`}>
                <Filter className="w-4 h-4"/>
                {selectedTagIds.length || selectedCategoryId ? <span className="inline-flex items-center justify-center w-5 h-5 text-[10px] font-bold bg-blue-500 text-white rounded-full">{(selectedTagIds.length) + (selectedCategoryId ? 1 : 0)}</span> : '筛选'}
              </button>
              {selected.length>0 && (<div className="flex items-center gap-2 flex-wrap">
                <span className="text-sm text-blue-600 font-medium">{selected.length} 已选</span>
                <button onClick={()=>setSelected([])} className="px-3 py-2 text-sm bg-gray-200 dark:bg-gray-700 rounded-lg">取消</button>
                <button onClick={()=>{if(selected.length)setShowMoveDialog(true);}} className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700"><FolderClosed className="w-4 h-4 inline mr-1"/>移动</button>
                <button onClick={()=>{if(selected.length)setTagEditorMedia({id:0, tags:'', multiple:true});}} className="px-3 py-2 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700"><Tag className="w-4 h-4 inline mr-1"/>标签</button>
                <button onClick={async () => {
                  if (selected.length) setCategoryEditorMedia({id: 0, category: null, multiple: true});
                }} className="px-3 py-2 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"><FolderClosed
                  className="w-4 h-4 inline mr-1"/>分类
                </button>
                <button onClick={async () => {
                  if (!await confirm({message: `删除 ${selected.length} 个文件？`, variant: 'danger'})) return;
                  const r = await MediaService.deleteMediaFile(selected);
                  if (r.success) {
                    setSelected([]);
                    loadFiles();
                  }
                }} className="px-3 py-2 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700"><Trash2
                  className="w-4 h-4 inline mr-1"/>删除
                </button>
              </div>)}
            </div>

            {/* 高级筛选面板 */}
            {showFilters && (
                <motion.div
                    initial={{height: 0, opacity: 0}}
                    animate={{height: 'auto', opacity: 1}}
                    className="overflow-hidden mb-4"
                >
                  <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 space-y-4">
                    {/* 类型筛选 */}
                    <div>
                      <label className="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-2">文件类型</label>
                      <div className="flex flex-wrap gap-2">
                        {[
                          {key: '', label: '全部'},
                          {key: 'image', label: '图片'},
                          {key: 'video', label: '视频'},
                          {key: 'audio', label: '音频'},
                          {key: 'application/pdf', label: 'PDF'},
                        ].map(t => (
                            <button key={t.key}
                                    onClick={() => { setFilterType(t.key); setPage(1); }}
                                    className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                                        filterType === t.key
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                                    }`}
                            >{t.label}</button>
                        ))}
                      </div>
                    </div>

                    {/* 标签筛选 */}
                    {allTags.length > 0 && (
                        <div>
                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-2">
                            标签 {selectedTagIds.length > 0 && (
                              <button onClick={() => { setSelectedTagIds([]); setPage(1); }}
                                      className="ml-2 text-blue-500 hover:text-blue-600 text-[10px]">清除</button>
                          )}
                          </label>
                          <div className="flex flex-wrap gap-1.5">
                            {allTags.map(tag => (
                                <button key={tag.id}
                                        onClick={() => {
                                          setSelectedTagIds(prev =>
                                              prev.includes(tag.id)
                                                  ? prev.filter(id => id !== tag.id)
                                                  : [...prev, tag.id]
                                          );
                                          setPage(1);
                                        }}
                                        className={`px-2.5 py-1 rounded-lg text-xs transition-colors ${
                                            selectedTagIds.includes(tag.id)
                                                ? 'bg-purple-600 text-white'
                                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                                        }`}
                                >{tag.name}</button>
                            ))}
                          </div>
                        </div>
                    )}

                    {/* 分类筛选 */}
                    {allCategories.length > 0 && (
                        <div>
                          <label className="text-xs font-medium text-gray-500 dark:text-gray-400 block mb-2">
                            分类 {selectedCategoryId && (
                              <button onClick={() => { setSelectedCategoryId(null); setPage(1); }}
                                      className="ml-2 text-blue-500 hover:text-blue-600 text-[10px]">清除</button>
                          )}
                          </label>
                          <div className="flex flex-wrap gap-1.5">
                            {allCategories.map(cat => (
                                <button key={cat.id}
                                        onClick={() => {
                                          setSelectedCategoryId(prev => prev === cat.id ? null : cat.id);
                                          setPage(1);
                                        }}
                                        className={`px-2.5 py-1 rounded-lg text-xs transition-colors ${
                                            selectedCategoryId === cat.id
                                                ? 'bg-emerald-600 text-white'
                                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                                        }`}
                                >{cat.name}</button>
                            ))}
                          </div>
                        </div>
                    )}

                    {/* 摘要: 当前筛选条件 */}
                    {(selectedTagIds.length > 0 || selectedCategoryId || filterType) && (
                        <div className="flex items-center gap-2 pt-2 border-t border-gray-100 dark:border-gray-800">
                          <span className="text-xs text-gray-400">当前筛选:</span>
                          {filterType && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-50 dark:bg-blue-900/20 text-blue-600 dark:text-blue-400 text-xs">
                            {filterType === 'application/pdf' ? 'PDF' : filterType}
                                <button onClick={() => { setFilterType(''); setPage(1); }} className="hover:text-blue-800">✕</button>
                          </span>
                          )}
                          {selectedTagIds.map(id => {
                            const tag = allTags.find(t => t.id === id);
                            return tag ? (
                                <span key={id} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-50 dark:bg-purple-900/20 text-purple-600 dark:text-purple-400 text-xs">
                              {tag.name}
                                  <button onClick={() => { setSelectedTagIds(prev => prev.filter(i => i !== id)); setPage(1); }} className="hover:text-purple-800">✕</button>
                            </span>
                            ) : null;
                          })}
                          {selectedCategoryId && allCategories.find(c => c.id === selectedCategoryId) && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-emerald-50 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 text-xs">
                            {allCategories.find(c => c.id === selectedCategoryId)?.name}
                                <button onClick={() => { setSelectedCategoryId(null); setPage(1); }} className="hover:text-emerald-800">✕</button>
                            </span>
                          )}
                          <button onClick={() => { setSelectedTagIds([]); setSelectedCategoryId(null); setFilterType(''); setPage(1); }}
                                  className="text-xs text-red-500 hover:text-red-600 ml-auto">清除全部</button>
                        </div>
                    )}
                  </div>
                </motion.div>
            )}

            <MediaGrid files={files} loading={loading} viewMode={viewMode} selected={selected} onSelect={id=>setSelected(s=>s.includes(id)?s.filter(x=>x!==id):[...s,id])} onPreview={f => {
              if (f.mime_type?.startsWith('audio/')) { setNowPlaying(f); }
              else { setPreviewMedia(f); }
            }} onDelete={setDeleteItem} onEditTags={f => setTagEditorMedia({id: f.id, tags: (f as any).tags || ''})} onEditCategory={f => setCategoryEditorMedia({id: f.id, category: (f as any).category || null})}/>

            {totalPages>1 && (<div className="flex items-center justify-center gap-2 mt-8">
              <button disabled={page<=1} onClick={()=>setPage(p=>p-1)} className="p-2 rounded-lg border disabled:opacity-30 hover:bg-gray-100"><ChevronLeft className="w-4 h-4"/></button>
              {Array.from({length:totalPages},(_,i)=>i+1).map(p=><button key={p} onClick={()=>setPage(p)} className={`px-3 py-1.5 rounded-lg text-sm ${p===page?'bg-blue-600 text-white':'border hover:bg-gray-100 dark:hover:bg-gray-800'}`}>{p}</button>)}
              <button disabled={page>=totalPages} onClick={()=>setPage(p=>p+1)} className="p-2 rounded-lg border disabled:opacity-30 hover:bg-gray-100"><ChevronRight className="w-4 h-4"/></button>
            </div>)}
          </main>
        </div>
      </div>

      {/* 非音频预览 */}
      <PreviewModal media={previewMedia} onClose={()=>setPreviewMedia(null)}/>
      {/* 持久音频层 — 独立于预览，不被打断 */}
      {nowPlaying && (
          <AudioLayer
              media={nowPlaying}
              onClose={() => { setNowPlaying(null); }}
          />
      )}
      {deleteItem && <DeleteConfirm item={deleteItem} onCancel={()=>setDeleteItem(null)} onConfirm={()=>handleDelete(deleteItem.id)}/>}
      <CreateFolderDialog open={showCreateFolder} onClose={()=>setShowCreateFolder(false)} onCreate={handleCreateFolder}/>
      <MoveDialog open={showMoveDialog} onClose={()=>setShowMoveDialog(false)} folders={folders} mediaCount={selected.length} onMove={handleMoveToFolder}/>
      <TagEditor
          media={tagEditorMedia}
          allTags={allTags}
          onClose={() => setTagEditorMedia(null)}
          onSave={handleSaveTags}
      />
      <BatchTagDialog
          open={tagEditorMedia?.multiple === true}
          mediaCount={selected.length}
          onClose={() => setTagEditorMedia(null)}
          onSave={handleSaveBatchTags}
          allTags={allTags}
      />
      <CategoryEditor
          media={categoryEditorMedia}
          allCategories={allCategories}
          onClose={() => setCategoryEditorMedia(null)}
          onSave={handleSaveCategory}
      />
      <BatchCategoryDialog
          open={categoryEditorMedia?.multiple === true}
          mediaCount={selected.length}
          onClose={() => setCategoryEditorMedia(null)}
          onSave={handleSaveBatchCategory}
          allCategories={allCategories}
      />
    </div>
  );
};

const MediaPageGuard: React.FC = () => <AuthGuard><QueryProvider><MediaPage/></QueryProvider></AuthGuard>;
export default MediaPageGuard;

/* ========== Tag Editor (single media) ========== */
const TagEditor: React.FC<{
  media: {id: number; tags: string; multiple?: boolean} | null;
  allTags: {id: string; name: string; count?: number}[];
  onClose: () => void;
  onSave: (mediaId: number, tags: string[], mode: 'add'|'replace') => Promise<boolean>;
}> = ({media, allTags, onClose, onSave}) => {
  const [tags, setTags] = useState<string[]>([]);
  const [inputVal, setInputVal] = useState('');
  const [saving, setSaving] = useState(false);
  const [suggestions, setSuggestions] = useState<{id: string; name: string}[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (media) {
      setTags((media.tags || '').split(',').filter(Boolean).map(t => t.trim()));
      setInputVal('');
    }
  }, [media]);

  useEffect(() => {
    if (!inputVal.trim()) { setSuggestions([]); return; }
    const q = inputVal.toLowerCase();
    setSuggestions(
        allTags.filter(t => t.name.toLowerCase().includes(q) && !tags.includes(t.name)).slice(0, 5)
    );
  }, [inputVal, allTags, tags]);

  if (!media || media.multiple) return null;

  const addTag = (name: string) => {
    const trimmed = name.trim();
    if (!trimmed || tags.includes(trimmed) || tags.length >= 5) return;
    setTags(prev => [...prev, trimmed]);
    setInputVal('');
    setSuggestions([]);
  };

  const removeTag = (name: string) => setTags(prev => prev.filter(t => t !== name));

  const handleSave = async () => {
    setSaving(true);
    const ok = await onSave(media.id, tags, 'replace');
    setSaving(false);
    if (ok) onClose();
  };

  return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">编辑标签</h3>
            <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400">✕</button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">最多 5 个标签</p>

          {/* 已选标签 */}
          <div className="flex flex-wrap gap-2 mb-3 min-h-[32px] p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
            {tags.map(tag => (
                <span key={tag}
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 text-xs font-medium">
                  {tag}
                  <button onClick={() => removeTag(tag)} className="hover:text-red-500">✕</button>
                </span>
            ))}
            {tags.length === 0 && <span className="text-xs text-gray-400">暂无标签，输入添加</span>}
          </div>

          {/* 输入框 + 建议 */}
          <div className="relative mb-4">
            <input ref={inputRef} type="text" value={inputVal}
                   onChange={e => setInputVal(e.target.value)}
                   onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); addTag(inputVal); } }}
                   placeholder="输入标签名称..."
                   className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:text-white"
                   disabled={tags.length >= 5}
            />
            {suggestions.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-lg overflow-hidden z-10">
                  {suggestions.map(s => (
                      <button key={s.id} onClick={() => addTag(s.name)}
                              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 flex items-center gap-2">
                        <Tag className="w-3 h-3 text-purple-500"/>
                        {s.name}
                      </button>
                  ))}
                </div>
            )}
          </div>

          {/* 快速标签 */}
          {allTags.length > 0 && (
              <div className="mb-4">
                <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">常用标签</p>
                <div className="flex flex-wrap gap-1.5">
                  {allTags.filter(t => !tags.includes(t.name)).slice(0, 10).map(t => (
                      <button key={t.id} onClick={() => addTag(t.name)}
                              className="px-2 py-1 rounded-lg text-xs bg-gray-100 dark:bg-gray-800 hover:bg-purple-100 dark:hover:bg-purple-900/30 text-gray-600 dark:text-gray-400 hover:text-purple-600 transition-colors">
                        {t.name}
                      </button>
                  ))}
                </div>
              </div>
          )}

          <button onClick={handleSave} disabled={saving}
                  className="w-full py-2.5 rounded-xl bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors">
            {saving ? '保存中...' : '保存标签'}
          </button>
        </div>
      </div>
  );
};

/* ========== Batch Tag Dialog ========== */
const BatchTagDialog: React.FC<{
  open: boolean;
  mediaCount: number;
  onClose: () => void;
  onSave: (tag: string) => Promise<void>;
  allTags: {id: string; name: string; count?: number}[];
}> = ({open, mediaCount, onClose, onSave, allTags}) => {
  const [inputVal, setInputVal] = useState('');
  const [saving, setSaving] = useState(false);

  if (!open) return null;

  const handleSave = async () => {
    if (!inputVal.trim()) return;
    setSaving(true);
    await onSave(inputVal.trim());
    setSaving(false);
    onClose();
  };

  return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-6 w-full max-w-sm" onClick={e => e.stopPropagation()}>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">批量添加标签</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">将为 {mediaCount} 个文件添加标签</p>

          <input type="text" value={inputVal}
                 onChange={e => setInputVal(e.target.value)}
                 onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleSave(); } }}
                 placeholder="输入标签名称..."
                 className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-white mb-3"
                 autoFocus
          />

          <div className="flex gap-2">
            <button onClick={onClose}
                    className="flex-1 py-2 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800">
              取消
            </button>
            <button onClick={handleSave} disabled={saving || !inputVal.trim()}
                    className="flex-1 py-2 rounded-xl bg-purple-600 text-white text-sm font-medium hover:bg-purple-700 disabled:opacity-50 transition-colors">
              {saving ? '添加中...' : '添加标签'}
            </button>
          </div>
        </div>
      </div>
  );
};

/* ========== Category Editor (single media) ========== */
const CategoryEditor: React.FC<{
  media: {id: number; category: string | null; multiple?: boolean} | null;
  allCategories: {id: string; name: string; count?: number}[];
  onClose: () => void;
  onSave: (mediaId: number, category: string | null) => Promise<boolean>;
}> = ({media, allCategories, onClose, onSave}) => {
  const [selected, setSelected] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [customVal, setCustomVal] = useState('');

  useEffect(() => {
    if (media && !media.multiple) {
      setSelected(media.category);
      setCustomVal('');
    }
  }, [media]);

  if (!media || media.multiple) return null;

  const handleSave = async () => {
    const category = selected || customVal.trim() || null;
    setSaving(true);
    const ok = await onSave(media.id, category);
    setSaving(false);
    if (ok) onClose();
  };

  return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-6 w-full max-w-md" onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">设置分类</h3>
            <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400">✕</button>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">一个媒体文件只能属于一个分类</p>

          {/* 已有分类列表 */}
          <div className="flex flex-wrap gap-2 mb-4">
            {allCategories.map(cat => (
                <button key={cat.id}
                        onClick={() => { setSelected(cat.name); setCustomVal(''); }}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                            selected === cat.name
                                ? 'bg-emerald-600 text-white'
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                        }`}
                >{cat.name}</button>
            ))}
            <button onClick={() => { setSelected(null); setCustomVal(''); }}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                        selected === null && !customVal
                            ? 'bg-gray-600 text-white'
                            : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200'
                    }`}>
              无
            </button>
          </div>

          {/* 自定义分类 */}
          <div className="mb-4">
            <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">或输入自定义分类</label>
            <input type="text" value={customVal}
                   onChange={e => { setCustomVal(e.target.value); setSelected(null); }}
                   placeholder="输入新分类名称..."
                   className="w-full px-3 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 dark:text-white"
            />
          </div>

          <button onClick={handleSave} disabled={saving}
                  className="w-full py-2.5 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors">
            {saving ? '保存中...' : '保存分类'}
          </button>
        </div>
      </div>
  );
};

/* ========== Batch Category Dialog ========== */
const BatchCategoryDialog: React.FC<{
  open: boolean;
  mediaCount: number;
  onClose: () => void;
  onSave: (category: string) => Promise<void>;
  allCategories: {id: string; name: string; count?: number}[];
}> = ({open, mediaCount, onClose, onSave, allCategories}) => {
  const [selected, setSelected] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  if (!open) return null;

  const handleSave = async () => {
    if (!selected) return;
    setSaving(true);
    await onSave(selected);
    setSaving(false);
    onClose();
  };

  return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl p-6 w-full max-w-sm" onClick={e => e.stopPropagation()}>
          <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">批量设置分类</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">将为 {mediaCount} 个文件设置分类</p>

          <div className="flex flex-wrap gap-2 mb-4">
            {allCategories.map(cat => (
                <button key={cat.id}
                        onClick={() => setSelected(cat.name)}
                        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                            selected === cat.name
                                ? 'bg-emerald-600 text-white'
                                : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
                        }`}
                >{cat.name}</button>
            ))}
          </div>

          <div className="flex gap-2">
            <button onClick={onClose}
                    className="flex-1 py-2 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800">
              取消
            </button>
            <button onClick={handleSave} disabled={saving || !selected}
                    className="flex-1 py-2 rounded-xl bg-emerald-600 text-white text-sm font-medium hover:bg-emerald-700 disabled:opacity-50 transition-colors">
              {saving ? '设置中...' : '设置分类'}
            </button>
          </div>
        </div>
      </div>
  );
};

/* ========== Image Crop Dialog ========== */
const _ImageCropDialog: React.FC<{
  open: boolean;
  media: MediaFile | null;
  onClose: () => void;
  onOptimize: (mediaId: number, cropData?: any) => Promise<void>;
}> = ({open, media, onClose, onOptimize}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [crop, setCrop] = useState({x: 0, y: 0, width: 100, height: 100});
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    if (media && canvasRef.current) {
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        const canvas = canvasRef.current!;
        const ctx = canvas.getContext('2d')!;
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        setCrop({x: 0, y: 0, width: img.width, height: img.height});
      };
      img.src = getFullMediaUrl(media.url);
    }
  }, [media]);

  const handleOptimize = async () => {
    if (!media || !canvasRef.current) return;
    setProcessing(true);
    try {
      // Convert crop to WebP and send to backend
      const canvas = canvasRef.current;
      const blob = await new Promise<Blob>((resolve) => {
        canvas.toBlob((b) => resolve(b!), 'image/webp', 0.8);
      });
      const formData = new FormData();
      formData.append('file', blob, `${media.filename}.webp`);
      formData.append('crop_data', JSON.stringify(crop));

      await onOptimize(media.id, crop);
      onClose();
    } catch (error) {
      console.error('优化失败:', error);
    } finally {
      setProcessing(false);
    }
  };

  if (!open || !media) return null;

  return (
      <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4" onClick={onClose}>
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col"
             onClick={e => e.stopPropagation()}>
          <div className="flex items-center justify-between px-6 py-4 border-b dark:border-gray-700">
            <h3 className="text-lg font-bold text-gray-900 dark:text-white">图像裁剪与优化</h3>
            <button onClick={onClose} className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800"><X
                className="w-5 h-5"/></button>
          </div>
          <div className="flex-1 overflow-auto p-6">
            <div className="mb-4">
              <canvas ref={canvasRef} className="max-w-full border rounded-lg"/>
            </div>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">X 坐标</label>
                <input type="number" value={crop.x} onChange={e => setCrop({...crop, x: Number(e.target.value)})}
                       className="w-full px-3 py-2 border rounded-lg"/>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">Y 坐标</label>
                <input type="number" value={crop.y} onChange={e => setCrop({...crop, y: Number(e.target.value)})}
                       className="w-full px-3 py-2 border rounded-lg"/>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">宽度</label>
                <input type="number" value={crop.width}
                       onChange={e => setCrop({...crop, width: Number(e.target.value)})}
                       className="w-full px-3 py-2 border rounded-lg"/>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-gray-400 mb-1 block">高度</label>
                <input type="number" value={crop.height}
                       onChange={e => setCrop({...crop, height: Number(e.target.value)})}
                       className="w-full px-3 py-2 border rounded-lg"/>
              </div>
            </div>
          </div>
          <div className="px-6 py-4 border-t dark:border-gray-700 flex gap-2">
            <button onClick={onClose} className="flex-1 py-2 rounded-xl border text-sm">取消</button>
            <button onClick={handleOptimize} disabled={processing}
                    className="flex-1 py-2 rounded-xl bg-blue-600 text-white text-sm hover:bg-blue-700 disabled:opacity-50">
              {processing ? '优化中...' : '生成 WebP'}
            </button>
          </div>
        </div>
      </div>
  );
};
