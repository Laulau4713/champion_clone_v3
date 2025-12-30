"use client";

import React from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { Calendar, Clock, Target, ChevronRight, User } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import type { TrainingSession } from "@/types";
import { cn, formatDate, formatDuration, getScoreColor, getStatusColor } from "@/lib/utils";

interface SessionHistoryProps {
  sessions: TrainingSession[];
  isLoading?: boolean;
  limit?: number;
}

const statusLabels: Record<string, string> = {
  active: "En cours",
  completed: "Terminée",
  abandoned: "Abandonnée",
};

const SessionRow: React.FC<{
  session: TrainingSession;
  index: number;
}> = ({ session, index }) => {
  const router = useRouter();

  const handleClick = () => {
    router.push(`/training?sessionId=${session.id}`);
  };

  const duration = session.ended_at
    ? Math.floor(
        (new Date(session.ended_at).getTime() - new Date(session.started_at).getTime()) / 1000
      )
    : 0;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05 }}
    >
      <div
        onClick={handleClick}
        className={cn(
          "flex items-center gap-4 p-4 rounded-lg cursor-pointer transition-all",
          "hover:bg-slate-800/50 border border-transparent hover:border-slate-700/50"
        )}
      >
        {/* Score */}
        <div
          className={cn(
            "w-12 h-12 rounded-lg flex items-center justify-center font-bold text-lg",
            session.overall_score
              ? `${getScoreColor(session.overall_score)} bg-slate-800`
              : "text-slate-500 bg-slate-800"
          )}
        >
          {session.overall_score?.toFixed(1) || "-"}
        </div>

        {/* Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-white truncate">
              {session.scenario?.prospect_type || "Session d'entraînement"}
            </span>
            <Badge className={getStatusColor(session.status)}>
              {statusLabels[session.status]}
            </Badge>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {formatDate(session.started_at)}
            </span>
            {duration > 0 && (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDuration(duration)}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Target className="h-3 w-3" />
              {(session.messages ?? []).filter((m) => m.role === "user").length} échanges
            </span>
          </div>
        </div>

        {/* Arrow */}
        <ChevronRight className="h-5 w-5 text-slate-500" />
      </div>
    </motion.div>
  );
};

const LoadingSkeleton: React.FC = () => (
  <div className="space-y-2">
    {[1, 2, 3].map((i) => (
      <div key={i} className="flex items-center gap-4 p-4">
        <Skeleton className="w-12 h-12 rounded-lg" />
        <div className="flex-1 space-y-2">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-3 w-1/3" />
        </div>
      </div>
    ))}
  </div>
);

export const SessionHistory: React.FC<SessionHistoryProps> = ({
  sessions,
  isLoading,
  limit,
}) => {
  const displayedSessions = limit ? sessions.slice(0, limit) : sessions;

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Historique des sessions</CardTitle>
        </CardHeader>
        <CardContent>
          <LoadingSkeleton />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Historique des sessions</CardTitle>
        {sessions.length > 0 && (
          <span className="text-sm text-slate-400">{sessions.length} session(s)</span>
        )}
      </CardHeader>
      <CardContent>
        {displayedSessions.length === 0 ? (
          <div className="text-center py-8">
            <User className="h-12 w-12 text-slate-500 mx-auto mb-4" />
            <p className="text-slate-400">Aucune session d&apos;entraînement</p>
            <p className="text-sm text-slate-500 mt-1">
              Commencez votre premier entraînement !
            </p>
          </div>
        ) : (
          <div className="space-y-1 -mx-4">
            {displayedSessions.map((session, index) => (
              <SessionRow key={session.id} session={session} index={index} />
            ))}
          </div>
        )}

        {limit && sessions.length > limit && (
          <div className="mt-4 text-center">
            <Button variant="ghost" size="sm">
              Voir tout ({sessions.length})
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SessionHistory;
