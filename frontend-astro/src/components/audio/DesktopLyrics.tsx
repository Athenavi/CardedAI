'use client';

import React, {useCallback, useEffect, useRef, useState, useMemo} from 'react';
import {motion, AnimatePresence} from 'framer-motion';

/* ---------- Types ---------- */

interface LyricLine {
  time: number;
  text: string;
}

type AnimPreset = 'fade-up' | 'fade-scale' | 'slide-left' | 'slide-right' | 'typewriter';

interface LyricsSettings {
  x: number;
  y: number;
  fontSize: number;
  fontFamily: string;
  opacity: number;
  gradientId: string;
  boxWidth: number;
  entryAnim: AnimPreset;
  exitAnim: AnimPreset;
}

const GRADIENTS: { id: string; label: string; from: string; via: string; to: string; shadow: string }[] = [
  {id: 'purple-pink', label: '紫粉', from: '#a855f7', via: '#d946ef', to: '#ec4899', shadow: 'rgba(168,85,247,0.5)'},
  {id: 'cyan-blue', label: '青蓝', from: '#06b6d4', via: '#3b82f6', to: '#6366f1', shadow: 'rgba(59,130,246,0.5)'},
  {id: 'green-emerald', label: '翠绿', from: '#34d399', via: '#10b981', to: '#059669', shadow: 'rgba(16,185,129,0.5)'},
  {id: 'orange-rose', label: '暖橙', from: '#fb923c', via: '#f43f5e', to: '#e11d48', shadow: 'rgba(244,63,94,0.5)'},
  {id: 'white-glow', label: '白辉', from: '#ffffff', via: '#e2e8f0', to: '#94a3b8', shadow: 'rgba(255,255,255,0.4)'},
  {id: 'gold-amber', label: '金色', from: '#fbbf24', via: '#f59e0b', to: '#d97706', shadow: 'rgba(245,158,11,0.5)'},
];

const FONTS: { value: string; label: string }[] = [
  {value: 'system-ui, sans-serif', label: '系统'},
  {value: '"PingFang SC", "Microsoft YaHei", sans-serif', label: '雅黑'},
  {value: '"Noto Sans SC", sans-serif', label: 'Noto'},
  {value: '"Songti SC", "SimSun", serif', label: '宋体'},
  {value: '"STKaiti", "KaiTi", serif', label: '楷体'},
  {value: 'monospace', label: '等宽'},
];

const ANIM_PRESETS: { value: AnimPreset; label: string; desc: string }[] = [
  {value: 'fade-up', label: '淡入上移', desc: 'opacity 0→1 + y 16→0'},
  {value: 'fade-scale', label: '淡入缩放', desc: 'opacity 0→1 + scale 0.8→1'},
  {value: 'slide-left', label: '右侧滑入', desc: 'x 40→0 + opacity'},
  {value: 'slide-right', label: '左侧滑入', desc: 'x -40→0 + opacity'},
  {value: 'typewriter', label: '打字机', desc: 'clipPath 逐字展开'},
];

const LS_KEY = 'fastblog_desktop_lyrics';
const DEFAULT_SETTINGS: LyricsSettings = {
  x: 50, y: 50, fontSize: 18, fontFamily: 'system-ui, sans-serif', opacity: 90, gradientId: 'purple-pink',
  boxWidth: 520, entryAnim: 'fade-up', exitAnim: 'fade-scale',
};

function loadSettings(): LyricsSettings {
  try {
    const raw = localStorage.getItem(LS_KEY);
    return raw ? {...DEFAULT_SETTINGS, ...JSON.parse(raw)} : DEFAULT_SETTINGS;
  } catch { return DEFAULT_SETTINGS; }
}

function saveSettings(s: LyricsSettings) {
  localStorage.setItem(LS_KEY, JSON.stringify(s));
}

function resetSettings(): LyricsSettings {
  localStorage.removeItem(LS_KEY);
  return {...DEFAULT_SETTINGS};
}

/* ---------- Tokenize ---------- */

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

/* ---------- Animation variants ---------- */

