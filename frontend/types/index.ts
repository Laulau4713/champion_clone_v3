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

// V2 Scenario types (from backend)
export interface ScenarioProspectV2 {
  name?: string;
  role?: string;
  company?: string;
  personality?: string;
  pain_points?: string[];
  hidden_need?: string;
}

export interface ScenarioObjection {
  expressed: string;
  hidden?: string;
}

export interface ScenarioSolution {
  product_name?: string;
  value_proposition?: string;
  key_benefits?: string[];
  pricing_hint?: string;
  differentiator?: string;
}

export interface ScenarioV2 {
  title?: string;
  context?: string;
  prospect?: ScenarioProspectV2;
  objections?: ScenarioObjection[];
  solution?: ScenarioSolution;
  product_pitch?: string;
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
  // Subscription & trial info
  subscription_plan: 'free' | 'starter' | 'pro' | 'enterprise';
  trial_sessions_used: number;
  trial_sessions_max: number;
}

export interface TrialStatus {
  is_premium: boolean;
  trial_sessions_used: number;
  trial_sessions_max: number;
  trial_remaining: number;
  trial_expired: boolean;
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
  notes: { id: number; content: string; is_pinned: boolean; admin_id: number; created_at: string }[];
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

// Skill (compétence)
export interface Skill {
  id: number;
  slug: string;
  name: string;
  level: DifficultyLevel;
  description: string;
  order: number;
  pass_threshold: number;
  scenarios_required: number;
}

// Key point in a course
export interface KeyPoint {
  title: string;
  summary: string;
  template?: string;
  content?: Record<string, unknown>;
  checklist?: string[];
  warning?: string;
  example_dialogue?: {
    context?: string;
    bad?: string;
    good?: string;
    why_bad?: string;
    why_good?: string;
  };
}

// Course (module de formation)
export interface Cours {
  id: number;
  order: number;  // Module order in the curriculum
  day?: number;   // Deprecated: kept for backward compatibility
  level: DifficultyLevel;
  title: string;
  objective: string;
  duration_minutes: number;
  skill_id: number | null;
  skill_slug?: string;  // Skill slug for linking
  // Full course detail fields (returned by getCourseByOrder)
  key_points?: KeyPoint[];
  common_mistakes?: string[];
  emotional_tips?: string[];
  takeaways?: string[];
  stat_cle?: string;
  intro?: string;
  full_content?: string;
}

// Quiz response from API
export interface Quiz {
  skill_slug: string;
  skill_name: string;
  questions: QuizQuestion[];
  total_questions: number;
  pass_threshold: number;
}

export interface QuizQuestion {
  id: number;
  question: string;
  options: string[];
  correct_index: number;
  explanation: string;
}

export interface QuizResultDetail {
  question_index: number;
  your_answer: string;
  correct_answer: string;
  is_correct: boolean;
  explanation: string;
}

export interface QuizResult {
  score: number;
  passed: boolean;
  correct_count: number;
  total_questions: number;
  details: QuizResultDetail[];
}

// V2 Voice Training
export interface VoiceSessionStartResponse {
  session_id: number;
  level?: DifficultyLevel;
  scenario?: ScenarioV2;
  skill?: {
    slug: string;
    name: string;
    evaluation_criteria?: string[];
  };
  prospect_message?: string;
  prospect_audio_base64?: string;
  mood?: MoodState;
  current_mood?: MoodState;
  jauge?: number | null;
  current_gauge?: number;
  jauge_visible?: boolean;
  config?: LevelConfig;
  opening_message?: string | { text: string; audio_base64?: string };
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
  feedback?: {
    jauge?: number;
    jauge_delta?: number;
    positive_actions: string[];
    negative_actions: string[];
    tips: string[];
  };
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
  // V2 fields from backend
  total_training_minutes?: number;
  total_scenarios_completed?: number;
  skills_validated?: number;
}

// ============ ACHIEVEMENTS & GAMIFICATION ============

export type AchievementCategory = 'progression' | 'skill' | 'special';

export interface Achievement {
  id: string;
  category: AchievementCategory;
  name: string;
  description: string;
  icon: string;
  color: string;
  xp_reward: number;
  unlocked: boolean;
  unlocked_at?: string;
}

export interface UserXP {
  total_xp: number;
  level: number;
  xp_for_next_level: number;
  xp_progress: number;
}

export interface AchievementUnlockResult {
  newly_unlocked: Achievement[];
  total_xp_gained: number;
  level_up: boolean;
  new_level?: number;
}

// ============ SESSION REPORT TYPES (Phase 3) ============

export interface PatternAggregate {
  pattern: string;
  label: string;
  count: number;
  examples: string[];
  advice?: string;  // Only for negative patterns
}

export interface ReportMessage {
  role: 'user' | 'prospect';
  content: string;
  gauge_after: number;
  gauge_impact: number | null;
  mood: string | null;
  patterns_detected: string[];
  behavioral_cue: string | null;
  is_event: boolean;
  event_type: string | null;
  timestamp: string;
}

export interface SessionReport {
  // Header
  session_id: number;
  skill_name: string;
  skill_slug: string | null;
  sector_name: string | null;
  sector_slug: string | null;
  level: DifficultyLevel;
  duration_seconds: number;
  completed_at: string | null;
  status: string;

