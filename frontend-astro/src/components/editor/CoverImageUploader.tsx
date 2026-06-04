'use client';

import React, {useCallback, useEffect, useRef, useState} from 'react';
import {Check, Crop, Image as ImageIcon, Link as LinkIcon, Upload, X} from 'lucide-react';
import {getConfig} from '@/lib/config';
import {getFullMediaUrl} from '@/lib/utils';

/* ── Types ── */
interface CoverImageUploaderProps {
  value?: string;
  onChange: (url: string) => void;
  className?: string;
}

type UploadMode = 'file' | 'url';

/* ── Constants ── */
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
const MAX_FILE_SIZE = 8 * 1024 * 1024; // 8MB
const COVER_UPLOAD_ENDPOINT = '/api/v2/media/cover';
const ASPECT_RATIO = 16 / 9;

/* ── Upload Progress ── */
const UploadProgress: React.FC<{ progress: number }> = ({progress}) => (
  <div className="absolute inset-0 bg-black/40 flex flex-col items-center justify-center rounded-xl z-10">
    <div className="w-10 h-10 rounded-full border-2 border-white/30 border-t-white animate-spin mb-2"/>
    <span className="text-xs text-white font-medium">{progress}%</span>
    <div className="w-32 h-1.5 bg-white/20 rounded-full mt-2 overflow-hidden">
      <div className="h-full bg-white rounded-full transition-all duration-300" style={{width: `${progress}%`}}/>
    </div>
  </div>
);

/* ── Crop Modal (native Canvas implementation) ── */
interface CropModalProps {
  imageUrl: string;
  onCrop: (croppedBlob: Blob) => void;
  onClose: () => void;
}

