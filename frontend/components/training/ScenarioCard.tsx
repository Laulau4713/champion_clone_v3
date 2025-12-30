"use client";

import { motion } from "framer-motion";
import { Target, Users, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, getDifficultyColor } from "@/lib/utils";
import type { TrainingScenario } from "@/types";

interface ScenarioCardProps {
  scenario: TrainingScenario;
  isSelected?: boolean;
  onClick?: () => void;
}

export function ScenarioCard({
  scenario,
  isSelected = false,
  onClick,
}: ScenarioCardProps) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      <Card
        className={cn(
          "glass border-white/10 cursor-pointer transition-all duration-300",
          isSelected
            ? "border-primary-500/50 bg-primary-500/10"
            : "hover:border-primary-500/30"
        )}
        onClick={onClick}
      >
        <CardContent className="p-6">
          {/* Header */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h3 className="font-semibold mb-1">{scenario.name}</h3>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {scenario.description}
              </p>
            </div>
            <Badge
              className={cn(
                "ml-3 flex-shrink-0",
                getDifficultyColor(scenario.difficulty)
              )}
            >
              {scenario.difficulty === "easy"
                ? "Facile"
                : scenario.difficulty === "medium"
                ? "Moyen"
                : "Difficile"}
            </Badge>
          </div>

          {/* Prospect info */}
          {scenario.prospect_profile && (
            <div className="flex items-center gap-2 mb-4 p-3 rounded-lg bg-white/5">
              <Users className="h-4 w-4 text-muted-foreground" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {scenario.prospect_profile.name}
                </p>
                <p className="text-xs text-muted-foreground truncate">
                  {scenario.prospect_profile.role} - {scenario.prospect_profile.company}
                </p>
              </div>
            </div>
          )}

          {/* Objectives */}
          {scenario.objectives && scenario.objectives.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Target className="h-4 w-4" />
                <span>Objectifs</span>
              </div>
              <ul className="space-y-1">
                {scenario.objectives.slice(0, 3).map((objective, index) => (
                  <li
                    key={index}
                    className="text-xs text-muted-foreground flex items-start gap-2"
                  >
                    <span className="text-primary-400 mt-0.5">•</span>
                    <span className="line-clamp-1">{objective}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Pain points preview */}
          {scenario.prospect_profile?.pain_points &&
            scenario.prospect_profile.pain_points.length > 0 && (
              <div className="mt-4 pt-4 border-t border-white/10">
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Points de douleur</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {scenario.prospect_profile.pain_points
                    .slice(0, 3)
                    .map((painPoint, index) => (
                      <Badge
                        key={index}
                        variant="outline"
                        className="text-xs border-orange-500/30 text-orange-400"
                      >
                        {painPoint}
                      </Badge>
                    ))}
                </div>
              </div>
            )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
