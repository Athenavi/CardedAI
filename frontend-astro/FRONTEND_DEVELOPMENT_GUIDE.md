# FastBlog 前端开发指南

本文档说明如何为已完成的 API 创建对应的前端管理界面。

## 📋 已完成的后端 API 清单

### P0: AI 原生集成

- ✅ `/api/v1/ai/workflows` - AI 工作流管理
- ✅ `/api/v1/ai/assist/*` - AI 辅助功能

**前端实现**: `AdminAIWorkflows.tsx` (已创建)

---

### P2: 可视化构建与主题生态

#### 页面构建器

- ✅ `/api/v1/page-builder/pages` - 页面 CRUD
- ✅ `/api/v1/components/templates` - 组件库
- ✅ `/api/v1/components/render` - 组件渲染

**前端实现**: `PageBuilder.tsx` (已创建)

#### 主题市场

- ✅ `/api/v1/themes/marketplace` - 浏览主题
- ✅ `/api/v1/themes/install` - 安装主题
- ✅ `/api/v1/themes/{slug}/activate` - 激活主题
- ✅ `/api/v1/themes/{slug}/config` - 主题配置

**待实现**: `AdminThemeMarketplace.tsx`

---

### P3: Webhook 支持

- ✅ `/api/v1/webhooks` - Webhook 管理
- ✅ `/api/v1/webhooks/deliveries` - 投递记录

**待实现**: `AdminWebhooks.tsx`

---

### P4: 安全监控

- ✅ `/api/v1/security/dashboard/summary` - 安全概览
- ✅ `/api/v1/security/audit/logs` - 审计日志

**待实现**: `AdminSecurityDashboard.tsx`

---

### P5: 第三方发布

- ✅ `/api/v1/publish/sync` - 一键发布

**待实现**: `AdminThirdPartyPublish.tsx`

---

## 🎨 前端开发模板

### 标准页面结构

```tsx
import React, { useState } from 'react';
import AdminShell from '@/components/layouts/AdminShell';
import AuthGuard from '@/components/auth/AuthGuard';
import QueryProvider from '@/components/providers/QueryProvider';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '@/lib/api-client';
import { IconName } from 'lucide-react';

function ComponentNameInner() {
  const qc = useQueryClient();
  
  // 1. 数据查询
  const { data, isLoading } = useQuery({
    queryKey: ['your-api-key'],
    queryFn: async () => {
      const res = await apiClient.get('/your-api-endpoint');
      return res.data;
    }
  });

  // 2. 数据变更
  const mutation = useMutation({
    mutationFn: (data: any) => apiClient.post('/your-api-endpoint', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['your-api-key'] });
      alert('操作成功！');
    }
  });

  // 3. UI 渲染
  return (
    <AdminShell title="页面标题">
      <div className="space-y-6">
        {/* 统计卡片、列表、表单等 */}
      </div>
    </AdminShell>
  );
}

export default function ComponentName() {
  return (
    <AuthGuard>
      <QueryProvider>
        <ComponentNameInner />
      </QueryProvider>
    </AuthGuard>
  );
}
```

---

## 📝 需要创建的页面清单

### 1. 主题市场管理 (`AdminThemeMarketplace.tsx`)

**API 端点**:

- GET `/api/v1/themes/marketplace` - 获取可用主题
- GET `/api/v1/themes/installed` - 获取已安装主题
- POST `/api/v1/themes/install` - 安装主题
- POST `/api/v1/themes/{slug}/activate` - 激活主题
- DELETE `/api/v1/themes/{slug}/uninstall` - 卸载主题
- GET/PUT `/api/v1/themes/{slug}/config` - 主题配置

**功能需求**:

- [ ] 主题卡片展示（截图、名称、描述、作者）
- [ ] 安装/卸载按钮
- [ ] 激活/停用切换
- [ ] 主题配置表单（根据 settings_schema 动态生成）
- [ ] 分类过滤
- [ ] 搜索功能

---

### 2. Webhook 管理 (`AdminWebhooks.tsx`)

**API 端点**:

- GET/POST `/api/v1/webhooks` - Webhook CRUD
- GET `/api/v1/webhooks/deliveries` - 投递记录

**功能需求**:

- [ ] Webhook 列表（URL、事件、状态）
- [ ] 创建/编辑 Webhook 表单
- [ ] 事件类型多选（article.published, comment.created 等）
- [ ] 投递历史记录
- [ ] 重试失败投递
- [ ] 测试 Webhook 功能

