"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Play, Clock, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { Champion } from "@/types";

interface ChampionCardProps {
  champion: Champion;
  index?: number;
}

const statusConfig = {
  ready: {
    label: "Prêt",
    color: "bg-green-500/20 text-green-400 border-green-500/30",
    icon: CheckCircle,
  },
  processing: {
    label: "En cours",
    color: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    icon: Loader2,
  },
  error: {
    label: "Erreur",
    color: "bg-red-500/20 text-red-400 border-red-500/30",
    icon: AlertCircle,
  },
  uploaded: {
    label: "Uploadé",
    color: "bg-blue-500/20 text-blue-400 border-blue-500/30",
    icon: Clock,
  },
  pending: {
    label: "En attente",
    color: "bg-gray-500/20 text-gray-400 border-gray-500/30",
    icon: Clock,
  },
};

export function ChampionCard({ champion, index = 0 }: ChampionCardProps) {
  const status = statusConfig[champion.status] || statusConfig.pending;
  const StatusIcon = status.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card className="glass border-white/10 hover:border-primary-500/30 transition-all h-full">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-lg truncate">{champion.name}</CardTitle>
            <Badge
              variant="outline"
              className={cn("flex-shrink-0", status.color)}
            >
              <StatusIcon
                className={cn(
                  "h-3 w-3 mr-1",
                  champion.status === "processing" && "animate-spin"
                )}
              />
              {status.label}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {champion.description && (
            <p className="text-sm text-muted-foreground line-clamp-2">
              {champion.description}
            </p>
          )}

          <p className="text-xs text-muted-foreground">
            Créé le{" "}
            {new Date(champion.created_at).toLocaleDateString("fr-FR", {
              day: "numeric",
              month: "long",
              year: "numeric",
            })}
          </p>

          {champion.status === "ready" ? (
            <Link href={`/training?champion=${champion.id}`}>
              <Button
                size="sm"
                className="w-full bg-gradient-primary hover:opacity-90"
              >
                <Play className="h-4 w-4 mr-2" />
                S&apos;entraîner
              </Button>
            </Link>
          ) : champion.status === "processing" ? (
            <Button size="sm" className="w-full" disabled>
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              Analyse en cours...
            </Button>
          ) : champion.status === "error" ? (
            <Button size="sm" variant="outline" className="w-full">
              Réessayer l&apos;analyse
            </Button>
          ) : (
            <Button size="sm" variant="outline" className="w-full" disabled>
              En attente d&apos;analyse
            </Button>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
