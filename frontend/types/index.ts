// Champion types
export interface Champion {
  id: number;
  name: string;
  description?: string;
  video_path?: string;
  audio_path?: string;
  transcript?: string;
  patterns_json?: SalesPatterns;
  status: 'pending' | 'uploaded' | 'processing' | 'ready' | 'error';
  created_at: string;
  updated_at: string;
}

export interface SalesPatterns {
  openings: Pattern[];
  objection_handling: Pattern[];
  closings: Pattern[];
  key_phrases: string[];
  communication_style: string;
  effectiveness_score: number;
}

export interface Pattern {
  text: string;
  context: string;
  effectiveness: number;
  tags?: string[];
}

// Training types
export interface TrainingScenario {
  id: string;
  name: string;
  description: string;
  difficulty: 'easy' | 'medium' | 'hard';
  context: string;
  objectives: string[];
  prospect_profile: ProspectProfile;
  prospect_type?: string;
  challenge?: string;
}

export interface ProspectProfile {
  name: string;
  company: string;
  role: string;
  pain_points: string[];
  objections: string[];
}

export interface TrainingSession {
  id: number;
  user_id: string;
  champion_id: number;
  scenario?: TrainingScenario;
  status: 'active' | 'completed' | 'abandoned';
  score: number;
  overall_score?: number;
  started_at: string;
  ended_at?: string;
  messages?: Message[];
  duration_seconds?: number;
}

export interface Message {
  id: string;
  role: 'user' | 'champion';
  content: string;
  timestamp: Date;
  score?: number;
  feedback?: string;
}

// Alias for ChatInterface component compatibility
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  score?: number;
  feedback?: string;
}

export interface SessionFeedback {
  score: number;
  strengths: string[];
  improvements: string[];
  suggestions: string[];
  champion_would_say?: string;
}

// API Response types
export interface UploadResponse {
  champion_id: number;
  name: string;
  status: string;
  message: string;
  video_path: string;
}

export interface AnalyzeResponse {
  champion_id: number;
  status: string;
  message: string;
  patterns?: SalesPatterns;
}

export interface ScenarioResponse {
  champion_id: number;
  champion_name: string;
  scenarios: TrainingScenario[];
}

export interface SessionStartResponse {
  session_id: number;
  champion_name: string;
  scenario?: TrainingScenario;
  first_message: string;
  tips: string[];
}

export interface SessionRespondResponse {
  champion_response: string;
  feedback: string;
  score: number;
  suggestions: string[];
  session_complete: boolean;
}

export interface SessionSummary {
  session_id: number;
  champion_name: string;
  total_exchanges: number;
  overall_score: number;
  feedback_summary: string;
  strengths: string[];
  areas_for_improvement: string[];
  duration_seconds: number;
}

// Dashboard types
export interface DashboardStats {
  total_sessions: number;
  average_score: number;
  best_score: number;
  improvement_percentage: number;
}

export interface SessionHistory {
  id: number;
  date: string;
  scenario: string;
  score: number;
  duration: number;
  champion_name: string;
}

export interface ProgressData {
  date: string;
  score: number;
  sessions: number;
}

// ============ AUTH TYPES ============
export interface User {
  id: number;
  email: string;
  full_name?: string;
  is_active: boolean;
  role: 'user' | 'admin';
  created_at: string;
}

// ============ ADMIN TYPES ============
export interface AdminStats {
  total_users: number;
  total_champions: number;
  total_sessions: number;
  avg_score: number;
  new_users_week: number;
  sessions_week: number;
  subscriptions: Record<string, number>;
  unread_alerts: number;
}

export interface FunnelStats {
  stages: Record<string, number>;
  total_users: number;
  conversion_rates: Record<string, number>;
}

export interface ActivityStats {
  period_days: number;
  total_activities: number;
  active_users: number;
  daily: Record<string, number>;
  by_action: Record<string, number>;
}

export interface ErrorStats {
  period_days: number;
  total: number;
  resolved: number;
  unresolved: number;
  by_type: Record<string, number>;
}

export interface EmailStats {
  total: number;
  sent: number;
  failed: number;
  opened: number;
  clicked: number;
  open_rate: number;
  click_rate: number;
  delivery_rate: number;
  by_trigger: Record<string, number>;
}

export interface WebhookStats {
  total_deliveries: number;
  success: number;
  failed: number;
  pending_retries: number;
  success_rate: number;
  by_event: Record<string, number>;
  active_endpoints: number;
  available_events: string[];
}

export interface AdminAlert {
  id: number;
  type: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  title: string;
  message: string;
  extra_data?: Record<string, unknown>;
  is_read: boolean;
  is_dismissed: boolean;
  created_at: string;
}

export interface AdminUserFull {
  id: number;
  email: string;
  full_name: string | null;
  role: 'user' | 'admin';
  is_active: boolean;
  subscription_plan: string;
  subscription_status: string;
  journey_stage: string;
  last_login_at: string | null;
  last_activity_at: string | null;
  created_at: string;
}

