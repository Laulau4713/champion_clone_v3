"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/auth-store";

// Routes that require authentication
const protectedRoutes = ["/dashboard", "/learn", "/training", "/upload", "/admin"];

// Routes only accessible when NOT authenticated
const authRoutes = ["/login", "/register"];

/**
 * Hook to handle auth-based redirections
 * - Redirects authenticated users from "/" to "/dashboard"
 * - Redirects authenticated users from auth pages to "/dashboard"
 * - Redirects non-authenticated users from protected routes to "/login"
 */
export function useAuthRedirect() {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isHydrated } = useAuthStore();

  useEffect(() => {
    // Wait for auth store to hydrate from localStorage
    if (!isHydrated) return;

    const isProtectedRoute = protectedRoutes.some(
      (route) => pathname === route || pathname.startsWith(route + "/")
    );
    const isAuthRoute = authRoutes.includes(pathname);
    const isHomePage = pathname === "/";

    if (isAuthenticated) {
      // Redirect authenticated users from home and auth pages to dashboard
      if (isHomePage || isAuthRoute) {
        router.replace("/dashboard");
      }
    } else {
      // Redirect non-authenticated users from protected routes to login
      if (isProtectedRoute) {
        router.replace("/login");
      }
    }
  }, [isAuthenticated, isHydrated, pathname, router]);

  return { isAuthenticated, isHydrated };
}