  // Score global
  final_score: number;
  final_gauge: number;
  starting_gauge: number;
  gauge_progression: number;
  converted: boolean;
  passed: boolean;

  // Patterns
  positive_patterns: PatternAggregate[];
  negative_patterns: PatternAggregate[];
  positive_count: number;
  negative_count: number;

  // Objections
  hidden_objections: HiddenObjection[];
  discovered_objections: string[];

  // Events
  triggered_events: SituationalEvent[];
  reversal_triggered: boolean;
  reversal_type: string | null;

  // Blockers
  conversion_blockers: string[];

  // Conseils
  personalized_tips: string[];
  points_forts: string[];
  axes_amelioration: string[];
  conseil_principal: string;

  // Conversation
  messages: ReportMessage[];
  message_count: number;

  // Graphique
  gauge_history: Array<{ timestamp: string; value: number; reason?: string }>;
}

// ============ V3 TRAINING SYSTEM TYPES (Playbook + Module) ============

// Playbook (produit à vendre)
export interface PlaybookSummary {
  id: string;
  name: string;
  company: string;
  sector: string;
}

// Module de formation (méthodologie)
export interface ModuleSummary {
  id: string;
  name: string;
  description: string;
  category: string;
}

// Session V3
export interface V3SessionStartResponse {
  success: boolean;
  session_id: string;
  first_message: string;
  prospect: V3Prospect;
  playbook_data: V3PlaybookData;
  module_data: V3ModuleData;
  jauge: V3JaugeState;
}

export interface V3Prospect {
  name: string;
  persona: string;
  company_type: string;
  pain_points: string[];
  hidden_objections: Array<{
    type: string;
    label: string;
    hidden_meaning: string;
  }>;
  decision_context: {
    budget: string;
    timing: string;
    decision_maker: string;
    competitors_looking: boolean;
  };
}

export interface V3PlaybookData {
  id: string;
  product: {
    name: string;
    company: string;
  };
  pitch: {
    hook_30s: string;
    discovery_questions: string[];
    key_phrases: string[];
  };
  objections: Array<{
    type: string;
    label: string;
    response: string;
    proof: string;
  }>;
  proofs: {
    global_stats: Record<string, string>;
    testimonials: Array<{
      name: string;
      role: string;
      company: string;
      quote: string;
    }>;
  };
  benefits: Record<string, string[]>;
}

export interface V3ModuleData {
  id: string;
  name: string;
  checklist: Array<{
    id: string;
    label: string;
    description: string;
  }>;
}

export interface V3JaugeState {
  value: number;
  mood: string;
  behavior: string;
}

export interface V3MessageResponse {
  success: boolean;
  prospect_response?: string;
  evaluation: {
    detected?: Array<{
      id: string;
      label: string;
      quality: string;
    }>;
    progress?: {
      detected: string[];
      scores: Record<string, number>;
    };
  };
  jauge: V3JaugeState;
  behaviors: {
    patterns?: {
      positive: Array<{ pattern: string; action: string }>;
      negative: Array<{ pattern: string; action: string }>;
    };
    modifications?: Array<{
      action: string;
      delta: number;
      new_value: number;
      reason: string;
    }>;
  };
  session_complete: boolean;
}

export interface V3SessionEndResponse {
  success: boolean;
  session_id: string;
  evaluation: {
    score: number;
    level: string;
    level_description: string;
    elements_detected: Array<{
      id: string;
      label: string;
      quality: string;
    }>;
    elements_missing: Array<{
      id: string;
      label: string;
      description: string;
    }>;
  };
  final_result: {
    result_key: string;
    emoji: string;
    label: string;
    message: string;
    coaching: string;
    next_focus: string;
  };
  report: Record<string, unknown>;
}
