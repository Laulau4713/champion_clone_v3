import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage, TrainingScenario } from "@/types";
import { generateId } from "@/lib/utils";

interface TrainingState {
  // Session state
  sessionId: number | null;
  championId: number | null;
  championName: string | null;
  scenario: TrainingScenario | null;
  messages: ChatMessage[];
  currentScore: number;
  isLoading: boolean;
  isComplete: boolean;

  // Tips for the user
  tips: string[];

  // Session timing
  startedAt: Date | null;
  elapsedSeconds: number;

  // Actions
  startSession: (data: {
    sessionId: number;
    championId: number;
    championName: string;
    scenario: TrainingScenario;
    firstMessage: string;
    tips: string[];
  }) => void;
  addUserMessage: (content: string) => void;
  addAssistantMessage: (content: string, feedback?: string, score?: number) => void;
  updateScore: (score: number) => void;
  setLoading: (loading: boolean) => void;
  completeSession: () => void;
  updateElapsedTime: () => void;
  reset: () => void;
}

const initialState = {
  sessionId: null,
  championId: null,
  championName: null,
  scenario: null,
  messages: [],
  currentScore: 0,
  isLoading: false,
  isComplete: false,
  tips: [],
  startedAt: null,
  elapsedSeconds: 0,
};

export const useTrainingStore = create<TrainingState>()(
  persist(
    (set, get) => ({
      ...initialState,

      startSession: ({ sessionId, championId, championName, scenario, firstMessage, tips }) => {
        set({
          sessionId,
          championId,
          championName,
          scenario,
          tips,
          messages: [
            {
              id: generateId(),
              role: "assistant",
              content: firstMessage,
              timestamp: new Date(),
            },
          ],
          currentScore: 0,
          isLoading: false,
          isComplete: false,
          startedAt: new Date(),
          elapsedSeconds: 0,
        });
      },

      addUserMessage: (content: string) => {
        const message: ChatMessage = {
          id: generateId(),
          role: "user",
          content,
          timestamp: new Date(),
        };
        set((state) => ({
          messages: [...state.messages, message],
        }));
      },

      addAssistantMessage: (content: string, feedback?: string, score?: number) => {
        const message: ChatMessage = {
          id: generateId(),
          role: "assistant",
          content,
          timestamp: new Date(),
          feedback,
          score,
        };
        set((state) => ({
          messages: [...state.messages, message],
          currentScore: score ?? state.currentScore,
        }));
      },

      updateScore: (score: number) => {
        set({ currentScore: score });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      completeSession: () => {
        set({ isComplete: true });
      },

      updateElapsedTime: () => {
        const { startedAt } = get();
        if (startedAt) {
          const elapsed = Math.floor((Date.now() - startedAt.getTime()) / 1000);
          set({ elapsedSeconds: elapsed });
        }
      },

      reset: () => {
        set(initialState);
      },
    }),
    {
      name: "training-session",
      partialize: (state) => ({
        sessionId: state.sessionId,
        championId: state.championId,
        championName: state.championName,
        scenario: state.scenario,
        messages: state.messages,
        currentScore: state.currentScore,
        isComplete: state.isComplete,
        startedAt: state.startedAt,
      }),
    }
  )
);

// ============================================
// Upload Store
// ============================================

interface UploadState {
  championId: number | null;
  status: "idle" | "uploading" | "processing" | "analyzing" | "complete" | "error";
  progress: number;
  message: string;
  error: string | null;

  setUploading: (progress: number) => void;
  setProcessing: () => void;
  setAnalyzing: () => void;
  setComplete: (championId: number) => void;
  setError: (error: string) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  championId: null,
  status: "idle",
  progress: 0,
  message: "",
  error: null,

  setUploading: (progress: number) => {
    set({
      status: "uploading",
      progress,
      message: `Upload en cours... ${progress}%`,
      error: null,
    });
  },

  setProcessing: () => {
    set({
      status: "processing",
      progress: 100,
      message: "Extraction audio et transcription...",
    });
  },

  setAnalyzing: () => {
    set({
      status: "analyzing",
      message: "Analyse des patterns de vente...",
    });
  },

  setComplete: (championId: number) => {
    set({
      championId,
      status: "complete",
      message: "Analyse terminée !",
    });
  },

  setError: (error: string) => {
    set({
      status: "error",
      message: error,
      error,
    });
  },

  reset: () => {
    set({
      championId: null,
      status: "idle",
      progress: 0,
      message: "",
      error: null,
    });
  },
}));
