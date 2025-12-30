"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bell,
  AlertTriangle,
  Info,
  AlertCircle,
  XCircle,
  Check,
  CheckCheck,
  X,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import type { AdminAlert, PaginatedResponse } from '@/types';

const severityConfig = {
  info: {
    icon: Info,
    color: 'text-blue-400',
    bg: 'bg-blue-500/10',
    border: 'border-blue-500/30',
  },
  warning: {
    icon: AlertTriangle,
    color: 'text-yellow-400',
    bg: 'bg-yellow-500/10',
    border: 'border-yellow-500/30',
  },
  error: {
    icon: AlertCircle,
    color: 'text-orange-400',
    bg: 'bg-orange-500/10',
    border: 'border-orange-500/30',
  },
  critical: {
    icon: XCircle,
    color: 'text-red-400',
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
  },
};

export default function AlertsTab() {
  const [alerts, setAlerts] = useState<AdminAlert[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const perPage = 20;

  const fetchAlerts = useCallback(async (pageNum: number, unread: boolean) => {
    setLoading(true);
    try {
      const res = await adminAPI.getAlerts({
        page: pageNum,
        per_page: perPage,
        unread_only: unread,
      });
      setAlerts(res.data.items);
      setPage(res.data.page);
      setTotalPages(res.data.total_pages);
      setTotal(res.data.total);
    } catch (error) {
      console.error('Error fetching alerts:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAlerts(1, unreadOnly);
  }, [fetchAlerts, unreadOnly]);

  const markAsRead = async (id: number) => {
    try {
      await adminAPI.markAlertRead(id);
      setAlerts(alerts.map(a =>
        a.id === id ? { ...a, is_read: true } : a
      ));
    } catch (error) {
      console.error('Error marking alert as read:', error);
    }
  };

  const dismissAlert = async (id: number) => {
    try {
      await adminAPI.dismissAlert(id);
      setAlerts(alerts.filter(a => a.id !== id));
      setTotal(total - 1);
    } catch (error) {
      console.error('Error dismissing alert:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      await adminAPI.markAllAlertsRead();
      setAlerts(alerts.map(a => ({ ...a, is_read: true })));
    } catch (error) {
      console.error('Error marking all as read:', error);
    }
  };

  const unreadCount = alerts.filter(a => !a.is_read).length;

  return (
    <div className="space-y-6">
      {/* Header Actions */}
      <Card className="glass border-white/10">
        <CardContent className="p-4">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-primary" />
                <span className="font-medium">
                  {total} alerte{total > 1 ? 's' : ''}
                </span>
                {unreadCount > 0 && (
                  <Badge variant="outline" className="bg-red-500/20 text-red-400 border-red-500/30">
                    {unreadCount} non lue{unreadCount > 1 ? 's' : ''}
                  </Badge>
                )}
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={unreadOnly}
                  onChange={(e) => setUnreadOnly(e.target.checked)}
                  className="rounded border-white/20 bg-slate-800"
                />
                <span className="text-sm text-slate-400">Non lues uniquement</span>
              </label>
            </div>
            <Button
              variant="outline"
              className="border-white/20"
              onClick={markAllAsRead}
              disabled={unreadCount === 0}
            >
              <CheckCheck className="h-4 w-4 mr-2" />
              Tout marquer comme lu
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Alerts List */}
      <Card className="glass border-white/10">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Bell className="h-5 w-5 text-primary" />
            Alertes système
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-24 bg-slate-800" />
              ))}
            </div>
          ) : alerts.length === 0 ? (
            <div className="py-12 text-center">
              <Bell className="h-12 w-12 text-slate-600 mx-auto mb-4" />
              <p className="text-slate-400">Aucune alerte</p>
            </div>
          ) : (
            <AnimatePresence mode="popLayout">
              <div className="space-y-4">
                {alerts.map((alert) => {
                  const config = severityConfig[alert.severity];
                  const Icon = config.icon;

                  return (
                    <motion.div
                      key={alert.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: -100 }}
                      className={cn(
                        "p-4 rounded-lg border transition-all",
                        config.bg,
                        config.border,
                        !alert.is_read && "ring-2 ring-offset-2 ring-offset-slate-900",
                        !alert.is_read && alert.severity === 'critical' && "ring-red-500",
                        !alert.is_read && alert.severity === 'error' && "ring-orange-500",
                        !alert.is_read && alert.severity === 'warning' && "ring-yellow-500",
                        !alert.is_read && alert.severity === 'info' && "ring-blue-500"
                      )}
                    >
                      <div className="flex items-start gap-4">
                        <div className={cn("p-2 rounded-lg", config.bg)}>
                          <Icon className={cn("h-5 w-5", config.color)} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <div className="flex items-center gap-2 mb-1">
                                <h4 className="font-medium text-white">{alert.title}</h4>
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    "text-xs",
                                    config.bg,
                                    config.border,
                                    config.color
                                  )}
                                >
                                  {alert.severity}
                                </Badge>
                                {!alert.is_read && (
                                  <span className="h-2 w-2 rounded-full bg-blue-500" />
                                )}
                              </div>
                              <p className="text-sm text-slate-300">{alert.message}</p>
                              <p className="text-xs text-slate-500 mt-2">
                                {new Date(alert.created_at).toLocaleDateString('fr-FR', {
                                  day: '2-digit',
                                  month: 'short',
                                  year: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })}
                                {' • '}
                                Type: {alert.type}
                              </p>
                            </div>
                            <div className="flex items-center gap-2">
                              {!alert.is_read && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="text-slate-400 hover:text-white"
                                  onClick={() => markAsRead(alert.id)}
                                >
                                  <Check className="h-4 w-4" />
                                </Button>
                              )}
                              <Button
                                size="sm"
                                variant="ghost"
                                className="text-slate-400 hover:text-red-400"
                                onClick={() => dismissAlert(alert.id)}
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </AnimatePresence>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-white/10 mt-4">
              <p className="text-sm text-slate-400">
                Page {page} sur {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="border-white/20"
                  onClick={() => fetchAlerts(page - 1, unreadOnly)}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="border-white/20"
                  onClick={() => fetchAlerts(page + 1, unreadOnly)}
                  disabled={page >= totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
