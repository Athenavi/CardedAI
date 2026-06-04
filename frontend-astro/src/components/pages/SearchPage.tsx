'use client';

import React from 'react';

const SearchPage: React.FC = () => {
  const [query, setQuery] = React.useState('');

  return (
    <div>
      <div className="relative mb-8">
        <input type="text" value={query} onChange={e => setQuery(e.target.value)}
          placeholder="输入关键词搜索文章..."
          className="w-full px-6 py-4 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:text-white" />
      </div>
      <p className="text-gray-500 dark:text-gray-400 text-center py-12">输入关键词开始搜索</p>
    </div>
  );
};

export default SearchPage;
