'use client';

import React, {useState} from 'react';
import {useMutation} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {AdminShell} from '@/components/admin/AdminShell';
import {apiClient} from '@/lib/api/base-client';
import {Save} from 'lucide-react';
import {useToast} from '@/components/ui/toast-provider';
import CoverImageUploader from '@/components/editor/CoverImageUploader';

const RichEditor = React.lazy(() => import('@/components/editor/RichEditor'));

function EditorInner() {
  const toast = useToast();
  const [content, setContent] = useState('');
  const [coverImage, setCoverImage] = useState('');
  const [title, setTitle] = useState('');

  const submitMut = useMutation({
    mutationFn: async () => {
      const fd = new FormData();
      fd.append('title', title || 'New Article');
      fd.append('content', content);
      if (coverImage) fd.append('cover_image', coverImage);
      return apiClient.request('/articles', {method: 'POST', body: fd});
    },
    onSuccess: (res) => {
      if (res.success) toast.success('文章已创建');
    },
  });

  return (
    <AdminShell title="写文章" actions={
      <button onClick={() => submitMut.mutate()} disabled={submitMut.isPending} className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg flex items-center gap-1.5"><Save className="w-4 h-4"/>{submitMut.isPending ? '发布中...' : '发布'}</button>
    }>
      <div className="space-y-4">
        {/* Title */}
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="在此输入文章标题..."
          className="w-full text-2xl font-bold px-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 dark:text-white placeholder-gray-300 dark:placeholder-gray-600"
        />

        {/* Cover Image */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 p-4">
          <label
            className="block text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">封面图</label>
          <CoverImageUploader value={coverImage} onChange={setCoverImage}/>
        </div>

        {/* Editor */}
        <div
          className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-700 overflow-hidden">
          <React.Suspense fallback={<div className="h-[60vh] animate-pulse bg-gray-50 dark:bg-gray-800"/>}>
            <RichEditor value={content} onChange={setContent}/>
          </React.Suspense>
        </div>
      </div>
    </AdminShell>
  );
}

export default function ArticleEditor() {
  return <AuthGuard><QueryProvider><EditorInner /></QueryProvider></AuthGuard>;
}
