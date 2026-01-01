"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Webhook,
  Plus,
  CheckCircle,
  XCircle,
  PlayCircle,
  RefreshCw,
  Trash2,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Copy,
  Eye,
  EyeOff,
  Edit3,
  Save,
  X,
  Key,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Switch } from '@/components/ui/switch';
import { cn } from '@/lib/utils';
import { adminAPI } from '@/lib/admin-api';
import type { WebhookStats } from '@/types';

interface WebhookEndpoint {
  id: number;
  name: string;
  url: string;
  events: string[];
  is_active: boolean;
  created_at: string;
  secret?: string;
}

interface WebhookLog {
  id: number;
  endpoint_id: number;
  event: string;
  status: string;
  response_code: number | null;
  error_message: string | null;
  attempts: number;
  created_at: string;
}

export default function WebhooksTab() {
  const [stats, setStats] = useState<WebhookStats | null>(null);
  const [endpoints, setEndpoints] = useState<WebhookEndpoint[]>([]);
  const [logs, setLogs] = useState<WebhookLog[]>([]);
  const [availableEvents, setAvailableEvents] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<number | null>(null);
  const [showSecret, setShowSecret] = useState<number | null>(null);
  const [activeView, setActiveView] = useState<'endpoints' | 'logs'>('endpoints');

  // New endpoint form
  const [showForm, setShowForm] = useState(false);
  const [newEndpoint, setNewEndpoint] = useState({ name: '', url: '', events: [] as string[] });
  const [creating, setCreating] = useState(false);

  // Edit modal state
  const [editingEndpoint, setEditingEndpoint] = useState<{
    id: number;
    name: string;
    url: string;
    events: string[];
    is_active: boolean;
    secret: string;
  } | null>(null);
  const [editLoading, setEditLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const perPage = 20;

  const fetchData = useCallback(async (logsPage: number) => {
    setLoading(true);
    try {
      const [statsRes, endpointsRes, logsRes] = await Promise.all([
        adminAPI.getWebhookStats(),
        adminAPI.getWebhooks(),
        adminAPI.getWebhookLogs({ page: logsPage, per_page: perPage }),
      ]);
      setStats(statsRes.data);
      setEndpoints(endpointsRes.data.items);
      setAvailableEvents(endpointsRes.data.available_events);
      setLogs(logsRes.data.items);
      setPage(logsRes.data.page);
      setTotalPages(logsRes.data.total_pages);
    } catch (error) {
      console.error('Error fetching webhook data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(1);
  }, [fetchData]);

  const testWebhook = async (id: number) => {
    setTesting(id);
    try {
      const res = await adminAPI.testWebhook(id);
      alert(`Test: ${res.data.status} (${res.data.response_code || 'N/A'})`);
      fetchData(page);
    } catch (error) {
      console.error('Error testing webhook:', error);
      alert('Erreur lors du test');
    } finally {
      setTesting(null);
    }
  };

  const deleteWebhook = async (id: number) => {
    if (!confirm('Supprimer ce webhook ?')) return;
    try {
      await adminAPI.deleteWebhook(id);
      setEndpoints(endpoints.filter(e => e.id !== id));
    } catch (error) {
      console.error('Error deleting webhook:', error);
    }
  };

  const createWebhook = async () => {
    if (!newEndpoint.name || !newEndpoint.url || newEndpoint.events.length === 0) {
      alert('Remplissez tous les champs');
      return;
    }
    setCreating(true);
    try {
      const res = await adminAPI.createWebhook(newEndpoint);
      alert(`Webhook créé! Secret: ${res.data.secret}`);
      setShowForm(false);
      setNewEndpoint({ name: '', url: '', events: [] });
      fetchData(1);
    } catch (error) {
      console.error('Error creating webhook:', error);
      alert('Erreur lors de la création');
    } finally {
      setCreating(false);
    }
  };

  const copySecret = async (endpointId: number) => {
    try {
      const res = await adminAPI.getWebhook(endpointId);
      await navigator.clipboard.writeText(res.data.secret);
      alert('Secret copié!');
    } catch (error) {
      console.error('Error copying secret:', error);
    }
  };

  const openEditModal = async (endpointId: number) => {
    setEditLoading(true);
    try {
      const res = await adminAPI.getWebhook(endpointId);
      setEditingEndpoint({
        id: res.data.id,
        name: res.data.name,
        url: res.data.url,
        events: res.data.events,
        is_active: res.data.is_active,
        secret: res.data.secret,
      });
    } catch (error) {
      console.error('Error fetching webhook:', error);
      alert('Erreur lors du chargement');
    } finally {
      setEditLoading(false);
    }
  };

  const saveWebhook = async () => {
    if (!editingEndpoint) return;
    setSaveLoading(true);
    try {
      await adminAPI.updateWebhook(editingEndpoint.id, {
        name: editingEndpoint.name,
        url: editingEndpoint.url,
        events: editingEndpoint.events,
        is_active: editingEndpoint.is_active,
      });
      setEditingEndpoint(null);
      fetchData(page);
    } catch (error) {
      console.error('Error saving webhook:', error);
      alert('Erreur lors de la sauvegarde');
    } finally {
      setSaveLoading(false);
    }
  };

  const regenerateSecret = async () => {
    if (!editingEndpoint) return;
    if (!confirm('Régénérer le secret ? L\'ancien ne fonctionnera plus.')) return;
    setRegenerating(true);
    try {
      const res = await adminAPI.regenerateWebhookSecret(editingEndpoint.id);
      setEditingEndpoint({ ...editingEndpoint, secret: res.data.secret });
      alert('Nouveau secret généré!');
    } catch (error) {
      console.error('Error regenerating secret:', error);
      alert('Erreur lors de la régénération');
    } finally {
      setRegenerating(false);
    }
  };

  const statusColors: Record<string, string> = {
    success: 'bg-green-500/20 text-green-400 border-green-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  };

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/20">
                  <Webhook className="h-4 w-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Endpoints actifs</p>
                  <p className="text-xl font-bold">{stats?.active_endpoints || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-500/20">
                  <CheckCircle className="h-4 w-4 text-green-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Succès</p>
                  <p className="text-xl font-bold text-green-400">{stats?.success || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/20">
                  <RefreshCw className="h-4 w-4 text-blue-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Livraisons</p>
                  <p className="text-xl font-bold">{stats?.total_deliveries || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-cyan-500/20">
                  <CheckCircle className="h-4 w-4 text-cyan-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Taux succès</p>
                  <p className="text-xl font-bold text-cyan-400">
                    {((stats?.success_rate || 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* View Toggle + Add Button */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <Button
            variant={activeView === 'endpoints' ? 'default' : 'outline'}
            className={activeView === 'endpoints' ? 'bg-primary' : 'border-white/20'}
            onClick={() => setActiveView('endpoints')}
          >
            <Webhook className="h-4 w-4 mr-2" />
            Endpoints
          </Button>
          <Button
            variant={activeView === 'logs' ? 'default' : 'outline'}
            className={activeView === 'logs' ? 'bg-primary' : 'border-white/20'}
            onClick={() => setActiveView('logs')}
          >
            <RefreshCw className="h-4 w-4 mr-2" />
            Logs
          </Button>
        </div>
        {activeView === 'endpoints' && (
          <Button
            className="bg-primary hover:bg-primary/90"
            onClick={() => setShowForm(!showForm)}
          >
            <Plus className="h-4 w-4 mr-2" />
            Nouveau webhook
          </Button>
        )}
      </div>

      {/* New Endpoint Form */}
      {showForm && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
        >
          <Card className="border-primary/30 bg-primary/5">
            <CardContent className="p-4 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="Nom du webhook"
                  value={newEndpoint.name}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, name: e.target.value })}
                  className="px-4 py-2 bg-slate-800 border border-white/10 rounded-lg text-white placeholder:text-slate-400 focus:outline-none focus:border-primary"
                />
                <input
                  type="url"
                  placeholder="URL (https://...)"
                  value={newEndpoint.url}
                  onChange={(e) => setNewEndpoint({ ...newEndpoint, url: e.target.value })}
                  className="px-4 py-2 bg-slate-800 border border-white/10 rounded-lg text-white placeholder:text-slate-400 focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <p className="text-sm text-slate-400 mb-2">Événements:</p>
                <div className="flex flex-wrap gap-2">
                  {availableEvents.map((event) => (
                    <Badge
                      key={event}
                      variant="outline"
                      className={cn(
                        "cursor-pointer transition-colors",
                        newEndpoint.events.includes(event)
                          ? "bg-primary/20 text-primary border-primary/30"
                          : "bg-slate-500/20 text-slate-400 border-slate-500/30 hover:border-primary/30"
                      )}
                      onClick={() => {
                        const events = newEndpoint.events.includes(event)
                          ? newEndpoint.events.filter(e => e !== event)
                          : [...newEndpoint.events, event];
                        setNewEndpoint({ ...newEndpoint, events });
                      }}
                    >
                      {event}
                    </Badge>
                  ))}
                </div>
              </div>
              <div className="flex gap-2">
                <Button
                  className="bg-primary hover:bg-primary/90"
                  onClick={createWebhook}
                  disabled={creating}
                >
                  {creating ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Plus className="h-4 w-4 mr-2" />}
                  Créer
                </Button>
                <Button variant="outline" className="border-white/20" onClick={() => setShowForm(false)}>
                  Annuler
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Endpoints View */}
      {activeView === 'endpoints' && (
        <Card className="glass border-white/10">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Webhook className="h-5 w-5 text-primary" />
              Webhooks configurés ({endpoints.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-24 bg-slate-800" />
                ))}
              </div>
            ) : endpoints.length === 0 ? (
              <div className="py-12 text-center">
                <Webhook className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Aucun webhook configuré</p>
              </div>
            ) : (
              <div className="space-y-4">
                {endpoints.map((endpoint) => (
                  <div
                    key={endpoint.id}
                    className="p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge
                            variant="outline"
                            className={cn(
                              endpoint.is_active
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                            )}
                          >
                            {endpoint.is_active ? 'Actif' : 'Inactif'}
                          </Badge>
                          <span className="font-medium text-white">{endpoint.name}</span>
                        </div>
                        <p className="text-sm text-slate-400 font-mono mb-2">{endpoint.url}</p>
                        <div className="flex flex-wrap gap-1">
                          {endpoint.events.map((event) => (
                            <Badge
                              key={event}
                              variant="outline"
                              className="text-xs bg-purple-500/10 text-purple-400 border-purple-500/20"
                            >
                              {event}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-white/20"
                          onClick={() => openEditModal(endpoint.id)}
                          disabled={editLoading}
                        >
                          <Edit3 className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-white/20"
                          onClick={() => copySecret(endpoint.id)}
                          title="Copier le secret"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-primary/30 text-primary hover:bg-primary/10"
                          onClick={() => testWebhook(endpoint.id)}
                          disabled={testing === endpoint.id || !endpoint.is_active}
                          title="Tester"
                        >
                          {testing === endpoint.id ? (
                            <Loader2 className="h-3 w-3 animate-spin" />
                          ) : (
                            <PlayCircle className="h-3 w-3" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                          onClick={() => deleteWebhook(endpoint.id)}
                          title="Supprimer"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Logs View */}
      {activeView === 'logs' && (
        <Card className="glass border-white/10">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <RefreshCw className="h-5 w-5 text-primary" />
              Logs de livraison
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-16 bg-slate-800" />
                ))}
              </div>
            ) : logs.length === 0 ? (
              <div className="py-12 text-center">
                <RefreshCw className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Aucune livraison</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left border-b border-white/10">
                        <th className="pb-3 text-sm font-medium text-slate-400">Endpoint</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Événement</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Statut</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Code</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Tentatives</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr key={log.id} className="border-b border-white/5 hover:bg-white/5">
                          <td className="py-3 text-sm">#{log.endpoint_id}</td>
                          <td className="py-3">
                            <Badge variant="outline" className="bg-purple-500/10 text-purple-400 border-purple-500/20">
                              {log.event}
                            </Badge>
                          </td>
                          <td className="py-3">
                            <Badge variant="outline" className={statusColors[log.status] || statusColors.pending}>
                              {log.status}
                            </Badge>
                          </td>
                          <td className="py-3 text-sm font-mono">{log.response_code || '-'}</td>
                          <td className="py-3 text-sm">{log.attempts}</td>
                          <td className="py-3 text-sm text-slate-400">
                            {new Date(log.created_at).toLocaleDateString('fr-FR', {
                              day: '2-digit',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between pt-4 border-t border-white/10 mt-4">
                  <p className="text-sm text-slate-400">Page {page} sur {totalPages}</p>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-white/20"
                      onClick={() => fetchData(page - 1)}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      className="border-white/20"
                      onClick={() => fetchData(page + 1)}
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
      )}

      {/* Edit Webhook Modal */}
      <Dialog open={!!editingEndpoint} onOpenChange={() => setEditingEndpoint(null)}>
        <DialogContent className="glass border-white/10 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Webhook className="h-5 w-5 text-primary" />
              Modifier le webhook
            </DialogTitle>
          </DialogHeader>

          {editLoading ? (
            <div className="space-y-4 py-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-20 w-full" />
            </div>
          ) : editingEndpoint && (
            <div className="space-y-6 py-4">
              {/* Active Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">Webhook actif</p>
                  <p className="text-sm text-slate-400">
                    Les événements seront envoyés si actif
                  </p>
                </div>
                <Switch
                  checked={editingEndpoint.is_active}
                  onCheckedChange={(checked) =>
                    setEditingEndpoint({ ...editingEndpoint, is_active: checked })
                  }
                />
              </div>

              {/* Name */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">Nom</label>
                <input
                  type="text"
                  value={editingEndpoint.name}
                  onChange={(e) =>
                    setEditingEndpoint({ ...editingEndpoint, name: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              {/* URL */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">URL</label>
                <input
                  type="url"
                  value={editingEndpoint.url}
                  onChange={(e) =>
                    setEditingEndpoint({ ...editingEndpoint, url: e.target.value })
                  }
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              {/* Events */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">Événements</label>
                <div className="flex flex-wrap gap-2">
                  {availableEvents.map((event) => (
                    <Badge
                      key={event}
                      variant="outline"
                      className={cn(
                        "cursor-pointer transition-colors",
                        editingEndpoint.events.includes(event)
                          ? "bg-primary/20 text-primary border-primary/30"
                          : "bg-slate-500/20 text-slate-400 border-slate-500/30 hover:border-primary/30"
                      )}
                      onClick={() => {
                        const events = editingEndpoint.events.includes(event)
                          ? editingEndpoint.events.filter(e => e !== event)
                          : [...editingEndpoint.events, event];
                        setEditingEndpoint({ ...editingEndpoint, events });
                      }}
                    >
                      {event}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Secret */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">Secret</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={editingEndpoint.secret}
                    readOnly
                    className="flex-1 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white font-mono text-sm"
                  />
                  <Button
                    variant="outline"
                    className="border-white/20"
                    onClick={() => navigator.clipboard.writeText(editingEndpoint.secret)}
                  >
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    className="border-orange-500/30 text-orange-400 hover:bg-orange-500/10"
                    onClick={regenerateSecret}
                    disabled={regenerating}
                  >
                    {regenerating ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Key className="h-4 w-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs text-slate-400">
                  Utilisez ce secret pour vérifier les signatures des requêtes
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-3 justify-end pt-4 border-t border-white/10">
                <Button
                  variant="ghost"
                  onClick={() => setEditingEndpoint(null)}
                  disabled={saveLoading}
                >
                  <X className="h-4 w-4 mr-1" />
                  Annuler
                </Button>
                <Button
                  onClick={saveWebhook}
                  disabled={saveLoading || !editingEndpoint.name || !editingEndpoint.url || editingEndpoint.events.length === 0}
                >
                  {saveLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin mr-1" />
                  ) : (
                    <Save className="h-4 w-4 mr-1" />
                  )}
                  Sauvegarder
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
