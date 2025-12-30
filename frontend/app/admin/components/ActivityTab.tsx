"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Activity,
  TrendingUp,
  Users,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import type { ActivityStats, PaginatedResponse } from '@/types';

interface ActivityLogItem {
  id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id: string;
  extra_data: Record<string, unknown>;
  ip_address: string;
  created_at: string;
}

const actionColors: Record<string, string> = {
  login: 'bg-green-500/20 text-green-400 border-green-500/30',
  logout: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
  register: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  upload: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  analyze: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  training_start: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
  training_complete: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
};

export default function ActivityTab() {
  const [stats, setStats] = useState<ActivityStats | null>(null);
  const [activities, setActivities] = useState<ActivityLogItem[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [days, setDays] = useState(30);

  const perPage = 20;

  const fetchData = useCallback(async (pageNum: number, periodDays: number) => {
    setLoading(true);
    try {
      const [statsRes, activitiesRes] = await Promise.all([
        adminAPI.getActivityStats(periodDays),
        adminAPI.getActivities({ page: pageNum, per_page: perPage }),
      ]);
      setStats(statsRes.data);
      setActivities(activitiesRes.data.items);
      setPage(activitiesRes.data.page);
      setTotalPages(activitiesRes.data.total_pages);
    } catch (error) {
      console.error('Error fetching activity data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(1, days);
  }, [fetchData, days]);

  const chartData = stats?.daily
    ? Object.entries(stats.daily)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([date, count]) => ({
          date: new Date(date).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }),
          activités: count,
        }))
    : [];

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Total activités</p>
                  <p className="text-2xl font-bold">{stats?.total_activities || 0}</p>
                  <p className="text-xs text-slate-500">{days} derniers jours</p>
                </div>
                <div className="p-3 rounded-xl bg-blue-500/20">
                  <Activity className="h-5 w-5 text-blue-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Utilisateurs actifs</p>
                  <p className="text-2xl font-bold">{stats?.active_users || 0}</p>
                  <p className="text-xs text-slate-500">{days} derniers jours</p>
                </div>
                <div className="p-3 rounded-xl bg-green-500/20">
                  <Users className="h-5 w-5 text-green-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">Moy. par jour</p>
                  <p className="text-2xl font-bold">
                    {stats ? Math.round(stats.total_activities / stats.period_days) : 0}
                  </p>
                  <p className="text-xs text-slate-500">activités/jour</p>
                </div>
                <div className="p-3 rounded-xl bg-purple-500/20">
                  <TrendingUp className="h-5 w-5 text-purple-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Period Selector */}
      <div className="flex gap-2">
        {[7, 14, 30, 90].map((d) => (
          <Button
            key={d}
            size="sm"
            variant={days === d ? 'default' : 'outline'}
            className={days === d ? 'bg-primary' : 'border-white/20'}
            onClick={() => setDays(d)}
          >
            {d} jours
          </Button>
        ))}
      </div>

      {/* Activity Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
      >
        <Card className="glass border-white/10">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary" />
              Activité quotidienne
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <Skeleton className="h-64 bg-slate-800" />
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient id="activityGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date" stroke="#94a3b8" fontSize={12} />
                    <YAxis stroke="#94a3b8" fontSize={12} />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="activités"
                      stroke="#8b5cf6"
                      fillOpacity={1}
                      fill="url(#activityGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Actions Breakdown */}
      {stats?.by_action && (
        <Card className="glass border-white/10">
          <CardHeader>
            <CardTitle className="text-lg">Répartition par action</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(stats.by_action).map(([action, count]) => (
                <div
                  key={action}
                  className="p-3 rounded-lg bg-slate-800/50 flex items-center justify-between"
                >
                  <Badge
                    variant="outline"
                    className={actionColors[action] || 'bg-slate-500/20 text-slate-400 border-slate-500/30'}
                  >
                    {action}
                  </Badge>
                  <span className="font-bold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Activity Log */}
      <Card className="glass border-white/10">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            Journal d'activité
          </CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-4">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-16 bg-slate-800" />
              ))}
            </div>
          ) : (
            <>
              <div className="space-y-3">
                {activities.map((a) => (
                  <div
                    key={a.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <Badge
                        variant="outline"
                        className={actionColors[a.action] || 'bg-slate-500/20 text-slate-400 border-slate-500/30'}
                      >
                        {a.action}
                      </Badge>
                      <div>
                        <p className="text-sm">
                          User #{a.user_id}
                          {a.resource_type && (
                            <span className="text-slate-400">
                              {' → '}{a.resource_type} #{a.resource_id}
                            </span>
                          )}
                        </p>
                        <p className="text-xs text-slate-500">{a.ip_address}</p>
                      </div>
                    </div>
                    <p className="text-xs text-slate-400">
                      {new Date(a.created_at).toLocaleDateString('fr-FR', {
                        day: '2-digit',
                        month: 'short',
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </p>
                  </div>
                ))}
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between pt-4 border-t border-white/10 mt-4">
                <p className="text-sm text-slate-400">Page {page} sur {totalPages}</p>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20"
                    onClick={() => fetchData(page - 1, days)}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20"
                    onClick={() => fetchData(page + 1, days)}
                    disabled={page >= totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
