'use client';

import React, {useCallback, useEffect, useRef, useState} from 'react';
import {EditorContent, useEditor} from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import ImageExt from '@tiptap/extension-image';
import LinkExt from '@tiptap/extension-link';
import Underline from '@tiptap/extension-underline';
import TextAlign from '@tiptap/extension-text-align';
import Highlight from '@tiptap/extension-highlight';
import Typography from '@tiptap/extension-typography';
import TaskList from '@tiptap/extension-task-list';
import TaskItem from '@tiptap/extension-task-item';
import {Table} from '@tiptap/extension-table';
import {TableRow} from '@tiptap/extension-table-row';
import {TableCell} from '@tiptap/extension-table-cell';
import {TableHeader} from '@tiptap/extension-table-header';
import Collaboration from '@tiptap/extension-collaboration';
import CollaborationCursor from '@tiptap/extension-collaboration-cursor';
import {WebsocketProvider} from 'y-websocket';
import * as Y from 'yjs';
import {Image as ImageIcon2, ImageIcon, LayoutGrid, Loader, Palette, Sparkles, X} from 'lucide-react';
import {apiClient} from '@/lib/api/base-client';

interface RichEditorProps {value:string;onChange:(v:string)=>void;placeholder?:string;editorRef?:React.MutableRefObject<any>;}

const AI_TOOLS = [
  {id:'polish',label:'润色'},{id:'grammar',label:'语法'},{id:'titles',label:'标题'},{id:'keywords',label:'关键词'},{id:'continue',label:'续写'},{id:'summary',label:'摘要'},{id:'style',label:'改风格'},
];

/* ── Block Patterns & Global Styles ── */
function PatternLibrary({onSelect, onClose}: { onSelect: (blocks: any) => void; onClose: () => void }) {
  const [patterns, setPatterns] = useState<any[]>([]);
  React.useEffect(() => {
    apiClient.get('/block-patterns/list').then(r => {
      if (r.success) setPatterns(r.data || [])
    }).catch(console.error);
  }, []);
  return <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/40" onClick={onClose}>
    <div className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl"
         onClick={e => e.stopPropagation()}>
      <div className="flex items-center justify-between px-6 py-4 border-b shrink-0"><h3
          className="font-bold text-gray-900 dark:text-white">块模式库</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-gray-100"><X className="w-5 h-5"/></button>
      </div>
      <div className="flex-1 overflow-y-auto p-6">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {patterns.map(p => <button key={p.id} onClick={() => onSelect(JSON.parse(p.blocks))}
                                     className="group p-4 rounded-xl border hover:border-blue-500 hover:shadow-md transition-all text-left">
            <div
                className="aspect-video bg-gray-100 dark:bg-gray-800 rounded-lg mb-3 flex items-center justify-center overflow-hidden">
              {p.thumbnail ? <img src={p.thumbnail} className="w-full h-full object-cover"/> :
                  <LayoutGrid className="w-8 h-8 text-gray-300"/>}
            </div>
            <h4 className="font-semibold text-sm truncate">{p.title}</h4>
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{p.description}</p>
          </button>)}
        </div>
      </div>
    </div>
  </div>;
}

function StyleManager({onClose}: { onClose: () => void }) {
  const [styles, setStyles] = useState<any[]>([]);
  React.useEffect(() => {
    apiClient.get('/global-styles/list').then(r => {
      if (r.success) setStyles(r.data || [])
    }).catch(console.error);
  }, []);
  const activate = (id: number) => {
    apiClient.post(`/global-styles/${id}/activate`).then(r => {
      if (r.success) onClose()
    });
  };
  return <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/40" onClick={onClose}>
    <div className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-md flex flex-col shadow-2xl"
         onClick={e => e.stopPropagation()}>
      <div className="flex items-center justify-between px-6 py-4 border-b shrink-0"><h3
          className="font-bold text-gray-900 dark:text-white">全局样式方案</h3>
        <button onClick={onClose} className="p-1 rounded hover:bg-gray-100"><X className="w-5 h-5"/></button>
      </div>
      <div className="p-4 space-y-3 max-h-[60vh] overflow-y-auto">
        {styles.map(s => <div key={s.id}
                              className={`p-4 rounded-xl border ${s.is_active ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800'} flex items-center justify-between`}>
          <div><h4 className="font-semibold">{s.theme_name}</h4><p
              className="text-xs text-gray-500 mt-1">创建于 {new Date(s.created_at).toLocaleDateString()}</p></div>
          {!s.is_active && <button onClick={() => activate(s.id)}
                                   className="px-3 py-1.5 text-xs bg-gray-100 dark:bg-gray-800 rounded-lg hover:bg-gray-200">应用</button>}
          {s.is_active && <span className="text-xs font-medium text-blue-600">当前激活</span>}
        </div>)}
      </div>
    </div>
  </div>;
}
const AI_ENDPOINTS:Record<string,string> = {
  polish:'/ext/ai-recommendations/writing/polish',grammar:'/ext/ai-recommendations/writing/check-grammar',
  titles:'/ext/ai-recommendations/writing/generate-titles',keywords:'/ext/ai-recommendations/recommend-tags',
  continue:'/ext/ai-recommendations/writing/continue',summary:'/ext/ai-recommendations/extract-summary',
  style:'/ext/ai-recommendations/writing/transform-style',
};

