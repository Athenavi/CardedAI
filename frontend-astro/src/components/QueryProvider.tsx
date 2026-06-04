'use client';

import React, {useState} from 'react';
import {QueryClient, QueryClientProvider} from '@tanstack/react-query';
import {ErrorBoundary} from '@/components/ui/ErrorBoundary';
import {ConfirmProvider} from '@/components/ui/confirm-provider';
import {I18nProvider} from '@/lib/i18n';

export function QueryProvider({children}: {children: React.ReactNode}) {
  const [qc] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60_000,
        gcTime: 5 * 60_000,
        retry: 1,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10_000),
        refetchOnWindowFocus: false,
        refetchOnMount: true,
        refetchOnReconnect: true,
      },
      mutations: {
        retry: 0,
      },
    },
  }));
  return (
      <ErrorBoundary>
        <I18nProvider>
          <QueryClientProvider client={qc}>
            <ConfirmProvider>
              {children}
            </ConfirmProvider>
          </QueryClientProvider>
        </I18nProvider>
      </ErrorBoundary>
  );
}
