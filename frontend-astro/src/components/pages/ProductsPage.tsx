'use client';

import React from 'react';
import {useQuery} from '@tanstack/react-query';
import {AuthGuard} from '@/components/AuthGuard';
import {QueryProvider} from '@/components/QueryProvider';
import {apiClient} from '@/lib/api/base-client';
import {Search, ShoppingBag} from 'lucide-react';

function ProductsInner() {
  const [search, setSearch] = React.useState('');
    const {data: products, isLoading} = useQuery<any[]>({
    queryKey: ['products', search],
    queryFn: async () => {
      const r = await apiClient.get('/shop', {q: search || undefined});
      return r.success && r.data ? (Array.isArray(r.data) ? r.data : r.data.products||[]) : [];
    },
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 dark:from-gray-950 dark:to-gray-900 pt-20">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex items-center justify-between mb-8">
          <div><h1 className="text-2xl font-bold text-gray-900 dark:text-white">商城</h1><p
            className="text-sm text-gray-500 dark:text-gray-400 mt-1">发现精选产品</p></div>
        </div>
        <div className="relative mb-6"><Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"/><input type="text" value={search} onChange={e=>setSearch(e.target.value)} placeholder="搜索产品..." className="w-full pl-11 pr-4 py-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white"/></div>
        {isLoading ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">{[1,2,3,4].map(i=><div key={i} className="aspect-[3/4] bg-gray-100 dark:bg-gray-800 rounded-2xl animate-pulse"/>)}</div>
        ) : !products?.length ? (
          <div className="text-center py-20 text-gray-400"><ShoppingBag className="w-12 h-12 mx-auto mb-3 opacity-40"/><p className="text-sm">暂无产品</p></div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {products.map((p:any,i:number) => (
              <div key={p.id||i} className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-100 dark:border-gray-800 overflow-hidden hover:shadow-md transition-shadow">
                <div className="aspect-square bg-gray-50 dark:bg-gray-800 flex items-center justify-center text-gray-300 text-4xl">{p.images?.[0] ? <img src={p.images[0]} alt={p.name} className="w-full h-full object-cover"/> : '📦'}</div>
                <div className="p-4"><h3 className="font-semibold text-sm text-gray-900 dark:text-white truncate">{p.name||'产品'}</h3><p className="text-lg font-bold text-blue-600 mt-1">¥{p.price||'—'}</p></div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default function ProductsPage() { return <AuthGuard><QueryProvider><ProductsInner /></QueryProvider></AuthGuard>; }
