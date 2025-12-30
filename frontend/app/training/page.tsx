"use client";

import { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, X, Trophy, Target, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ChatInterface } from "@/components/training/ChatInterface";
import { ResponseInput } from "@/components/training/ResponseInput";
import { FeedbackPanel } from "@/components/training/FeedbackPanel";
import { ScenarioCard } from "@/components/training/ScenarioCard";
import { ScoreCircle } from "@/components/training/ScoreCircle";
import { useTrainingStore } from "@/store/training-store";
import { useAuthStore } from "@/store/auth-store";
import { formatDuration, generateId } from "@/lib/utils";
import { getScenarios, startTraining, respondTraining, endTraining } from "@/lib/api";
import type { TrainingScenario, ChatMessage, SessionSummary } from "@/types";

type TrainingPhase = "select" | "training" | "summary";

function TrainingPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const championId = searchParams.get("champion");

  const { user } = useAuthStore();

  const [phase, setPhase] = useState<TrainingPhase>("select");
  const [scenarios, setScenarios] = useState<TrainingScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<TrainingScenario | null>(null);
  const [selectedScenarioIndex, setSelectedScenarioIndex] = useState<number>(0);
  const [isTyping, setIsTyping] = useState(false);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(false);
  const [isStartingSession, setIsStartingSession] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionSummary, setSessionSummary] = useState<SessionSummary | null>(null);

  const [currentFeedback, setCurrentFeedback] = useState<{
    strengths: string[];
    improvements: string[];
    suggestions: string[];
    championWouldSay?: string;
  } | null>(null);

  const {
    sessionId,
    messages,
    currentScore,
    elapsedSeconds,
    championName,
    startSession,
    addUserMessage,
    addChampionMessage,
    setTyping,
    updateTimer,
    reset,
  } = useTrainingStore();

  // Load scenarios from API
  useEffect(() => {
    const loadScenarios = async () => {
      if (!championId) return;

      setIsLoadingScenarios(true);
      setError(null);

      try {
        const response = await getScenarios(parseInt(championId), 3);
        setScenarios(response.scenarios);
      } catch (err: unknown) {
        const error = err as { response?: { data?: { detail?: string } } };
        setError(error.response?.data?.detail || "Erreur lors du chargement des scénarios");
        // Fallback to mock scenarios if API fails
        setScenarios([]);
      } finally {
        setIsLoadingScenarios(false);
      }
    };

    loadScenarios();
  }, [championId]);

  // Timer effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (phase === "training") {
      interval = setInterval(() => {
        updateTimer();
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [phase, updateTimer]);

  const handleSelectScenario = (scenario: TrainingScenario, index: number) => {
    setSelectedScenario(scenario);
    setSelectedScenarioIndex(index);
  };

  const handleStartTraining = async () => {
    if (!selectedScenario || !championId) return;

    setIsStartingSession(true);
    setError(null);

    try {
      const response = await startTraining({
        champion_id: parseInt(championId),
        user_id: user?.id?.toString() || "anonymous",
        scenario_index: selectedScenarioIndex,
      });

      // Start session in store
      reset();
      startSession({
        sessionId: response.session_id,
        championId: parseInt(championId),
        championName: response.champion_name,
        scenario: selectedScenario,
        firstMessage: response.first_message,
      });

      setPhase("training");
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || "Erreur lors du démarrage de la session");
    } finally {
      setIsStartingSession(false);
    }
  };

  const handleSendMessage = useCallback(async (content: string) => {
    if (!sessionId) return;

    addUserMessage(content);
    setIsTyping(true);
    setTyping(true);

    try {
      const response = await respondTraining({
        session_id: sessionId,
        user_response: content,
      });

      // Update feedback
      setCurrentFeedback({
        strengths: [],
        improvements: [],
        suggestions: response.suggestions,
        championWouldSay: response.feedback,
      });

      // Add champion response
      addChampionMessage(response.champion_response, response.score, response.feedback);

      // Check if session is complete
      if (response.session_complete) {
        handleEndSession();
      }
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      addChampionMessage(
        "Désolé, une erreur est survenue. Veuillez réessayer.",
        currentScore
      );
      console.error("Training respond error:", error.response?.data?.detail);
    } finally {
      setIsTyping(false);
      setTyping(false);
    }
  }, [sessionId, addUserMessage, addChampionMessage, setTyping, currentScore]);

  const handleEndSession = async () => {
    if (!sessionId) {
      setPhase("summary");
      return;
    }

    try {
      const summary = await endTraining(sessionId);
      setSessionSummary(summary);
    } catch (err) {
      console.error("Error ending session:", err);
    }

    setPhase("summary");
  };

  const handleNewSession = () => {
    reset();
    setSelectedScenario(null);
    setCurrentFeedback(null);
    setSessionSummary(null);
    setPhase("select");
  };

  // Convert store messages to ChatMessage format for ChatInterface
  const chatMessages: ChatMessage[] = messages.map((m) => ({
    id: m.id || generateId(),
    content: m.content,
    timestamp: m.timestamp,
    score: m.score,
    feedback: m.feedback,
    role: m.role === "champion" ? "assistant" : "user",
  }));

  // No champion selected
  if (!championId) {
    return (
      <div className="min-h-[calc(100vh-6rem)] flex items-center justify-center px-4">
        <Card className="glass border-white/10 max-w-md w-full">
          <CardContent className="p-8 text-center">
            <AlertCircle className="h-12 w-12 text-warning-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Aucun champion sélectionné</h2>
            <p className="text-muted-foreground mb-6">
              Vous devez d'abord créer et analyser un champion pour commencer l'entraînement.
            </p>
            <Button
              onClick={() => router.push("/upload")}
              className="bg-gradient-primary hover:opacity-90"
            >
              Créer un champion
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="relative min-h-[calc(100vh-6rem)]">
      {/* Background */}
      <div className="absolute inset-0 gradient-mesh opacity-20" />

      <AnimatePresence mode="wait">
        {/* Scenario Selection Phase */}
        {phase === "select" && (
          <motion.div
            key="select"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="relative mx-auto max-w-6xl px-4 sm:px-6 lg:px-8 py-12"
          >
            <div className="text-center mb-12">
              <h1 className="text-3xl lg:text-4xl font-bold mb-4">
                Choisissez votre <span className="gradient-text">scénario</span>
              </h1>
              <p className="text-muted-foreground max-w-xl mx-auto">
                Sélectionnez un scénario d'entraînement adapté à votre niveau
              </p>
            </div>

            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg flex items-center gap-3 max-w-xl mx-auto"
              >
                <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0" />
                <span className="text-sm text-destructive">{error}</span>
              </motion.div>
            )}

            {isLoadingScenarios ? (
              <div className="flex flex-col items-center justify-center py-12">
                <Loader2 className="h-12 w-12 animate-spin text-primary-500 mb-4" />
                <p className="text-muted-foreground">Génération des scénarios...</p>
              </div>
            ) : scenarios.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">Aucun scénario disponible</p>
                <Button
                  onClick={() => router.push("/upload")}
                  variant="outline"
                  className="mt-4"
                >
                  Créer un champion
                </Button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                  {scenarios.map((scenario, index) => (
                    <ScenarioCard
                      key={scenario.id}
                      scenario={scenario}
                      isSelected={selectedScenario?.id === scenario.id}
                      onClick={() => handleSelectScenario(scenario, index)}
                    />
                  ))}
                </div>

                {selectedScenario && (
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="flex justify-center"
                  >
                    <Button
                      onClick={handleStartTraining}
                      disabled={isStartingSession}
                      size="lg"
                      className="bg-gradient-primary hover:opacity-90 text-white px-12 py-6 text-lg"
                    >
                      {isStartingSession ? (
                        <>
                          <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                          Démarrage...
                        </>
                      ) : (
                        <>
                          <Target className="h-5 w-5 mr-2" />
                          Démarrer l'entraînement
                        </>
                      )}
                    </Button>
                  </motion.div>
                )}
              </>
            )}
          </motion.div>
        )}

        {/* Training Phase */}
        {phase === "training" && (
          <motion.div
            key="training"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="relative h-[calc(100vh-6rem)] flex"
          >
            {/* Main chat area */}
            <div className="flex-1 flex flex-col lg:w-[60%]">
              {/* Top bar */}
              <div className="glass border-b border-white/10 px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <Badge
                      variant="outline"
                      className="border-primary-500/50 text-primary-400"
                    >
                      {selectedScenario?.name}
                    </Badge>
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      {formatDuration(elapsedSeconds)}
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <ScoreCircle score={currentScore} size={48} strokeWidth={4} />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleEndSession}
                      className="text-muted-foreground hover:text-foreground"
                    >
                      <X className="h-4 w-4 mr-1" />
                      Terminer
                    </Button>
                  </div>
                </div>
              </div>

              {/* Chat interface */}
              <ChatInterface
                messages={chatMessages}
                isTyping={isTyping}
              />

              {/* Response input */}
              <ResponseInput
                onSubmit={handleSendMessage}
                isLoading={isTyping}
                placeholder="Répondez au prospect..."
              />
            </div>

            {/* Feedback panel - desktop only */}
            <div className="hidden lg:block w-[40%] border-l border-white/10 bg-black/20">
              <FeedbackPanel
                score={currentScore}
                strengths={currentFeedback?.strengths}
                improvements={currentFeedback?.improvements}
                suggestions={currentFeedback?.suggestions}
                championWouldSay={currentFeedback?.championWouldSay}
              />
            </div>
          </motion.div>
        )}

        {/* Summary Phase */}
        {phase === "summary" && (
          <motion.div
            key="summary"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="relative mx-auto max-w-2xl px-4 sm:px-6 lg:px-8 py-12"
          >
            <Card className="glass border-white/10">
              <CardContent className="p-8 text-center">
                <div className="mb-8">
                  <Trophy className="h-16 w-16 text-yellow-400 mx-auto mb-4" />
                  <h2 className="text-2xl font-bold mb-2">Session terminée!</h2>
                  <p className="text-muted-foreground">
                    Voici le résumé de votre entraînement
                  </p>
                </div>

                <div className="flex justify-center mb-8">
                  <ScoreCircle
                    score={sessionSummary?.overall_score ?? currentScore}
                    size={160}
                    strokeWidth={12}
                  />
                </div>

                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="p-4 rounded-lg bg-white/5">
                    <div className="text-2xl font-bold">
                      {sessionSummary?.total_exchanges ?? messages.length}
                    </div>
                    <div className="text-sm text-muted-foreground">Échanges</div>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5">
                    <div className="text-2xl font-bold">
                      {sessionSummary
                        ? formatDuration(sessionSummary.duration_seconds)
                        : formatDuration(elapsedSeconds)}
                    </div>
                    <div className="text-sm text-muted-foreground">Durée</div>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5">
                    <div className="text-2xl font-bold gradient-text">
                      {selectedScenario?.difficulty === "easy"
                        ? "Facile"
                        : selectedScenario?.difficulty === "medium"
                        ? "Moyen"
                        : "Difficile"}
                    </div>
                    <div className="text-sm text-muted-foreground">Niveau</div>
                  </div>
                </div>

                {/* Summary feedback from API */}
                {sessionSummary && (
                  <div className="text-left mb-8 space-y-4">
                    {sessionSummary.feedback_summary && (
                      <div className="p-4 rounded-lg bg-white/5">
                        <p className="text-sm text-muted-foreground mb-1">Résumé</p>
                        <p className="text-sm">{sessionSummary.feedback_summary}</p>
                      </div>
                    )}

                    {sessionSummary.strengths && sessionSummary.strengths.length > 0 && (
                      <div className="p-4 rounded-lg bg-success-500/10 border border-success-500/20">
                        <p className="text-sm text-success-400 font-medium mb-2">Points forts</p>
                        <ul className="text-sm space-y-1">
                          {sessionSummary.strengths.map((s, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-success-400">✓</span>
                              {s}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {sessionSummary.areas_for_improvement && sessionSummary.areas_for_improvement.length > 0 && (
                      <div className="p-4 rounded-lg bg-warning-500/10 border border-warning-500/20">
                        <p className="text-sm text-warning-400 font-medium mb-2">À améliorer</p>
                        <ul className="text-sm space-y-1">
                          {sessionSummary.areas_for_improvement.map((a, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-warning-400">→</span>
                              {a}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-4">
                  <Button
                    onClick={handleNewSession}
                    variant="outline"
                    className="flex-1"
                  >
                    Nouveau scénario
                  </Button>
                  <Button
                    onClick={() => router.push("/dashboard")}
                    className="flex-1 bg-gradient-primary hover:opacity-90"
                  >
                    Voir le dashboard
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Loading component for Suspense
function TrainingLoading() {
  return (
    <div className="min-h-[calc(100vh-6rem)] flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-4" />
        <p className="text-muted-foreground">Chargement...</p>
      </div>
    </div>
  );
}

// Wrap with Suspense for useSearchParams
export default function TrainingPage() {
  return (
    <Suspense fallback={<TrainingLoading />}>
      <TrainingPageContent />
    </Suspense>
  );
}
