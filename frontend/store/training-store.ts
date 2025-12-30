import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Message, TrainingScenario, SessionFeedback } from '@/types';
import { generateId } from '@/lib/utils';

interface TrainingState {
  // Session state
  sessionId: number | null;
  championId: number | null;
  championName: string;
  scenario: TrainingScenario | null;

  // Messages
  messages: Message[];
  isTyping: boolean;

  // Scoring
  currentScore: number;
  feedback: SessionFeedback | null;

  // Timer
  startTime: Date | null;
  elapsedSeconds: number;

  // Actions
  startSession: (params: {
    sessionId: number;
    championId: number;
    championName: string;
    scenario: TrainingScenario;
    firstMessage: string;
  }) => void;

  addUserMessage: (content: string) => void;
  addChampionMessage: (content: string, score?: number, feedbackText?: string) => void;

  setTyping: (isTyping: boolean) => void;
  updateScore: (score: number) => void;
  setFeedback: (feedback: SessionFeedback) => void;

  updateTimer: () => void;

  endSession: () => void;
  reset: () => void;
}

export const useTrainingStore = create<TrainingState>()(
  persist(
    (set, get) => ({
      // Initial state
      sessionId: null,
      championId: null,
      championName: '',
      scenario: null,
      messages: [],
      isTyping: false,
      currentScore: 0,
      feedback: null,
      startTime: null,
      elapsedSeconds: 0,

      // Actions
      startSession: ({ sessionId, championId, championName, scenario, firstMessage }) => {
        set({
          sessionId,
          championId,
          championName,
          scenario,
          messages: [
            {
              id: generateId(),
              role: 'champion',
              content: firstMessage,
              timestamp: new Date(),
            },
          ],
          isTyping: false,
          currentScore: 0,
          feedback: null,
          startTime: new Date(),
          elapsedSeconds: 0,
        });
      },

      addUserMessage: (content) => {
        const message: Message = {
          id: generateId(),
          role: 'user',
          content,
          timestamp: new Date(),
        };
        set((state) => ({
          messages: [...state.messages, message],
        }));
      },

      addChampionMessage: (content, score, feedbackText) => {
        const message: Message = {
          id: generateId(),
          role: 'champion',
          content,
          timestamp: new Date(),
          score,
          feedback: feedbackText,
        };
        set((state) => ({
          messages: [...state.messages, message],
          currentScore: score ?? state.currentScore,
        }));
      },

      setTyping: (isTyping) => set({ isTyping }),

      updateScore: (score) => set({ currentScore: score }),

      setFeedback: (feedback) => set({ feedback }),

      updateTimer: () => {
        const { startTime } = get();
        if (startTime) {
          const elapsed = Math.floor((Date.now() - new Date(startTime).getTime()) / 1000);
          set({ elapsedSeconds: elapsed });
        }
      },

      endSession: () => {
        set({
          sessionId: null,
          startTime: null,
        });
      },

      reset: () => {
        set({
          sessionId: null,
          championId: null,
          championName: '',
          scenario: null,
          messages: [],
          isTyping: false,
          currentScore: 0,
          feedback: null,
          startTime: null,
          elapsedSeconds: 0,
        });
      },
    }),
    {
      name: 'training-storage',
      partialize: (state) => ({
        sessionId: state.sessionId,
        championId: state.championId,
        championName: state.championName,
        messages: state.messages,
        currentScore: state.currentScore,
        startTime: state.startTime,
      }),
    }
  )
);