export interface ChurnRiskUser {
  id: number;
  email: string;
  full_name: string | null;
  subscription_plan: string;
  journey_stage: string;
  last_activity_at: string | null;
  days_inactive: number | null;
}

export interface AdminUserItem {
  id: number;
  email: string;
  full_name: string | null;
  role: 'user' | 'admin';
  is_active: boolean;
  created_at: string;
}

export interface AdminUserDetail {
  user: AdminUserItem;
  champions: { id: number; name: string; status: string; created_at: string }[];
  sessions: { id: number; champion_id: number; score: number | null; status: string; started_at: string }[];
  stats: { total_champions: number; total_sessions: number; avg_score: number };
}

export interface AdminSessionItem {
  id: number;
  user_id: string;
  user_email: string;
  champion_id: number;
  champion_name: string;
  score: number | null;
  status: string;
  started_at: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name?: string;
}

// Chart types
export interface ChartDataPoint {
  date: string;
  score: number;
  sessionId: number | string;
}

// Analytics types
export interface StatsData {
  totalSessions: number;
  avgScore: number;
  bestScore: number;
  improvementRate: number;
}

// Champion alias for list views
export type ChampionListItem = Champion;

// Pattern types for champion components
export interface ObjectionHandler {
  objection: string;
  response: string;
  example?: string;
}

export interface ChampionPatterns {
  openings: string[];
  objection_handlers: ObjectionHandler[];
  closes: string[];
  key_phrases: string[];
  tone_style?: string;
  success_patterns: string[];
}

// ============ V2 PEDAGOGICAL SYSTEM TYPES ============

export type DifficultyLevel = 'easy' | 'medium' | 'expert';
export type MoodState = 'hostile' | 'aggressive' | 'skeptical' | 'neutral' | 'interested' | 'enthusiastic';

// Learning content
export interface Cours {
  id: string;
  title: string;
  description: string;
  duration_minutes: number;
  difficulty: DifficultyLevel;
  category: string;
  content: CoursContent[];
  prerequisites?: string[];
}

export interface CoursContent {
  type: 'text' | 'video' | 'example' | 'exercise';
  title?: string;
  content: string;
}

export interface Quiz {
  id: string;
  title: string;
  course_id: string;
  questions: QuizQuestion[];
}

export interface QuizQuestion {
  id: string;
  question: string;
  options: string[];
  correct_answer: number;
  explanation: string;
}

export interface QuizResult {
  quiz_id: string;
  score: number;
  total: number;
  percentage: number;
  passed: boolean;
  answers: {
    question_id: string;
    selected: number;
    correct: boolean;
  }[];
}

// V2 Voice Training
export interface VoiceSessionStartResponse {
  session_id: number;
  level: DifficultyLevel;
  scenario: TrainingScenario;
  prospect_message: string;
  prospect_audio_base64?: string;
  mood: MoodState;
  jauge: number;
  jauge_visible: boolean;
  config: LevelConfig;
}

export interface VoiceSessionMessageResponse {
  text: string;
  audio_base64?: string;
  mood: MoodState;
  jauge: number;
  jauge_delta: number;
  behavioral_cue?: string;
  hint?: string;
  session_complete: boolean;
  detected_patterns?: DetectedPattern[];
  event?: SituationalEvent;
  reversal?: Reversal;
}

export interface LevelConfig {
  starting_jauge: number;
  conversion_threshold: number;
  jauge_volatility: 'low' | 'medium' | 'high';
  show_jauge: boolean;
  hidden_objections: boolean;
  hidden_objection_probability: number;
  situational_events: boolean;
  reversals: boolean;
  reversal_probability: number;
  hints_enabled: boolean;
}

export interface DetectedPattern {
  type: 'positive' | 'negative';
  action: string;
  points: number;
  description?: string;
}

export interface SituationalEvent {
  type: string;
  description: string;
  impact: number;
}

export interface Reversal {
  type: 'last_minute_bomb' | 'price_attack' | 'ghost_decision_maker';
  description: string;
  jauge_drop: number;
}

export interface HiddenObjection {
  expressed: string;
  hidden: string;
  discovery_question?: string;
  discovered: boolean;
}

export interface VoiceSessionSummary {
  session_id: number;
  level: DifficultyLevel;
  duration_seconds: number;
  final_jauge: number;
  starting_jauge: number;
  jauge_progression: number;
  conversion_achieved: boolean;
  detected_patterns: DetectedPattern[];
  hidden_objections_discovered: number;
  hidden_objections_total: number;
  events_handled: number;
  reversals_recovered: number;
  strengths: string[];
  improvements: string[];
  overall_feedback: string;
}

export interface VoiceConfig {
  status: string;
  services: {
    elevenlabs: boolean;
    whisper: boolean;
    voice_friendly: boolean;
    voice_neutral: boolean;
    voice_aggressive: boolean;
    jauge_service: boolean;
    event_service: boolean;
    behavioral_detector: boolean;
  };
}

export interface UserProgress {
  user_id: number;
  completed_courses: string[];
  quiz_scores: Record<string, number>;
  training_sessions: number;
  average_score: number;
  current_level: DifficultyLevel;
  unlocked_levels: DifficultyLevel[];
}