/* ── Media Browser ── */
function MediaBrowser({onSelect,onClose}:{onSelect:(url:string)=>void;onClose:()=>void}) {
  const [files,setFiles]=useState<any[]>([]);const [loading,setLoading]=useState(true);
  React.useEffect(()=>{apiClient.get('/media/files/list',{page:1,per_page:30}).then(r=>{setFiles(r.success&&r.data?((r.data as any).files||(r.data as any).media_items||[]):[])}).finally(()=>setLoading(false));},[]);
  return <div className="fixed inset-0 z-[70] flex items-center justify-center bg-black/40" onClick={onClose}>
    <div className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl" onClick={e=>e.stopPropagation()}>
      <div className="flex items-center justify-between px-6 py-4 border-b shrink-0"><h3 className="font-bold text-gray-900 dark:text-white">媒体库</h3><button onClick={onClose} className="p-1 rounded hover:bg-gray-100"><X className="w-5 h-5"/></button></div>
      <div className="flex-1 overflow-y-auto p-4">
        {loading?<div className="p-12 text-center"><div className="animate-spin w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full mx-auto"/></div>
        :!files.length?<div className="p-12 text-center text-gray-400"><ImageIcon className="w-10 h-10 mx-auto mb-3 opacity-40"/><p className="text-sm">暂无媒体文件</p></div>
        :<div className="grid grid-cols-3 sm:grid-cols-4 gap-3">{files.map((f:any,i:number)=>(
          <button key={f.id||i} onClick={()=>onSelect(f.url)} className="group aspect-square rounded-xl overflow-hidden border hover:border-blue-500 hover:shadow-md transition-all relative">
            {f.mime_type?.startsWith('image/')?<img src={f.url} alt={f.original_filename} className="w-full h-full object-cover group-hover:scale-105"/>:<div className="w-full h-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-gray-300 text-4xl">🎬</div>}
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/60 to-transparent p-1.5 opacity-0 group-hover:opacity-100"><p className="text-white text-xs truncate">{f.original_filename}</p></div>
          </button>
        ))}</div>}
      </div>
    </div>
  </div>;
}