const CropModal: React.FC<CropModalProps> = ({imageUrl, onCrop, onClose}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [cropArea, setCropArea] = useState({x: 0, y: 0, w: 0, h: 0});
  const [imgDisplay, setImgDisplay] = useState({x: 0, y: 0, w: 0, h: 0});
  const dragRef = useRef<{ startX: number; startY: number; startCropX: number; startCropY: number } | null>(null);

  // Calculate display dimensions when image loads
  useEffect(() => {
    if (!imgRef.current || !containerRef.current) return;
    const img = imgRef.current;

    const calcLayout = () => {
      const container = containerRef.current!;
      const cw = container.clientWidth;
      const ch = container.clientHeight;
      const iw = img.naturalWidth;
      const ih = img.naturalHeight;

      // Fit image into container
      const scale = Math.min(cw / iw, ch / ih, 1);
      const dw = iw * scale;
      const dh = ih * scale;
      const dx = (cw - dw) / 2;
      const dy = (ch - dh) / 2;
      setImgDisplay({x: dx, y: dy, w: dw, h: dh});

      // Initial crop area: largest 16:9 rect centered in the displayed image
      let cropW = dw;
      let cropH = cropW / ASPECT_RATIO;
      if (cropH > dh) {
        cropH = dh;
        cropW = cropH * ASPECT_RATIO;
      }
      const cropX = dx + (dw - cropW) / 2;
      const cropY = dy + (dh - cropH) / 2;
      setCropArea({x: cropX, y: cropY, w: cropW, h: cropH});
      setImageLoaded(true);
    };

    if (img.complete && img.naturalWidth > 0) {
      calcLayout();
    } else {
      img.onload = calcLayout;
    }
    // Recalculate on resize
    const ro = new ResizeObserver(calcLayout);
    ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [imageUrl]);

  /* ── Drag to move crop area ── */
  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    e.preventDefault();
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    dragRef.current = {
      startX: e.clientX,
      startY: e.clientY,
      startCropX: cropArea.x,
      startCropY: cropArea.y,
    };
  }, [cropArea.x, cropArea.y]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!dragRef.current || !containerRef.current) return;
    const container = containerRef.current;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;

    setCropArea(prev => {
      const newX = Math.max(imgDisplay.x, Math.min(dragRef.current!.startCropX + dx, imgDisplay.x + imgDisplay.w - prev.w));
      const newY = Math.max(imgDisplay.y, Math.min(dragRef.current!.startCropY + dy, imgDisplay.y + imgDisplay.h - prev.h));
      return {...prev, x: newX, y: newY};
    });
  }, [imgDisplay]);

  const handlePointerUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  /* ── Crop the original image using canvas ── */
  const handleCrop = useCallback(() => {
    if (!imgRef.current) return;
    const img = imgRef.current;
    const {naturalWidth: nw, naturalHeight: nh} = img;

    // Scale factors from display to natural
    const sx = nw / imgDisplay.w;
    const sy = nh / imgDisplay.h;

    const srcX = (cropArea.x - imgDisplay.x) * sx;
    const srcY = (cropArea.y - imgDisplay.y) * sy;
    const srcW = cropArea.w * sx;
    const srcH = cropArea.h * sy;

    const canvas = document.createElement('canvas');
    canvas.width = Math.min(Math.round(srcW), 1920);
    canvas.height = Math.min(Math.round(srcH), 1080);
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = '#fff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, srcX, srcY, srcW, srcH, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
      if (blob) onCrop(blob);
    }, 'image/jpeg', 0.9);
  }, [cropArea, imgDisplay, onCrop]);

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/60 backdrop-blur-sm"
         onClick={onClose}>
      <div
        className="bg-white dark:bg-gray-900 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl border border-gray-200 dark:border-gray-700 overflow-hidden"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800">
          <div className="flex items-center gap-2">
            <Crop className="w-4.5 h-4.5 text-blue-600"/>
            <h3 className="font-bold text-gray-900 dark:text-white text-base">裁剪封面图</h3>
          </div>
          <span className="text-xs text-gray-400">比例 16:9</span>
        </div>

        {/* Image container */}
        <div
          ref={containerRef}
          className="flex-1 overflow-hidden p-4 relative select-none touch-none"
          style={{minHeight: 300}}
        >
          {/* Original image (hidden behind overlay) */}
          <img
            ref={imgRef}
            src={imageUrl}
            alt="裁剪"
            crossOrigin="anonymous"
            className="block pointer-events-none"
            style={{
              position: 'absolute',
              left: imgDisplay.x,
              top: imgDisplay.y,
              width: imgDisplay.w,
              height: imgDisplay.h,
            }}
          />

          {/* Dim overlay outside crop area */}
          {imageLoaded && (
            <>
              {/* Top */}
              <div className="absolute bg-black/50 pointer-events-none" style={{
                left: 0, top: 0, right: 0, height: cropArea.y,
              }}/>
              {/* Bottom */}
              <div className="absolute bg-black/50 pointer-events-none" style={{
                left: 0, top: cropArea.y + cropArea.h, right: 0, bottom: 0,
              }}/>
              {/* Left */}
              <div className="absolute bg-black/50 pointer-events-none" style={{
                left: 0, top: cropArea.y, width: cropArea.x, height: cropArea.h,
              }}/>
              {/* Right */}
              <div className="absolute bg-black/50 pointer-events-none" style={{
                left: cropArea.x + cropArea.w, top: cropArea.y, right: 0, height: cropArea.h,
              }}/>

              {/* Crop frame */}
              <div
                className="absolute border-2 border-white cursor-move"
                style={{
                  left: cropArea.x,
                  top: cropArea.y,
                  width: cropArea.w,
                  height: cropArea.h,
                  boxShadow: '0 0 0 1px rgba(0,0,0,0.3)',
                }}
                onPointerDown={handlePointerDown}
                onPointerMove={handlePointerMove}
                onPointerUp={handlePointerUp}
              >
                {/* Grid lines */}
                <div className="absolute inset-0 pointer-events-none">
                  <div className="absolute left-1/3 top-0 bottom-0 w-px bg-white/40"/>
                  <div className="absolute left-2/3 top-0 bottom-0 w-px bg-white/40"/>
                  <div className="absolute top-1/3 left-0 right-0 h-px bg-white/40"/>
                  <div className="absolute top-2/3 left-0 right-0 h-px bg-white/40"/>
                </div>
                {/* Corner handles */}
                {[
                  {top: -4, left: -4},
                  {top: -4, right: -4},
                  {bottom: -4, left: -4},
                  {bottom: -4, right: -4},
                ].map((pos, i) => (
                  <div
                    key={i}
                    className="absolute w-2.5 h-2.5 bg-white border border-blue-500 rounded-sm pointer-events-none"
                    style={pos as React.CSSProperties}
                  />
                ))}
              </div>
            </>
          )}
        </div>

        <div className="flex items-center justify-end gap-3 px-5 py-4 border-t border-gray-100 dark:border-gray-800">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700 rounded-xl hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleCrop}
            className="px-5 py-2 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-sm transition-colors flex items-center gap-1.5"
          >
            <Check className="w-4 h-4"/>确认裁剪
          </button>
        </div>
      </div>
    </div>
  );
};

