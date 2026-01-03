"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Eye, MoreVertical, Calendar, Clock, Trophy } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn, formatDate, formatDuration, getScoreColor } from "@/lib/utils";
import type { SessionHistory } from "@/types";

interface SessionsTableProps {
  sessions: SessionHistory[];
  onViewSession?: (id: number) => void;
}

export function SessionsTable({ sessions, onViewSession }: SessionsTableProps) {
  const router = useRouter();

  const handleViewSession = (id: number) => {
    // Navigate to the report page for this session
    router.push(`/training/report/${id}`);
    onViewSession?.(id);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
    >
      <Card className="glass border-white/10">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Historique des sessions</CardTitle>
            <Button variant="outline" size="sm" className="border-white/20">
              Voir tout
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-white/10">
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                    Date
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                    Scénario
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                    Champion
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                    Score
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">
                    Durée
                  </th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((session, index) => (
                  <motion.tr
                    key={session.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 * index }}
                    className="border-b border-white/5 hover:bg-white/5 transition-colors"
                  >
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2 text-sm">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        {formatDate(session.date)}
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <span className="text-sm">{session.scenario}</span>
                    </td>
                    <td className="py-4 px-4">
                      <Badge
                        variant="outline"
                        className="border-primary-500/30 text-primary-400"
                      >
                        {session.champion_name}
                      </Badge>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2">
                        <Trophy
                          className={cn("h-4 w-4", getScoreColor(session.score))}
                        />
                        <span
                          className={cn(
                            "text-sm font-medium",
                            getScoreColor(session.score)
                          )}
                        >
                          {Math.round(session.score)}/100
                        </span>
                      </div>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Clock className="h-4 w-4" />
                        {formatDuration(session.duration)}
                      </div>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleViewSession(session.id)}
                        className="h-8 w-8"
                        title="Voir le rapport"
                      >
                        <Eye className="h-4 w-4" />
                      </Button>
                    </td>
                  </motion.tr>
                ))}
              </tbody>
            </table>

            {sessions.length === 0 && (
              <div className="text-center py-12 text-muted-foreground">
                <Trophy className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Aucune session enregistrée</p>
                <p className="text-sm">
                  Commencez un entraînement pour voir vos résultats ici
                </p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
