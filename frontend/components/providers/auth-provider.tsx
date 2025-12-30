'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { authAPI } from '@/lib/api';

const PUBLIC_ROUTES = ['/', '/login', '/register'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, setUser, setLoading, logout } = useAuthStore();

  useEffect(() => {
    const checkAuth = async () => {
      if (typeof window === 'undefined') return;

      const token = localStorage.getItem('access_token');

      if (!token) {
        setLoading(false);
        if (!PUBLIC_ROUTES.includes(pathname)) {
          router.push('/login');
        }
        return;
      }

      try {
        const { data: user } = await authAPI.me();
        setUser(user);
      } catch {
        logout();
        if (!PUBLIC_ROUTES.includes(pathname)) {
          router.push('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [pathname, router, setUser, setLoading, logout]);

  // Don't block rendering, just check auth in background
  return <>{children}</>;
}