/* ── Main Component ── */
export default function CoverImageUploader({value, onChange, className}: CoverImageUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [mode, setMode] = useState<UploadMode>(value ? 'url' : 'file');
  const [urlInput, setUrlInput] = useState('');
  const [cropImageUrl, setCropImageUrl] = useState<string | null>(null);
  const [pendingFile, setPendingFile] = useState<File | null>(null);

  // Reset mode when value is externally cleared
  useEffect(() => {
    if (!value && mode === 'url' && !urlInput) {
      setMode('file');
    }
  }, [value]);

  /* ── Upload to server ── */
  const uploadFile = useCallback(async (file: Blob, filename?: string) => {
    setUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('cover_image', file, filename || 'cover.jpg');

      const xhr = new XMLHttpRequest();
      // Build full URL with API base (same as base-client.buildUrl)
      const {API_BASE_URL} = getConfig();
      const uploadUrl = `${API_BASE_URL}${COVER_UPLOAD_ENDPOINT}`;

      // Read JWT token from cookie (same method as base-client)
      const accessToken = (() => {
        for (const c of document.cookie.split(';')) {
          const [n, v] = c.trim().split('=');
          if (n === 'access_token' && v) return decodeURIComponent(v);
        }
        return null;
      })();

      const promise = new Promise<string>((resolve, reject) => {
        xhr.upload.onprogress = (e) => {
          if (e.lengthComputable) {
            setUploadProgress(Math.round((e.loaded / e.total) * 100));
          }
        };
        xhr.onload = () => {
          // Handle auth redirect (login page returns HTML)
          if (xhr.status === 302 || xhr.status === 401 || xhr.status === 403) {
            reject(new Error('未登录或登录已过期，请重新登录'));
            return;
          }
          try {
            const resp = JSON.parse(xhr.responseText);
            if (xhr.status >= 200 && xhr.status < 300 && resp.code === 200 && resp.data) {
              resolve(resp.data);
            } else {
              reject(new Error(resp.msg || resp.error || `上传失败 (HTTP ${xhr.status})`));
            }
          } catch {
            // Response is not JSON — show status and a snippet of the body
            const snippet = xhr.responseText?.slice(0, 120) || '(empty)';
            reject(new Error(`服务器返回非 JSON 响应 (HTTP ${xhr.status}): ${snippet}`));
          }
        };
        xhr.onerror = () => reject(new Error('网络错误，请检查网络连接'));
        xhr.open('POST', uploadUrl);
        xhr.withCredentials = true;
        if (accessToken) {
          xhr.setRequestHeader('Authorization', `Bearer ${accessToken}`);
        }
        xhr.send(formData);
      });

      const url = await promise;
      onChange(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : '上传失败');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  }, [onChange]);

  /* ── File selection handler ── */
  const handleFileSelect = useCallback((file: File) => {
    setError(null);

    // Validate type
    if (!ACCEPTED_TYPES.includes(file.type)) {
      setError('仅支持 JPG、PNG、GIF、WebP 格式');
      return;
    }
    // Validate size
    if (file.size > MAX_FILE_SIZE) {
      setError('文件大小不能超过 8MB');
      return;
    }

    // Show crop modal
    const reader = new FileReader();
    reader.onload = (e) => {
      setCropImageUrl(e.target?.result as string);
      setPendingFile(file);
    };
    reader.readAsDataURL(file);
  }, []);

  /* ── Crop complete handler ── */
  const handleCropComplete = useCallback(async (croppedBlob: Blob) => {
    setCropImageUrl(null);
    if (pendingFile) {
      await uploadFile(croppedBlob, pendingFile.name);
      setPendingFile(null);
    }
  }, [pendingFile, uploadFile]);

  /* ── Skip crop (upload original) ── */
  const handleSkipCrop = useCallback(async () => {
    setCropImageUrl(null);
    if (pendingFile) {
      await uploadFile(pendingFile, pendingFile.name);
      setPendingFile(null);
    }
  }, [pendingFile, uploadFile]);

  /* ── Drag handlers ── */
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true);
    else if (e.type === 'dragleave') setDragActive(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  }, [handleFileSelect]);

  /* ── URL submit ── */
  const handleUrlSubmit = useCallback(() => {
    if (!urlInput.trim()) return;
    // Basic URL validation
    try {
      new URL(urlInput);
      onChange(urlInput.trim());
      setUrlInput('');
    } catch {
      setError('请输入有效的图片 URL');
    }
  }, [urlInput, onChange]);

  /* ── Remove cover ── */
  const handleRemove = useCallback(() => {
    onChange('');
    setError(null);
    setUrlInput('');
  }, [onChange]);

  return (
    <div className={`w-full ${className || ''}`.trim()}>
      {/* Crop Modal */}
      {cropImageUrl && (
        <CropModal
          imageUrl={cropImageUrl}
          onCrop={handleCropComplete}
          onClose={handleSkipCrop}
        />
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES.join(',')}
        className="hidden"
        onChange={(e) => {
          if (e.target.files?.[0]) handleFileSelect(e.target.files[0]);
          e.target.value = '';
        }}
      />

      {/* Existing image preview */}
      {value && (
        <div className="relative rounded-xl overflow-hidden group mb-3">
          <img
            src={getFullMediaUrl(value)}
            alt="封面图"
            className="w-full aspect-video object-cover"
            onError={(e) => {
              (e.target as HTMLImageElement).style.display = 'none';
            }}
          />
          <div
            className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
            <button
              type="button"
              onClick={handleRemove}
              className="opacity-0 group-hover:opacity-100 p-2 bg-white/90 dark:bg-gray-800/90 text-gray-700 dark:text-gray-300 rounded-full shadow-lg transition-opacity hover:bg-white"
            >
              <X className="w-4 h-4"/>
            </button>
          </div>
        </div>
      )}

      {/* Upload area (show when no image) */}
      {!value && (
        <div className="space-y-2">
          {/* Mode toggle */}
          <div className="flex items-center gap-1 p-0.5 bg-gray-100 dark:bg-gray-800 rounded-lg">
            <button
              type="button"
              onClick={() => setMode('file')}
              className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                mode === 'file'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <Upload className="w-3.5 h-3.5"/>上传文件
            </button>
            <button
              type="button"
              onClick={() => setMode('url')}
              className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                mode === 'url'
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              <LinkIcon className="w-3.5 h-3.5"/>URL 链接
            </button>
          </div>

          {/* File upload mode */}
          {mode === 'file' && (
            <div
              className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
                dragActive
                  ? 'border-blue-500 bg-blue-50/50 dark:bg-blue-900/20'
                  : uploading
                    ? 'border-gray-200 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-800/30 pointer-events-none'
                    : 'border-gray-200 dark:border-gray-700 hover:border-blue-400 dark:hover:border-blue-600 hover:bg-blue-50/30 dark:hover:bg-blue-900/10'
              }`}
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              onClick={() => !uploading && fileInputRef.current?.click()}
            >
              {uploading ? (
                <UploadProgress progress={uploadProgress}/>
              ) : (
                <div className="flex flex-col items-center gap-2">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                    <ImageIcon className="w-5 h-5 text-blue-500 dark:text-blue-400"/>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      {dragActive ? '松开上传' : '拖拽或点击上传封面图'}
                    </p>
                    <p className="text-xs text-gray-400 mt-0.5">JPG / PNG / GIF / WebP · 最大 8MB</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* URL input mode */}
          {mode === 'url' && (
            <div className="flex gap-2">
              <input
                type="url"
                value={urlInput}
                onChange={(e) => {
                  setUrlInput(e.target.value);
                  setError(null);
                }}
                placeholder="输入封面图片 URL..."
                className="flex-1 px-3 py-2.5 border border-gray-200 dark:border-gray-700 rounded-xl bg-white dark:bg-gray-800 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white placeholder-gray-400 transition-all"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault();
                    handleUrlSubmit();
                  }
                }}
              />
              <button
                type="button"
                onClick={handleUrlSubmit}
                className="px-3 py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-xl transition-colors flex items-center gap-1"
              >
                <Check className="w-4 h-4"/>
              </button>
            </div>
          )}
        </div>
      )}

      {/* Error message */}
      {error && (
        <p className="flex items-center gap-1.5 text-red-500 text-xs mt-2">
          <span className="w-1 h-1 rounded-full bg-red-500"/>{error}
        </p>
      )}
    </div>
  );
}
