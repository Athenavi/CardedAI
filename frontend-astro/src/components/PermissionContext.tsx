'use client';

import React, {createContext, useContext, useEffect, useState} from 'react';
import {apiClient} from '@/lib/api/base-client';

interface UserPermissions {
  is_superuser: boolean;
  is_staff: boolean;
  username?: string;
  id?: number;
}

interface PermissionContextType {
  permissions: UserPermissions | null;
  loading: boolean;
}

const PermissionContext = createContext<PermissionContextType>({
  permissions: null,
  loading: true,
});

export function usePermissions() {
  return useContext(PermissionContext);
}

export function PermissionProvider({children}: {children: React.ReactNode}) {
  const [permissions, setPermissions] = useState<UserPermissions | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const fetchPermissions = async () => {
      try {
        const res = await apiClient.get('/users/me');
        if (res.success && res.data && !cancelled) {
          setPermissions({
            is_superuser: res.data.is_superuser ?? false,
            is_staff: res.data.is_staff ?? false,
            username: res.data.username,
            id: res.data.id,
          });
        }
      } catch {
        // ignore - AuthGuard handles redirect
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    // Small delay to let AuthGuard finish first
    const timer = setTimeout(fetchPermissions, 100);
    return () => { cancelled = true; clearTimeout(timer); };
  }, []);

  return (
    <PermissionContext.Provider value={{permissions, loading}}>
      {children}
    </PermissionContext.Provider>
  );
}
