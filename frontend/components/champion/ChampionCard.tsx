"use client";

import React from "react";
import { motion } from "framer-motion";
import { useRouter } from "next/navigation";
import { User, Calendar, Play, MoreVertical, Trash2, RefreshCw } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { ChampionListItem } from "@/types";
import { formatDate, getStatusColor, cn } from "@/lib/utils";

interface ChampionCardProps {
  champion: ChampionListItem;
  onDelete?: (id: number) => void;
  onReanalyze?: (id: number) => void;
  isDeleting?: boolean;
}

const statusLabels: Record<string, string> = {
  pending: "En attente",
  uploaded: "Uploadé",
  processing: "Traitement",
  ready: "Prêt",
  error: "Erreur",
};

export const ChampionCard: React.FC<ChampionCardProps> = ({
  champion,
  onDelete,
  onReanalyze,
  isDeleting,
}) => {
  const router = useRouter();
  const [showActions, setShowActions] = React.useState(false);

  const handleStartTraining = () => {
    router.push(`/training?championId=${champion.id}`);
  };

  const isReady = champion.status === "ready";

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -2 }}
      className="group"
    >
      <Card
        className={cn(
          "relative overflow-hidden transition-all",
          "hover:border-primary-500/50 hover:shadow-lg hover:shadow-primary-500/10",
          isDeleting && "opacity-50 pointer-events-none"
        )}
      >
        {/* Status Indicator */}
        <div
          className={cn(
            "absolute top-0 left-0 right-0 h-1",
            champion.status === "ready" && "bg-success-500",
            champion.status === "processing" && "bg-primary-500 animate-pulse",
            champion.status === "error" && "bg-error-500",
            (champion.status === "pending" || champion.status === "uploaded") && "bg-warning-500"
          )}
        />

        <CardContent className="p-5">
          <div className="flex items-start justify-between gap-4">
            {/* Avatar & Info */}
            <div className="flex items-center gap-4 min-w-0">
              <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center flex-shrink-0">
                <User className="h-6 w-6 text-white" />
              </div>

              <div className="min-w-0">
                <h3 className="font-semibold text-white truncate">{champion.name}</h3>
                {champion.description && (
                  <p className="text-sm text-slate-400 truncate">{champion.description}</p>
                )}
                <div className="flex items-center gap-2 mt-1">
                  <Calendar className="h-3 w-3 text-slate-500" />
                  <span className="text-xs text-slate-500">
                    {formatDate(champion.created_at)}
                  </span>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              <Badge className={getStatusColor(champion.status)}>
                {statusLabels[champion.status] || champion.status}
              </Badge>

              {/* Action Menu */}
              <div className="relative">
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8"
                  onClick={() => setShowActions(!showActions)}
                >
                  <MoreVertical className="h-4 w-4" />
                </Button>

                {showActions && (
                  <>
                    <div
                      className="fixed inset-0 z-10"
                      onClick={() => setShowActions(false)}
                    />
                    <div className="absolute right-0 top-full mt-1 z-20 w-40 rounded-lg border border-slate-700 bg-slate-800 shadow-xl py-1">
                      {isReady && onReanalyze && (
                        <button
                          onClick={() => {
                            onReanalyze(champion.id);
                            setShowActions(false);
                          }}
                          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 transition-colors"
                        >
                          <RefreshCw className="h-4 w-4" />
                          Ré-analyser
                        </button>
                      )}
                      {onDelete && (
                        <button
                          onClick={() => {
                            onDelete(champion.id);
                            setShowActions(false);
                          }}
                          className="flex items-center gap-2 w-full px-3 py-2 text-sm text-error-400 hover:bg-slate-700 transition-colors"
                        >
                          <Trash2 className="h-4 w-4" />
                          Supprimer
                        </button>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Action Button */}
          {isReady && (
            <div className="mt-4 pt-4 border-t border-slate-700/50">
              <Button
                onClick={handleStartTraining}
                className="w-full"
                variant="default"
              >
                <Play className="mr-2 h-4 w-4" />
                Commencer l&apos;entraînement
              </Button>
            </div>
          )}

          {champion.status === "processing" && (
            <div className="mt-4 pt-4 border-t border-slate-700/50">
              <div className="flex items-center justify-center gap-2 text-sm text-slate-400">
                <RefreshCw className="h-4 w-4 animate-spin" />
                Analyse en cours...
              </div>
            </div>
          )}

          {champion.status === "error" && (
            <div className="mt-4 pt-4 border-t border-slate-700/50">
              <Button
                onClick={() => onReanalyze?.(champion.id)}
                className="w-full"
                variant="outline"
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                Réessayer l&apos;analyse
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default ChampionCard;
