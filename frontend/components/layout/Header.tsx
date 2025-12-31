"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Menu,
  X,
  Sparkles,
  LogOut,
  User,
  Shield,
  LayoutDashboard,
  BookOpen,
  Target,
  Upload,
  ChevronDown,
} from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/store/auth-store";
import { authAPI } from "@/lib/api";

// Navigation for authenticated users only
const authNavLinks = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, premiumOnly: false },
  { href: "/learn", label: "Apprendre", icon: BookOpen, premiumOnly: false },
  { href: "/training", label: "Training", icon: Target, premiumOnly: false },
  { href: "/upload", label: "Upload", icon: Upload, premiumOnly: true },
];

export function Header() {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, isAuthenticated, logout } = useAuthStore();

  // Filter nav links based on user subscription
  const isFreeUser = user?.subscription_plan === "free";
  const filteredNavLinks = authNavLinks.filter(link => !link.premiumOnly || !isFreeUser);

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch {
      // Ignore error, still logout locally
    }
    logout();
    router.push('/');
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <motion.nav
          initial={{ y: -20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="glass mt-4 rounded-2xl px-6 py-4"
        >
          <div className="flex items-center justify-between">
            {/* Logo */}
            <Link href={isAuthenticated ? "/dashboard" : "/"} className="flex items-center gap-2 group">
              <div className="relative">
                <div className="absolute inset-0 bg-gradient-primary rounded-lg blur-lg opacity-50 group-hover:opacity-75 transition-opacity" />
                <div className="relative bg-gradient-primary p-2 rounded-lg">
                  <Sparkles className="h-5 w-5 text-white" />
                </div>
              </div>
              <span className="font-bold text-xl gradient-text">
                Champion Clone
              </span>
            </Link>

            {/* Desktop Navigation - Only for authenticated users */}
            {isAuthenticated && (
              <div className="hidden md:flex items-center gap-1">
                {filteredNavLinks.map((link) => {
                  const Icon = link.icon;
                  const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
                  return (
                    <Link
                      key={link.href}
                      href={link.href}
                      className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200",
                        isActive
                          ? "bg-primary-500/20 text-primary-400"
                          : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                      )}
                    >
                      <Icon className="h-4 w-4" />
                      {link.label}
                    </Link>
                  );
                })}
              </div>
            )}

            {/* Auth Section */}
            <div className="hidden md:flex items-center gap-3">
              {isAuthenticated ? (
                <>
                  {/* Admin link */}
                  {user?.role === "admin" && (
                    <Link
                      href="/admin"
                      className={cn(
                        "flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium transition-all",
                        pathname === "/admin" || pathname.startsWith("/admin/")
                          ? "bg-purple-500/20 text-purple-400"
                          : "text-purple-400 hover:bg-purple-500/10"
                      )}
                    >
                      <Shield className="h-4 w-4" />
                      Admin
                    </Link>
                  )}

                  {/* User dropdown */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10"
                      >
                        <div className="h-8 w-8 rounded-full bg-primary-500/20 flex items-center justify-center">
                          <User className="h-4 w-4 text-primary-400" />
                        </div>
                        <span className="text-sm text-muted-foreground max-w-[120px] truncate">
                          {user?.full_name || user?.email?.split('@')[0]}
                        </span>
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <div className="px-2 py-1.5">
                        <p className="text-sm font-medium">{user?.full_name || "Utilisateur"}</p>
                        <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
                      </div>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem onClick={handleLogout} className="text-red-400 focus:text-red-400">
                        <LogOut className="h-4 w-4 mr-2" />
                        Déconnexion
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </>
              ) : (
                /* Non-authenticated: Features + Connexion + Essai gratuit */
                <>
                  <Link
                    href="/features"
                    className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                  >
                    En savoir plus
                  </Link>
                  <Button
                    asChild
                    variant="ghost"
                    className="text-sm"
                  >
                    <Link href="/login">Connexion</Link>
                  </Button>
                  <Button
                    asChild
                    className="bg-gradient-primary hover:opacity-90 text-white border-0"
                  >
                    <Link href="/register">Essai gratuit</Link>
                  </Button>
                </>
              )}
            </div>

            {/* Mobile Menu Button */}
            <button
              className="md:hidden p-2 text-muted-foreground hover:text-foreground"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="h-6 w-6" />
              ) : (
                <Menu className="h-6 w-6" />
              )}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="md:hidden mt-4 pt-4 border-t border-white/10"
            >
              <div className="flex flex-col gap-2">
                {isAuthenticated ? (
                  <>
                    {/* Navigation links for authenticated users */}
                    {filteredNavLinks.map((link) => {
                      const Icon = link.icon;
                      const isActive = pathname === link.href || pathname.startsWith(link.href + "/");
                      return (
                        <Link
                          key={link.href}
                          href={link.href}
                          onClick={() => setMobileMenuOpen(false)}
                          className={cn(
                            "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
                            isActive
                              ? "bg-primary-500/20 text-primary-400"
                              : "text-muted-foreground hover:text-foreground hover:bg-white/5"
                          )}
                        >
                          <Icon className="h-5 w-5" />
                          {link.label}
                        </Link>
                      );
                    })}

                    <div className="border-t border-white/10 pt-4 mt-2">
                      <div className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground">
                        <User className="h-4 w-4" />
                        {user?.full_name || user?.email}
                      </div>
                      {user?.role === "admin" && (
                        <Link
                          href="/admin"
                          onClick={() => setMobileMenuOpen(false)}
                          className={cn(
                            "flex items-center gap-2 px-4 py-3 rounded-lg text-sm font-medium transition-all",
                            pathname === "/admin" || pathname.startsWith("/admin/")
                              ? "bg-purple-500/20 text-purple-400"
                              : "text-purple-400 hover:bg-purple-500/10"
                          )}
                        >
                          <Shield className="h-4 w-4" />
                          Panel Admin
                        </Link>
                      )}
                      <Button
                        variant="ghost"
                        className="w-full justify-start text-red-400 hover:text-red-400 hover:bg-red-500/10"
                        onClick={() => {
                          handleLogout();
                          setMobileMenuOpen(false);
                        }}
                      >
                        <LogOut className="h-4 w-4 mr-2" />
                        Déconnexion
                      </Button>
                    </div>
                  </>
                ) : (
                  /* Non-authenticated mobile */
                  <div className="space-y-2">
                    <Link
                      href="/features"
                      onClick={() => setMobileMenuOpen(false)}
                      className="block px-4 py-3 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-white/5"
                    >
                      En savoir plus
                    </Link>
                    <Button
                      asChild
                      variant="ghost"
                      className="w-full justify-start"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Link href="/login">Connexion</Link>
                    </Button>
                    <Button
                      asChild
                      className="w-full bg-gradient-primary hover:opacity-90 text-white border-0"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      <Link href="/register">Essai gratuit</Link>
                    </Button>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </motion.nav>
      </div>
    </header>
  );
}
