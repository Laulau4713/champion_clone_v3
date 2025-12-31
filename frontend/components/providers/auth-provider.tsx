'use client';

import { useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuthStore } from '@/store/auth-store';
import { authAPI } from '@/lib/api';

// Routes that require authentication
const PROTECTED_ROUTES = ['/dashboard', '/learn', '/training', '/upload', '/admin'];

// Routes only accessible when NOT authenticated
const AUTH_ROUTES = ['/login', '/register'];

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isHydrated, setUser, setLoading, logout } = useAuthStore();

  // Check auth status on mount
  useEffect(() => {
    const checkAuth = async () => {
      if (typeof window === 'undefined') return;

      const token = localStorage.getItem('access_token');

      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const { data: user } = await authAPI.me();
        setUser(user);
      } catch {
        logout();
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, [setUser, setLoading, logout]);

  // Handle route redirections after hydration
  useEffect(() => {
    if (!isHydrated) return;

    const isProtectedRoute = PROTECTED_ROUTES.some(
      (route) => pathname === route || pathname.startsWith(route + '/')
    );
    const isAuthRoute = AUTH_ROUTES.includes(pathname);
    const isHomePage = pathname === '/';

    if (isAuthenticated) {
      // Redirect authenticated users from home and auth pages to dashboard
      if (isHomePage || isAuthRoute) {
        router.replace('/dashboard');
      }
    } else {
      // Redirect non-authenticated users from protected routes to login
      if (isProtectedRoute) {
        router.replace('/login');
      }
    }
  }, [isAuthenticated, isHydrated, pathname, router]);

  return <>{children}</>;
}
