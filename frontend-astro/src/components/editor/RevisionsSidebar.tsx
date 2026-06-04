'use client';

import React, {useState} from 'react';
import {useMutation, useQuery, useQueryClient} from '@tanstack/react-query';
import {apiClient} from '@/lib/api/base-client';
import {ChevronRight, Clock, FileText, GitCompare, History, RotateCcw, Trash2, User, X} from 'lucide-react';
import {useConfirm} from '@/components/ui/confirm-provider';

interface Revision {id:number;revision_number:number;title:string;excerpt:string;content:string;change_summary:string|null;created_at:string;author?:{username:string};}
interface Props {articleId:number|string;open:boolean;onClose:()=>void;onCollapse?:()=>void;onRestore:(c:string,t:string,e:string)=>void;}

const RevisionsSidebar: React.FC<Props> = ({articleId,open,onClose,onCollapse,onRestore}) => {
  const qc = useQueryClient();
  const [selected, setSelected] = useState<Revision|null>(null);
  const [compareWith, setCompareWith] = useState<Revision|null>(null);
  const [preview, setPreview] = useState<string|null>(null);
  const [diff, setDiff] = useState<{title_changed?:boolean;excerpt_changed?:boolean;content_changed?:boolean}|null>(null);

  const {data:revisions,isLoading} = useQuery({
    queryKey:['revisions',articleId],enabled:open&&!!articleId,
    queryFn:async()=>{const r=await apiClient.get<Revision[]>(`/articles/${articleId}/revisions`);return r.success&&r.data?(Array.isArray(r.data)?r.data:(r.data as any).revisions||[]):[]},
  });

  const rollbackMut=useMutation({mutationFn:(revId:number)=>apiClient.post(`/articles/${articleId}/revisions/${revId}/rollback`),onSuccess:()=>{if(selected){onRestore(selected.content,selected.title,selected.excerpt);onClose();}}});

  const deleteRevMut=useMutation({mutationFn:(revId:number)=>apiClient.delete(`/articles/${articleId}/revisions/${revId}`),onSuccess:()=>{qc.invalidateQueries({queryKey:['revisions',articleId]});setSelected(null);}});

  const viewRevision=async(rev:Revision)=>{setSelected(rev);setCompareWith(null);setDiff(null);setPreview(rev.content);};

  const compareRevisions = async (a: Revision, b: Revision) => {
    setSelected(a);
    setCompareWith(b);
    try {
      const r = await apiClient.get('/articles/revisions/compare', {rev1: a.id, rev2: b.id});
      if (r.success && r.data) setDiff(r.data.differences || r.data); else setDiff({
        title_changed: a.title !== b.title,
        content_changed: true
      });
    } catch {
      setDiff({title_changed: true, content_changed: true});
    }
  };
  const confirm = useConfirm();

  if(!open)return null;

  return (
    <div className="fixed inset-y-0 right-0 z-[60] w-[32rem] bg-white dark:bg-gray-900 border-l border-gray-200 dark:border-gray-800 shadow-2xl flex flex-col">
      {/* Collapse tab at waist */}
      <button onClick={onCollapse} className="absolute left-0 top-1/2 -translate-x-full -translate-y-1/2 w-6 h-12 bg-white dark:bg-gray-900 border border-r-0 border-gray-200 dark:border-gray-800 rounded-l-lg flex items-center justify-center hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer z-[61] shadow-sm" title="收起"><ChevronRight className="w-4 h-4 text-gray-400"/></button>
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shrink-0 z-10">
        <div className="flex items-center gap-2"><History className="w-5 h-5 text-gray-600 dark:text-gray-300"/><h2 className="font-bold text-gray-900 dark:text-white">版本历史</h2></div>
        <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 hover:text-gray-700 mr-0"><X className="w-5 h-5"/></button>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Left: Revision list */}
        <div className={`${selected?'w-1/2':'flex-1'} overflow-y-auto p-4 space-y-2 border-r border-gray-100 dark:border-gray-800`}>
          {isLoading?<div className="space-y-3">{[1,2,3].map(i=><div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 rounded-lg animate-pulse"/>)}</div>
          : !revisions?.length ? <div className="text-center py-8 text-gray-400"><FileText className="w-10 h-10 mx-auto mb-2 opacity-50"/><p className="text-sm">暂无版本记录</p></div>
          : revisions.map(rev=>(
                <button key={rev.id} onClick={async () => viewRevision(rev)}
              className={`w-full text-left p-3 rounded-xl border transition-colors ${selected?.id===rev.id&&!compareWith?'border-blue-500 bg-blue-50 dark:bg-blue-900/20':compareWith?.id===rev.id?'border-orange-400 bg-orange-50 dark:bg-orange-900/20':'border-gray-200 dark:border-gray-700 hover:border-gray-300'}`}>
              <div className="flex items-center gap-2 text-sm font-medium text-gray-900 dark:text-white"><Clock className="w-3.5 h-3.5 text-gray-400"/>v{rev.revision_number}</div>
              <p className="text-xs text-gray-500">{new Date(rev.created_at).toLocaleString('zh-CN')}</p>
              {rev.change_summary&&<p className="text-xs text-gray-500 mt-1 line-clamp-1">{rev.change_summary}</p>}
              <div className="flex gap-1 mt-1.5">
                {rev.author&&<span className="text-xs text-gray-400"><User className="w-3 h-3 inline mr-0.5"/>{rev.author.username}</span>}
                <button onClick={async e => {
                  e.stopPropagation();
                  if (await confirm({message: '确定删除此版本？', variant: 'danger'})) deleteRevMut.mutate(rev.id);
                }} className="text-xs text-red-400 hover:text-red-600 ml-1" title="删除"><Trash2 className="w-3 h-3"/>
                </button>
                {/* Compare button: visible on non-selected items when another is selected */}
                {selected&&selected.id!==rev.id&&!compareWith&&<button onClick={e=>{e.stopPropagation();compareRevisions(selected,rev);}} className="text-xs text-blue-600 hover:underline ml-auto"><GitCompare className="w-3 h-3 inline mr-0.5"/>对比</button>}
              </div>
            </button>
          ))}
        </div>

        {/* Right: Preview / Diff */}
        {selected && <div className="w-1/2 flex flex-col">
          {/* Compare info */}
          {diff&&compareWith? (
            <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-orange-50 dark:bg-orange-900/10 shrink-0">
              <p className="text-xs font-semibold text-orange-700 dark:text-orange-300 mb-1 flex items-center gap-1"><GitCompare className="w-3.5 h-3.5"/>v{selected.revision_number} ↔ v{compareWith.revision_number}</p>
              <div className="flex gap-3 text-xs">
                {diff.title_changed!==undefined&&<span className={`px-1.5 py-0.5 rounded ${diff.title_changed?'bg-orange-100 text-orange-700':'bg-green-100 text-green-700'}'}`}>{diff.title_changed?'标题不同':'标题相同'}</span>}
                {diff.content_changed!==undefined&&<span className={`px-1.5 py-0.5 rounded ${diff.content_changed?'bg-orange-100 text-orange-700':'bg-green-100 text-green-700'}'}`}>{diff.content_changed?'内容不同':'内容相同'}</span>}
                {diff.excerpt_changed!==undefined&&<span className={`px-1.5 py-0.5 rounded ${diff.excerpt_changed?'bg-orange-100 text-orange-700':'bg-green-100 text-green-700'}'}`}>{diff.excerpt_changed?'摘要不同':'摘要相同'}</span>}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 shrink-0">
              <span className="text-sm font-medium">v{selected.revision_number}</span>
              <button onClick={async () => {
                if (await confirm({message: '确定回滚到此版本？', variant: 'warning'})) rollbackMut.mutate(selected.id);
              }}
                      className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-1">
                <RotateCcw className="w-3 h-3"/>回滚
              </button>
              <button onClick={async () => {
                if (await confirm({message: '确定删除此版本？', variant: 'danger'})) deleteRevMut.mutate(selected.id);
              }}
                      className="px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600 flex items-center gap-1">
                <Trash2 className="w-3 h-3"/>删除
              </button>
            </div>
          )}
          <div className="flex-1 overflow-y-auto p-4">
            <h3 className="font-bold text-gray-900 dark:text-white mb-2">{selected.title}</h3>
            {selected.excerpt&&<p className="text-sm text-gray-500 mb-4">{selected.excerpt}</p>}
            <div className="prose prose-sm dark:prose-invert max-w-none" dangerouslySetInnerHTML={{__html:preview||selected.content}}/>
          </div>
        </div>}
      </div>
    </div>
  );
};
export default RevisionsSidebar;
