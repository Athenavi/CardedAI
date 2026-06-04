'use client';

import React, {useEffect, useState} from 'react';
import {CategoryService} from '@/lib/api';
import type {Category} from '@/lib/api/base-types';

const CategoriesPage: React.FC = () => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    CategoryService.getCategories({per_page: 50}).then(res => {
      if (res.success && res.data) {
        setCategories(res.data.categories || []);
      }
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto" />;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
      {categories.map(cat => (
        <a key={cat.id} href={`/articles?category=${cat.slug || cat.id}`}
          className="p-6 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 hover:shadow-lg hover:border-blue-500 transition-all">
          <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">{cat.name}</h3>
          {cat.description && <p className="text-sm text-gray-600 dark:text-gray-400">{cat.description}</p>}
          {cat.article_count !== undefined && <span
            className="inline-block mt-3 text-xs px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded-full text-gray-500 dark:text-gray-400">{cat.article_count} 篇文章</span>}
        </a>
      ))}
    </div>
  );
};

export default CategoriesPage;
