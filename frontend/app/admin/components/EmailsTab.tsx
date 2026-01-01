"use client";

import { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Mail,
  Send,
  CheckCircle,
  XCircle,
  Eye,
  MousePointer,
  ChevronLeft,
  ChevronRight,
  PlayCircle,
  Loader2,
  Edit3,
  Save,
  X,
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
import type { EmailStats } from '@/types';

interface EmailTemplate {
  id: number;
  trigger: string;
  subject: string;
  is_active: boolean;
  variables: string[];
  updated_at: string;
}

interface EmailLog {
  id: number;
  user_id: number;
  trigger: string;
  to_email: string;
  subject: string;
  status: string;
  opened_at: string | null;
  clicked_at: string | null;
  error_message: string | null;
  created_at: string;
}

interface EmailTemplateDetail {
  id: number;
  trigger: string;
  subject: string;
  body_html: string;
  body_text: string;
  is_active: boolean;
  variables: string[];
  created_at: string;
  updated_at: string;
}

export default function EmailsTab() {
  const [stats, setStats] = useState<EmailStats | null>(null);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [logs, setLogs] = useState<EmailLog[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [sendingTest, setSendingTest] = useState<number | null>(null);
  const [activeView, setActiveView] = useState<'templates' | 'logs'>('templates');

  // Edit modal state
  const [editingTemplate, setEditingTemplate] = useState<EmailTemplateDetail | null>(null);
  const [editLoading, setEditLoading] = useState(false);
  const [saveLoading, setSaveLoading] = useState(false);
  const [editForm, setEditForm] = useState({
    subject: '',
    body_html: '',
    body_text: '',
    is_active: true,
  });

  const perPage = 20;

  const fetchData = useCallback(async (logsPage: number) => {
    setLoading(true);
    try {
      const [statsRes, templatesRes, logsRes] = await Promise.all([
        adminAPI.getEmailStats(),
        adminAPI.getEmailTemplates(),
        adminAPI.getEmailLogs({ page: logsPage, per_page: perPage }),
      ]);
      setStats(statsRes.data);
      setTemplates(templatesRes.data.items);
      setLogs(logsRes.data.items);
      setPage(logsRes.data.page);
      setTotalPages(logsRes.data.total_pages);
    } catch (error) {
      console.error('Error fetching email data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData(1);
  }, [fetchData]);

  const sendTestEmail = async (templateId: number) => {
    setSendingTest(templateId);
    try {
      const res = await adminAPI.sendTestEmail(templateId);
      alert(`Email de test envoyé à ${res.data.to}`);
    } catch (error) {
      console.error('Error sending test email:', error);
      alert('Erreur lors de l\'envoi');
    } finally {
      setSendingTest(null);
    }
  };

  const openEditModal = async (templateId: number) => {
    setEditLoading(true);
    try {
      const res = await adminAPI.getEmailTemplate(templateId);
      setEditingTemplate(res.data);
      setEditForm({
        subject: res.data.subject,
        body_html: res.data.body_html,
        body_text: res.data.body_text,
        is_active: res.data.is_active,
      });
    } catch (error) {
      console.error('Error fetching template:', error);
      alert('Erreur lors du chargement du template');
    } finally {
      setEditLoading(false);
    }
  };

  const saveTemplate = async () => {
    if (!editingTemplate) return;
    setSaveLoading(true);
    try {
      await adminAPI.updateEmailTemplate(editingTemplate.id, editForm);
      setEditingTemplate(null);
      fetchData(page);
    } catch (error) {
      console.error('Error saving template:', error);
      alert('Erreur lors de la sauvegarde');
    } finally {
      setSaveLoading(false);
    }
  };

  const statusColors: Record<string, string> = {
    sent: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
    delivered: 'bg-green-500/20 text-green-400 border-green-500/30',
    opened: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
    clicked: 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30',
    failed: 'bg-red-500/20 text-red-400 border-red-500/30',
    pending: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  };

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/20">
                  <Send className="h-4 w-4 text-blue-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Total</p>
                  <p className="text-xl font-bold">{stats?.total || 0}</p>
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
                  <p className="text-xs text-slate-400">Envoyés</p>
                  <p className="text-xl font-bold text-green-400">{stats?.sent || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/20">
                  <Eye className="h-4 w-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Taux ouverture</p>
                  <p className="text-xl font-bold text-purple-400">
                    {((stats?.open_rate || 0) * 100).toFixed(1)}%
                  </p>
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
                  <MousePointer className="h-4 w-4 text-cyan-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Taux clic</p>
                  <p className="text-xl font-bold text-cyan-400">
                    {((stats?.click_rate || 0) * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }}>
          <Card className="glass border-white/10">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-red-500/20">
                  <XCircle className="h-4 w-4 text-red-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-400">Échecs</p>
                  <p className="text-xl font-bold text-red-400">{stats?.failed || 0}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* View Toggle */}
      <div className="flex gap-2">
        <Button
          variant={activeView === 'templates' ? 'default' : 'outline'}
          className={activeView === 'templates' ? 'bg-primary' : 'border-white/20'}
          onClick={() => setActiveView('templates')}
        >
          <Mail className="h-4 w-4 mr-2" />
          Templates
        </Button>
        <Button
          variant={activeView === 'logs' ? 'default' : 'outline'}
          className={activeView === 'logs' ? 'bg-primary' : 'border-white/20'}
          onClick={() => setActiveView('logs')}
        >
          <Send className="h-4 w-4 mr-2" />
          Logs d&apos;envoi
        </Button>
      </div>

      {/* Templates View */}
      {activeView === 'templates' && (
        <Card className="glass border-white/10">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Mail className="h-5 w-5 text-primary" />
              Templates email ({templates.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-20 bg-slate-800" />
                ))}
              </div>
            ) : templates.length === 0 ? (
              <div className="py-12 text-center">
                <Mail className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Aucun template configuré</p>
              </div>
            ) : (
              <div className="space-y-4">
                {templates.map((template) => (
                  <div
                    key={template.id}
                    className="p-4 rounded-lg bg-slate-800/50 hover:bg-slate-800 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <Badge
                            variant="outline"
                            className={cn(
                              template.is_active
                                ? "bg-green-500/20 text-green-400 border-green-500/30"
                                : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                            )}
                          >
                            {template.is_active ? 'Actif' : 'Inactif'}
                          </Badge>
                          <Badge variant="outline" className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                            {template.trigger}
                          </Badge>
                        </div>
                        <p className="font-medium text-white">{template.subject}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          Variables: {template.variables?.join(', ') || 'Aucune'}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          Mis à jour: {new Date(template.updated_at).toLocaleDateString('fr-FR')}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-white/20"
                          onClick={() => openEditModal(template.id)}
                          disabled={editLoading}
                        >
                          <Edit3 className="h-3 w-3 mr-1" />
                          Modifier
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="border-primary/30 text-primary hover:bg-primary/10"
                          onClick={() => sendTestEmail(template.id)}
                          disabled={sendingTest === template.id || !template.is_active}
                        >
                          {sendingTest === template.id ? (
                            <Loader2 className="h-3 w-3 animate-spin mr-1" />
                          ) : (
                            <PlayCircle className="h-3 w-3 mr-1" />
                          )}
                          Tester
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
              <Send className="h-5 w-5 text-primary" />
              Logs d&apos;envoi
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
                <Send className="h-12 w-12 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">Aucun email envoyé</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="text-left border-b border-white/10">
                        <th className="pb-3 text-sm font-medium text-slate-400">Destinataire</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Trigger</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Sujet</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Statut</th>
                        <th className="pb-3 text-sm font-medium text-slate-400">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logs.map((log) => (
                        <tr key={log.id} className="border-b border-white/5 hover:bg-white/5">
                          <td className="py-3 text-sm">{log.to_email}</td>
                          <td className="py-3">
                            <Badge variant="outline" className="bg-slate-500/20 text-slate-400 border-slate-500/30">
                              {log.trigger}
                            </Badge>
                          </td>
                          <td className="py-3 text-sm text-slate-300 max-w-xs truncate">
                            {log.subject}
                          </td>
                          <td className="py-3">
                            <Badge
                              variant="outline"
                              className={statusColors[log.status] || statusColors.pending}
                            >
                              {log.status}
                            </Badge>
                          </td>
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

      {/* Edit Template Modal */}
      <Dialog open={!!editingTemplate} onOpenChange={() => setEditingTemplate(null)}>
        <DialogContent className="glass border-white/10 max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-primary" />
              Modifier le template: {editingTemplate?.trigger}
            </DialogTitle>
          </DialogHeader>

          {editLoading ? (
            <div className="space-y-4 py-4">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-40 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          ) : editingTemplate && (
            <div className="space-y-6 py-4">
              {/* Active Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-white">Template actif</p>
                  <p className="text-sm text-slate-400">
                    Les emails seront envoyés si actif
                  </p>
                </div>
                <Switch
                  checked={editForm.is_active}
                  onCheckedChange={(checked) => setEditForm({ ...editForm, is_active: checked })}
                />
              </div>

              {/* Subject */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">Sujet</label>
                <input
                  type="text"
                  value={editForm.subject}
                  onChange={(e) => setEditForm({ ...editForm, subject: e.target.value })}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              </div>

              {/* Variables Info */}
              {editingTemplate.variables?.length > 0 && (
                <div className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
                  <p className="text-sm text-blue-400 font-medium mb-1">Variables disponibles:</p>
                  <div className="flex flex-wrap gap-2">
                    {editingTemplate.variables.map(v => (
                      <code key={v} className="px-2 py-0.5 bg-blue-500/20 rounded text-xs text-blue-300">
                        {`{{${v}}}`}
                      </code>
                    ))}
                  </div>
                </div>
              )}

              {/* HTML Body */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">Contenu HTML</label>
                <textarea
                  value={editForm.body_html}
                  onChange={(e) => setEditForm({ ...editForm, body_html: e.target.value })}
                  rows={10}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>

              {/* Text Body */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-white">Contenu texte (fallback)</label>
                <textarea
                  value={editForm.body_text}
                  onChange={(e) => setEditForm({ ...editForm, body_text: e.target.value })}
                  rows={6}
                  className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary/50 resize-none"
                />
              </div>

              {/* Actions */}
              <div className="flex gap-3 justify-end pt-4 border-t border-white/10">
                <Button
                  variant="ghost"
                  onClick={() => setEditingTemplate(null)}
                  disabled={saveLoading}
                >
                  <X className="h-4 w-4 mr-1" />
                  Annuler
                </Button>
                <Button
                  onClick={saveTemplate}
                  disabled={saveLoading}
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
