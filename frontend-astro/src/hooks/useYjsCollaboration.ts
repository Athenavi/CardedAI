import {useEffect, useRef, useState, useCallback, useMemo} from 'react';
import {getConfig} from '@/lib/config';

export interface Collaborator {
  client_id: string;
  user_id?: number | string;
  user_name?: string;
  color?: string;
}

export interface CollabState {
  connected: boolean;
  connecting: boolean;
  collaborators: Collaborator[];
  content: string;               // Latest HTML received from other editors
  error?: string;
  start: () => void;
  stop: () => void;
  sendContent: (html: string) => void;
  requestSave: () => void;
}

const COLLABORATOR_COLORS = [
  '#ff6b6b', '#51cf66', '#339af0', '#f59f00', '#cc5de8',
  '#20c997', '#e64980', '#15aabf', '#fab005', '#7950f2',
];

// Throttle helper — at most one send per `ms` interval, last call wins
function throttle(fn: (...args: any[]) => void, ms: number) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  let lastArgs: any[] | null = null;
  const later = () => {
    timer = null;
    if (lastArgs) { fn(...lastArgs); lastArgs = null; }
  };
  return (...args: any[]) => {
    lastArgs = args;
    if (!timer) { timer = setTimeout(later, ms); }
  };
}

export function useYjsCollaboration(
  documentId: string | null,
  articleId?: number | string | null,
  token?: string | null,
): CollabState {
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [content, setContent] = useState('');
  const [error, setError] = useState<string | undefined>();

  const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
    const pingTimerRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const colorIndexRef = useRef(0);
  const myClientIdRef = useRef<string>('');
  const stoppedRef = useRef(false);

  // Throttled send to avoid flooding on every keystroke
  const throttledSend = useMemo(() => throttle((html: string) => {
    const ws = wsRef.current;
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({type: 'html_snapshot', html}));
    }
  }, 300), []);

  const sendJson = useCallback((msg: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  const sendContent = useCallback((html: string) => {
    throttledSend(html);
  }, [throttledSend]);

  const requestSave = useCallback(() => {
    sendJson({type: 'save'});
  }, [sendJson]);

  const stop = useCallback(() => {
    stoppedRef.current = true;
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    if (pingTimerRef.current) clearInterval(pingTimerRef.current);
    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.onmessage = null;
      wsRef.current.close();
      wsRef.current = null;
    }
    setConnected(false);
    setConnecting(false);
    setCollaborators([]);
    setContent('');
  }, []);

  const start = useCallback(() => {
    if (!documentId) return;
    stoppedRef.current = false;
    setConnecting(true);
    setError(undefined);
    setContent('');

    const baseUrl = getConfig().API_BASE_URL || `http://${window.location.host}`;
    const wsBase = baseUrl.replace(/^https?:/, (m) => m === 'https:' ? 'wss:' : 'ws:');
    const wsUrl = `${wsBase}/api/v2/collaboration/yjs/ws/${documentId}?article_id=${articleId || ''}${token ? `&token=${encodeURIComponent(token)}` : ''}`;
    console.debug('[Collab WS] Connecting to:', wsUrl);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (stoppedRef.current) { ws.close(); return; }
      setConnected(true);
      setConnecting(false);
      setError(undefined);

      pingTimerRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({type: 'ping'}));
        }
      }, 15000);
    };

    ws.onmessage = (event) => {
      if (event.data instanceof Blob) return; // ignore binary (Yjs not used for content)

      try {
        const msg = JSON.parse(event.data);
        const type = msg.type;

        if (type === 'welcome') {
          myClientIdRef.current = msg.client_id || '';
          // Set initial collaborators list
          const existing: Collaborator[] = (msg.clients || []).map((c) => ({
            client_id: c.client_id,
          }));
          setCollaborators(existing);
          // If server has an HTML snapshot, load it
          if (msg.html_snapshot) {
            setContent(msg.html_snapshot);
          }
        } else if (type === 'awareness') {
          const state = msg.state || {};
          if (state.type === 'user_joined') {
            setCollaborators(prev => {
              if (prev.find(c => c.client_id === state.client_id)) return prev;
              const color = COLLABORATOR_COLORS[colorIndexRef.current % COLLABORATOR_COLORS.length];
              colorIndexRef.current++;
              return [...prev, {client_id: state.client_id, user_id: state.user_id, user_name: state.user_name, color}];
            });
          } else if (state.type === 'user_left') {
            setCollaborators(prev => prev.filter(c => c.client_id !== state.client_id));
          }
        } else if (type === 'html_snapshot') {
          // Another collaborator's content snapshot — update our editor
          if (msg.html && msg.client_id !== myClientIdRef.current) {
            setContent(msg.html);
          }
        } else if (type === 'save_result') {
          window.dispatchEvent(new CustomEvent('yjs-save-result', {
            detail: { success: msg.success, message: msg.message },
          }));
        }
      } catch (e) {
        // ignore
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (pingTimerRef.current) clearInterval(pingTimerRef.current);
      if (!stoppedRef.current) {
        reconnectTimerRef.current = setTimeout(() => {
          if (!stoppedRef.current) start();
        }, 3000);
      }
    };

    ws.onerror = () => {
      setError('连接失败');
      setConnecting(false);
    };
  }, [documentId, articleId, token]);

  // Cleanup
  useEffect(() => {
    return () => { stop(); };
  }, [stop]);

  return {
    connected,
    connecting,
    collaborators,
    content,
    error,
    start,
    stop,
    sendContent,
    requestSave,
  };
}
