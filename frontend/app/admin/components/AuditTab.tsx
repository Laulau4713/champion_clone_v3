"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  FileText,
  Filter,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  User,
  Clock,
  Globe,
  Eye,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface AuditLog {
  id: number;
  admin_id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  old_value: Record<string, unknown> | null;
  new_value: Record<string, unknown> | null;
  ip_address: string;
  created_at: string;
}

interface AuditLogDetail extends AuditLog {
  user_agent: string;
}

export default function AuditTab() {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [actionFilter, setActionFilter] = useState<string>('');
  const [resourceFilter, setResourceFilter] = useState<string>('');
  const [availableActions, setAvailableActions] = useState<string[]>([]);
  const [selectedLog, setSelectedLog] = useState<AuditLogDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const perPage = 20;

  const fetchLogs = useCallback(async (pageNum: number, action: string, resource: string) => {
    setLoading(true);
    try {
      const res = await adminAPI.getAuditLogs({
        page: pageNum,
        per_page: perPage,
        action: action || undefined,
        resource_type: resource || undefined,
      });
      setLogs(res.data.items);
      setPage(res.data.page);
      setTotalPages(res.data.total_pages);
      setTotal(res.data.total);
      if (res.data.available_actions) {
        setAvailableActions(res.data.available_actions);
      }
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLogs(1, actionFilter, resourceFilter);
  }, [fetchLogs, actionFilter, resourceFilter]);

  const viewLogDetail = async (logId: number) => {
    setDetailLoading(true);
    try {
      const res = await adminAPI.getAuditLog(logId);
      setSelectedLog(res.data);
    } catch (error) {
      console.error('Error fetching audit log detail:', error);
    } finally {
      setDetailLoading(false);
    }
  };

  const getActionBadge = (action: string) => {
    if (action.includes('create') || action.includes('add')) {
      return <Badge className="bg-green-500/20 text-green-400 border-green-500/30">{action}</Badge>;
    }
    if (action.includes('delete') || action.includes('remove')) {
      return <Badge className="bg-red-500/20 text-red-400 border-red-500/30">{action}</Badge>;
    }
    if (action.includes('update') || action.includes('edit')) {
      return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">{action}</Badge>;
    }
    return <Badge variant="outline">{action}</Badge>;
  };

  const getResourceBadge = (resourceType: string) => {
    const colors: Record<string, string> = {
      user: 'bg-purple-500/20 text-purple-400',
      webhook: 'bg-orange-500/20 text-orange-400',
      email_template: 'bg-cyan-500/20 text-cyan-400',
      champion: 'bg-yellow-500/20 text-yellow-400',
      session: 'bg-pink-500/20 text-pink-400',
    };
    const color = colors[resourceType] || 'bg-slate-500/20 text-slate-400';
    return <Badge className={color}>{resourceType}</Badge>;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const uniqueResourceTypes = Array.from(new Set(logs.map(l => l.resource_type)));

  return (
    <div className="space-y-6">
      {/* Stats Card */}
      <Card className="glass border-white/10">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">Total Logs</p>
              <p className="text-2xl font-bold text-white">{total}</p>
            </div>
            <div className="p-3 rounded-lg bg-primary/20">
              <FileText className="h-6 w-6 text-primary" />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Audit Logs List */}
      <Card className="glass border-white/10">
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Journal d&apos;audit
            </CardTitle>

            {/* Filters */}
            <div className="flex items-center gap-2 flex-wrap">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="">Toutes les actions</option>
                {availableActions.map(action => (
                  <option key={action} value={action}>{action}</option>
                ))}
              </select>
              <select
                value={resourceFilter}
                onChange={(e) => setResourceFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="">Toutes les ressources</option>
                {uniqueResourceTypes.map(type => (
                  <option key={type} value={type}>{type}</option>
                ))}
              </select>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Aucun log d&apos;audit trouvé</p>
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log, index) => (
                <motion.div
                  key={log.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.03 }}
                  className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 rounded-lg bg-primary/20">
                      <FileText className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        {getActionBadge(log.action)}
                        {getResourceBadge(log.resource_type)}
                        <span className="text-sm text-slate-400">#{log.resource_id}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          Admin #{log.admin_id}
                        </span>
                        <span>|</span>
                        <span className="flex items-center gap-1">
                          <Globe className="h-3 w-3" />
                          {log.ip_address}
                        </span>
                        <span>|</span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {formatDate(log.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => viewLogDetail(log.id)}
                  >
                    <Eye className="h-4 w-4 mr-1" />
                    Détails
                  </Button>
                </motion.div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/10">
              <p className="text-sm text-slate-400">
                Page {page} sur {totalPages} ({total} logs)
              </p>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchLogs(1, actionFilter, resourceFilter)}
                  disabled={page === 1}
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchLogs(page - 1, actionFilter, resourceFilter)}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="px-3 py-1 text-sm text-white">{page}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchLogs(page + 1, actionFilter, resourceFilter)}
                  disabled={page === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchLogs(totalPages, actionFilter, resourceFilter)}
                  disabled={page === totalPages}
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="glass border-white/10 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5 text-primary" />
              Détail du log #{selectedLog?.id}
            </DialogTitle>
          </DialogHeader>

          {detailLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-24 w-full" />
            </div>
          ) : selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400">Action</p>
                  <div className="mt-1">{getActionBadge(selectedLog.action)}</div>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Ressource</p>
                  <div className="mt-1 flex items-center gap-2">
                    {getResourceBadge(selectedLog.resource_type)}
                    <span className="text-white">#{selectedLog.resource_id}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Admin ID</p>
                  <p className="text-white">{selectedLog.admin_id}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Date</p>
                  <p className="text-white">{formatDate(selectedLog.created_at)}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">Adresse IP</p>
                  <p className="text-white">{selectedLog.ip_address}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400">User Agent</p>
                  <p className="text-white text-xs truncate">{selectedLog.user_agent || '-'}</p>
                </div>
              </div>

              {selectedLog.old_value && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">Ancienne valeur</p>
                  <pre className="bg-white/5 rounded-lg p-3 text-xs text-slate-300 overflow-auto max-h-32">
                    {JSON.stringify(selectedLog.old_value, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.new_value && (
                <div>
                  <p className="text-sm text-slate-400 mb-2">Nouvelle valeur</p>
                  <pre className="bg-white/5 rounded-lg p-3 text-xs text-slate-300 overflow-auto max-h-32">
                    {JSON.stringify(selectedLog.new_value, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
