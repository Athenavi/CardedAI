'use client';

import React, {useState, useRef, useEffect, useCallback} from 'react';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {
  Bot,
  Send,
  Settings2,
  Save,
  Trash2,
  Sparkles,
  User,
  AlertCircle,
  Loader2,
  ChevronDown,
  ChevronUp,
  Terminal,
  Check,
  X,
} from 'lucide-react';

// ═══ Types ═══
interface ChatMessage {
  role: 'user' | 'assistant';
  content?: string | null;
  tool_calls?: any[];
  tool_call_id?: string;
}

interface ToolResult {
  tool: string;
  arguments: any;
  result: any;
}

interface LLMConfig {
  endpoint: string;
  key: string;
  model: string;
}

// ═══ Config Form ═══
function ConfigPanel({config, onSave, onClose}: {
  config: LLMConfig;
  onSave: (c: LLMConfig) => void;
  onClose: () => void;
}) {
  const [endpoint, setEndpoint] = useState(config.endpoint);
  const [key, setKey] = useState(config.key);
  const [model, setModel] = useState(config.model);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    onSave({endpoint, key, model});
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm"
         onClick={onClose}>
      <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-6 w-full max-w-lg mx-4"
           onClick={e => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Settings2 className="w-5 h-5 text-blue-500"/>
            LLM 连接配置
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300">
            <X className="w-5 h-5"/>
          </button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              请求端点 <span className="text-red-500">*</span>
            </label>
            <input type="text" value={endpoint}
              onChange={e => setEndpoint(e.target.value)}
              placeholder="https://api.openai.com/v1"
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"/>
            <p className="text-xs text-gray-400 mt-1">兼容 OpenAI API 格式的端点地址</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              API Key (sk-...) <span className="text-red-500">*</span>
            </label>
            <input type="password" value={key}
              onChange={e => setKey(e.target.value)}
              placeholder="sk-..."
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"/>
            <p className="text-xs text-gray-400 mt-1">仅保存在当前浏览器会话中，不会上传到服务器</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              模型
            </label>
            <input type="text" value={model}
              onChange={e => setModel(e.target.value)}
              placeholder="gpt-4o"
              className="w-full px-3 py-2 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"/>
          </div>
        </div>

        <div className="flex items-center gap-3 mt-6">
          <button onClick={handleSave}
            className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition-colors">
            {saved ? <><Check className="w-4 h-4"/> 已保存</> : <><Save className="w-4 h-4"/> 保存配置</>}
          </button>
          <button onClick={onClose}
            className="px-4 py-2.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors">
            取消
          </button>
        </div>
      </div>
    </div>
  );
}