function entryVariants(preset: AnimPreset) {
  switch (preset) {
    case 'fade-up':
      return {initial: {opacity: 0, y: 20, filter: 'blur(4px)'}, animate: {opacity: 1, y: 0, filter: 'blur(0px)'}};
    case 'fade-scale':
      return {initial: {opacity: 0, scale: 0.8, filter: 'blur(3px)'}, animate: {opacity: 1, scale: 1, filter: 'blur(0px)'}};
    case 'slide-left':
      return {initial: {opacity: 0, x: 40}, animate: {opacity: 1, x: 0}};
    case 'slide-right':
      return {initial: {opacity: 0, x: -40}, animate: {opacity: 1, x: 0}};
    case 'typewriter':
      return {initial: {opacity: 0, clipPath: 'inset(0 100% 0 0)'}, animate: {opacity: 1, clipPath: 'inset(0 0% 0 0)'}};
  }
}

function exitVariants(preset: AnimPreset) {
  switch (preset) {
    case 'fade-up':
      return {exit: {opacity: 0, y: -16, scale: 0.95, filter: 'blur(3px)'}};
    case 'fade-scale':
      return {exit: {opacity: 0, scale: 0.85, filter: 'blur(4px)'}};
    case 'slide-left':
      return {exit: {opacity: 0, x: -30}};
    case 'slide-right':
      return {exit: {opacity: 0, x: 30}};
    case 'typewriter':
      return {exit: {opacity: 0, clipPath: 'inset(0 0% 0 100%)'}};
  }
}

/* ========== Settings Panel ========== */

