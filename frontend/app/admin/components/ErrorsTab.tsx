"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  AlertTriangle,
  CheckCircle,
  XCircle,
  ChevronLeft,
  ChevronRight,
  Eye,
  Check,
  Filter,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import type { ErrorStats, PaginatedResponse } from '@/types';

interface ErrorLogItem {
  id: number;
  user_id: number | null;
  error_type: string;
  error_message: string;
  endpoint: string;
  is_resolved: boolean;
  resolved_at: string | null;
  resolution_notes: string | null;
  created_at: string;
}

export default function ErrorsTab() {
  const [stats, setStats] = useState<ErrorStats | null>(null);
  const [errors, setErrors] = useState<ErrorLogItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [resolvedFilter, setResolvedFilter] = useState<boolean | undefined>(undefined);
  const [selectedError, setSelectedError] = useState<number | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  const perPage = 20;

  const fetchData = useCallback(async (pageNum: number, resolved?: boolean) => {
    setLoading(true);
    try {
      const [statsRes, errorsRes] = await Promise.all([
        adminAPI.getErrorStats(7),
        adminAPI.getErrors({ page: pageNum, per_page: perPage, resolved }),
      ]);
      setStats(statsRes.data);
      setErrors(errorsRes.data.items);
      setPage(errorsRes.data.page);
      setTotalPages(errorsRes.data.total_pages);
      setTotal(errorsRes.data.total);
    } catch (error) {
      console.error('Error fetching errors data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(1, resolvedFilter);
  }, [fetchData, resolvedFilter]);

  const resolveError = async (id: number) => {
    try {
      await adminAPI.resolveError(id, resolutionNotes || undefined);
      setErrors(errors.map(e =>
        e.id === id ? { ...e, is_resolved: true, resolution_notes: resolutionNotes } : e
      ));
      setSelectedError(null);
      setResolutionNotes('');
      if (stats) {
        setStats({
          ...stats,
          resolved: stats.resolved + 1,
          unresolved: stats.unresolved - 1,
        });
      }
    } catch (error) {
      console.error('Error resolving error:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Total erreurs</p>
                  <p className="text-2xl font-bold">{stats?.total || 0}</p>
                  <p className="text-xs text-slate-500">7 derniers jours</p>
                </div>
                <div className="p-3 rounded-xl bg-red-500/20">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Non résolues</p>
                  <p className="text-2xl font-bold text-red-400">{stats?.unresolved || 0}</p>
                </div>
                <div className="p-3 rounded-xl bg-red-500/20">
                  <XCircle className="h-5 w-5 text-red-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Résolues</p>
                  <p className="text-2xl font-bold text-green-400">{stats?.resolved || 0}</p>
                </div>
                <div className="p-3 rounded-xl bg-green-500/20">
                  <CheckCircle className="h-5 w-5 text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Taux résolution</p>
                  <p className="text-2xl font-bold text-blue-400">
                    {stats && stats.total > 0
                      ? ((stats.resolved / stats.total) * 100).toFixed(0)
                      : 0}%
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-blue-500/20">
                  <Check className="h-5 w-5 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Error Types */}
      {stats?.by_type && Object.keys(stats.by_type).length > 0 && (
        <Card className="glass border-white/10">
          <CardHeader>
            <CardTitle className="text-lg">Erreurs par type</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              {Object.entries(stats.by_type).map(([type, count]) => (
                <Badge
                  key={type}
                  variant="outline"
                  className="bg-red-500/10 text-red-400 border-red-500/30 text-sm py-1 px-3"
                >
                  {type}: {count}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card className="glass border-white/10">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <Filter className="h-4 w-4 text-slate-400" />
            <div className="flex gap-2">
              <Button
                size="sm"
                variant={resolvedFilter === undefined ? 'default' : 'outline'}
                className={resolvedFilter === undefined ? 'bg-primary' : 'border-white/20'}
                onClick={() => setResolvedFilter(undefined)}
              >
                Toutes
              </Button>
              <Button
                size="sm"
                variant={resolvedFilter === false ? 'default' : 'outline'}
                className={resolvedFilter === false ? 'bg-red-500' : 'border-white/20'}
                onClick={() => setResolvedFilter(false)}
              >
                Non résolues
              </Button>
              <Button
                size="sm"
                variant={resolvedFilter === true ? 'default' : 'outline'}
                className={resolvedFilter === true ? 'bg-green-500' : 'border-white/20'}
                onClick={() => setResolvedFilter(true)}
              >
                Résolues
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Errors List */}
      <Card className="glass border-white/10">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <AlertTriangle className="h-5 w-5 text-primary" />
            Journal des erreurs ({total})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-20 bg-slate-800" />
              ))}
            </div>
          ) : errors.length === 0 ? (
            <div className="py-12 text-center">
              <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
              <p className="text-slate-400">Aucune erreur à afficher</p>
            </div>
          ) : (
            <div className="space-y-4">
              {errors.map((error) => (
                <motion.div
                  key={error.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className={cn(
                    "p-4 rounded-lg border",
                    error.is_resolved
                      ? "bg-green-500/5 border-green-500/20"
                      : "bg-red-500/5 border-red-500/20"
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Badge
                          variant="outline"
                          className={cn(
                            error.is_resolved
                              ? "bg-green-500/20 text-green-400 border-green-500/30"
                              : "bg-red-500/20 text-red-400 border-red-500/30"
                          )}
                        >
                          {error.is_resolved ? 'Résolu' : 'Non résolu'}
                        </Badge>
                        <Badge variant="outline" className="bg-slate-500/20 text-slate-400 border-slate-500/30">
                          {error.error_type}
                        </Badge>
                        <span className="text-xs text-slate-500">#{error.id}</span>
                      </div>
                      <p className="text-sm text-white mb-1">{error.error_message}</p>
                      <p className="text-xs text-slate-400">
                        Endpoint: {error.endpoint}
                        {error.user_id && ` • User #${error.user_id}`}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {new Date(error.created_at).toLocaleDateString('fr-FR', {
                          day: '2-digit',
                          month: 'short',
                          year: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                      {error.resolution_notes && (
                        <p className="text-xs text-green-400 mt-2">
                          Note: {error.resolution_notes}
                        </p>
                      )}
                    </div>
                    {!error.is_resolved && (
                      <div className="flex gap-2">
                        {selectedError === error.id ? (
                          <div className="flex flex-col gap-2">
                            <input
                              type="text"
                              placeholder="Notes de résolution..."
                              value={resolutionNotes}
                              onChange={(e) => setResolutionNotes(e.target.value)}
                              className="px-3 py-1 text-sm bg-slate-800 border border-white/10 rounded focus:outline-none focus:border-primary"
                            />
                            <div className="flex gap-2">
                              <Button
                                size="sm"
                                className="bg-green-500 hover:bg-green-600"
                                onClick={() => resolveError(error.id)}
                              >
                                <Check className="h-3 w-3 mr-1" />
                                Confirmer
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="border-white/20"
                                onClick={() => {
                                  setSelectedError(null);
                                  setResolutionNotes('');
                                }}
                              >
                                Annuler
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            className="border-green-500/30 text-green-400 hover:bg-green-500/10"
                            onClick={() => setSelectedError(error.id)}
                          >
                            <Check className="h-3 w-3 mr-1" />
                            Résoudre
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}

              {/* Pagination */}
              <div className="flex items-center justify-between pt-4 border-t border-white/10">
                <p className="text-sm text-slate-400">Page {page} sur {totalPages}</p>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20"
                    onClick={() => fetchData(page - 1, resolvedFilter)}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20"
                    onClick={() => fetchData(page + 1, resolvedFilter)}
                    disabled={page >= totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
