"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  User,
  Mail,
  Calendar,
  Trophy,
  Target,
  TrendingUp,
  Shield,
  ShieldCheck,
  UserCheck,
  UserX,
  Clock,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/store/auth-store";
import api from "@/lib/api";
import type { AdminUserDetail } from "@/types";
import { cn } from "@/lib/utils";
import UserNotesSection from "./UserNotesSection";

// Loading Skeleton
function UserDetailSkeleton() {
  return (
    <div className="container mx-auto py-8 space-y-8">
      <Skeleton className="h-10 w-48" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Skeleton className="h-64" />
        <Skeleton className="h-64 lg:col-span-2" />
      </div>
      <Skeleton className="h-[300px]" />
    </div>
  );
}

export default function UserDetailPage() {
  const router = useRouter();
  const params = useParams();
  const userId = params.id as string;
  const { user: currentUser, isAuthenticated } = useAuthStore();
  const [userDetail, setUserDetail] = useState<AdminUserDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login");
      return;
    }

    if (currentUser && currentUser.role !== "admin") {
      router.push("/dashboard");
      return;
    }

    const fetchUser = async () => {
      try {
        const response = await api.get(`/admin/users/${userId}`);
        setUserDetail(response.data);
      } catch (err: any) {
        if (err.response?.status === 403) {
          router.push("/dashboard");
        } else if (err.response?.status === 404) {
          setError("Utilisateur non trouve");
        } else {
          setError("Erreur lors du chargement");
          console.error("User detail fetch error:", err);
        }
      } finally {
        setLoading(false);
      }
    };

    if (currentUser) {
      fetchUser();
    }
  }, [userId, currentUser, isAuthenticated, router]);

  const toggleUserStatus = async () => {
    if (!userDetail) return;
    try {
      await api.patch(`/admin/users/${userId}`, {
        is_active: !userDetail.user.is_active,
      });
      setUserDetail({
        ...userDetail,
        user: { ...userDetail.user, is_active: !userDetail.user.is_active },
      });
    } catch (err) {
      console.error("Error toggling user status:", err);
    }
  };

  const toggleUserRole = async () => {
    if (!userDetail) return;
    const newRole = userDetail.user.role === "admin" ? "user" : "admin";
    try {
      await api.patch(`/admin/users/${userId}`, { role: newRole });
      setUserDetail({
        ...userDetail,
        user: { ...userDetail.user, role: newRole as "user" | "admin" },
      });
    } catch (err) {
      console.error("Error toggling user role:", err);
    }
  };

  if (loading) return <UserDetailSkeleton />;
  if (error) {
    return (
      <div className="container mx-auto py-8">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Link href="/admin">
            <Button variant="outline">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour au panel admin
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  if (!userDetail) return null;

  const { user, champions, sessions, stats, notes } = userDetail;
  const isSelf = currentUser?.id === user.id;

  return (
    <div className="relative min-h-[calc(100vh-6rem)]">
      {/* Background */}
      <div className="absolute inset-0 gradient-mesh opacity-20" />

      <div className="relative container mx-auto py-8 space-y-6">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-4"
        >
          <Link href="/admin">
            <Button variant="outline" size="icon" className="border-white/20">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">
              {user.full_name || user.email}
            </h1>
            <p className="text-muted-foreground text-sm">{user.email}</p>
          </div>
        </motion.div>

        {/* User Info + Stats */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* User Card */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="glass border-white/10">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Profil
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-primary-500/20">
                    <User className="h-8 w-8 text-primary-500" />
                  </div>
                  <div>
                    <p className="font-medium">{user.full_name || "Sans nom"}</p>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2">
                    <Mail className="h-4 w-4 text-muted-foreground" />
                    <span>{user.email}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>
                      Inscrit le{" "}
                      {new Date(user.created_at).toLocaleDateString("fr-FR", {
                        day: "numeric",
                        month: "long",
                        year: "numeric",
                      })}
                    </span>
                  </div>
                </div>

                <div className="flex gap-2">
                  <Badge
                    variant="outline"
                    className={cn(
                      user.role === "admin"
                        ? "bg-purple-500/20 text-purple-400 border-purple-500/30"
                        : "bg-gray-500/20 text-gray-400 border-gray-500/30"
                    )}
                  >
                    {user.role === "admin" ? (
                      <ShieldCheck className="h-3 w-3 mr-1" />
                    ) : (
                      <Shield className="h-3 w-3 mr-1" />
                    )}
                    {user.role}
                  </Badge>
                  <Badge
                    variant="outline"
                    className={cn(
                      user.is_active
                        ? "bg-green-500/20 text-green-400 border-green-500/30"
                        : "bg-red-500/20 text-red-400 border-red-500/30"
                    )}
                  >
                    {user.is_active ? (
                      <UserCheck className="h-3 w-3 mr-1" />
                    ) : (
                      <UserX className="h-3 w-3 mr-1" />
                    )}
                    {user.is_active ? "Actif" : "Inactif"}
                  </Badge>
                </div>

                {/* Actions */}
                {!isSelf && (
                  <div className="flex gap-2 pt-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 border-white/20"
                      onClick={toggleUserStatus}
                    >
                      {user.is_active ? (
                        <>
                          <UserX className="h-3 w-3 mr-1" />
                          Desactiver
                        </>
                      ) : (
                        <>
                          <UserCheck className="h-3 w-3 mr-1" />
                          Activer
                        </>
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="flex-1 border-white/20"
                      onClick={toggleUserRole}
                    >
                      {user.role === "admin" ? (
                        <>
                          <Shield className="h-3 w-3 mr-1" />
                          Retirer admin
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="h-3 w-3 mr-1" />
                          Promouvoir
                        </>
                      )}
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Stats Cards */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.15 }}
            className="lg:col-span-2"
          >
            <Card className="glass border-white/10 h-full">
              <CardHeader>
                <CardTitle className="text-lg flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Statistiques
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className="text-center p-4 rounded-lg bg-white/5">
                    <Trophy className="h-8 w-8 mx-auto mb-2 text-yellow-400" />
                    <p className="text-2xl font-bold">{stats.total_champions}</p>
                    <p className="text-sm text-muted-foreground">Champions</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-white/5">
                    <Target className="h-8 w-8 mx-auto mb-2 text-purple-400" />
                    <p className="text-2xl font-bold">{stats.total_sessions}</p>
                    <p className="text-sm text-muted-foreground">Sessions</p>
                  </div>
                  <div className="text-center p-4 rounded-lg bg-white/5">
                    <TrendingUp className="h-8 w-8 mx-auto mb-2 text-green-400" />
                    <p className="text-2xl font-bold">
                      {stats.avg_score.toFixed(1)}/10
                    </p>
                    <p className="text-sm text-muted-foreground">Score moyen</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Champions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
        >
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Trophy className="h-5 w-5 text-yellow-400" />
                Champions ({champions.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {champions.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">
                  Aucun champion
                </p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {champions.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 rounded-lg bg-white/5 border border-white/10"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-medium">{c.name}</p>
                        <Badge
                          variant="outline"
                          className={cn(
                            c.status === "ready"
                              ? "bg-green-500/20 text-green-400 border-green-500/30"
                              : c.status === "processing"
                              ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                              : c.status === "error"
                              ? "bg-red-500/20 text-red-400 border-red-500/30"
                              : "bg-gray-500/20 text-gray-400 border-gray-500/30"
                          )}
                        >
                          {c.status}
                        </Badge>
                      </div>
                      <p className="text-xs text-muted-foreground">
                        <Clock className="h-3 w-3 inline mr-1" />
                        {new Date(c.created_at).toLocaleDateString("fr-FR")}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Recent Sessions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
        >
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Target className="h-5 w-5 text-purple-400" />
                Sessions recentes ({sessions.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              {sessions.length === 0 ? (
                <p className="text-muted-foreground text-center py-4">
                  Aucune session
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left border-b border-white/10">
                        <th className="pb-2 text-sm font-medium text-muted-foreground">
                          ID
                        </th>
                        <th className="pb-2 text-sm font-medium text-muted-foreground">
                          Champion
                        </th>
                        <th className="pb-2 text-sm font-medium text-muted-foreground">
                          Score
                        </th>
                        <th className="pb-2 text-sm font-medium text-muted-foreground">
                          Status
                        </th>
                        <th className="pb-2 text-sm font-medium text-muted-foreground">
                          Date
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {sessions.map((s) => (
                        <tr
                          key={s.id}
                          className="border-b border-white/5 hover:bg-white/5"
                        >
                          <td className="py-2 text-sm font-mono">#{s.id}</td>
                          <td className="py-2 text-sm">
                            Champion #{s.champion_id}
                          </td>
                          <td className="py-2">
                            {s.score !== null ? (
                              <Badge
                                variant="outline"
                                className={cn(
                                  s.score >= 7
                                    ? "bg-green-500/20 text-green-400 border-green-500/30"
                                    : s.score >= 5
                                    ? "bg-yellow-500/20 text-yellow-400 border-yellow-500/30"
                                    : "bg-red-500/20 text-red-400 border-red-500/30"
                                )}
                              >
                                {s.score.toFixed(1)}/10
                              </Badge>
                            ) : (
                              <span className="text-muted-foreground">-</span>
                            )}
                          </td>
                          <td className="py-2">
                            <Badge
                              variant="outline"
                              className={cn(
                                s.status === "completed"
                                  ? "bg-green-500/20 text-green-400 border-green-500/30"
                                  : s.status === "active"
                                  ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                                  : "bg-gray-500/20 text-gray-400 border-gray-500/30"
                              )}
                            >
                              {s.status}
                            </Badge>
                          </td>
                          <td className="py-2 text-sm text-muted-foreground">
                            {new Date(s.started_at).toLocaleDateString("fr-FR")}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Admin Notes */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <UserNotesSection userId={user.id} initialNotes={notes || []} />
        </motion.div>
      </div>
    </div>
  );
}
