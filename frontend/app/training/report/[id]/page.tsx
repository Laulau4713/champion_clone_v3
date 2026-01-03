"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import {
  Trophy,
  TrendingUp,
  TrendingDown,
  Clock,
  Target,
  CheckCircle2,
  XCircle,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  MessageSquare,
  RotateCcw,
  ArrowRight,
  BookOpen,
  AlertTriangle,
  ThumbsUp,
  ThumbsDown,
  Sparkles,
  User,
  Bot,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { voiceAPI } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { SessionReport, PatternAggregate, ReportMessage } from "@/types";

// ==========================================
// SCORE OVERVIEW COMPONENT
// ==========================================

function ScoreOverview({ report }: { report: SessionReport }) {
  const progressionColor = report.gauge_progression >= 0 ? "text-green-400" : "text-red-400";
  const ProgressIcon = report.gauge_progression >= 0 ? TrendingUp : TrendingDown;

  // Format duration
  const minutes = Math.floor(report.duration_seconds / 60);
  const seconds = report.duration_seconds % 60;
  const durationStr = minutes > 0 ? `${minutes}min ${seconds}s` : `${seconds}s`;

  // Level labels
  const levelLabels: Record<string, string> = {
    easy: "Debutant",
    medium: "Intermediaire",
    expert: "Expert",
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Target className="h-6 w-6 text-primary-400" />
            Session terminee - {report.skill_name}
          </h1>
          <p className="text-muted-foreground mt-1">
            {report.sector_name && <span>{report.sector_name} | </span>}
            {levelLabels[report.level] || report.level} | {durationStr}
          </p>
        </div>
        <div className={cn(
          "px-4 py-2 rounded-full text-sm font-medium",
          report.passed ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
        )}>
          {report.passed ? "Reussi" : "A ameliorer"}
        </div>
      </div>

      {/* Score Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Score */}
        <Card className="glass">
          <CardContent className="pt-6 text-center">
            <div className="text-4xl font-bold text-primary-400">
              {Math.round(report.final_score)}%
            </div>
            <p className="text-sm text-muted-foreground mt-1">Score global</p>
            <div className="mt-3 flex justify-center">
              {report.final_score >= 80 ? (
                <Trophy className="h-8 w-8 text-yellow-400" />
              ) : report.final_score >= 60 ? (
                <ThumbsUp className="h-8 w-8 text-green-400" />
              ) : (
                <Target className="h-8 w-8 text-muted-foreground" />
              )}
            </div>
          </CardContent>
        </Card>

        {/* Gauge Progression */}
        <Card className="glass">
          <CardContent className="pt-6 text-center">
            <div className="flex items-center justify-center gap-2">
              <span className="text-2xl text-muted-foreground">{report.starting_gauge}</span>
              <ArrowRight className="h-5 w-5 text-muted-foreground" />
              <span className="text-4xl font-bold">{report.final_gauge}</span>
            </div>
            <p className="text-sm text-muted-foreground mt-1">Jauge emotionnelle</p>
            <div className={cn("mt-3 flex items-center justify-center gap-1", progressionColor)}>
              <ProgressIcon className="h-5 w-5" />
              <span className="font-medium">
                {report.gauge_progression >= 0 ? "+" : ""}{report.gauge_progression}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Conversion */}
        <Card className="glass">
          <CardContent className="pt-6 text-center">
            <div className="flex justify-center">
              {report.converted ? (
                <CheckCircle2 className="h-12 w-12 text-green-400" />
              ) : (
                <XCircle className="h-12 w-12 text-muted-foreground" />
              )}
            </div>
            <p className="text-sm text-muted-foreground mt-2">
              {report.converted ? "Prospect converti !" : "Non converti"}
            </p>
            {report.conversion_blockers.length > 0 && (
              <p className="text-xs text-red-400 mt-1">
                {report.conversion_blockers.length} bloqueur(s)
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

// ==========================================
// PATTERN ANALYSIS COMPONENT
// ==========================================

function PatternAnalysis({ report }: { report: SessionReport }) {
  const [showAllPositive, setShowAllPositive] = useState(false);
  const [showAllNegative, setShowAllNegative] = useState(false);

  const displayedPositive = showAllPositive
    ? report.positive_patterns
    : report.positive_patterns.slice(0, 3);

  const displayedNegative = showAllNegative
    ? report.negative_patterns
    : report.negative_patterns.slice(0, 3);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Points forts */}
      <Card className="glass border-green-500/20">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-green-400">
            <ThumbsUp className="h-5 w-5" />
            Points forts ({report.positive_count})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {displayedPositive.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucun pattern positif detecte</p>
          ) : (
            displayedPositive.map((pattern, idx) => (
              <PatternItem key={idx} pattern={pattern} type="positive" />
            ))
          )}
          {report.positive_patterns.length > 3 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAllPositive(!showAllPositive)}
              className="w-full"
            >
              {showAllPositive ? (
                <>Voir moins <ChevronUp className="h-4 w-4 ml-1" /></>
              ) : (
                <>Voir tout ({report.positive_patterns.length}) <ChevronDown className="h-4 w-4 ml-1" /></>
              )}
            </Button>
          )}
        </CardContent>
      </Card>

      {/* Points a ameliorer */}
      <Card className="glass border-red-500/20">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-red-400">
            <ThumbsDown className="h-5 w-5" />
            A ameliorer ({report.negative_count})
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {displayedNegative.length === 0 ? (
            <p className="text-sm text-muted-foreground">Aucune erreur detectee - Bravo !</p>
          ) : (
            displayedNegative.map((pattern, idx) => (
              <PatternItem key={idx} pattern={pattern} type="negative" />
            ))
          )}
          {report.negative_patterns.length > 3 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAllNegative(!showAllNegative)}
              className="w-full"
            >
              {showAllNegative ? (
                <>Voir moins <ChevronUp className="h-4 w-4 ml-1" /></>
              ) : (
                <>Voir tout ({report.negative_patterns.length}) <ChevronDown className="h-4 w-4 ml-1" /></>
              )}
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function PatternItem({ pattern, type }: { pattern: PatternAggregate; type: "positive" | "negative" }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={cn(
        "p-3 rounded-lg cursor-pointer transition-colors",
        type === "positive" ? "bg-green-500/10 hover:bg-green-500/20" : "bg-red-500/10 hover:bg-red-500/20"
      )}
      onClick={() => setExpanded(!expanded)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {type === "positive" ? (
            <CheckCircle2 className="h-4 w-4 text-green-400" />
          ) : (
            <AlertTriangle className="h-4 w-4 text-red-400" />
          )}
          <span className="font-medium">{pattern.label}</span>
          {pattern.count > 1 && (
            <span className="text-xs bg-white/10 px-2 py-0.5 rounded-full">
              x{pattern.count}
            </span>
          )}
        </div>
        {(pattern.examples.length > 0 || pattern.advice) && (
          <ChevronDown className={cn(
            "h-4 w-4 transition-transform",
            expanded && "rotate-180"
          )} />
        )}
      </div>

      <AnimatePresence>
        {expanded && (pattern.examples.length > 0 || pattern.advice) && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="pt-3 space-y-2">
              {pattern.examples.map((ex, i) => (
                <p key={i} className="text-sm text-muted-foreground italic">
                  &quot;{ex}&quot;
                </p>
              ))}
              {pattern.advice && (
                <div className="flex items-start gap-2 text-sm bg-blue-500/10 p-2 rounded">
                  <Lightbulb className="h-4 w-4 text-blue-400 mt-0.5 flex-shrink-0" />
                  <span>{pattern.advice}</span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ==========================================
// CONVERSATION REPLAY COMPONENT
// ==========================================

function ConversationReplay({ report }: { report: SessionReport }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <Card className="glass">
      <CardHeader
        className="pb-3 cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary-400" />
            Replay de la conversation ({report.message_count} messages)
          </div>
          <ChevronDown className={cn(
            "h-5 w-5 transition-transform",
            expanded && "rotate-180"
          )} />
        </CardTitle>
      </CardHeader>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            <CardContent className="space-y-4 max-h-[500px] overflow-y-auto">
              {report.messages.map((msg, idx) => (
                <MessageBubble key={idx} message={msg} />
              ))}
            </CardContent>
          </motion.div>
        )}
      </AnimatePresence>
    </Card>
  );
}

function MessageBubble({ message }: { message: ReportMessage }) {
  const isUser = message.role === "user";

  return (
    <div className={cn(
      "flex gap-3",
      isUser ? "flex-row-reverse" : ""
    )}>
      {/* Avatar */}
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
        isUser ? "bg-primary-500/20" : "bg-gray-500/20"
      )}>
        {isUser ? (
          <User className="h-4 w-4 text-primary-400" />
        ) : (
          <Bot className="h-4 w-4 text-gray-400" />
        )}
      </div>

      {/* Content */}
      <div className={cn(
        "max-w-[70%] space-y-1",
        isUser ? "items-end" : "items-start"
      )}>
        <div className={cn(
          "p-3 rounded-lg",
          isUser ? "bg-primary-500/20 rounded-br-none" : "bg-gray-500/20 rounded-bl-none"
        )}>
          <p className="text-sm">{message.content}</p>

          {/* Behavioral cue */}
          {message.behavioral_cue && (
            <p className="text-xs text-muted-foreground italic mt-1">
              {message.behavioral_cue}
            </p>
          )}
        </div>

        {/* Annotations */}
        <div className={cn(
          "flex flex-wrap gap-1 text-xs",
          isUser ? "justify-end" : "justify-start"
        )}>
          {/* Gauge impact */}
          {isUser && message.gauge_impact !== null && message.gauge_impact !== 0 && (
            <span className={cn(
              "px-2 py-0.5 rounded-full",
              message.gauge_impact > 0 ? "bg-green-500/20 text-green-400" : "bg-red-500/20 text-red-400"
            )}>
              {message.gauge_impact > 0 ? "+" : ""}{message.gauge_impact} jauge
            </span>
          )}

          {/* Patterns */}
          {message.patterns_detected.slice(0, 2).map((p, i) => (
            <span key={i} className="px-2 py-0.5 rounded-full bg-white/10">
              {p.replace(/_/g, " ")}
            </span>
          ))}

          {/* Event indicator */}
          {message.is_event && (
            <span className="px-2 py-0.5 rounded-full bg-yellow-500/20 text-yellow-400">
              {message.event_type}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

// ==========================================
// NEXT STEPS COMPONENT
// ==========================================

function NextSteps({ report }: { report: SessionReport }) {
  const router = useRouter();

  return (
    <Card className="glass">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-primary-400" />
          Conseils pour progresser
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Main advice */}
        <div className="p-4 bg-primary-500/10 rounded-lg border border-primary-500/20">
          <p className="font-medium">{report.conseil_principal}</p>
        </div>

        {/* Tips list */}
        {report.personalized_tips.length > 0 && (
          <div className="space-y-2">
            {report.personalized_tips.map((tip, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm">
                <Lightbulb className="h-4 w-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                <span>{tip}</span>
              </div>
            ))}
          </div>
        )}

        {/* Points forts recap */}
        {report.points_forts.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-green-400">Points forts:</p>
            <ul className="text-sm text-muted-foreground list-disc list-inside">
              {report.points_forts.map((p, i) => <li key={i}>{p}</li>)}
            </ul>
          </div>
        )}

        {/* Axes amelioration */}
        {report.axes_amelioration.length > 0 && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-red-400">Axes d&apos;amelioration:</p>
            <ul className="text-sm text-muted-foreground list-disc list-inside">
              {report.axes_amelioration.map((a, i) => <li key={i}>{a}</li>)}
            </ul>
          </div>
        )}

        {/* Action buttons */}
        <div className="flex flex-wrap gap-3 pt-4">
          <Button
            onClick={() => router.push(`/training/setup?skill=${report.skill_slug}&retry=true`)}
            className="flex items-center gap-2"
          >
            <RotateCcw className="h-4 w-4" />
            Refaire ce scenario
          </Button>
          <Button
            variant="outline"
            onClick={() => router.push("/training")}
            className="flex items-center gap-2"
          >
            <ArrowRight className="h-4 w-4" />
            Scenario suivant
          </Button>
          <Button
            variant="ghost"
            onClick={() => router.push("/learn")}
            className="flex items-center gap-2"
          >
            <BookOpen className="h-4 w-4" />
            Retour aux cours
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

// ==========================================
// MAIN PAGE COMPONENT
// ==========================================

export default function SessionReportPage() {
  const params = useParams();
  const router = useRouter();
  const sessionId = Number(params.id);

  const [report, setReport] = useState<SessionReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadReport = useCallback(async () => {
    try {
      setLoading(true);
      const response = await voiceAPI.getSessionReport(sessionId);
      setReport(response.data);
    } catch (err: unknown) {
      console.error("Failed to load report:", err);
      const errorMessage = err instanceof Error ? err.message : "Impossible de charger le rapport";
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  useEffect(() => {
    if (sessionId) {
      loadReport();
    }
  }, [sessionId, loadReport]);

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-400 mx-auto" />
          <p className="text-muted-foreground">Chargement du rapport...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !report) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <Card className="glass max-w-md mx-4">
          <CardContent className="pt-6 text-center space-y-4">
            <XCircle className="h-12 w-12 text-red-400 mx-auto" />
            <p className="text-lg font-medium">Rapport introuvable</p>
            <p className="text-sm text-muted-foreground">{error}</p>
            <Button onClick={() => router.push("/training")}>
              Retour aux entrainements
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-dark py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Score Overview */}
        <ScoreOverview report={report} />

        {/* Pattern Analysis */}
        <PatternAnalysis report={report} />

        {/* Conversation Replay */}
        <ConversationReplay report={report} />

        {/* Next Steps */}
        <NextSteps report={report} />
      </div>
    </div>
  );
}
