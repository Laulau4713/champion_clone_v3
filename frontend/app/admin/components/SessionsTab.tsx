"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Mic,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Trophy,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import Link from 'next/link';

interface Session {
  id: number;
  user_id: string;
  user_email: string;
  champion_id: number;
  champion_name: string;
  score: number | null;
  status: string;
  started_at: string;
}

export default function SessionsTab() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [stats, setStats] = useState({ total: 0, completed: 0, avgScore: 0 });

  const perPage = 10;

  const fetchSessions = useCallback(async (pageNum: number, status: string) => {
    setLoading(true);
    try {
      const res = await adminAPI.getSessions({
        page: pageNum,
        per_page: perPage,
        status: status || undefined,
      });
      setSessions(res.data.items);
      setPage(res.data.page);
      setTotalPages(res.data.total_pages);
      setTotal(res.data.total);

      // Calculate stats
      const items = res.data.items;
      const completed = items.filter(s => s.status === 'completed').length;
      const scores = items.filter(s => s.score !== null).map(s => s.score as number);
      const avgScore = scores.length > 0 ? scores.reduce((a, b) => a + b, 0) / scores.length : 0;
      setStats({ total: res.data.total, completed, avgScore: Math.round(avgScore) });
    } catch (error) {
      console.error('Error fetching sessions:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions(1, statusFilter);
  }, [fetchSessions, statusFilter]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-500/20 text-green-400 border-green-500/30"><CheckCircle2 className="h-3 w-3 mr-1" />Terminée</Badge>;
      case 'active':
        return <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30"><Clock className="h-3 w-3 mr-1" />En cours</Badge>;
      case 'abandoned':
        return <Badge className="bg-red-500/20 text-red-400 border-red-500/30"><XCircle className="h-3 w-3 mr-1" />Abandonnée</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const getScoreBadge = (score: number | null) => {
    if (score === null) return <span className="text-slate-500">-</span>;
    if (score >= 80) return <Badge className="bg-green-500/20 text-green-400">{score}%</Badge>;
    if (score >= 50) return <Badge className="bg-yellow-500/20 text-yellow-400">{score}%</Badge>;
    return <Badge className="bg-red-500/20 text-red-400">{score}%</Badge>;
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

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="glass border-white/10">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Total Sessions</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <div className="p-3 rounded-lg bg-primary/20">
                <Mic className="h-6 w-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-white/10">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Terminées (page)</p>
                <p className="text-2xl font-bold text-green-400">{stats.completed}</p>
              </div>
              <div className="p-3 rounded-lg bg-green-500/20">
                <CheckCircle2 className="h-6 w-6 text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="glass border-white/10">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Score Moyen (page)</p>
                <p className="text-2xl font-bold text-yellow-400">{stats.avgScore}%</p>
              </div>
              <div className="p-3 rounded-lg bg-yellow-500/20">
                <Trophy className="h-6 w-6 text-yellow-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Sessions List */}
      <Card className="glass border-white/10">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Mic className="h-5 w-5 text-primary" />
              Sessions d&apos;entraînement
            </CardTitle>

            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="bg-white/5 border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
              >
                <option value="">Tous les statuts</option>
                <option value="completed">Terminées</option>
                <option value="active">En cours</option>
                <option value="abandoned">Abandonnées</option>
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
          ) : sessions.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <Mic className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Aucune session trouvée</p>
            </div>
          ) : (
            <div className="space-y-3">
              {sessions.map((session, index) => (
                <motion.div
                  key={session.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="p-2 rounded-lg bg-primary/20">
                      <Mic className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-white">Session #{session.id}</span>
                        {getStatusBadge(session.status)}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {session.user_email}
                        </span>
                        <span>|</span>
                        <span>{formatDate(session.started_at)}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-sm text-slate-400">Score</p>
                      {getScoreBadge(session.score)}
                    </div>
                    <Link href={`/admin/users/${session.user_id}`}>
                      <Button variant="ghost" size="sm">
                        Voir utilisateur
                      </Button>
                    </Link>
                  </div>
                </motion.div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t border-white/10">
              <p className="text-sm text-slate-400">
                Page {page} sur {totalPages} ({total} sessions)
              </p>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchSessions(1, statusFilter)}
                  disabled={page === 1}
                >
                  <ChevronsLeft className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchSessions(page - 1, statusFilter)}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="px-3 py-1 text-sm text-white">{page}</span>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchSessions(page + 1, statusFilter)}
                  disabled={page === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => fetchSessions(totalPages, statusFilter)}
                  disabled={page === totalPages}
                >
                  <ChevronsRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
