import api from './api';
import type {
  AdminStats,
  FunnelStats,
  ActivityStats,
  ErrorStats,
  EmailStats,
  WebhookStats,
  AdminAlert,
  AdminUserFull,
  ChurnRiskUser,
  PaginatedResponse,
} from '@/types';

// ============ ADMIN API ============
export const adminAPI = {
  // Stats
  getStats: () => api.get<AdminStats>('/admin/stats'),
  getFunnelStats: () => api.get<FunnelStats>('/admin/stats/funnel'),
  getActivityStats: (days = 30) => api.get<ActivityStats>('/admin/stats/activity', { params: { days } }),
  getErrorStats: (days = 7) => api.get<ErrorStats>('/admin/stats/errors', { params: { days } }),
  getEmailStats: () => api.get<EmailStats>('/admin/stats/emails'),
  getWebhookStats: () => api.get<WebhookStats>('/admin/stats/webhooks'),

  // Users
  getUsers: (params?: {
    page?: number;
    per_page?: number;
    search?: string;
    role?: string;
    is_active?: boolean;
    subscription_plan?: string;
    journey_stage?: string;
  }) => api.get<PaginatedResponse<AdminUserFull>>('/admin/users', { params }),

  getUser: (id: number) => api.get<{
    user: AdminUserFull;
    champions: { id: number; name: string; status: string; created_at: string }[];
    sessions: { id: number; champion_id: number; score: number | null; status: string; started_at: string }[];
    activities: { id: number; action: string; resource_type: string; resource_id: string; created_at: string }[];
    notes: { id: number; content: string; is_pinned: boolean; admin_id: number; created_at: string }[];
    stats: { total_champions: number; total_sessions: number; avg_score: number };
  }>(`/admin/users/${id}`),

  updateUser: (id: number, data: {
    is_active?: boolean;
    role?: string;
    subscription_plan?: string;
    subscription_status?: string;
  }) => api.patch(`/admin/users/${id}`, data),

  getChurnRiskUsers: (days = 14) => api.get<{ users: ChurnRiskUser[]; count: number; threshold_days: number }>(
    '/admin/users/churn-risk',
    { params: { days } }
  ),

  // Sessions
  getSessions: (params?: {
    page?: number;
    per_page?: number;
    status?: string;
    champion_id?: number;
  }) => api.get<PaginatedResponse<{
    id: number;
    user_id: string;
    user_email: string;
    champion_id: number;
    champion_name: string;
    score: number | null;
    status: string;
    started_at: string;
  }>>('/admin/sessions', { params }),

  // Activities
  getActivities: (params?: {
    page?: number;
    per_page?: number;
    user_id?: number;
    action?: string;
  }) => api.get<PaginatedResponse<{
    id: number;
    user_id: number;
    action: string;
    resource_type: string;
    resource_id: string;
    extra_data: Record<string, unknown>;
    ip_address: string;
    created_at: string;
  }>>('/admin/activities', { params }),

  // Errors
  getErrors: (params?: {
    page?: number;
    per_page?: number;
    resolved?: boolean;
    error_type?: string;
  }) => api.get<PaginatedResponse<{
    id: number;
    user_id: number | null;
    error_type: string;
    error_message: string;
    endpoint: string;
    is_resolved: boolean;
    resolved_at: string | null;
    resolution_notes: string | null;
    created_at: string;
  }>>('/admin/errors', { params }),

  getError: (id: number) => api.get<{
    id: number;
    user_id: number | null;
    error_type: string;
    error_message: string;
    stack_trace: string | null;
    endpoint: string;
    request_data: Record<string, unknown> | null;
    is_resolved: boolean;
    resolved_at: string | null;
    resolved_by: number | null;
    resolution_notes: string | null;
    created_at: string;
  }>(`/admin/errors/${id}`),

  resolveError: (id: number, resolution_notes?: string) =>
    api.post(`/admin/errors/${id}/resolve`, { resolution_notes }),

  // Email Templates
  getEmailTemplates: () => api.get<{ items: {
    id: number;
    trigger: string;
    subject: string;
    is_active: boolean;
    variables: string[];
    updated_at: string;
  }[] }>('/admin/email-templates'),

  getEmailTemplate: (id: number) => api.get<{
    id: number;
    trigger: string;
    subject: string;
    body_html: string;
    body_text: string;
    is_active: boolean;
    variables: string[];
    created_at: string;
    updated_at: string;
  }>(`/admin/email-templates/${id}`),

  sendTestEmail: (id: number) => api.post<{ status: string; email_log_id: number; to: string }>(
    `/admin/email-templates/${id}/send-test`
  ),

  updateEmailTemplate: (id: number, data: {
    subject?: string;
    body_html?: string;
    body_text?: string;
    variables?: string[];
    is_active?: boolean;
  }) => api.patch(`/admin/email-templates/${id}`, data),

  getEmailLogs: (params?: {
    page?: number;
    per_page?: number;
    user_id?: number;
    trigger?: string;
    status?: string;
  }) => api.get<PaginatedResponse<{
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
  }>>('/admin/email-logs', { params }),

  // Webhooks
  getWebhooks: () => api.get<{
    items: {
      id: number;
      name: string;
      url: string;
      events: string[];
      is_active: boolean;
      created_at: string;
    }[];
    available_events: string[];
  }>('/admin/webhooks'),

  getWebhook: (id: number) => api.get<{
    id: number;
    name: string;
    url: string;
    secret: string;
    events: string[];
    is_active: boolean;
    created_at: string;
    updated_at: string;
  }>(`/admin/webhooks/${id}`),

  createWebhook: (data: { name: string; url: string; events: string[]; is_active?: boolean }) =>
    api.post<{ status: string; endpoint_id: number; secret: string }>('/admin/webhooks', data),

  updateWebhook: (id: number, data: {
    name?: string;
    url?: string;
    events?: string[];
    is_active?: boolean;
  }) => api.patch(`/admin/webhooks/${id}`, data),

  deleteWebhook: (id: number) => api.delete(`/admin/webhooks/${id}`),

  testWebhook: (id: number) => api.post<{ status: string; response_code: number; error_message: string | null }>(
    `/admin/webhooks/${id}/test`
  ),

  regenerateWebhookSecret: (id: number) => api.post<{ status: string; secret: string }>(
    `/admin/webhooks/${id}/regenerate-secret`
  ),

  getWebhookLogs: (params?: {
    page?: number;
    per_page?: number;
    endpoint_id?: number;
    event?: string;
    status?: string;
  }) => api.get<PaginatedResponse<{
    id: number;
    endpoint_id: number;
    event: string;
    status: string;
    response_code: number | null;
    error_message: string | null;
    attempts: number;
    created_at: string;
  }>>('/admin/webhook-logs', { params }),

  // Alerts
  getAlerts: (params?: {
    page?: number;
    per_page?: number;
    unread_only?: boolean;
  }) => api.get<PaginatedResponse<AdminAlert>>('/admin/alerts', { params }),

  markAlertRead: (id: number) => api.post(`/admin/alerts/${id}/read`),

  dismissAlert: (id: number) => api.post(`/admin/alerts/${id}/dismiss`),

  markAllAlertsRead: () => api.post('/admin/alerts/read-all'),

  // Notes
  getUserNotes: (userId: number) => api.get<{ items: {
    id: number;
    content: string;
    is_pinned: boolean;
    admin_id: number;
    created_at: string;
    updated_at: string;
  }[] }>(`/admin/users/${userId}/notes`),

  createUserNote: (userId: number, data: { content: string; is_pinned?: boolean }) =>
    api.post(`/admin/users/${userId}/notes`, data),

  updateNote: (noteId: number, data: { content: string; is_pinned?: boolean }) =>
    api.patch(`/admin/notes/${noteId}`, data),

  deleteNote: (noteId: number) => api.delete(`/admin/notes/${noteId}`),

  // Audit Logs
  getAuditLogs: (params?: {
    page?: number;
    per_page?: number;
    admin_id?: number;
    action?: string;
    resource_type?: string;
  }) => api.get<{
    items: {
      id: number;
      admin_id: number;
      action: string;
      resource_type: string;
      resource_id: string;
      old_value: Record<string, unknown> | null;
      new_value: Record<string, unknown> | null;
      ip_address: string;
      created_at: string;
    }[];
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
    available_actions: string[];
  }>('/admin/audit-logs', { params }),

  getAuditLog: (id: number) => api.get<{
    id: number;
    admin_id: number;
    action: string;
    resource_type: string;
    resource_id: string;
    old_value: Record<string, unknown> | null;
    new_value: Record<string, unknown> | null;
    ip_address: string;
    user_agent: string;
    created_at: string;
  }>(`/admin/audit-logs/${id}`),
};

export default adminAPI;