const SettingsPanel: React.FC<{
  settings: LyricsSettings;
  onChange: (s: LyricsSettings) => void;
  onClose: () => void;
  onReset: () => void;
  prevLyric: string | null;
  nextLyric: string | null;
}> = ({settings, onChange, onClose, onReset, prevLyric, nextLyric}) => {
  return (
      <motion.div
          initial={{opacity: 0, y: 10, scale: 0.95}}
          animate={{opacity: 1, y: 0, scale: 1}}
          exit={{opacity: 0, y: 10, scale: 0.95}}
          className="fixed bottom-6 right-6 z-[70] bg-neutral-900/95 backdrop-blur-2xl rounded-2xl border border-white/10 shadow-2xl p-4 w-80 max-h-[80vh] overflow-y-auto"
          onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-3">
          <span className="text-white text-sm font-semibold">桌面歌词设置</span>
          <button onClick={onClose} className="w-6 h-6 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white/50 text-xs">✕</button>
        </div>

        {/* 容器宽度 */}
        <div className="mb-3">
          <label className="text-white/50 text-xs block mb-1">歌词框宽度 ({settings.boxWidth}px)</label>
          <input type="range" min={260} max={900} step={10} value={settings.boxWidth}
                 onChange={e => onChange({...settings, boxWidth: parseInt(e.target.value)})}
                 className="w-full h-1 bg-white/20 rounded-full appearance-none cursor-pointer accent-purple-500"
                 style={{background: `linear-gradient(to right, #a855f7 ${(settings.boxWidth-260)/(900-260)*100}%, rgba(255,255,255,0.15) ${(settings.boxWidth-260)/(900-260)*100}%)`}}
          />
          <div className="flex justify-between text-[10px] text-white/30 mt-0.5"><span>260</span><span>900</span></div>
        </div>

        {/* 字号 */}
        <div className="mb-3">
          <label className="text-white/50 text-xs block mb-1">字号</label>
          <div className="flex items-center gap-2">
            <button onClick={() => onChange({...settings, fontSize: Math.max(12, settings.fontSize - 1)})}
                    className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 text-white/80 text-sm font-bold">A−</button>
            <span className="text-white text-sm text-center w-10 tabular-nums">{settings.fontSize}</span>
            <button onClick={() => onChange({...settings, fontSize: Math.min(40, settings.fontSize + 1)})}
                    className="w-8 h-8 rounded-lg bg-white/10 hover:bg-white/20 text-white/80 text-sm font-bold">A+</button>
          </div>
        </div>

        {/* 字体 */}
        <div className="mb-3">
          <label className="text-white/50 text-xs block mb-1">字体</label>
          <div className="flex flex-wrap gap-1.5">
            {FONTS.map(f => (
                <button key={f.value}
                        onClick={() => onChange({...settings, fontFamily: f.value})}
                        className={`px-3 py-1.5 rounded-lg text-xs transition-colors ${
                            settings.fontFamily === f.value
                                ? 'bg-purple-600/40 text-purple-300 border border-purple-500/40'
                                : 'bg-white/10 hover:bg-white/20 text-white/70 border border-transparent'
                        }`}
                        style={{fontFamily: f.value}}
                >{f.label}</button>
            ))}
          </div>
        </div>

        {/* 高亮颜色 */}
        <div className="mb-3">
          <label className="text-white/50 text-xs block mb-1">高亮颜色</label>
          <div className="flex flex-wrap gap-1.5">
            {GRADIENTS.map(g => (
                <button key={g.id}
                        onClick={() => onChange({...settings, gradientId: g.id})}
                        className={`w-7 h-7 rounded-full transition-all ${
                            settings.gradientId === g.id ? 'ring-2 ring-white scale-110' : ''
                        }`}
                        style={{background: `linear-gradient(135deg, ${g.from}, ${g.via}, ${g.to})`}}
                        title={g.label}
                />
            ))}
          </div>
        </div>

        {/* 透明度 */}
        <div className="mb-3">
          <label className="text-white/50 text-xs block mb-1">透明度 ({settings.opacity}%)</label>
          <input type="range" min={30} max={100} value={settings.opacity}
                 onChange={e => onChange({...settings, opacity: parseInt(e.target.value)})}
                 className="w-full h-1 bg-white/20 rounded-full appearance-none cursor-pointer accent-purple-500"
                 style={{background: `linear-gradient(to right, #a855f7 ${settings.opacity}%, rgba(255,255,255,0.15) ${settings.opacity}%)`}}
          />
        </div>

        {/* 入场动画 */}
        <div className="mb-3">
          <label className="text-white/50 text-xs block mb-1">入场动画</label>
          <div className="grid grid-cols-2 gap-1.5">
            {ANIM_PRESETS.map(a => (
                <button key={a.value}
                        onClick={() => onChange({...settings, entryAnim: a.value})}
                        className={`px-2 py-1.5 rounded-lg text-xs transition-colors text-left ${
                            settings.entryAnim === a.value
                                ? 'bg-purple-600/40 text-purple-300 border border-purple-500/40'
                                : 'bg-white/10 hover:bg-white/20 text-white/60 border border-transparent'
                        }`}
                >
                  <div className="font-medium">{a.label}</div>
                  <div className="text-[10px] opacity-60 mt-0.5">{a.desc}</div>
                </button>
            ))}
          </div>
        </div>

        {/* 退场动画 */}
        <div className="mb-3">
          <label className="text-white/50 text-xs block mb-1">退场动画</label>
          <div className="grid grid-cols-2 gap-1.5">
            {ANIM_PRESETS.map(a => (
                <button key={a.value}
                        onClick={() => onChange({...settings, exitAnim: a.value})}
                        className={`px-2 py-1.5 rounded-lg text-xs transition-colors text-left ${
                            settings.exitAnim === a.value
                                ? 'bg-purple-600/40 text-purple-300 border border-purple-500/40'
                                : 'bg-white/10 hover:bg-white/20 text-white/60 border border-transparent'
                        }`}
                >
                  <div className="font-medium">{a.label}</div>
                  <div className="text-[10px] opacity-60 mt-0.5">{a.desc}</div>
                </button>
            ))}
          </div>
        </div>

        {/* 预览 */}
        <div className="border-t border-white/10 pt-3 mt-1">
          <label className="text-white/50 text-xs block mb-2">预览</label>
          <div className="space-y-2 text-center" style={{fontFamily: settings.fontFamily}}>
            {prevLyric && <p className="text-white/30 text-xs truncate" style={{fontSize: settings.fontSize - 4}}>{prevLyric}</p>}
            {nextLyric && <p className="text-white/60 text-sm truncate" style={{fontSize: settings.fontSize}}>{nextLyric}</p>}
          </div>
        </div>

        {/* 恢复默认 */}
        <button onClick={onReset}
                className="w-full mt-3 py-2 rounded-lg bg-red-500/15 hover:bg-red-500/25 text-red-400 text-xs font-medium transition-colors flex items-center justify-center gap-2 border border-red-500/20">
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
          </svg>
          恢复所有设置为默认
        </button>
      </motion.div>
  );
};

