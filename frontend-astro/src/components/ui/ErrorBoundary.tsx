'use client';
import React from 'react';

interface ErrorBoundaryProps {
    children: React.ReactNode;
    fallback?: React.ReactNode;
    onError?: (error: Error, errorInfo: React.ErrorInfo) => void;
}

interface ErrorBoundaryState {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
    constructor(props: ErrorBoundaryProps) {
        super(props);
        this.state = {hasError: false, error: null};
    }

    static getDerivedStateFromError(error: Error): ErrorBoundaryState {
        return {hasError: true, error};
    }

    componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
        console.error('[ErrorBoundary]', error, errorInfo);
        this.props.onError?.(error, errorInfo);
    }

    private handleRetry = () => {
        this.setState({hasError: false, error: null});
    };

    render() {
        if (this.state.hasError) {
            if (this.props.fallback) return this.props.fallback;

            return (
                <div className="min-h-[200px] flex items-center justify-center p-8">
                    <div className="text-center max-w-md">
                        {/* Error icon */}
                        <div
                            className="mx-auto w-16 h-16 rounded-2xl bg-gradient-to-br from-red-50 to-orange-50 dark:from-red-900/20 dark:to-orange-900/20 flex items-center justify-center mb-5 border border-red-100 dark:border-red-800/30">
                            <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor"
                                 strokeWidth={1.5}>
                                <path strokeLinecap="round" strokeLinejoin="round"
                                      d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/>
                            </svg>
                        </div>

                        {/* Error message */}
                        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                            组件加载出错
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">
                            该组件在渲染过程中遇到了问题
                        </p>
                        {this.state.error && (
                            <p className="text-xs text-red-500 dark:text-red-400 font-mono bg-red-50 dark:bg-red-900/20 px-3 py-2 rounded-lg mb-5 break-all">
                                {this.state.error.message}
                            </p>
                        )}

                        {/* Actions */}
                        <div className="flex items-center justify-center gap-3">
                            <button
                                onClick={this.handleRetry}
                                className="px-5 py-2.5 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white text-sm font-medium rounded-xl shadow-lg shadow-blue-500/25 transition-all duration-200 active:scale-95"
                            >
                                重新加载
                            </button>
                            <button
                                onClick={() => window.location.reload()}
                                className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium rounded-xl transition-all duration-200 active:scale-95"
                            >
                                刷新页面
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

/**
 * Hook-based wrapper for simpler usage
 */
export const withErrorBoundary = <P extends object>(
    Component: React.ComponentType<P>,
    fallback?: React.ReactNode
) => {
    const Wrapped = (props: P) => (
        <ErrorBoundary fallback={fallback}>
            <Component {...props} />
        </ErrorBoundary>
    );
    Wrapped.displayName = `withErrorBoundary(${Component.displayName || Component.name})`;
    return Wrapped;
};
