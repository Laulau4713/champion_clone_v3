"use client";

import React from "react";
import { motion } from "framer-motion";
import { Target, Users, AlertTriangle, CheckCircle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { TrainingScenario } from "@/types";
import { cn, getDifficultyColor } from "@/lib/utils";

interface ScenarioSelectorProps {
  scenarios: TrainingScenario[];
  selectedIndex: number | null;
  onSelect: (index: number) => void;
  onStart: () => void;
  isLoading?: boolean;
  isStarting?: boolean;
}

const difficultyLabels = {
  easy: "Facile",
  medium: "Moyen",
  hard: "Difficile",
};

const ScenarioCard: React.FC<{
  scenario: TrainingScenario;
  index: number;
  isSelected: boolean;
  onSelect: () => void;
}> = ({ scenario, index, isSelected, onSelect }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.1 }}
  >
    <Card
      className={cn(
        "cursor-pointer transition-all",
        isSelected
          ? "border-primary-500 bg-primary-500/10 shadow-lg shadow-primary-500/20"
          : "hover:border-slate-600"
      )}
      onClick={onSelect}
    >
      <CardContent className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "w-10 h-10 rounded-lg flex items-center justify-center",
                isSelected ? "bg-primary-500" : "bg-slate-700"
              )}
            >
              <Target className={cn("h-5 w-5", isSelected ? "text-white" : "text-slate-400")} />
            </div>
            <div>
              <h4 className="font-medium text-white">Scénario {index + 1}</h4>
              <Badge className={getDifficultyColor(scenario.difficulty)}>
                {difficultyLabels[scenario.difficulty]}
              </Badge>
            </div>
          </div>
          {isSelected && (
            <CheckCircle className="h-5 w-5 text-primary-400 flex-shrink-0" />
          )}
        </div>

        {/* Context */}
        <p className="text-sm text-slate-300 mb-4 line-clamp-2">{scenario.context}</p>

        {/* Prospect Type */}
        <div className="flex items-center gap-2 mb-3">
          <Users className="h-4 w-4 text-slate-500" />
          <span className="text-sm text-slate-400">{scenario.prospect_type}</span>
        </div>

        {/* Challenge */}
        <div className="flex items-start gap-2 mb-4">
          <AlertTriangle className="h-4 w-4 text-warning-400 flex-shrink-0 mt-0.5" />
          <span className="text-sm text-slate-400">{scenario.challenge}</span>
        </div>

        {/* Objectives */}
        <div className="space-y-1">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Objectifs</p>
          <ul className="space-y-1">
            {scenario.objectives.slice(0, 3).map((obj, i) => (
              <li key={i} className="flex items-center gap-2 text-xs text-slate-400">
                <span className="w-1 h-1 rounded-full bg-primary-400" />
                {obj}
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  </motion.div>
);

const LoadingSkeleton: React.FC = () => (
  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
    {[1, 2, 3].map((i) => (
      <Card key={i}>
        <CardContent className="p-5 space-y-4">
          <div className="flex items-center gap-3">
            <Skeleton className="w-10 h-10 rounded-lg" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-5 w-16" />
            </div>
          </div>
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </CardContent>
      </Card>
    ))}
  </div>
);

export const ScenarioSelector: React.FC<ScenarioSelectorProps> = ({
  scenarios,
  selectedIndex,
  onSelect,
  onStart,
  isLoading,
  isStarting,
}) => {
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (scenarios.length === 0) {
    return (
      <div className="text-center py-12">
        <Target className="h-12 w-12 text-slate-500 mx-auto mb-4" />
        <p className="text-slate-400">Aucun scénario disponible</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {scenarios.map((scenario, index) => (
          <ScenarioCard
            key={index}
            scenario={scenario}
            index={index}
            isSelected={selectedIndex === index}
            onSelect={() => onSelect(index)}
          />
        ))}
      </div>

      {selectedIndex !== null && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex justify-center"
        >
          <Button
            size="lg"
            onClick={onStart}
            loading={isStarting}
            className="px-8"
          >
            Démarrer l&apos;entraînement
          </Button>
        </motion.div>
      )}
    </div>
  );
};

export default ScenarioSelector;