/* ── Main Editor (no toolbar — the parent renders it) ── */
const RichEditor: React.FC<RichEditorProps> = ({value,onChange,placeholder='开始写作...',editorRef}) => {
  const [showAI,setShowAI]=useState(false);
  const [showMedia,setShowMedia]=useState(false);
  const [showPatterns, setShowPatterns] = useState(false);
  const [showStyles, setShowStyles] = useState(false);
  const [aiResult,setAiResult]=useState('');
  const [aiBusy,setAiBusy]=useState(false);
  const prevValueRef = useRef(value);
  const ydocRef = useRef<Y.Doc | null>(null);
  const providerRef = useRef<any>(null);

  // Initialize Collaboration
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const ydoc = new Y.Doc();
      const provider = new WebsocketProvider('ws://localhost:1234', 'article-room', ydoc);
      ydocRef.current = ydoc;
      providerRef.current = provider;
      return () => {
        provider.destroy();
        ydoc.destroy();
      };
    }
  }, []);

  const editor = useEditor({
    extensions:[
        StarterKit.configure({heading: {levels: [1, 2, 3]}}), Placeholder.configure({placeholder}),
      Underline,Typography,TextAlign.configure({types:['heading','paragraph']}),Highlight,ImageExt,
      LinkExt.configure({openOnClick:false}),Table.configure({resizable:true}),TableRow,TableCell,TableHeader,
      TaskList,TaskItem.configure({nested:true}),
      ...(ydocRef.current ? [Collaboration.configure({document: ydocRef.current}), CollaborationCursor.configure({
        provider: providerRef.current,
        user: {name: 'User', color: '#f783ac'}
      })] : []),
    ],
    content: value || '',
    onUpdate:({editor})=>onChange(editor.getHTML()),
    editorProps:{attributes:{class:'prose prose-lg dark:prose-invert max-w-none focus:outline-none min-h-[60vh] px-6 py-4'}},
  });

  // Expose editor to parent
  useEffect(()=>{if(editor&&editorRef)editorRef.current=editor;},[editor,editorRef]);

  // Sync external value changes
    useEffect(() => {
        if (!editor || value === prevValueRef.current) return;
        prevValueRef.current = value;
        if (value && !editor.isDestroyed) editor.commands.setContent(value, {emitUpdate: false});
    }, [value, editor]);

  const runAI=useCallback(async(mode:string)=>{
    if(!editor)return;setShowAI(true);setAiBusy(true);setAiResult('');
    const sel=!editor.state.selection.empty?editor.state.doc.textBetween(editor.state.selection.from,editor.state.selection.to):null;
    const text=sel||editor.getText();
    if(!text.trim()){setAiResult('请先输入内容');setAiBusy(false);return;}
    try{
      const r=await apiClient.post(AI_ENDPOINTS[mode],mode==='titles'?{content:text}:{text});
      if(r.success&&r.data){const d=r.data as any;setAiResult(d.result||d.text||d.keywords?.join(', ')||d.titles?.join('\n')||JSON.stringify(d));}
      else setAiResult(r.error||'请求失败');
    }catch{setAiResult('网络错误');}finally{setAiBusy(false);}
  },[editor]);

  const applyAI=()=>{if(!editor||!aiResult)return;const{from,to}=editor.state.selection;if(from!==to)editor.chain().focus().deleteRange({from,to}).insertContent(aiResult).run();else editor.chain().focus().insertContentAt(editor.state.selection.head,'\n'+aiResult).run();setShowAI(false);setAiResult('');};

  if(!editor)return<div className="h-[60vh] bg-gray-50 dark:bg-gray-800 rounded-xl animate-pulse"/>;

  return (
    <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden relative">
      <EditorContent editor={editor} />

      {/* Floating buttons */}
      <button onClick={() => setShowPatterns(true)}
              className="fixed bottom-36 right-6 z-40 w-11 h-11 bg-indigo-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center"
              title="块模式"><LayoutGrid className="w-5 h-5"/></button>
      <button onClick={() => setShowStyles(true)}
              className="fixed bottom-28 right-6 z-40 w-11 h-11 bg-pink-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center"
              title="全局样式"><Palette className="w-5 h-5"/></button>
      <button onClick={()=>setShowMedia(true)} className="fixed bottom-20 right-6 z-40 w-11 h-11 bg-blue-600 text-white rounded-full shadow-lg hover:shadow-xl hover:scale-105 transition-all flex items-center justify-center" title="媒体库"><ImageIcon2 className="w-5 h-5"/></button>
      <button onClick={()=>setShowAI(!showAI)} className="fixed bottom-6 right-6 z-40 w-12 h-12 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-full shadow-xl hover:shadow-2xl hover:scale-105 transition-all flex items-center justify-center" title="AI 助手"><Sparkles className="w-5 h-5"/></button>

      {/* AI Menu */}
      {showAI && !aiResult && !aiBusy && (
        <div className="fixed bottom-20 right-6 z-40 w-48 bg-white dark:bg-gray-800 rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 p-1.5">
          {AI_TOOLS.map(t=><button key={t.id} onClick={()=>runAI(t.id)} disabled={aiBusy} className="w-full text-left px-4 py-2.5 rounded-xl text-sm hover:bg-gray-100 dark:hover:bg-gray-700 flex items-center gap-2"><Sparkles className="w-3.5 h-3.5 text-purple-500"/>{t.label}</button>)}
        </div>
      )}

      {/* AI Result */}
      {showAI&&aiResult&&<div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-purple-50 dark:bg-purple-900/10">
        <div className="flex items-center justify-between mb-2"><span className="text-xs font-semibold text-purple-700 uppercase">结果</span>
          <div className="flex gap-2"><button onClick={applyAI} className="px-3 py-1 bg-purple-600 text-white text-xs rounded-lg hover:bg-purple-700">插入</button>
          <button onClick={()=>{setShowAI(false);setAiResult('');}} className="p-1 text-gray-400"><X className="w-4 h-4"/></button></div>
        </div>
        <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{aiResult}</p>
      </div>}
      {aiBusy&&<div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-purple-50 dark:bg-purple-900/10 flex items-center gap-2 text-sm text-purple-600"><Loader className="w-4 h-4 animate-spin"/>AI 处理中...</div>}
      {showMedia&&<MediaBrowser onSelect={(url)=>{editor.chain().focus().setImage({src:url}).run();setShowMedia(false);}} onClose={()=>setShowMedia(false)}/>}
      {showPatterns && <PatternLibrary onSelect={(blocks) => {
        blocks.forEach((b) => editor.commands.insertContent(b));
        setShowPatterns(false);
      }} onClose={() => setShowPatterns(false)}/>}
      {showStyles && <StyleManager onClose={() => setShowStyles(false)}/>}
    </div>
  );
};
export default RichEditor;
