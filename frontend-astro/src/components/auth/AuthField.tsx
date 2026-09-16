'use client';

import React from 'react';
import {AlertCircle, type LucideIcon} from 'lucide-react';
import {cn} from '@/lib/utils';

interface AuthFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'className'> {
  /** 字段名（同时用于 label 与 id） */
  label: string;
  /** label 行的小图标 */
  icon: LucideIcon;
  /** 校验错误信息 */
  error?: string;
  /** label 行右侧内容（如“忘记密码”链接） */
  hint?: React.ReactNode;
  /** 输入框右侧动作（如密码可见切换） */
  action?: React.ReactNode;
  /** 输入框下方补充说明（如“用户名可用”） */
  description?: React.ReactNode;
  className?: string;
  inputClassName?: string;
}

/**
 * 认证表单字段（登录 / 注册共用）—— 下划线式
 *
 * 编辑风：字段只有一条底线，聚焦时底线转墨蓝、label 由灰转深；
 * 图标退到 label 行，不再占据输入框内部。
 */
const AuthField = React.forwardRef<HTMLInputElement, AuthFieldProps>(({
                                                                        label,
                                                                        icon: Icon,
                                                                        error,
                                                                        hint,
                                                                        action,
                                                                        description,
                                                                        className,
                                                                        inputClassName,
                                                                        id,
                                                                        ...props
                                                                      }, ref) => {
  const autoId = React.useId();
  const fieldId = id || autoId;

  return (
    <div className={cn('group', className)}>
      <div className="flex items-baseline justify-between gap-3">
        <label
          htmlFor={fieldId}
          className="flex items-center gap-2 text-[13px] font-medium text-muted-foreground transition-colors group-focus-within:text-foreground"
        >
          <Icon className="h-3.5 w-3.5 shrink-0" aria-hidden="true"/>
          {label}
        </label>
        {hint}
      </div>

      <div className="relative mt-1">
        <input
          id={fieldId}
          ref={ref}
          aria-invalid={error ? true : undefined}
          className={cn(
            'h-11 w-full appearance-none rounded-none border-0 border-b bg-transparent pb-1 text-[15px] text-foreground transition-colors',
            'placeholder:text-muted-foreground/60 focus:outline-none disabled:opacity-50',
            error ? 'border-destructive' : 'border-input focus:border-primary',
            action ? 'pr-10' : '',
            inputClassName,
          )}
          {...props}
        />
        {action && (
          <div className="absolute right-0 top-1/2 -translate-y-1/2">{action}</div>
        )}
      </div>

      {error ? (
        <p className="mt-2 flex items-center gap-1.5 text-xs text-destructive">
          <AlertCircle className="h-3 w-3 shrink-0"/>
          {error}
        </p>
      ) : description ? (
        <div className="mt-2">{description}</div>
      ) : null}
    </div>
  );
});

AuthField.displayName = 'AuthField';

export default AuthField;
