"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter, useParams } from "next/navigation";
import {
  ArrowLeft,
  Send,
  Loader2,
  CheckCircle2,
  XCircle,
  Target,
  MessageSquare,
  User,
  Bot,
  Trophy,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { trainingV3API } from "@/lib/api";
import type {
  V3SessionStartResponse,
  V3MessageResponse,
  V3SessionEndResponse,
  V3JaugeState,
  V3ModuleData,
  V3PlaybookData,
} from "@/types";

interface Message {
  id: string;
  role: "user" | "prospect";
  text: string;
  evaluation?: {
    detected?: Array<{ id: string; label: string; quality: string }>;
  };
  timestamp: Date;
}

// Mood colors
const moodColors: Record<string, string> = {
  hostile: "text-red-500",
  aggressive: "text-red-400",
  skeptical: "text-orange-400",
  neutral: "text-gray-400",
  interested: "text-green-400",
  ready: "text-green-500",
  ready_to_buy: "text-green-500",
};

export default function V3SessionPage() {
  const router = useRouter();
  const params = useParams();
  const sessionId = params.id as string;

  // Session state
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<V3SessionStartResponse | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [sending, setSending] = useState(false);
  const [jauge, setJauge] = useState<V3JaugeState | null>(null);
  const [detectedElements, setDetectedElements] = useState<string[]>([]);

  // End session state
  const [sessionEnded, setSessionEnded] = useState(false);
  const [endResult, setEndResult] = useState<V3SessionEndResponse | null>(null);
  const [ending, setEnding] = useState(false);

  // UI state
  const [showChecklist, setShowChecklist] = useState(true);
  const [showPlaybook, setShowPlaybook] = useState(false);

  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Load session data on mount
  useEffect(() => {
    loadSession();
  }, [sessionId]);

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const loadSession = async () => {
    try {
      // Get session status to retrieve stored data
      const response = await trainingV3API.getSession(sessionId);

      if (response.data) {
        // Session exists, get initial state
        setJauge(response.data.jauge);
        setDetectedElements(response.data.module_progress?.detected || []);

        // For now, we need to store session data in localStorage or make another call
        // Since we just created the session, redirect to the session with data
        const storedData = sessionStorage.getItem(`v3_session_${sessionId}`);
        if (storedData) {
          const parsed = JSON.parse(storedData);
          setSessionData(parsed);
          setMessages([{
            id: "1",
            role: "prospect",
            text: parsed.first_message,
            timestamp: new Date(),
          }]);
          setJauge(parsed.jauge);
        }
      }
    } catch (err) {
      console.error("Error loading session:", err);
      setError("Session introuvable");
    } finally {
      setLoading(false);
    }
  };

  // Store session data when navigating from training page
  useEffect(() => {
    // Check if we have session data in URL state
    const storedData = sessionStorage.getItem(`v3_session_${sessionId}`);
    if (storedData && !sessionData) {
      const parsed = JSON.parse(storedData);
      setSessionData(parsed);
      setMessages([{
        id: "1",
        role: "prospect",
        text: parsed.first_message,
        timestamp: new Date(),
      }]);
      setJauge(parsed.jauge);
      setLoading(false);
    }
  }, [sessionId, sessionData]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || sending) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      text: inputText.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText("");
    setSending(true);

    try {
      const response = await trainingV3API.sendMessage(sessionId, userMessage.text);
      const data = response.data as V3MessageResponse;

      if (data.success) {
        // Update jauge
        if (data.jauge) {
          setJauge(data.jauge);
        }

        // Update detected elements
        if (data.evaluation?.detected) {
          const newDetected = data.evaluation.detected.map(d => d.id);
          setDetectedElements(prev => [...new Set([...prev, ...newDetected])]);
        }

        // Add prospect response
        if (data.prospect_response) {
          const prospectMessage: Message = {
            id: (Date.now() + 1).toString(),
            role: "prospect",
            text: data.prospect_response,
            evaluation: data.evaluation,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, prospectMessage]);
        }

        // Check if session auto-completed
        if (data.session_complete) {
          handleEndSession(true);
        }
      }
    } catch (err) {
      console.error("Error sending message:", err);
      setError("Erreur lors de l'envoi du message");
    } finally {
      setSending(false);
    }
  };

  const handleEndSession = async (closingAchieved: boolean = false) => {
    if (ending) return;
    setEnding(true);

    try {
      const response = await trainingV3API.endSession(sessionId, closingAchieved);
      const data = response.data as V3SessionEndResponse;

      if (data.success) {
        setEndResult(data);
        setSessionEnded(true);
      }
    } catch (err) {
      console.error("Error ending session:", err);
      setError("Erreur lors de la fin de session");
    } finally {
      setEnding(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-400" />
      </div>
    );
  }

  if (error && !sessionData) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <Card className="max-w-md">
          <CardContent className="pt-6 text-center">
            <AlertTriangle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
            <p className="text-lg font-medium mb-2">Erreur</p>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={() => router.push("/training")}>
              Retour à l&apos;entraînement
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Session ended - show results
  if (sessionEnded && endResult) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-8 pb-12">
        <div className="max-w-3xl mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            {/* Result Header */}
            <Card className="mb-6">
              <CardContent className="pt-6 text-center">
                <div className="text-6xl mb-4">{endResult.final_result.emoji}</div>
                <h1 className="text-2xl font-bold mb-2">{endResult.final_result.label}</h1>
                <p className="text-muted-foreground">{endResult.final_result.message}</p>
              </CardContent>
            </Card>

            {/* Score */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-500" />
                  Score: {endResult.evaluation.score}/100
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Progress value={endResult.evaluation.score} className="h-3 mb-4" />
                <p className="text-sm text-muted-foreground">
                  Niveau: {endResult.evaluation.level} - {endResult.evaluation.level_description}
                </p>
              </CardContent>
            </Card>

            {/* Elements Detected */}
            <div className="grid gap-6 md:grid-cols-2 mb-6">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                    Éléments détectés ({endResult.evaluation.elements_detected.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {endResult.evaluation.elements_detected.map((el) => (
                      <div key={el.id} className="flex items-center gap-2">
                        <Badge variant="outline" className="bg-green-500/10 text-green-500">
                          {el.label}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{el.quality}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-red-500" />
                    Éléments manquants ({endResult.evaluation.elements_missing.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {endResult.evaluation.elements_missing.map((el) => (
                      <div key={el.id} className="flex flex-col">
                        <Badge variant="outline" className="bg-red-500/10 text-red-500 w-fit">
                          {el.label}
                        </Badge>
                        <span className="text-xs text-muted-foreground mt-1">{el.description}</span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Coaching */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="text-base">Conseil de coaching</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{endResult.final_result.coaching}</p>
                <div className="mt-4 p-3 bg-primary-500/10 rounded-lg">
                  <p className="text-sm font-medium text-primary-400">
                    Prochaine étape: {endResult.final_result.next_focus}
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Actions */}
            <div className="flex gap-4 justify-center">
              <Button variant="outline" onClick={() => router.push("/training")}>
                <ArrowLeft className="h-4 w-4 mr-2" />
                Retour
              </Button>
              <Button onClick={() => window.location.reload()}>
                Recommencer
              </Button>
            </div>
          </motion.div>
        </div>
      </div>
    );
  }

  const moduleData = sessionData?.module_data as V3ModuleData | undefined;
  const playbookData = sessionData?.playbook_data as V3PlaybookData | undefined;

  return (
    <div className="min-h-screen bg-gradient-dark flex flex-col">
      {/* Header */}
      <div className="border-b border-border/50 bg-background/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => router.push("/training")}>
                <ArrowLeft className="h-4 w-4" />
              </Button>
              <div>
                <h1 className="font-semibold">
                  {playbookData?.product?.name || "Session"} × {moduleData?.name || "Module"}
                </h1>
                <p className="text-xs text-muted-foreground">
                  Session {sessionId}
                </p>
              </div>
            </div>

            {/* Jauge */}
            {jauge && (
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-medium">{jauge.value}%</div>
                  <div className={cn("text-xs", moodColors[jauge.mood] || "text-gray-400")}>
                    {jauge.mood}
                  </div>
                </div>
                <div className="w-24">
                  <Progress value={jauge.value} className="h-2" />
                </div>
              </div>
            )}

            <Button
              variant="destructive"
              size="sm"
              onClick={() => handleEndSession(false)}
              disabled={ending}
            >
              {ending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Terminer"}
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Sidebar - Checklist & Playbook */}
        <div className="w-80 border-r border-border/50 hidden lg:block">
          <div className="p-4 space-y-4">
            {/* Module Checklist */}
            <Card>
              <CardHeader
                className="pb-2 cursor-pointer"
                onClick={() => setShowChecklist(!showChecklist)}
              >
                <CardTitle className="text-sm flex items-center justify-between">
                  <span className="flex items-center gap-2">
                    <Target className="h-4 w-4 text-primary-400" />
                    {moduleData?.name || "Checklist"}
                  </span>
                  {showChecklist ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                </CardTitle>
              </CardHeader>
              <AnimatePresence>
                {showChecklist && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                  >
                    <CardContent className="pt-0">
                      <div className="space-y-2">
                        {moduleData?.checklist?.map((item) => {
                          const isDetected = detectedElements.includes(item.id);
                          return (
                            <div
                              key={item.id}
                              className={cn(
                                "flex items-center gap-2 p-2 rounded text-sm",
                                isDetected ? "bg-green-500/10" : "bg-muted/50"
                              )}
                            >
                              {isDetected ? (
                                <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0" />
                              ) : (
                                <div className="h-4 w-4 rounded-full border border-muted-foreground/50 shrink-0" />
                              )}
                              <span className={isDetected ? "text-green-500" : "text-muted-foreground"}>
                                {item.label}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </motion.div>
                )}
              </AnimatePresence>
            </Card>

            {/* Playbook Info */}
            {playbookData && (
              <Card>
                <CardHeader
                  className="pb-2 cursor-pointer"
                  onClick={() => setShowPlaybook(!showPlaybook)}
                >
                  <CardTitle className="text-sm flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <MessageSquare className="h-4 w-4 text-primary-400" />
                      Aide-mémoire
                    </span>
                    {showPlaybook ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </CardTitle>
                </CardHeader>
                <AnimatePresence>
                  {showPlaybook && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                    >
                      <CardContent className="pt-0 space-y-3">
                        {playbookData.pitch?.hook_30s && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">Accroche</p>
                            <p className="text-sm">{playbookData.pitch.hook_30s}</p>
                          </div>
                        )}
                        {playbookData.pitch?.discovery_questions?.length > 0 && (
                          <div>
                            <p className="text-xs font-medium text-muted-foreground mb-1">Questions découverte</p>
                            <ul className="text-sm space-y-1">
                              {playbookData.pitch.discovery_questions.slice(0, 3).map((q, i) => (
                                <li key={i} className="text-muted-foreground">• {q}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </CardContent>
                    </motion.div>
                  )}
                </AnimatePresence>
              </Card>
            )}
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 flex flex-col">
          <ScrollArea ref={scrollRef} className="flex-1 p-4">
            <div className="max-w-2xl mx-auto space-y-4">
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    "flex gap-3",
                    message.role === "user" ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === "prospect" && (
                    <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center shrink-0">
                      <Bot className="h-4 w-4 text-primary-400" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "max-w-[80%] rounded-lg px-4 py-2",
                      message.role === "user"
                        ? "bg-primary-500 text-white"
                        : "bg-muted"
                    )}
                  >
                    <p className="text-sm">{message.text}</p>
                    {message.evaluation?.detected && message.evaluation.detected.length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1">
                        {message.evaluation.detected.map((d) => (
                          <Badge
                            key={d.id}
                            variant="outline"
                            className="text-xs bg-green-500/10 text-green-500"
                          >
                            ✓ {d.label}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                  {message.role === "user" && (
                    <div className="w-8 h-8 rounded-full bg-primary-500 flex items-center justify-center shrink-0">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  )}
                </motion.div>
              ))}

              {sending && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex gap-3"
                >
                  <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center">
                    <Bot className="h-4 w-4 text-primary-400" />
                  </div>
                  <div className="bg-muted rounded-lg px-4 py-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                  </div>
                </motion.div>
              )}
            </div>
          </ScrollArea>

          {/* Input */}
          <div className="border-t border-border/50 p-4">
            <div className="max-w-2xl mx-auto flex gap-2">
              <Textarea
                ref={inputRef}
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Écrivez votre message..."
                className="min-h-[44px] max-h-32 resize-none"
                disabled={sending || sessionEnded}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!inputText.trim() || sending || sessionEnded}
                className="shrink-0"
              >
                {sending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
