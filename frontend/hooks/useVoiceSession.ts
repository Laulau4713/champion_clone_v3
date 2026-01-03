"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import {
  VoiceWebSocket,
  ProspectResponse,
  JaugeUpdate,
  SessionEnded,
} from "@/lib/websocket";

export interface VoiceMessage {
  id: string;
  role: "user" | "prospect";
  text: string;
  audioBase64?: string;
  mood?: string;
  jaugeDelta?: number;
  behavioralCue?: string;
  isEvent?: boolean;
  eventType?: string;
  timestamp: Date;
}

export interface ActiveReversal {
  type: string;
  message: string;
  jaugeDrop?: number;
  timestamp: Date;
}

export interface ActiveEvent {
  type: string;
  message: string;
  testDescription?: string;
  timestamp: Date;
}

export interface UseVoiceSessionOptions {
  sessionId: number;
  onSessionEnded?: (evaluation: SessionEnded["evaluation"]) => void;
}

// Phase 2: Info de fin automatique de conversation
export interface AutoEndInfo {
  endType: "mutual_goodbye" | "prospect_ending" | "user_ending";
  redirectUrl: string | null;
  timestamp: Date;
}

export interface UseVoiceSessionReturn {
  // State
  isConnected: boolean;
  isConnecting: boolean;
  isProspectThinking: boolean;
  messages: VoiceMessage[];
  currentJauge: number;
  currentMood: string;
  conversionPossible: boolean;
  feedback: ProspectResponse["feedback"] | null;
  error: string | null;

  // V2 Mechanics
  activeReversal: ActiveReversal | null;
  activeEvent: ActiveEvent | null;
  dismissReversal: () => void;
  dismissEvent: () => void;

  // Phase 2: Fin automatique de conversation
  autoEndInfo: AutoEndInfo | null;

  // Actions
  connect: () => void;
  disconnect: () => void;
  sendMessage: (text: string, audioBase64?: string) => void;
  endSession: () => void;
}

