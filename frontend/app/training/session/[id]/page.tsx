"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter, useSearchParams, useParams } from "next/navigation";
import {
  ArrowLeft,
  Send,
  Loader2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Lightbulb,
  Zap,
  MessageSquare,
  Mic,
  Wifi,
  WifiOff,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { JaugeEmotionnelle } from "@/components/training/JaugeEmotionnelle";
import { AudioRecorder } from "@/components/training/AudioRecorder";
import { AudioPlayer } from "@/components/training/AudioPlayer";
import { PremiumModal } from "@/components/ui/premium-modal";
import { voiceAPI } from "@/lib/api";
import { useVoiceSession, VoiceMessage } from "@/hooks/useVoiceSession";
import type { SessionEnded } from "@/lib/websocket";
import type {
  DifficultyLevel,
  MoodState,
  VoiceSessionStartResponse,
  VoiceSessionSummary,
  DetectedPattern,
} from "@/types";

interface Message {
  id: string;
  role: "user" | "prospect";
  text: string;
  audioBase64?: string;
  mood?: MoodState;
  jauge?: number;
  jaugeDelta?: number;
  behavioralCue?: string;
  isEvent?: boolean;
  eventType?: string;
  patterns?: DetectedPattern[];
  timestamp: Date;
}

export default function TrainingSessionPage() {
  const router = useRouter();
  const params = useParams();
  const searchParams = useSearchParams();

  const sessionId = params.id as string;
  const level = (searchParams.get("level") as DifficultyLevel) || "easy";

  const [session, setSession] = useState<VoiceSessionStartResponse | null>(null);
  const [localMessages, setLocalMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [isStarting, setIsStarting] = useState(true);
  const [localError, setLocalError] = useState<string | null>(null);
  const [jaugeDelta, setJaugeDelta] = useState(0);
  const [hint, setHint] = useState<string | null>(null);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [summary, setSummary] = useState<VoiceSessionSummary | null>(null);
  const [inputMode, setInputMode] = useState<"text" | "voice">("text");
  const [showPremiumModal, setShowPremiumModal] = useState(false);
  const [eventNotification, setEventNotification] = useState<{type: string; message: string} | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Handle session ended from WebSocket
  const handleSessionEnded = useCallback((evaluation: SessionEnded["evaluation"]) => {
    setSessionComplete(true);
    setSummary({
      session_id: session?.session_id || 0,
      level: level,
      duration_seconds: 0,
      final_jauge: evaluation.final_jauge,
      starting_jauge: 50,
      jauge_progression: evaluation.jauge_progression,
      conversion_achieved: evaluation.converted,
      detected_patterns: [],
      hidden_objections_discovered: 0,
      hidden_objections_total: 0,
      events_handled: 0,
      reversals_recovered: 0,
      strengths: evaluation.points_forts,
      improvements: evaluation.axes_amelioration,
      overall_feedback: evaluation.conseil_principal,
    });
  }, [session?.session_id, level]);

  // WebSocket hook - only active when we have a session
  const {
    isConnected,
    isConnecting,
    isProspectThinking,
    messages: wsMessages,
    currentJauge,
    currentMood,
    conversionPossible,
    feedback,
    error: wsError,
    connect,
    disconnect,
    sendMessage: wsSendMessage,
    endSession: wsEndSession,
  } = useVoiceSession({
    sessionId: session?.session_id || 0,
    onSessionEnded: handleSessionEnded,
  });

  // Convert WebSocket messages to local message format
  useEffect(() => {
    if (wsMessages.length > 0) {
      const convertedMessages: Message[] = wsMessages.map((msg: VoiceMessage) => ({
        id: msg.id,
        role: msg.role,
        text: msg.text,
        audioBase64: msg.audioBase64,
        mood: msg.mood as MoodState | undefined,
        jauge: undefined,
        jaugeDelta: msg.jaugeDelta,
        behavioralCue: msg.behavioralCue,
        isEvent: msg.isEvent,
        eventType: msg.eventType,
        patterns: [],
        timestamp: msg.timestamp,
      }));
      setLocalMessages(convertedMessages);

      // Update jaugeDelta from last prospect message
      const lastProspect = wsMessages.filter(m => m.role === "prospect").pop();
      if (lastProspect?.jaugeDelta !== undefined) {
        setJaugeDelta(lastProspect.jaugeDelta);
      }
    }
  }, [wsMessages]);

  // Combine errors
  const error = localError || wsError;

  // Start HTTP session, then connect WebSocket
  const startNewSession = useCallback(async () => {
    setIsStarting(true);
    setLocalError(null);

    try {
      const response = await voiceAPI.startSession({ level });
      const data = response.data;

      setSession(data);

      // Add initial prospect message to local state
      const initialMessage: Message = {
        id: crypto.randomUUID(),
        role: "prospect",
        text: data.prospect_message,
        audioBase64: data.prospect_audio_base64,
        mood: data.mood,
        jauge: data.jauge,
        timestamp: new Date(),
      };
      setLocalMessages([initialMessage]);

      // Update URL with session ID
      window.history.replaceState(
        null,
        "",
        `/training/session/${data.session_id}?level=${level}`
      );
    } catch (err: unknown) {
      console.error("Error starting session:", err);

      // Handle trial expired (402)
      const axiosError = err as { response?: { status: number; data?: { code?: string } } };
      if (axiosError.response?.status === 402 && axiosError.response?.data?.code === "TRIAL_EXPIRED") {
        setShowPremiumModal(true);
        setLocalError("Votre essai gratuit est terminé. Passez à Premium pour continuer.");
      } else {
        setLocalError("Impossible de démarrer la session. Veuillez réessayer.");
      }
    } finally {
      setIsStarting(false);
    }
  }, [level]);

  // Connect WebSocket when session is ready
  useEffect(() => {
    if (session?.session_id && !isConnected && !isConnecting) {
      connect();
    }
  }, [session?.session_id, isConnected, isConnecting, connect]);

  // Disconnect WebSocket on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Start session on mount
  useEffect(() => {
    if (sessionId === "new") {
      startNewSession();
    }
  }, [sessionId, startNewSession]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [localMessages]);

  // Send message via WebSocket
  const sendMessage = useCallback((text: string, audioBase64?: string) => {
    if ((!text.trim() && !audioBase64) || isProspectThinking || !isConnected) return;

    setLocalError(null);
    setHint(null);
    setInputText("");

    // Send via WebSocket (hook will add user message automatically)
    wsSendMessage(text || "", audioBase64);
  }, [isProspectThinking, isConnected, wsSendMessage]);

  // End session via WebSocket
  const endSession = useCallback(() => {
    if (!isConnected) return;
    wsEndSession();
  }, [isConnected, wsEndSession]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(inputText);
    }
  };

  const handleRecordingComplete = (audioBase64: string) => {
    sendMessage("", audioBase64);
  };

  // Loading state (starting session or connecting WebSocket)
  if (isStarting || (session && isConnecting)) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="text-center"
        >
          <Loader2 className="h-12 w-12 animate-spin text-primary-400 mx-auto mb-4" />
          <p className="text-muted-foreground">
            {isConnecting ? "Connexion en temps réel..." : "Préparation de votre session..."}
          </p>
        </motion.div>
      </div>
    );
  }

  // Error state
  if (error && !session) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-2xl p-8 max-w-md text-center"
        >
          <AlertTriangle className="h-12 w-12 text-red-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Erreur</h2>
          <p className="text-muted-foreground mb-6">{error}</p>
          <div className="flex gap-3 justify-center">
            <Button variant="outline" onClick={() => router.push("/learn")}>
              Retour
            </Button>
            <Button onClick={startNewSession}>Réessayer</Button>
          </div>
        </motion.div>
      </div>
    );
  }

  // Summary view
  if (summary) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
        <div className="max-w-3xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="glass rounded-2xl p-8"
          >
            <div className="text-center mb-8">
              {summary.conversion_achieved ? (
                <>
                  <CheckCircle2 className="h-16 w-16 text-green-400 mx-auto mb-4" />
                  <h1 className="text-2xl font-bold gradient-text mb-2">
                    Conversion Réussie !
                  </h1>
                </>
              ) : (
                <>
                  <XCircle className="h-16 w-16 text-orange-400 mx-auto mb-4" />
                  <h1 className="text-2xl font-bold mb-2">Session Terminée</h1>
                </>
              )}
              <p className="text-muted-foreground">
                Niveau {level} - {Math.floor(summary.duration_seconds / 60)}min{" "}
                {summary.duration_seconds % 60}s
              </p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-4 mb-8">
              <div className="text-center p-4 rounded-xl bg-white/5">
                <p className="text-2xl font-bold text-primary-400">
                  {summary.final_jauge}
                </p>
                <p className="text-sm text-muted-foreground">Jauge Finale</p>
              </div>
              <div className="text-center p-4 rounded-xl bg-white/5">
                <p
                  className={cn(
                    "text-2xl font-bold",
                    summary.jauge_progression >= 0
                      ? "text-green-400"
                      : "text-red-400"
                  )}
                >
                  {summary.jauge_progression >= 0 ? "+" : ""}
                  {summary.jauge_progression}
                </p>
                <p className="text-sm text-muted-foreground">Progression</p>
              </div>
              <div className="text-center p-4 rounded-xl bg-white/5">
                <p className="text-2xl font-bold text-yellow-400">
                  {summary.detected_patterns?.length || 0}
                </p>
                <p className="text-sm text-muted-foreground">Patterns</p>
              </div>
            </div>

            {/* Strengths & Improvements */}
            <div className="grid md:grid-cols-2 gap-6 mb-8">
              <div>
                <h3 className="font-semibold text-green-400 mb-3 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5" />
                  Points Forts
                </h3>
                <ul className="space-y-2">
                  {summary.strengths.map((s, i) => (
                    <li
                      key={i}
                      className="text-sm text-muted-foreground flex items-start gap-2"
                    >
                      <span className="text-green-400 mt-1">•</span>
                      {s}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-orange-400 mb-3 flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Axes d&apos;Amélioration
                </h3>
                <ul className="space-y-2">
                  {summary.improvements.map((i, idx) => (
                    <li
                      key={idx}
                      className="text-sm text-muted-foreground flex items-start gap-2"
                    >
                      <span className="text-orange-400 mt-1">•</span>
                      {i}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {/* Feedback */}
            <div className="p-4 rounded-xl bg-primary-500/10 border border-primary-500/20 mb-6">
              <p className="text-sm">{summary.overall_feedback}</p>
            </div>

            {/* Actions */}
            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => router.push("/learn")}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Retour
              </Button>
              <Button onClick={startNewSession}>Nouvelle Session</Button>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  // Main session view
  return (
    <TooltipProvider>
      <div className="min-h-screen bg-gradient-dark flex flex-col">
        {/* Header */}
        <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/learn")}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Quitter
            </Button>

            <div className="flex items-center gap-3">
              {/* Connection status */}
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className={cn(
                    "flex items-center gap-1.5 px-2 py-1 rounded-full text-xs",
                    isConnected
                      ? "bg-green-500/20 text-green-400"
                      : "bg-red-500/20 text-red-400"
                  )}>
                    {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                    {isConnected ? "Connecté" : "Déconnecté"}
                  </div>
                </TooltipTrigger>
                <TooltipContent>
                  {isConnected ? "Connexion temps réel active" : "Reconnexion en cours..."}
                </TooltipContent>
              </Tooltip>

              {/* Conversion possible indicator */}
              {conversionPossible && (
                <Badge className="bg-green-500/20 text-green-400 animate-pulse">
                  Conversion possible !
                </Badge>
              )}

              <Badge
                className={cn(
                  level === "easy" && "bg-green-500/20 text-green-400",
                  level === "medium" && "bg-yellow-500/20 text-yellow-400",
                  level === "expert" && "bg-red-500/20 text-red-400"
                )}
              >
                {level === "easy" && "Facile"}
                {level === "medium" && "Moyen"}
                {level === "expert" && "Expert"}
              </Badge>
            </div>

            <Button variant="outline" size="sm" onClick={endSession}>
              Terminer
            </Button>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 pt-20 pb-40 flex">
          <div className="flex-1 max-w-4xl mx-auto px-4 flex flex-col">
            {/* Jauge sidebar for desktop */}
            <div className="hidden lg:block fixed right-8 top-24 w-64">
              <JaugeEmotionnelle
                value={currentJauge}
                delta={jaugeDelta}
                mood={currentMood as MoodState}
                visible={session?.config.show_jauge ?? true}
                threshold={session?.config.conversion_threshold ?? 80}
              />

              {/* Real-time feedback */}
              <AnimatePresence>
                {feedback && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="mt-4 p-3 rounded-xl bg-white/5 border border-white/10"
                  >
                    {feedback.positive_actions.length > 0 && (
                      <div className="mb-2">
                        <p className="text-xs text-green-400 font-medium mb-1">Bien joué :</p>
                        {feedback.positive_actions.map((action, i) => (
                          <p key={i} className="text-xs text-muted-foreground">• {action}</p>
                        ))}
                      </div>
                    )}
                    {feedback.tips.length > 0 && (
                      <div>
                        <p className="text-xs text-yellow-400 font-medium mb-1">Conseil :</p>
                        {feedback.tips.map((tip, i) => (
                          <p key={i} className="text-xs text-muted-foreground">• {tip}</p>
                        ))}
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Hint */}
              <AnimatePresence>
                {hint && session?.config.hints_enabled && (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className="mt-4 p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20"
                  >
                    <div className="flex items-start gap-2">
                      <Lightbulb className="h-4 w-4 text-yellow-400 mt-0.5" />
                      <p className="text-sm text-yellow-200">{hint}</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Mobile jauge */}
            <div className="lg:hidden mb-4">
              <JaugeEmotionnelle
                value={currentJauge}
                delta={jaugeDelta}
                mood={currentMood as MoodState}
                visible={session?.config.show_jauge ?? true}
                threshold={session?.config.conversion_threshold ?? 80}
              />
            </div>

            {/* Messages */}
            <ScrollArea ref={scrollRef} className="flex-1 pr-4">
              <div className="space-y-4 pb-4">
                {localMessages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={cn(
                      "flex",
                      message.role === "user" ? "justify-end" : "justify-start"
                    )}
                  >
                    <div
                      className={cn(
                        "max-w-[80%] rounded-2xl p-4",
                        message.role === "user"
                          ? "bg-primary-500/20 border border-primary-500/30"
                          : "glass"
                      )}
                    >
                      {/* Behavioral cue */}
                      {message.behavioralCue && (
                        <p className="text-xs text-muted-foreground italic mb-2">
                          {message.behavioralCue}
                        </p>
                      )}

                      {/* Message text */}
                      <p className="text-sm">{message.text}</p>

                      {/* Audio player */}
                      {message.audioBase64 && (
                        <div className="mt-3">
                          <AudioPlayer
                            audioBase64={message.audioBase64}
                            autoPlay={message.role === "prospect"}
                          />
                        </div>
                      )}

                      {/* Detected patterns */}
                      {message.patterns && message.patterns.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1">
                          {message.patterns.map((pattern, i) => (
                            <Tooltip key={i}>
                              <TooltipTrigger>
                                <Badge
                                  className={cn(
                                    "text-xs",
                                    pattern.type === "positive"
                                      ? "bg-green-500/20 text-green-400"
                                      : "bg-red-500/20 text-red-400"
                                  )}
                                >
                                  {pattern.type === "positive" ? "+" : ""}
                                  {pattern.points}
                                </Badge>
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{pattern.action}</p>
                                {pattern.description && (
                                  <p className="text-xs text-muted-foreground">
                                    {pattern.description}
                                  </p>
                                )}
                              </TooltipContent>
                            </Tooltip>
                          ))}
                        </div>
                      )}
                    </div>
                  </motion.div>
                ))}

                {isProspectThinking && (
                  <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="flex justify-start"
                  >
                    <div className="glass rounded-2xl p-4">
                      <div className="flex items-center gap-2">
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="text-sm text-muted-foreground">
                          Le prospect réfléchit...
                        </span>
                      </div>
                    </div>
                  </motion.div>
                )}
              </div>
            </ScrollArea>
          </div>
        </main>

        {/* Input area */}
        <div className="fixed bottom-0 left-0 right-0 glass border-t border-white/10 p-4">
          <div className="max-w-4xl mx-auto">
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="flex items-end gap-3">
              {/* Mode toggle */}
              <div className="flex gap-1 p-1 rounded-lg bg-white/5">
                <Button
                  variant={inputMode === "text" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setInputMode("text")}
                  className="h-8"
                >
                  <MessageSquare className="h-4 w-4" />
                </Button>
                <Button
                  variant={inputMode === "voice" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setInputMode("voice")}
                  className="h-8"
                >
                  <Mic className="h-4 w-4" />
                </Button>
              </div>

              {inputMode === "text" ? (
                <>
                  <Textarea
                    ref={inputRef}
                    value={inputText}
                    onChange={(e) => setInputText(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={isConnected ? "Votre réponse au prospect..." : "Connexion en cours..."}
                    disabled={isProspectThinking || sessionComplete || !isConnected}
                    className="flex-1 min-h-[48px] max-h-32 resize-none"
                  />
                  <Button
                    onClick={() => sendMessage(inputText)}
                    disabled={!inputText.trim() || isProspectThinking || sessionComplete || !isConnected}
                    className="h-12 w-12 rounded-full bg-gradient-primary"
                  >
                    <Send className="h-5 w-5" />
                  </Button>
                </>
              ) : (
                <div className="flex-1 flex justify-center">
                  <AudioRecorder
                    onRecordingComplete={handleRecordingComplete}
                    disabled={isProspectThinking || sessionComplete || !isConnected}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Premium Modal */}
      <PremiumModal
        open={showPremiumModal}
        onOpenChange={setShowPremiumModal}
      />
    </TooltipProvider>
  );
}