---

### 3. 安全监控面板 (`AdminSecurityDashboard.tsx`)

**API 端点**:

- GET `/api/v1/security/dashboard/summary` - 安全概览
- GET `/api/v1/security/audit/logs` - 审计日志

**功能需求**:

- [ ] 统计卡片（24h 操作数、失败登录、可疑 IP）
- [ ] 实时告警列表
- [ ] 审计日志表格（时间、用户、动作、IP、结果）
- [ ] 日志过滤（按用户、动作类型、时间范围）
- [ ] 导出日志功能
- [ ] 异常流量图表

---

### 4. 第三方发布管理 (`AdminThirdPartyPublish.tsx`)

**API 端点**:

- POST `/api/v1/publish/sync` - 一键发布

**功能需求**:

- [ ] 文章选择器
- [ ] 平台复选框（知乎、掘金、Medium、Twitter）
- [ ] 发布历史记录
- [ ] 平台账号绑定配置
- [ ] 发布状态追踪
- [ ] 批量发布功能

---

## 🔧 通用组件复用

以下通用组件可以在多个页面中复用：

### 1. 统计卡片

```tsx
<div className="grid grid-cols-1 md:grid-cols-4 gap-4">
  <div className="bg-white dark:bg-gray-900 rounded-xl border p-4">
    <div className="text-sm text-gray-500 mb-1">标题</div>
    <div className="text-2xl font-bold">数值</div>
  </div>
</div>
```

### 2. 数据表格

```tsx
<div className="bg-white dark:bg-gray-900 rounded-xl border overflow-hidden">
  <table className="w-full">
    <thead className="bg-gray-50 dark:bg-gray-800">
      <tr>
        <th className="px-5 py-3 text-left text-xs font-semibold">列名</th>
      </tr>
    </thead>
    <tbody className="divide-y">
      {data.map(item => (
        <tr key={item.id} className="hover:bg-gray-50">
          <td className="px-5 py-4">{item.value}</td>
        </tr>
      ))}
    </tbody>
  </table>
</div>
```

### 3. 对话框

```tsx
{showDialog && (
  <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
    <div className="bg-white dark:bg-gray-900 rounded-2xl max-w-2xl w-full">
      <div className="px-6 py-4 border-b">
        <h3 className="font-semibold">标题</h3>
      </div>
      <div className="p-6">
        {/* 内容 */}
      </div>
    </div>
  </div>
)}
```

---

## 🚀 快速开始步骤

1. **选择要实现的页面**（从上述清单中）
2. **复制标准模板**到 `frontend-astro/src/components/pages/admin/YourPage.tsx`
3. **修改 API 端点**和数据结构
4. **添加业务逻辑**（表单、过滤、排序等）
5. **创建 Astro 入口文件** `frontend-astro/src/pages/admin/your-page.astro`:
   ```astro
   ---
   import YourPage from '@/components/pages/admin/YourPage';
   ---
   <!doctype html>
   <html lang="zh-CN">
     <head>
       <meta charset="utf-8"/>
       <meta name="viewport" content="width=device-width,initial-scale=1"/>
       <title>页面标题 - FastBlog</title>
       <link rel="stylesheet" href="/src/styles/globals.css"/>
     </head>
     <body><YourPage client:load /></body>
   </html>
   ```
6. **添加到导航菜单**（在 AdminShell 或侧边栏组件中）

---

## 📚 参考示例

已完成的两个页面可以作为参考：

- `AdminAIWorkflows.tsx` - 展示列表、详情、状态管理
- `PageBuilder.tsx` - 展示复杂交互、拖拽、预览

---

## 💡 最佳实践

1. **使用 TanStack Query** 管理服务器状态
2. **乐观更新**提升用户体验
3. **错误边界**处理 API 失败
4. **加载状态**显示骨架屏或 spinner
5. **响应式设计**确保移动端可用
6. **暗色模式**支持（使用 Tailwind 的 dark: 前缀）
7. **国际化**预留 i18n 接口

---

## 🎯 优先级建议

1. **高优先级**: 主题市场、Webhook 管理
2. **中优先级**: 安全监控面板
3. **低优先级**: 第三方发布管理

根据您的实际需求调整开发顺序。
