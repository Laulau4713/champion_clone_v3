import axios from 'axios';
import type {
  Champion,
  UploadResponse,
  AnalyzeResponse,
  ScenarioResponse,
  SessionStartResponse,
  SessionRespondResponse,
  SessionSummary,
  AuthResponse,
  User,
  LoginRequest,
  RegisterRequest,
  Cours,
  Skill,
  Quiz,
  QuizResult,
  DifficultyLevel,
  VoiceSessionStartResponse,
  VoiceSessionMessageResponse,
  VoiceSessionSummary,
  VoiceConfig,
  UserProgress,
  SessionReport,
} from '@/types';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Response interceptor - handle 401/403
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401 || error.response?.status === 403) {
      if (typeof window !== 'undefined') {
        const refreshToken = localStorage.getItem('refresh_token');

        // Try to refresh token if we have one and it's not a refresh request
        if (refreshToken && !error.config.url?.includes('/auth/refresh')) {
          try {
            const { data } = await axios.post(
              `${api.defaults.baseURL}/auth/refresh`,
              { refresh_token: refreshToken }
            );
            localStorage.setItem('access_token', data.access_token);

            // Retry original request
            error.config.headers.Authorization = `Bearer ${data.access_token}`;
            return api.request(error.config);
          } catch {
            // Refresh failed, clear tokens and redirect
          }
        }

        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');

        if (!window.location.pathname.includes('/login') &&
            !window.location.pathname.includes('/register') &&
            window.location.pathname !== '/') {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

// ============ AUTH ============
export const authAPI = {
  register: (data: RegisterRequest) =>
    api.post<AuthResponse>('/auth/register', data),

  login: (data: LoginRequest) =>
    api.post<AuthResponse>('/auth/login', data),

  me: () => api.get<User>('/auth/me'),

  refresh: (refresh_token: string) =>
    api.post<AuthResponse>('/auth/refresh', { refresh_token }),

  logout: () => api.post('/auth/logout'),

  logoutAll: () => api.post('/auth/logout-all'),

  // Profile management
  updateProfile: (data: { full_name?: string; email?: string }) =>
    api.patch<User>('/auth/me', data),

  changePassword: (data: { current_password: string; new_password: string }) =>
    api.post<{ message: string }>('/auth/change-password', data),
};

// Health check
export const healthCheck = () => api.get('/health');

// Champions
export const getChampions = () =>
  api.get<{ champions: Champion[] }>('/champions');

export const getChampion = (id: number) =>
  api.get<Champion>(`/champions/${id}`);

export const uploadChampion = async (formData: FormData): Promise<UploadResponse> => {
  const response = await api.post<UploadResponse>('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};

export const analyzeChampion = async (id: number): Promise<AnalyzeResponse> => {
  const response = await api.post<AnalyzeResponse>(`/analyze/${id}`);
  return response.data;
};

export const deleteChampion = (id: number) =>
  api.delete(`/champions/${id}`);

// Scenarios
export const getScenarios = async (championId: number, count = 3): Promise<ScenarioResponse> => {
  const response = await api.get<ScenarioResponse>(`/scenarios/${championId}`, {
    params: { count },
  });
  return response.data;
};

// Training sessions
export const startTraining = async (data: {
  champion_id: number;
  user_id: string;
  scenario_index?: number;
}): Promise<SessionStartResponse> => {
  const response = await api.post<SessionStartResponse>('/training/start', data);
  return response.data;
};

export const respondTraining = async (data: {
  session_id: number;
  user_response: string;
}): Promise<SessionRespondResponse> => {
  const response = await api.post<SessionRespondResponse>('/training/respond', data);
  return response.data;
};

export const endTraining = async (sessionId: number): Promise<SessionSummary> => {
  const response = await api.post<SessionSummary>('/training/end', {
    session_id: sessionId,
  });
  return response.data;
};

export const getTrainingSessions = () =>
  api.get('/training/sessions');

// Orchestration (advanced)
export const orchestrate = async (task: string, context?: Record<string, unknown>) => {
  const formData = new FormData();
  formData.append('task', task);
  if (context) {
    formData.append('context', JSON.stringify(context));
  }
  return api.post('/orchestrate', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
};

// ============ LEARNING API ============
export const learningAPI = {
  // Cours
  getCourses: () => api.get<Cours[]>('/learning/courses'),
  getCourseByDay: (day: number) => api.get<Cours>(`/learning/courses/day/${day}`),

  // Skills
  getSkills: () => api.get<Skill[]>('/learning/skills'),
  getSkillBySlug: (slug: string) => api.get<Skill>(`/learning/skills/${slug}`),

  // Sectors
  getSectors: () => api.get('/learning/sectors'),

  // Quiz
  getQuizBySkill: (skillSlug: string) => api.get<Quiz>(`/learning/quiz/${skillSlug}`),
  submitQuiz: (skillSlug: string, answers: string[]) =>
    api.post<QuizResult>(`/learning/quiz/${skillSlug}/submit`, { answers }),

  // Progress
  getProgress: () => api.get<UserProgress>('/learning/progress'),
  getSkillsProgress: () => api.get('/learning/progress/skills'),
  markCourseComplete: (day: number) =>
    api.post(`/learning/courses/day/${day}/complete`),

  // Difficulty levels
  getDifficultyLevels: () => api.get('/learning/difficulty-levels'),
};

// ============ VOICE API (V2) ============
export const voiceAPI = {
  // Config
  getConfig: () => api.get<VoiceConfig>('/voice/config'),

  // Session management
  startSession: (data: {
    skill_slug: string;
    sector_slug?: string;
  }) => api.post<VoiceSessionStartResponse>('/voice/session/start', data),

  sendMessage: (sessionId: number, data: {
    text?: string;
    audio_base64?: string;
  }) => api.post<VoiceSessionMessageResponse>(
    `/voice/session/${sessionId}/message`,
    data
  ),

  endSession: (sessionId: number) =>
    api.post<VoiceSessionSummary>(`/voice/session/${sessionId}/end`),

  getSession: (sessionId: number) =>
    api.get(`/voice/session/${sessionId}`),

  // Report (Phase 3)
  getSessionReport: (sessionId: number) =>
    api.get<SessionReport>(`/voice/session/${sessionId}/report`),

  // Audio
  textToSpeech: (text: string, voiceId?: string) =>
    api.post<{ audio_base64: string }>('/voice/tts', { text, voice_id: voiceId }),

  speechToText: (audioBase64: string) =>
    api.post<{ text: string }>('/voice/stt', { audio_base64: audioBase64 }),
};

// ============ PAYMENTS API ============
export interface PaymentStatus {
  enabled: boolean;
  plan: string;
  status: string;
  subscription_id?: string;
  expires_at?: string;
}

export interface CheckoutResponse {
  checkout_url?: string;
  message: string;
}

export interface SubscriptionDetails {
  plan: string;
  status: string;
  subscription_id?: string;
  started_at?: string;
  expires_at?: string;
  cancel_at_period_end: boolean;
}

export const paymentsAPI = {
  // Get payment status
  getStatus: () => api.get<PaymentStatus>('/payments/status'),

  // Create checkout session
  createCheckout: (plan: string = 'pro') =>
    api.post<CheckoutResponse>('/payments/checkout', { plan }),

  // Get subscription details
  getSubscription: () => api.get<SubscriptionDetails>('/payments/subscription'),

  // Cancel subscription
  cancelSubscription: () => api.post<{ success: boolean; message: string }>('/payments/cancel'),
};

// ============ ACHIEVEMENTS & GAMIFICATION ============
import type { Achievement, UserXP, AchievementUnlockResult, AchievementCategory } from '@/types';

export const achievementsAPI = {
  // Get all achievements with unlock status
  getAll: (category?: AchievementCategory) =>
    api.get<Achievement[]>('/achievements', { params: category ? { category } : {} }),

  // Get only unlocked achievements
  getUnlocked: () => api.get<Achievement[]>('/achievements/unlocked'),

  // Get user XP and level
  getXP: () => api.get<UserXP>('/achievements/xp'),

  // Check and unlock eligible achievements
  check: () => api.post<AchievementUnlockResult>('/achievements/check'),
};

export default api;
