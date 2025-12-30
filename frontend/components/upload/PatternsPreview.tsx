"use client";

import { motion } from "framer-motion";
import { MessageSquare, Shield, Target, Sparkles } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { SalesPatterns, Pattern } from "@/types";

interface PatternsPreviewProps {
  patterns: SalesPatterns;
}

const patternCategories = [
  {
    id: "openings",
    label: "Openings",
    icon: MessageSquare,
    color: "text-blue-400",
    bgColor: "bg-blue-500/20",
  },
  {
    id: "objection_handling",
    label: "Objections",
    icon: Shield,
    color: "text-orange-400",
    bgColor: "bg-orange-500/20",
  },
  {
    id: "closings",
    label: "Closings",
    icon: Target,
    color: "text-green-400",
    bgColor: "bg-green-500/20",
  },
];

function PatternCard({ pattern, index }: { pattern: Pattern; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <Card className="glass border-white/10 hover:border-primary-500/30 transition-all">
        <CardContent className="p-4">
          <p className="text-sm mb-3 leading-relaxed">"{pattern.text}"</p>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {pattern.context}
            </span>
            <Badge
              variant="outline"
              className={`text-xs ${
                pattern.effectiveness >= 8
                  ? "border-green-500/50 text-green-400"
                  : pattern.effectiveness >= 6
                  ? "border-yellow-500/50 text-yellow-400"
                  : "border-orange-500/50 text-orange-400"
              }`}
            >
              {pattern.effectiveness}/10
            </Badge>
          </div>
          {pattern.tags && pattern.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-3">
              {pattern.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="secondary"
                  className="text-xs bg-white/5"
                >
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}

export function PatternsPreview({ patterns }: PatternsPreviewProps) {
  return (
    <div className="glass rounded-2xl p-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 rounded-lg bg-primary-500/20">
          <Sparkles className="h-5 w-5 text-primary-400" />
        </div>
        <div>
          <h3 className="font-semibold">Patterns détectés</h3>
          <p className="text-sm text-muted-foreground">
            Score d'efficacité: {patterns.effectiveness_score}/10
          </p>
        </div>
      </div>

      {/* Communication style */}
      <div className="mb-6 p-4 rounded-lg bg-white/5">
        <p className="text-sm text-muted-foreground mb-1">Style de communication</p>
        <p className="text-sm">{patterns.communication_style}</p>
      </div>

      {/* Key phrases */}
      {patterns.key_phrases && patterns.key_phrases.length > 0 && (
        <div className="mb-6">
          <p className="text-sm text-muted-foreground mb-2">Phrases clés</p>
          <div className="flex flex-wrap gap-2">
            {patterns.key_phrases.map((phrase, index) => (
              <Badge
                key={index}
                variant="outline"
                className="border-primary-500/30 text-primary-300"
              >
                {phrase}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Tabs for pattern categories */}
      <Tabs defaultValue="openings" className="w-full">
        <TabsList className="w-full bg-white/5 p-1 rounded-lg">
          {patternCategories.map((category) => (
            <TabsTrigger
              key={category.id}
              value={category.id}
              className="flex-1 data-[state=active]:bg-primary-500/20 rounded-md transition-all"
            >
              <category.icon className={`h-4 w-4 mr-2 ${category.color}`} />
              {category.label}
            </TabsTrigger>
          ))}
        </TabsList>

        {patternCategories.map((category) => {
          const categoryPatterns =
            patterns[category.id as keyof Pick<SalesPatterns, 'openings' | 'objection_handling' | 'closings'>] || [];

          return (
            <TabsContent key={category.id} value={category.id} className="mt-4">
              {categoryPatterns.length > 0 ? (
                <div className="space-y-3">
                  {categoryPatterns.map((pattern, index) => (
                    <PatternCard
                      key={index}
                      pattern={pattern}
                      index={index}
                    />
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  <p>Aucun pattern détecté dans cette catégorie</p>
                </div>
              )}
            </TabsContent>
          );
        })}
      </Tabs>
    </div>
  );
}
