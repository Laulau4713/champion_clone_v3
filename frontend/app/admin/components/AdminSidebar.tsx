"use client";

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  Users,
  Activity,
  AlertTriangle,
  Mail,
  Webhook,
  Bell,
  Shield,
  Mic,
  FileText,
  ChevronLeft,
  ChevronRight,
  Home,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuthStore } from '@/store/auth-store';
import { Button } from '@/components/ui/button';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';

interface NavItem {
  id: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  href?: string;
}

const navItems: NavItem[] = [
  { id: 'overview', label: 'Vue d\'ensemble', icon: LayoutDashboard },
  { id: 'users', label: 'Utilisateurs', icon: Users },
  { id: 'sessions', label: 'Sessions', icon: Mic },
  { id: 'activity', label: 'Activité', icon: Activity },
  { id: 'errors', label: 'Erreurs', icon: AlertTriangle },
  { id: 'emails', label: 'Emails', icon: Mail },
  { id: 'webhooks', label: 'Webhooks', icon: Webhook },
  { id: 'alerts', label: 'Alertes', icon: Bell },
  { id: 'audit', label: 'Audit', icon: FileText },
];

interface AdminSidebarProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

export default function AdminSidebar({ activeTab, onTabChange }: AdminSidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();
  const [isCollapsed, setIsCollapsed] = useState(false);

  const isDetailPage = pathname.includes('/admin/users/');

  return (
    <TooltipProvider>
      <motion.aside
        initial={false}
        animate={{ width: isCollapsed ? 80 : 240 }}
        className={cn(
          "fixed left-0 top-16 bottom-0 z-40",
          "bg-slate-900/95 backdrop-blur-xl border-r border-white/10",
          "flex flex-col"
        )}
      >
        {/* Collapse Toggle */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-6 p-1.5 rounded-full bg-slate-800 border border-white/10 hover:bg-slate-700 transition-colors"
        >
          {isCollapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>

        {/* Header */}
        <div className={cn(
          "p-4 border-b border-white/10",
          isCollapsed ? "flex justify-center" : ""
        )}>
          {isCollapsed ? (
            <Shield className="h-6 w-6 text-primary" />
          ) : (
            <div className="flex items-center gap-2">
              <Shield className="h-6 w-6 text-primary" />
              <span className="font-bold text-white">Admin Panel</span>
            </div>
          )}
        </div>

        {/* Back to Dashboard */}
        <div className="p-2 border-b border-white/10">
          <Tooltip>
            <TooltipTrigger asChild>
              <Link href="/dashboard">
                <Button
                  variant="ghost"
                  className={cn(
                    "w-full justify-start gap-3 text-slate-400 hover:text-white hover:bg-white/5",
                    isCollapsed && "justify-center px-2"
                  )}
                >
                  <Home className="h-5 w-5 flex-shrink-0" />
                  <AnimatePresence>
                    {!isCollapsed && (
                      <motion.span
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: 'auto' }}
                        exit={{ opacity: 0, width: 0 }}
                      >
                        Dashboard
                      </motion.span>
                    )}
                  </AnimatePresence>
                </Button>
              </Link>
            </TooltipTrigger>
            {isCollapsed && (
              <TooltipContent side="right">
                <p>Dashboard</p>
              </TooltipContent>
            )}
          </Tooltip>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id && !isDetailPage;

            return (
              <Tooltip key={item.id}>
                <TooltipTrigger asChild>
                  <button
                    onClick={() => onTabChange(item.id)}
                    className={cn(
                      "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all",
                      isCollapsed && "justify-center px-2",
                      isActive
                        ? "bg-primary text-white shadow-lg shadow-primary/25"
                        : "text-slate-400 hover:text-white hover:bg-white/5"
                    )}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    <AnimatePresence>
                      {!isCollapsed && (
                        <motion.span
                          initial={{ opacity: 0, width: 0 }}
                          animate={{ opacity: 1, width: 'auto' }}
                          exit={{ opacity: 0, width: 0 }}
                          className="font-medium whitespace-nowrap"
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </button>
                </TooltipTrigger>
                {isCollapsed && (
                  <TooltipContent side="right">
                    <p>{item.label}</p>
                  </TooltipContent>
                )}
              </Tooltip>
            );
          })}
        </nav>

        {/* User Info & Logout */}
        <div className="p-2 border-t border-white/10">
          <div className={cn(
            "px-3 py-2 rounded-lg bg-white/5 mb-2",
            isCollapsed ? "text-center" : ""
          )}>
            {isCollapsed ? (
              <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center mx-auto">
                <span className="text-sm font-bold text-primary">
                  {user?.email?.[0]?.toUpperCase()}
                </span>
              </div>
            ) : (
              <>
                <p className="text-sm font-medium text-white truncate">
                  {user?.full_name || 'Admin'}
                </p>
                <p className="text-xs text-slate-400 truncate">{user?.email}</p>
              </>
            )}
          </div>

          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                onClick={logout}
                className={cn(
                  "w-full justify-start gap-3 text-red-400 hover:text-red-300 hover:bg-red-500/10",
                  isCollapsed && "justify-center px-2"
                )}
              >
                <LogOut className="h-5 w-5 flex-shrink-0" />
                <AnimatePresence>
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, width: 0 }}
                      animate={{ opacity: 1, width: 'auto' }}
                      exit={{ opacity: 0, width: 0 }}
                    >
                      Déconnexion
                    </motion.span>
                  )}
                </AnimatePresence>
              </Button>
            </TooltipTrigger>
            {isCollapsed && (
              <TooltipContent side="right">
                <p>Déconnexion</p>
              </TooltipContent>
            )}
          </Tooltip>
        </div>
      </motion.aside>
    </TooltipProvider>
  );
}
