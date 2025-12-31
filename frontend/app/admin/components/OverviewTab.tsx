"use client";

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  Trophy,
  Target,
  TrendingUp,
  UserPlus,
  Activity,
  Mail,
  Webhook,
  AlertTriangle,
  Bell,
  CheckCircle,
  XCircle,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import type { AdminStats, FunnelStats, EmailStats, WebhookStats } from '@/types';

// Stat Card Component
function StatCard({
  title,
  value,
  icon: Icon,
  iconColor,
  trend,
  delay = 0,
}: {
  title: string;
  value: number | string;
  icon: React.ElementType;
  iconColor: string;
  trend?: string;
  delay?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
    >
      <Card className="glass border-white/10 hover:border-white/20 transition-colors">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400">{title}</p>
              <p className="text-2xl font-bold text-white">{value}</p>
              {trend && (
                <p className="text-xs text-green-400 mt-1">{trend}</p>
              )}
            </div>
            <div className={cn("p-3 rounded-xl", `bg-${iconColor.split('-')[1]}-500/20`)}>
              <Icon className={cn("h-5 w-5", iconColor)} />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

const FUNNEL_COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899'];

export default function OverviewTab() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [funnelStats, setFunnelStats] = useState<FunnelStats | null>(null);
  const [emailStats, setEmailStats] = useState<EmailStats | null>(null);
  const [webhookStats, setWebhookStats] = useState<WebhookStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, funnelRes, emailRes, webhookRes] = await Promise.all([
          adminAPI.getStats(),
          adminAPI.getFunnelStats(),
          adminAPI.getEmailStats(),
          adminAPI.getWebhookStats(),
        ]);
        setStats(statsRes.data);
        setFunnelStats(funnelRes.data);
        setEmailStats(emailRes.data);
        setWebhookStats(webhookRes.data);
      } catch (error) {
        console.error('Error fetching overview data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-24 bg-slate-800" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Skeleton className="h-80 bg-slate-800" />
          <Skeleton className="h-80 bg-slate-800" />
        </div>
      </div>
    );
  }

  // Prepare funnel data from stages dict
  const funnelData = funnelStats?.stages ? [
    { name: 'Inscrits', value: funnelStats.stages.registered || 0, color: FUNNEL_COLORS[0] },
    { name: '1er login', value: funnelStats.stages.first_login || 0, color: FUNNEL_COLORS[1] },
    { name: '1er upload', value: funnelStats.stages.first_upload || 0, color: FUNNEL_COLORS[2] },
    { name: '1er training', value: funnelStats.stages.first_training || 0, color: FUNNEL_COLORS[3] },
    { name: 'Power Users', value: funnelStats.stages.power_user || 0, color: FUNNEL_COLORS[4] },
  ] : [];

  // Subscription data for pie chart
  const subscriptionData = stats?.subscriptions ?
    Object.entries(stats.subscriptions).map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value,
    })).filter(d => d.value > 0) : [];

  const SUBSCRIPTION_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444'];

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard
          title="Utilisateurs"
          value={stats?.total_users || 0}
          icon={Users}
          iconColor="text-blue-400"
          delay={0}
        />
        <StatCard
          title="Champions"
          value={stats?.total_champions || 0}
          icon={Trophy}
          iconColor="text-yellow-400"
          delay={0.05}
        />
        <StatCard
          title="Sessions"
          value={stats?.total_sessions || 0}
          icon={Target}
          iconColor="text-purple-400"
          delay={0.1}
        />
        <StatCard
          title="Score moyen"
          value={`${stats?.avg_score || 0}/10`}
          icon={TrendingUp}
          iconColor="text-green-400"
          delay={0.15}
        />
        <StatCard
          title="Nouveaux (7j)"
          value={stats?.new_users_week || 0}
          icon={UserPlus}
          iconColor="text-cyan-400"
          trend="+cette semaine"
          delay={0.2}
        />
        <StatCard
          title="Sessions (7j)"
          value={stats?.sessions_week || 0}
          icon={Activity}
          iconColor="text-orange-400"
          trend="+cette semaine"
          delay={0.25}
        />
      </div>

      {/* Alerts Banner */}
      {stats && stats.unread_alerts > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Card className="border-yellow-500/30 bg-yellow-500/10">
            <CardContent className="p-4 flex items-center gap-3">
              <Bell className="h-5 w-5 text-yellow-400" />
              <span className="text-yellow-200">
                Vous avez <strong>{stats.unread_alerts}</strong> alerte{stats.unread_alerts > 1 ? 's' : ''} non lue{stats.unread_alerts > 1 ? 's' : ''}
              </span>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Funnel Chart */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-primary" />
                Entonnoir de conversion
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={funnelData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis type="number" stroke="#94a3b8" />
                    <YAxis dataKey="name" type="category" width={100} stroke="#94a3b8" />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                      }}
                    />
                    <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                      {funnelData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              {funnelStats?.conversion_rates && (
                <div className="mt-4 text-center">
                  <span className="text-sm text-slate-400">Taux conversion Power User: </span>
                  <span className="text-lg font-bold text-green-400">
                    {(funnelStats.conversion_rates.power_user || 0).toFixed(1)}%
                  </span>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Subscriptions Pie Chart */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.3 }}
        >
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="h-5 w-5 text-primary" />
                Répartition des abonnements
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={subscriptionData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={80}
                      paddingAngle={5}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {subscriptionData.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={SUBSCRIPTION_COLORS[index % SUBSCRIPTION_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: '#1e293b',
                        border: '1px solid #334155',
                        borderRadius: '8px',
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* Email & Webhook Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Email Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
        >
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Mail className="h-5 w-5 text-primary" />
                Statistiques Emails
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Total</p>
                  <p className="text-xl font-bold">{emailStats?.total || 0}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Envoyés</p>
                  <p className="text-xl font-bold text-green-400">{emailStats?.sent || 0}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Taux d&apos;ouverture</p>
                  <p className="text-xl font-bold text-blue-400">
                    {((emailStats?.open_rate || 0) * 100).toFixed(1)}%
                  </p>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Taux de clic</p>
                  <p className="text-xl font-bold text-purple-400">
                    {((emailStats?.click_rate || 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              {emailStats && emailStats.failed > 0 && (
                <div className="flex items-center gap-2 p-3 rounded-lg bg-red-500/10 border border-red-500/30">
                  <XCircle className="h-4 w-4 text-red-400" />
                  <span className="text-sm text-red-200">{emailStats.failed} email(s) en échec</span>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Webhook Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.45 }}
        >
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Webhook className="h-5 w-5 text-primary" />
                Statistiques Webhooks
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Endpoints actifs</p>
                  <p className="text-xl font-bold">{webhookStats?.active_endpoints || 0}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Livraisons</p>
                  <p className="text-xl font-bold text-green-400">{webhookStats?.total_deliveries || 0}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Retries en attente</p>
                  <p className="text-xl font-bold text-yellow-400">{webhookStats?.pending_retries || 0}</p>
                </div>
                <div className="p-3 rounded-lg bg-slate-800/50">
                  <p className="text-sm text-slate-400">Taux de succès</p>
                  <p className="text-xl font-bold text-green-400">
                    {((webhookStats?.success_rate || 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-slate-800/50">
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-green-400" />
                  <span className="text-sm">Succès: {webhookStats?.success || 0}</span>
                </div>
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-red-400" />
                  <span className="text-sm">Échecs: {webhookStats?.failed || 0}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
}