// ═══ Tool Call Card ═══
function ToolCallCard({tool, args, result}: { tool: string; args: any; result: any }) {
  const [expanded, setExpanded] = useState(false);
  const success = result?.success !== false;

  return (
    <div className="mt-2 rounded-xl border border-gray-100 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 overflow-hidden">
      <button onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 text-xs">
        <div className="flex items-center gap-2">
          <Terminal className={`w-3.5 h-3.5 ${success ? 'text-green-500' : 'text-red-500'}`}/>
          <span className="font-mono text-gray-700 dark:text-gray-300">{tool}</span>
          {success
            ? <span className="text-green-500 text-[10px]">✓ 完成</span>
            : <span className="text-red-500 text-[10px]">✗ 失败</span>}
        </div>
        {expanded ? <ChevronUp className="w-3.5 h-3.5 text-gray-400"/> : <ChevronDown className="w-3.5 h-3.5 text-gray-400"/>}
      </button>
      {expanded && (
        <div className="px-3 pb-2 space-y-1.5">
          <div className="text-[10px] text-gray-400">参数:</div>
          <pre className="text-[10px] text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-900 rounded-lg p-2 overflow-x-auto">{JSON.stringify(args, null, 2)}</pre>
          <div className="text-[10px] text-gray-400">结果:</div>
          <pre className="text-[10px] text-gray-600 dark:text-gray-400 bg-white dark:bg-gray-900 rounded-lg p-2 overflow-x-auto max-h-32 overflow-y-auto">{JSON.stringify(result, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

// ═══ Message Bubble ═══
function MessageBubble({msg, toolResults, streamingContent}: {
  msg: ChatMessage;
  toolResults?: ToolResult[];
  streamingContent?: string;
}) {
  const isUser = msg.role === 'user';
  const hasToolCalls = msg.tool_calls && msg.tool_calls.length > 0;
  const displayContent = streamingContent ?? msg.content ?? '';

  // Lazy-load react-markdown only when rendering assistant messages
  const [Markdown, setMarkdown] = useState<React.ComponentType<{children: string}> | null>(null);
  useEffect(() => {
    if (!isUser && displayContent) {
      import('react-markdown').then(mod => setMarkdown(() => mod.default));
    }
  }, [isUser, displayContent]);

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 ${
        isUser ? 'bg-blue-100 dark:bg-blue-900/30' : 'bg-purple-100 dark:bg-purple-900/30'
      }`}>
        {isUser
          ? <User className="w-4 h-4 text-blue-600 dark:text-blue-400"/>
          : <Bot className="w-4 h-4 text-purple-600 dark:text-purple-400"/>}
      </div>

      <div className={`max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        {/* Message content with markdown rendering */}
        {displayContent && (
          <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? 'bg-blue-600 text-white rounded-tr-md'
              : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-tl-md prose prose-sm dark:prose-invert max-w-none'
          }`}>
            {isUser ? (
              <span className="whitespace-pre-wrap">{displayContent}</span>
            ) : Markdown ? (
              <Markdown>{displayContent}</Markdown>
            ) : (
              <span className="whitespace-pre-wrap">{displayContent}</span>
            )}
            {streamingContent !== undefined && (
              <span className="animate-pulse ml-0.5 inline-block w-1.5 h-4 bg-purple-500 rounded-sm"/>
            )}
          </div>
        )}

        {/* Tool calls (assistant only) */}
        {hasToolCalls && toolResults && toolResults.map((tr, i) => (
          <ToolCallCard key={i} tool={tr.tool} args={tr.arguments} result={tr.result}/>
        ))}
      </div>
    </div>
  );
}

// ═══ Welcome Screen ═══
function WelcomeScreen({onExample}: { onExample: (text: string) => void }) {
  const examples = [
    '帮我写一篇关于 AI 技术的文章，标题为「2026年AI趋势展望」',
    '列出所有已发布文章',
    '搜索情报中关于「人工智能」的内容',
    '当前系统有哪些 MCP 工具可用？',
  ];

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-purple-500 to-blue-600 flex items-center justify-center mb-4 shadow-lg">
        <Bot className="w-8 h-8 text-white"/>
      </div>
      <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">CardedAI 助手</h2>
      <p className="text-sm text-gray-500 dark:text-gray-400 text-center max-w-md mb-8">
        通过自然语言对话管理你的站点。输入你的 LLM API Key 和端点后即可开始。
      </p>

      <div className="grid gap-2 w-full max-w-lg">
        <p className="text-xs text-gray-400 mb-1 text-center">试试这些问题：</p>
        {examples.map((ex, i) => (
          <button key={i} onClick={() => onExample(ex)}
            className="text-left px-4 py-2.5 rounded-xl border border-gray-200 dark:border-gray-700 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 hover:border-gray-300 dark:hover:border-gray-600 transition-colors">
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}

// ═══ Chat Area ═══
function ChatArea() {
  const [config, setConfig] = useState<LLMConfig>(() => {
    try {
      const saved = localStorage.getItem('ai-llm-config');
      return saved ? JSON.parse(saved) : {endpoint: 'https://api.openai.com/v1', key: '', model: 'gpt-4o'};
    } catch { return {endpoint: 'https://api.openai.com/v1', key: '', model: 'gpt-4o'}; }
  });
  const [showConfig, setShowConfig] = useState(!config.key);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [toolResults, setToolResults] = useState<ToolResult[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => { chatEndRef.current?.scrollIntoView({behavior: 'smooth'}); }, [messages, toolResults]);

  const saveConfig = useCallback((c: LLMConfig) => {
    setConfig(c);
    localStorage.setItem('ai-llm-config', JSON.stringify(c));
    setShowConfig(false);
  }, []);

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim() || loading) return;
    if (!config.key) { setShowConfig(true); return; }

    const userMsg: ChatMessage = {role: 'user', content: text};
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);
    setStreamingContent('');
    setToolResults([]);

    const abortController = new AbortController();
    abortRef.current = abortController;

    try {
      const url = `${window.location.origin}/api/v2/ai/mcp-chat/stream`;
      const resp = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          messages: newMessages.map(m => ({
            role: m.role,
            content: m.content || '',
            tool_calls: m.tool_calls,
          })),
          llm_endpoint: config.endpoint,
          llm_key: config.key,
          model: config.model,
        }),
        signal: abortController.signal,
      });

      if (!resp.ok) {
        setMessages(prev => [...prev, {role: 'assistant', content: `❌ 请求失败 (${resp.status})`}]);
        setLoading(false);
        setStreamingContent(null);
        return;
      }

      const reader = resp.body?.getReader();
      if (!reader) throw new Error('No reader available');

      const decoder = new TextDecoder();
      let buffer = '';
      let finalReply = '';

      while (true) {
        const {done, value} = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, {stream: true});
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          try {
            const data = JSON.parse(line.slice(6));
            if (data.type === 'token') {
              finalReply += data.content;
              setStreamingContent(finalReply);
            } else if (data.type === 'tool_result') {
              setToolResults(prev => [...prev, {
                tool: data.tool, arguments: {}, result: {data: data.result},
              }]);
            } else if (data.type === 'done') {
              if (data.reply) finalReply = data.reply;
              const results = data.tool_results || [];
              const assistantMsg: ChatMessage = {role: 'assistant', content: finalReply};
              if (results.length > 0) {
                assistantMsg.tool_calls = results.map(() => ({type: 'function'}));
              }
              setMessages(prev => [...prev, assistantMsg]);
              setToolResults(prev => [...prev, ...results]);
              setStreamingContent(null);
            } else if (data.type === 'error') {
              setMessages(prev => [...prev, {role: 'assistant', content: `❌ ${data.content}`}]);
              setStreamingContent(null);
            }
          } catch {}
        }
      }
    } catch (e: any) {
      if (e.name === 'AbortError') return;
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ 网络错误: ${e.message || '无法连接到服务器'}`,
      }]);
    } finally {
      setLoading(false);
      abortRef.current = null;
      setStreamingContent(prev => {
        if (prev) {
          setMessages(msgs => [...msgs, {role: 'assistant', content: prev}]);
        }
        return null;
      });
    }
  }, [config, messages, loading]);

  const clearChat = () => {
    setMessages([]);
    setToolResults([]);
  };

  const handleExample = (text: string) => {
    if (!config.key) { setShowConfig(true); return; }
    sendMessage(text);
  };

  return (
    <>
      {/* Header bar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-500"/>
            AI 助手
          </h1>
          {config.key && (
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/20 text-green-600 dark:text-green-400">
              已连接
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={clearChat} disabled={messages.length === 0}
            className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-30"
            title="清空对话">
            <Trash2 className="w-4 h-4"/>
          </button>
          <button onClick={() => setShowConfig(true)}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
            <Settings2 className="w-3.5 h-3.5"/>
            配置
          </button>
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto min-h-0 space-y-4 pb-4">
        {messages.length === 0 && !loading ? (
          <WelcomeScreen onExample={handleExample}/>
        ) : (
          messages.map((msg, i) => (
            <MessageBubble key={i} msg={msg}
              toolResults={i === messages.length - 1 ? toolResults : undefined}
              streamingContent={i === messages.length - 1 && streamingContent !== null && msg.role === 'assistant' ? streamingContent : undefined}/>
          ))
        )}

        {loading && (
          streamingContent ? (
            <MessageBubble msg={{role: 'assistant', content: streamingContent}} streamingContent={streamingContent}/>
          ) : (
            <div className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-xl bg-purple-100 dark:bg-purple-900/30 flex items-center justify-center">
                <Bot className="w-4 h-4 text-purple-600 dark:text-purple-400"/>
              </div>
              <div className="px-4 py-3 rounded-2xl bg-gray-100 dark:bg-gray-800 rounded-tl-md">
                <Loader2 className="w-5 h-5 text-purple-500 animate-spin"/>
              </div>
            </div>
          )
        )}
        <div ref={chatEndRef}/>
      </div>

      {/* Input bar */}
      <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
        <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-2">
          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); } }}
            placeholder={config.key ? '输入你的需求，例如「写一篇关于AI的文章」...' : '请先点击右上角配置 LLM 连接...'}
            disabled={loading}
            className="flex-1 bg-transparent text-sm text-gray-900 dark:text-white placeholder-gray-400 outline-none resize-none py-1.5 disabled:opacity-50"
          />
          <button onClick={() => sendMessage(input)} disabled={loading || !input.trim()}
            className="p-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition-colors disabled:opacity-40 disabled:cursor-not-allowed">
            <Send className="w-4 h-4"/>
          </button>
        </div>
        <p className="text-[10px] text-gray-400 mt-1.5 text-center">
          发送即表示你的 API Key 仅用于本次对话，不会被持久化存储
        </p>
      </div>

      {/* Config modal */}
      {showConfig && <ConfigPanel config={config} onSave={saveConfig} onClose={() => config.key && setShowConfig(false)}/>}
    </>
  );
}

// ═══ Export ═══
export default function AdminAI() {
  return (
    <AuthGuard>
      <QueryProvider>
        <AdminShell title="AI 助手">
          <div className="h-[calc(100vh-8rem)] flex flex-col">
            <ChatArea/>
          </div>
        </AdminShell>
      </QueryProvider>
    </AuthGuard>
  );
}
