"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Users,
  Search,
  UserCheck,
  UserX,
  ShieldCheck,
  Eye,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  AlertTriangle,
  Filter,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import type { AdminUserFull, ChurnRiskUser, PaginatedResponse } from '@/types';
import Link from 'next/link';

export default function UsersTab() {
  const [users, setUsers] = useState<AdminUserFull[]>([]);
  const [churnRiskUsers, setChurnRiskUsers] = useState<ChurnRiskUser[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [showChurnRisk, setShowChurnRisk] = useState(false);

  const perPage = 10;

  const fetchUsers = useCallback(async (pageNum: number, searchQuery: string, role: string) => {
    setLoading(true);
    try {
      const res = await adminAPI.getUsers({
        page: pageNum,
        per_page: perPage,
        search: searchQuery || undefined,
        role: role || undefined,
      });
      setUsers(res.data.items);
      setPage(res.data.page);
      setTotalPages(res.data.total_pages);
      setTotal(res.data.total);
    } catch (error) {
      console.error('Error fetching users:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchChurnRisk = useCallback(async () => {
    try {
      const res = await adminAPI.getChurnRiskUsers(14);
      setChurnRiskUsers(res.data.users);
    } catch (error) {
      console.error('Error fetching churn risk users:', error);
    }
  }, []);

  useEffect(() => {
    fetchUsers(1, search, roleFilter);
    fetchChurnRisk();
  }, [fetchUsers, fetchChurnRisk, search, roleFilter]);

  const toggleUserStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await adminAPI.updateUser(userId, { is_active: !currentStatus });
      setUsers(users.map(u =>
        u.id === userId ? { ...u, is_active: !currentStatus } : u
      ));
    } catch (error) {
      console.error('Error toggling user status:', error);
    }
  };

  const toggleUserRole = async (userId: number, currentRole: string) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    try {
      await adminAPI.updateUser(userId, { role: newRole });
      setUsers(users.map(u =>
        u.id === userId ? { ...u, role: newRole as 'user' | 'admin' } : u
      ));
    } catch (error) {
      console.error('Error toggling user role:', error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchUsers(1, search, roleFilter);
  };

  return (
    <div className="space-y-6">
      {/* Churn Risk Alert */}
      {churnRiskUsers.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-orange-500/30 bg-orange-500/10">
            <CardContent className="p-4">
              <button
                onClick={() => setShowChurnRisk(!showChurnRisk)}
                className="w-full flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <AlertTriangle className="h-5 w-5 text-orange-400" />
                  <span className="text-orange-200">
                    <strong>{churnRiskUsers.length}</strong> utilisateur{churnRiskUsers.length > 1 ? 's' : ''} à risque de churn (inactif{churnRiskUsers.length > 1 ? 's' : ''} depuis 14+ jours)
                  </span>
                </div>
                <ChevronRight className={cn(
                  "h-5 w-5 text-orange-400 transition-transform",
                  showChurnRisk && "rotate-90"
                )} />
              </button>
              <AnimatePresence>
                {showChurnRisk && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="mt-4 space-y-2 overflow-hidden"
                  >
                    {churnRiskUsers.slice(0, 5).map((u) => (
                      <div key={u.id} className="flex items-center justify-between p-2 rounded bg-slate-800/50">
                        <div>
                          <p className="text-sm text-white">{u.email}</p>
                          <p className="text-xs text-slate-400">
                            {u.days_inactive} jours d&apos;inactivité • {u.subscription_plan}
                          </p>
                        </div>
                        <Link href={`/admin/users/${u.id}`}>
                          <Button size="sm" variant="outline" className="border-orange-500/30 text-orange-400">
                            <Eye className="h-3 w-3 mr-1" /> Voir
                          </Button>
                        </Link>
                      </div>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Filters */}
      <Card className="glass border-white/10">
        <CardContent className="p-4">
          <form onSubmit={handleSearch} className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Rechercher par email ou nom..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-800/50 border border-white/10 rounded-lg text-white placeholder:text-slate-400 focus:outline-none focus:border-primary"
                />
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="px-4 py-2 bg-slate-800/50 border border-white/10 rounded-lg text-white focus:outline-none focus:border-primary"
              >
                <option value="">Tous les rôles</option>
                <option value="user">Utilisateur</option>
                <option value="admin">Admin</option>
              </select>
              <Button type="submit" variant="outline" className="border-white/20">
                <Filter className="h-4 w-4 mr-2" />
                Filtrer
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card className="glass border-white/10">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Users className="h-5 w-5 text-primary" />
            Utilisateurs ({total})
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
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left border-b border-white/10">
                      <th className="pb-3 text-sm font-medium text-slate-400">Email</th>
                      <th className="pb-3 text-sm font-medium text-slate-400">Nom</th>
                      <th className="pb-3 text-sm font-medium text-slate-400">Rôle</th>
                      <th className="pb-3 text-sm font-medium text-slate-400">Plan</th>
                      <th className="pb-3 text-sm font-medium text-slate-400">Statut</th>
                      <th className="pb-3 text-sm font-medium text-slate-400">Dernière activité</th>
                      <th className="pb-3 text-sm font-medium text-slate-400">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="py-8 text-center text-slate-400">
                          Aucun utilisateur trouvé
                        </td>
                      </tr>
                    ) : (
                      users.map((u) => (
                        <tr key={u.id} className="border-b border-white/5 hover:bg-white/5">
                          <td className="py-3 text-sm">{u.email}</td>
                          <td className="py-3 text-sm text-slate-400">{u.full_name || '-'}</td>
                          <td className="py-3">
                            <Badge
                              variant="outline"
                              className={cn(
                                u.role === 'admin'
                                  ? 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                                  : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                              )}
                            >
                              {u.role === 'admin' ? (
                                <ShieldCheck className="h-3 w-3 mr-1" />
                              ) : (
                                <Users className="h-3 w-3 mr-1" />
                              )}
                              {u.role}
                            </Badge>
                          </td>
                          <td className="py-3">
                            <Badge
                              variant="outline"
                              className={cn(
                                u.subscription_plan === 'premium'
                                  ? 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
                                  : u.subscription_plan === 'pro'
                                  ? 'bg-blue-500/20 text-blue-400 border-blue-500/30'
                                  : 'bg-slate-500/20 text-slate-400 border-slate-500/30'
                              )}
                            >
                              {u.subscription_plan}
                            </Badge>
                          </td>
                          <td className="py-3">
                            <Badge
                              variant="outline"
                              className={cn(
                                u.is_active
                                  ? 'bg-green-500/20 text-green-400 border-green-500/30'
                                  : 'bg-red-500/20 text-red-400 border-red-500/30'
                              )}
                            >
                              {u.is_active ? (
                                <UserCheck className="h-3 w-3 mr-1" />
                              ) : (
                                <UserX className="h-3 w-3 mr-1" />
                              )}
                              {u.is_active ? 'Actif' : 'Inactif'}
                            </Badge>
                          </td>
                          <td className="py-3 text-sm text-slate-400">
                            {u.last_activity_at
                              ? new Date(u.last_activity_at).toLocaleDateString('fr-FR', {
                                  day: '2-digit',
                                  month: 'short',
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })
                              : '-'}
                          </td>
                          <td className="py-3">
                            <div className="flex gap-2">
                              <Link href={`/admin/users/${u.id}`}>
                                <Button size="sm" variant="outline" className="border-white/20">
                                  <Eye className="h-3 w-3" />
                                </Button>
                              </Link>
                              <Button
                                size="sm"
                                variant="outline"
                                className="border-white/20"
                                onClick={() => toggleUserStatus(u.id, u.is_active)}
                              >
                                {u.is_active ? <UserX className="h-3 w-3" /> : <UserCheck className="h-3 w-3" />}
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                className="border-white/20"
                                onClick={() => toggleUserRole(u.id, u.role)}
                              >
                                {u.role === 'admin' ? <Users className="h-3 w-3" /> : <ShieldCheck className="h-3 w-3" />}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              <div className="flex items-center justify-between pt-4 border-t border-white/10 mt-4">
                <p className="text-sm text-slate-400">
                  {total > 0 ? `${(page - 1) * perPage + 1}-${Math.min(page * perPage, total)} sur ${total}` : 'Aucun résultat'}
                </p>
                <div className="flex items-center gap-1">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20 h-8 w-8 p-0"
                    onClick={() => fetchUsers(1, search, roleFilter)}
                    disabled={page === 1}
                  >
                    <ChevronsLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20 h-8 w-8 p-0"
                    onClick={() => fetchUsers(page - 1, search, roleFilter)}
                    disabled={page === 1}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <span className="px-3 text-sm">{page} / {totalPages || 1}</span>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20 h-8 w-8 p-0"
                    onClick={() => fetchUsers(page + 1, search, roleFilter)}
                    disabled={page >= totalPages}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-white/20 h-8 w-8 p-0"
                    onClick={() => fetchUsers(totalPages, search, roleFilter)}
                    disabled={page >= totalPages}
                  >
                    <ChevronsRight className="h-4 w-4" />
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