/* ========== DesktopLyrics ========== */

const DesktopLyrics: React.FC<{
  lyrics: LyricLine[];
  activeLineIndex: number;
  karaokeProgress: number;
  visible: boolean;
  onVisibilityChange: (v: boolean) => void;
}> = ({lyrics, activeLineIndex, karaokeProgress, visible, onVisibilityChange}) => {
  const [settings, setSettings] = useState<LyricsSettings>(loadSettings);
  const [showSettings, setShowSettings] = useState(false);
  const [prevActiveIndex, setPrevActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const [scrollOffset, setScrollOffset] = useState(0);
  const dragRef = useRef<{startX: number; startY: number; origX: number; origY: number; dragging: boolean} | null>(null);

  useEffect(() => { saveSettings(settings); }, [settings]);

  // 跟踪上一行索引
  useEffect(() => {
    if (activeLineIndex >= 0 && activeLineIndex !== prevActiveIndex) {
      setPrevActiveIndex(activeLineIndex);
      setScrollOffset(0);
    }
  }, [activeLineIndex, prevActiveIndex]);

  // ESC
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        if (showSettings) setShowSettings(false);
        else onVisibilityChange(false);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showSettings, onVisibilityChange]);

  // Karaoke 横向滚动
  useEffect(() => {
    if (!textRef.current || !containerRef.current) return;
    const textEl = textRef.current;
    const containerWidth = settings.boxWidth;
    const textWidth = textEl.scrollWidth;

    if (textWidth <= containerWidth) {
      setScrollOffset(0);
      return;
    }

    const tokens = currentLyric ? tokenizeText(currentLyric.text) : [];
    if (!tokens.length) { setScrollOffset(0); return; }

    const highlightCount = Math.floor(tokens.length * karaokeProgress);
    if (highlightCount <= 0) { setScrollOffset(0); return; }

    const avgTokenWidth = textWidth / tokens.length;
    const highlightCenter = highlightCount * avgTokenWidth;
    const targetOffset = Math.max(0, highlightCenter - containerWidth / 2);
    const maxOffset = Math.max(0, textWidth - containerWidth);
    const clamped = Math.min(targetOffset, maxOffset);

    setScrollOffset(prev => {
      const diff = clamped - prev;
      if (Math.abs(diff) < 2) return clamped;
      return prev + diff * 0.15;
    });
  });

  // 拖拽
  const onPointerDown = useCallback((e: React.PointerEvent) => {
    dragRef.current = {
      startX: e.clientX, startY: e.clientY,
      origX: settings.x, origY: settings.y,
      dragging: false,
    };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }, [settings.x, settings.y]);

  const onPointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    if (Math.abs(dx) > 3 || Math.abs(dy) > 3) dragRef.current.dragging = true;
    setSettings(s => ({
      ...s,
      x: Math.max(0, Math.min(95, dragRef.current!.origX + dx / window.innerWidth * 100)),
      y: Math.max(0, Math.min(90, dragRef.current!.origY + dy / window.innerHeight * 100)),
    }));
  }, []);

  const onPointerUp = useCallback(() => { dragRef.current = null; }, []);

  // 阻止事件冒泡
  const stopProp = useCallback((e: React.MouseEvent | React.PointerEvent | React.TouchEvent) => {
    e.stopPropagation();
  }, []);

  // 重置设置
  const handleReset = useCallback(() => {
    setSettings(resetSettings());
  }, []);

  // ── 以下计算在 early-return 前完成，保证 hooks 顺序不变 ──

  const currentLyric = activeLineIndex >= 0 ? lyrics[activeLineIndex] : null;

  const highlightedTokens = useMemo(() => {
    if (!currentLyric) return [];
    const tokens = tokenizeText(currentLyric.text);
    const highlightCount = Math.floor(tokens.length * karaokeProgress);
    return tokens.map((t, i) => ({
      token: t,
      highlighted: i < highlightCount,
      transitioning: i === highlightCount - 1 && karaokeProgress < 1,
      clipProgress: i === highlightCount - 1 && karaokeProgress < 1
          ? (karaokeProgress * tokens.length - i)
          : (i < highlightCount ? 1 : 0),
    }));
  }, [currentLyric, karaokeProgress]);

  const prevLyric = activeLineIndex > 0 ? lyrics[activeLineIndex - 1] : null;
  const nextLyric = activeLineIndex >= 0 && activeLineIndex + 1 < lyrics.length ? lyrics[activeLineIndex + 1] : null;
  const gradient = GRADIENTS.find(g => g.id === settings.gradientId) ?? GRADIENTS[0];

  const entryV = entryVariants(settings.entryAnim);
  const exitV = exitVariants(settings.exitAnim);
    const entryTrans = {duration: 0.4, ease: [0.16, 1, 0.3, 1] as [number, number, number, number]};
    const exitTrans = {duration: 0.35, ease: 'easeOut' as const};

  if (!visible || !lyrics.length) return null;

  return (
      <>
        {/* ── 歌词容器 ── */}
        <motion.div
            ref={containerRef}
            className="fixed z-[65] select-none touch-none"
            style={{
              left: `${settings.x}%`,
              top: `${settings.y}%`,
              transform: 'translate(-50%, -50%)',
            }}
            initial={{opacity: 0, scale: 0.9}}
            animate={{opacity: settings.opacity / 100, scale: 1}}
            transition={{duration: 0.25}}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            onDoubleClick={() => onVisibilityChange(false)}
        >
          <div
              className="bg-black/55 backdrop-blur-2xl rounded-2xl px-6 py-5 border border-white/8 shadow-2xl text-center leading-relaxed cursor-grab active:cursor-grabbing transition-shadow hover:shadow-purple-500/5 overflow-hidden"
              style={{
                width: `${settings.boxWidth}px`,
                minWidth: '260px',
                maxWidth: '900px',
              }}
          >
            {/* 上一行 */}
            <AnimatePresence mode="popLayout">
              {prevLyric && activeLineIndex > 0 && prevActiveIndex === activeLineIndex - 1 && (
                  <motion.p
                      key={`prev-${activeLineIndex}`}
                      initial={{opacity: 1, y: 0}}
                      animate={{opacity: 0.25, y: -8}}
                      exit={{...exitV.exit, opacity: 0, transition: exitTrans}}
                      transition={{duration: 0.35, ease: 'easeOut' as const}}
                      className="text-white/40 text-sm truncate mb-2"
                      style={{fontSize: Math.max(12, settings.fontSize - 4), fontFamily: settings.fontFamily}}
                  >
                    {prevLyric.text}
                  </motion.p>
              )}
            </AnimatePresence>

            {/* 当前行 */}
            <div className="relative overflow-hidden" style={{height: `${settings.fontSize * 1.6}px`}}>
              <motion.div
                  ref={textRef}
                  key={`curr-${activeLineIndex}`}
                  initial={{...entryV.initial}}
                  animate={{...entryV.animate, x: -scrollOffset}}
                  exit={{...exitV.exit, transition: exitTrans}}
                  transition={entryTrans}
                  className="absolute inset-0 flex items-center justify-center font-bold tracking-wide whitespace-nowrap"
                  style={{fontFamily: settings.fontFamily, fontSize: `${settings.fontSize}px`}}
              >
                {currentLyric ? (
                    highlightedTokens.map((item, ti) => {
                      if (item.token === ' ') return <span key={ti} className="inline-block" style={{width: '0.3em'}}>&nbsp;</span>;
                      return (
                          <span key={ti} className="relative inline-block mx-[0.5px]">
                        <span className={item.highlighted ? 'text-transparent' : 'text-white/60'}>{item.token}</span>
                            {item.highlighted && (
                                <span className="absolute inset-0 bg-clip-text text-transparent"
                                      style={{
                                        background: `linear-gradient(135deg, ${gradient.from}, ${gradient.via}, ${gradient.to})`,
                                        WebkitBackgroundClip: 'text',
                                        filter: `drop-shadow(0 0 ${settings.fontSize > 20 ? 12 : 8}px ${gradient.shadow})`,
                                      }}
                                >{item.token}</span>
                            )}
                            {item.transitioning && (
                                <span className="absolute inset-0 overflow-hidden" style={{color: 'transparent'}}>
                              <span className="absolute inset-0 bg-clip-text text-transparent"
                                    style={{
                                      background: `linear-gradient(135deg, ${gradient.from}, ${gradient.via}, ${gradient.to})`,
                                      WebkitBackgroundClip: 'text',
                                      clipPath: `inset(0 ${(1 - item.clipProgress) * 100}% 0 0)`,
                                      filter: `drop-shadow(0 0 ${settings.fontSize > 20 ? 14 : 10}px ${gradient.shadow})`,
                                    }}
                              >{item.token}</span>
                            </span>
                            )}
                      </span>
                      );
                    })
                ) : (
                    <span className="text-white/30">等待播放...</span>
                )}
              </motion.div>
            </div>

            {/* 下一行 */}
            <AnimatePresence mode="popLayout">
              {nextLyric && activeLineIndex >= 0 && (
                  <motion.p
                      key={`next-${activeLineIndex}`}
                      initial={{opacity: 0, y: 12}}
                      animate={{opacity: 0.3, y: 6}}
                      exit={{opacity: 0, y: 20}}
                      transition={{duration: 0.4, delay: 0.15, ease: 'easeOut'}}
                      className="text-white/25 text-sm truncate mt-2"
                      style={{fontSize: Math.max(11, settings.fontSize - 6), fontFamily: settings.fontFamily}}
                  >
                    {nextLyric.text}
                  </motion.p>
              )}
            </AnimatePresence>
          </div>

          {/* ── 悬停控制条 ── */}
          <div
              className="flex items-center justify-center gap-2 mt-2 opacity-0 group-hover:opacity-100 sm:opacity-0 sm:hover:opacity-100 transition-opacity duration-200"
              onClick={stopProp}
              onPointerDown={stopProp}
          >
            <button onClick={(e) => { e.stopPropagation(); onVisibilityChange(false); }}
                    className="w-7 h-7 rounded-full bg-black/50 backdrop-blur border border-white/10 hover:bg-white/15 flex items-center justify-center text-white/50 text-xs transition-colors"
                    title="关闭桌面歌词">✕</button>
            <button onClick={(e) => { e.stopPropagation(); setShowSettings(v => !v); }}
                    className={`w-7 h-7 rounded-full backdrop-blur border flex items-center justify-center text-xs transition-colors ${
                        showSettings ? 'bg-purple-600/40 border-purple-500/40 text-purple-300' : 'bg-black/50 border-white/10 hover:bg-white/15 text-white/50'
                    }`}
                    title="歌词设置">
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
            </button>
          </div>
        </motion.div>

        {/* ── 设置面板 ── */}
        <AnimatePresence>
          {showSettings && (
              <SettingsPanel
                  settings={settings}
                  onChange={setSettings}
                  onClose={() => setShowSettings(false)}
                  onReset={handleReset}
                  prevLyric={prevLyric?.text ?? null}
                  nextLyric={nextLyric?.text ?? null}
              />
          )}
        </AnimatePresence>
      </>
  );
};

export default DesktopLyrics;
export {tokenizeText, GRADIENTS, FONTS, ANIM_PRESETS};
export type {LyricsSettings, LyricLine, AnimPreset};
