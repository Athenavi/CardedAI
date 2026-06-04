'use client';

import * as React from 'react';
import {useFormContext, type FieldValues, type FieldPath, type RegisterOptions} from 'react-hook-form';
import {cn} from '@/lib/utils';

/* ──────────────────────────────────────────────
   FormField — 通用表单字段包装器
   自动关联 react-hook-form 的 register + 错误显示

   用法（在 FormProvider 内）：
     <FormField name="username" label="用户名" placeholder="请输入用户名" />
   ────────────────────────────────────────────── */

interface FormFieldProps<T extends FieldValues = FieldValues> {
  name: FieldPath<T>;
  label?: string;
  type?: string;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  labelClassName?: string;
  disabled?: boolean;
  autoComplete?: string;
  rules?: RegisterOptions<T>;
  as?: 'input' | 'textarea' | 'select';
  rows?: number;
  children?: React.ReactNode;
}

export function FormField<T extends FieldValues = FieldValues>({
                                                                 name,
                                                                 label,
                                                                 type = 'text',
                                                                 placeholder,
                                                                 className,
                                                                 inputClassName,
                                                                 labelClassName,
                                                                 disabled,
                                                                 autoComplete,
                                                                 rules,
                                                                 as: Component = 'input',
                                                                 rows,
                                                                 children,
                                                               }: FormFieldProps<T>) {
  const {register, formState: {errors}} = useFormContext<T>();
  const error = errors[name];

  const baseInputClass = cn(
    'w-full px-4 py-2.5 border rounded-xl text-sm transition-all duration-200',
    'bg-white dark:bg-gray-800/80 text-gray-900 dark:text-white',
    'placeholder-gray-400 dark:placeholder-gray-500',
    'focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500',
    'dark:focus:border-blue-500',
    error
      ? 'border-red-400 dark:border-red-500 focus:ring-red-500/30 focus:border-red-500'
      : 'border-gray-200 dark:border-gray-700',
    disabled && 'opacity-50 cursor-not-allowed',
    inputClassName,
  );

  const inputProps = {
    ...register(name, rules),
    id: name,
    placeholder,
    disabled,
    autoComplete,
    className: baseInputClass,
  };

  return (
    <div className={cn('space-y-1.5', className)}>
      {label && (
        <label htmlFor={name} className={cn(
          'block text-sm font-medium',
          error ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300',
          labelClassName,
        )}>
          {label}
        </label>
      )}

      {Component === 'textarea' ? (
        <textarea {...(inputProps as any)} rows={rows || 4}/>
      ) : Component === 'select' ? (
        <select {...(inputProps as any)}>{children}</select>
      ) : (
        <input {...(inputProps as any)} type={type}/>
      )}

      {error && (
        <p className="text-xs text-red-500 dark:text-red-400 flex items-center gap-1">
          <svg className="w-3 h-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"/>
          </svg>
          {error.message as string}
        </p>
      )}
    </div>
  );
}

/* ──────────────────────────────────────────────
   FormError — 表单级别错误提示
   ────────────────────────────────────────────── */
export function FormError({message, className}: { message?: string; className?: string }) {
  if (!message) return null;
  return (
    <div className={cn(
      'p-3 rounded-xl text-sm flex items-center gap-2',
      'bg-red-50 text-red-700 border border-red-200',
      'dark:bg-red-900/20 dark:text-red-400 dark:border-red-800',
      className,
    )}>
      <svg className="w-4 h-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"/>
      </svg>
      {message}
    </div>
  );
}
