'use client';

import {z} from 'zod';

/* ──────────────────────────────────────────────
   公共 Zod Schema — 供各页面表单复用
   ────────────────────────────────────────────── */

// ── 认证 ──

export const loginSchema = z.object({
  username: z.string().min(1, '请输入用户名').max(50, '用户名过长'),
  password: z.string().min(1, '请输入密码').max(128, '密码过长'),
  remember: z.boolean().default(false),
});
export type LoginFormData = z.infer<typeof loginSchema>;

export const twoFactorSchema = z.object({
  code: z.string().regex(/^\d+$/, '验证码必须为数字').refine(
    v => v.length === 6 || v.length === 8,
    '验证码为 6 位数字（或备用码为 8 位数字）'
  ),
});
export type TwoFactorFormData = z.infer<typeof twoFactorSchema>;

export const registerSchema = z.object({
  username: z.string().min(3, '用户名至少 3 个字符').max(30, '用户名最多 30 个字符').regex(/^[a-zA-Z0-9_\u4e00-\u9fff]+$/, '用户名只能包含字母、数字、下划线和中文'),
  email: z.string().email('请输入有效的邮箱地址'),
  password: z.string().min(8, '密码至少 8 个字符').max(128, '密码过长')
    .regex(/^(?=.*[a-zA-Z])(?=.*\d)/, '密码必须包含字母和数字'),
  confirmPassword: z.string().min(1, '请确认密码'),
  locale: z.string().default('zh_CN'),
  terms: z.literal(true, {message: '请同意服务条款和隐私政策'}),
}).refine((data) => data.password === data.confirmPassword, {
  message: '两次输入的密码不一致',
  path: ['confirmPassword'],
});
export type RegisterFormData = z.infer<typeof registerSchema>;

// ── 文章 ──

export const articleSchema = z.object({
  title: z.string().min(1, '标题不能为空').max(200, '标题最多 200 字符'),
  slug: z.string().max(200, '别名过长').optional(),
  excerpt: z.string().max(500, '摘要最多 500 字符').optional(),
  cover_image: z.string().optional(),
  category_id: z.coerce.number().optional(),
  tags: z.string().optional(),
  status: z.union([z.literal(0), z.literal(1)]).default(0),
  hidden: z.boolean().optional().default(false),
  is_vip_only: z.boolean().optional().default(false),
});
export type ArticleFormData = z.infer<typeof articleSchema>;

// ── 评论 ──

export const commentSchema = z.object({
  content: z.string().min(1, '评论内容不能为空').max(2000, '评论最多 2000 字符'),
  parent_id: z.number().optional(),
});
export type CommentFormData = z.infer<typeof commentSchema>;

export const commentFormSchema = z.object({
  content: z.string().min(1, '评论内容不能为空').max(2000, '评论最多 2000 字符'),
  author_name: z.string().optional(),
  author_email: z.string().email('请输入有效的邮箱地址').optional().or(z.literal('')),
});
export type CommentFormFormData = z.infer<typeof commentFormSchema>;

// ── 用户管理 ──

export const userProfileSchema = z.object({
  nickname: z.string().min(1, '昵称不能为空').max(50, '昵称最多 50 字符').optional(),
  email: z.string().email('请输入有效的邮箱地址'),
  bio: z.string().max(500, '简介最多 500 字符').optional(),
  avatar: z.string().optional(),
});
export type UserProfileFormData = z.infer<typeof userProfileSchema>;

export const changePasswordSchema = z.object({
  current_password: z.string().min(1, '请输入当前密码'),
  new_password: z.string().min(8, '新密码至少 8 个字符').max(128, '密码过长')
    .regex(/^(?=.*[a-zA-Z])(?=.*\d)/, '密码必须包含字母和数字'),
  confirm_password: z.string().min(1, '请确认新密码'),
}).refine((data) => data.new_password === data.confirm_password, {
  message: '两次输入的密码不一致',
  path: ['confirm_password'],
});
export type ChangePasswordFormData = z.infer<typeof changePasswordSchema>;

// ── 通用 ──

export const searchSchema = z.object({
  query: z.string().min(1, '请输入搜索关键词').max(200, '搜索关键词过长'),
});
export type SearchFormData = z.infer<typeof searchSchema>;

export const subscribeSchema = z.object({
  email: z.string().email('请输入有效的邮箱地址'),
});
export type SubscribeFormData = z.infer<typeof subscribeSchema>;