export function useVoiceSession({
  sessionId,
  onSessionEnded,
}: UseVoiceSessionOptions): UseVoiceSessionReturn {
  // Connection state
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isProspectThinking, setIsProspectThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Session state
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [currentJauge, setCurrentJauge] = useState(50);
  const [currentMood, setCurrentMood] = useState("neutral");
  const [conversionPossible, setConversionPossible] = useState(false);
  const [feedback, setFeedback] = useState<ProspectResponse["feedback"] | null>(null);

  // V2 Mechanics state
  const [activeReversal, setActiveReversal] = useState<ActiveReversal | null>(null);
  const [activeEvent, setActiveEvent] = useState<ActiveEvent | null>(null);

  // Phase 2: Fin automatique de conversation
  const [autoEndInfo, setAutoEndInfo] = useState<AutoEndInfo | null>(null);

  // WebSocket ref
  const wsRef = useRef<VoiceWebSocket | null>(null);

  // Get token from localStorage
  const getToken = useCallback(() => {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }, []);

  // Handle connected
  const handleConnected = useCallback(
    (data: { session_id: number; jauge: number; mood: string }) => {
      console.log("[useVoiceSession] Connected:", data);
      setIsConnected(true);
      setIsConnecting(false);
      setCurrentJauge(data.jauge);
      setCurrentMood(data.mood);
      setError(null);
    },
    []
  );

  // Handle prospect thinking
  const handleProspectThinking = useCallback(() => {
    setIsProspectThinking(true);
  }, []);

  // Handle prospect response
  const handleProspectResponse = useCallback((response: ProspectResponse) => {
    console.log("[useVoiceSession] Prospect response:", response);
    setIsProspectThinking(false);

    // Add message
    const message: VoiceMessage = {
      id: `prospect-${Date.now()}`,
      role: "prospect",
      text: response.text,
      audioBase64: response.audio_base64,
      mood: response.mood,
      jaugeDelta: response.jauge_delta,
      behavioralCue: response.behavioral_cue,
      isEvent: response.is_event,
      eventType: response.event_type,
      timestamp: new Date(response.timestamp),
    };
    setMessages((prev) => [...prev, message]);

    // Update state
    if (response.jauge >= 0) {
      setCurrentJauge(response.jauge);
    }
    setCurrentMood(response.mood);
    setConversionPossible(response.conversion_possible);
    setFeedback(response.feedback || null);

    // Phase 2: Détection fin de conversation automatique
    if (response.session_ended && response.end_type) {
      console.log("[useVoiceSession] Session auto-ended:", response.end_type);
      setAutoEndInfo({
        endType: response.end_type,
        redirectUrl: response.redirect_url || null,
        timestamp: new Date(),
      });
    }
  }, []);

  // Handle jauge update
  const handleJaugeUpdate = useCallback((update: JaugeUpdate) => {
    console.log("[useVoiceSession] Jauge update:", update);
    setCurrentJauge(update.jauge);
    setCurrentMood(update.mood);
  }, []);

  // Handle reversal
  const handleReversal = useCallback(
    (data: { type: string; message: string; jauge_drop?: number }) => {
      console.log("[useVoiceSession] Reversal:", data);
      setActiveReversal({
        type: data.type,
        message: data.message,
        jaugeDrop: data.jauge_drop,
        timestamp: new Date(),
      });
    },
    []
  );

  // Handle event
  const handleEvent = useCallback(
    (data: { event_type: string; message: string; test?: string }) => {
      console.log("[useVoiceSession] Event:", data);
      setActiveEvent({
        type: data.event_type,
        message: data.message,
        testDescription: data.test,
        timestamp: new Date(),
      });
    },
    []
  );

  // Dismiss reversal
  const dismissReversal = useCallback(() => {
    setActiveReversal(null);
  }, []);

  // Dismiss event
  const dismissEvent = useCallback(() => {
    setActiveEvent(null);
  }, []);

  // Handle session ended
  const handleSessionEnded = useCallback(
    (data: SessionEnded) => {
      console.log("[useVoiceSession] Session ended:", data);
      setIsConnected(false);
      onSessionEnded?.(data.evaluation);
    },
    [onSessionEnded]
  );

  // Handle error
  const handleError = useCallback((message: string) => {
    console.error("[useVoiceSession] Error:", message);
    setError(message);
    setIsProspectThinking(false);
  }, []);

  // Handle disconnect
  const handleDisconnect = useCallback(() => {
    console.log("[useVoiceSession] Disconnected");
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  // Handle reconnecting
  const handleReconnecting = useCallback((attempt: number) => {
    console.log("[useVoiceSession] Reconnecting, attempt:", attempt);
    setIsConnecting(true);
  }, []);

  // Connect
  const connect = useCallback(() => {
    const token = getToken();
    if (!token) {
      setError("Not authenticated");
      return;
    }

    if (wsRef.current?.isConnected()) {
      console.log("[useVoiceSession] Already connected");
      return;
    }

    setIsConnecting(true);
    setError(null);

    wsRef.current = new VoiceWebSocket(sessionId, token, {
      onConnected: handleConnected,
      onProspectThinking: handleProspectThinking,
      onProspectResponse: handleProspectResponse,
      onJaugeUpdate: handleJaugeUpdate,
      onReversal: handleReversal,
      onEvent: handleEvent,
      onSessionEnded: handleSessionEnded,
      onError: handleError,
      onDisconnect: handleDisconnect,
      onReconnecting: handleReconnecting,
    });

    wsRef.current.connect();
  }, [
    sessionId,
    getToken,
    handleConnected,
    handleProspectThinking,
    handleProspectResponse,
    handleJaugeUpdate,
    handleReversal,
    handleEvent,
    handleSessionEnded,
    handleError,
    handleDisconnect,
    handleReconnecting,
  ]);

  // Disconnect
  const disconnect = useCallback(() => {
    wsRef.current?.disconnect();
    wsRef.current = null;
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  // Send message
  const sendMessage = useCallback((text: string, audioBase64?: string) => {
    if (!wsRef.current?.isConnected()) {
      setError("Not connected");
      return;
    }

    // Add user message immediately
    const message: VoiceMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text,
      audioBase64,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, message]);

    // Send to server
    wsRef.current.sendMessage(text, audioBase64);
  }, []);

  // End session
  const endSession = useCallback(() => {
    wsRef.current?.endSession();
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.disconnect();
    };
  }, []);

  return {
    isConnected,
    isConnecting,
    isProspectThinking,
    messages,
    currentJauge,
    currentMood,
    conversionPossible,
    feedback,
    error,

    // V2 Mechanics
    activeReversal,
    activeEvent,
    dismissReversal,
    dismissEvent,

    // Phase 2: Fin automatique de conversation
    autoEndInfo,

    // Actions
    connect,
    disconnect,
    sendMessage,
    endSession,
  };
}
