"use client";

import React from "react";
import { motion } from "framer-motion";
import { MessageSquare, Shield, Target, Quote, Sparkles } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { ChampionPatterns, ObjectionHandler } from "@/types";
import { cn } from "@/lib/utils";

interface PatternsListProps {
  patterns: ChampionPatterns | null;
  isLoading?: boolean;
}

const PatternCard: React.FC<{
  content: string;
  index: number;
  icon?: React.ReactNode;
}> = ({ content, index, icon }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.05 }}
  >
    <Card className="hover:border-primary-500/50 transition-colors">
      <CardContent className="p-4">
        <div className="flex gap-3">
          {icon && (
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-primary-500/10 flex items-center justify-center">
              {icon}
            </div>
          )}
          <p className="text-sm text-slate-300 leading-relaxed">{content}</p>
        </div>
      </CardContent>
    </Card>
  </motion.div>
);

const ObjectionCard: React.FC<{
  handler: ObjectionHandler;
  index: number;
}> = ({ handler, index }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ delay: index * 0.05 }}
  >
    <Card className="hover:border-warning-500/50 transition-colors">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center gap-2">
          <Badge variant="warning" className="text-xs">
            Objection
          </Badge>
          <span className="text-sm font-medium text-white">{handler.objection}</span>
        </div>

        <div className="pl-4 border-l-2 border-success-500/30">
          <p className="text-sm text-slate-400 mb-1">Réponse :</p>
          <p className="text-sm text-slate-200">{handler.response}</p>
        </div>

        {handler.example && (
          <div className="pl-4 border-l-2 border-slate-600">
            <p className="text-xs text-slate-500 mb-1">Exemple :</p>
            <p className="text-xs text-slate-400 italic">&quot;{handler.example}&quot;</p>
          </div>
        )}
      </CardContent>
    </Card>
  </motion.div>
);

const EmptyState: React.FC<{ message: string }> = ({ message }) => (
  <div className="text-center py-12">
    <div className="w-16 h-16 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-4">
      <Sparkles className="h-8 w-8 text-slate-500" />
    </div>
    <p className="text-slate-400">{message}</p>
  </div>
);

const LoadingSkeleton: React.FC = () => (
  <div className="space-y-4">
    {[1, 2, 3].map((i) => (
      <Card key={i}>
        <CardContent className="p-4">
          <div className="flex gap-3">
            <Skeleton className="w-8 h-8 rounded-lg" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
        </CardContent>
      </Card>
    ))}
  </div>
);

export const PatternsList: React.FC<PatternsListProps> = ({ patterns, isLoading }) => {
  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-full max-w-md" />
        <LoadingSkeleton />
      </div>
    );
  }

  if (!patterns) {
    return <EmptyState message="Aucun pattern extrait. Lancez l'analyse du champion." />;
  }

  const tabs = [
    {
      value: "openings",
      label: "Ouvertures",
      icon: <MessageSquare className="h-4 w-4" />,
      count: patterns.openings.length,
    },
    {
      value: "objections",
      label: "Objections",
      icon: <Shield className="h-4 w-4" />,
      count: patterns.objection_handlers.length,
    },
    {
      value: "closes",
      label: "Closings",
      icon: <Target className="h-4 w-4" />,
      count: patterns.closes.length,
    },
    {
      value: "phrases",
      label: "Phrases clés",
      icon: <Quote className="h-4 w-4" />,
      count: patterns.key_phrases.length,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Tone/Style Summary */}
      {patterns.tone_style && (
        <Card className="bg-gradient-to-r from-primary-500/10 to-secondary-500/10 border-primary-500/30">
          <CardContent className="p-4">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-primary-400 flex-shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-medium text-white mb-1">Style de communication</h4>
                <p className="text-sm text-slate-300">{patterns.tone_style}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs defaultValue="openings" className="w-full">
        <TabsList className="w-full grid grid-cols-4 h-auto p-1">
          {tabs.map((tab) => (
            <TabsTrigger
              key={tab.value}
              value={tab.value}
              className="flex items-center gap-2 py-2"
            >
              {tab.icon}
              <span className="hidden sm:inline">{tab.label}</span>
              <Badge variant="outline" className="ml-1 px-1.5 py-0 text-xs">
                {tab.count}
              </Badge>
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="openings" className="mt-4 space-y-3">
          {patterns.openings.length > 0 ? (
            patterns.openings.map((opening, index) => (
              <PatternCard
                key={index}
                content={opening}
                index={index}
                icon={<MessageSquare className="h-4 w-4 text-primary-400" />}
              />
            ))
          ) : (
            <EmptyState message="Aucune technique d'ouverture identifiée" />
          )}
        </TabsContent>

        <TabsContent value="objections" className="mt-4 space-y-3">
          {patterns.objection_handlers.length > 0 ? (
            patterns.objection_handlers.map((handler, index) => (
              <ObjectionCard key={index} handler={handler} index={index} />
            ))
          ) : (
            <EmptyState message="Aucune gestion d'objection identifiée" />
          )}
        </TabsContent>

        <TabsContent value="closes" className="mt-4 space-y-3">
          {patterns.closes.length > 0 ? (
            patterns.closes.map((close, index) => (
              <PatternCard
                key={index}
                content={close}
                index={index}
                icon={<Target className="h-4 w-4 text-success-400" />}
              />
            ))
          ) : (
            <EmptyState message="Aucune technique de closing identifiée" />
          )}
        </TabsContent>

        <TabsContent value="phrases" className="mt-4 space-y-3">
          {patterns.key_phrases.length > 0 ? (
            patterns.key_phrases.map((phrase, index) => (
              <PatternCard
                key={index}
                content={phrase}
                index={index}
                icon={<Quote className="h-4 w-4 text-secondary-400" />}
              />
            ))
          ) : (
            <EmptyState message="Aucune phrase clé identifiée" />
          )}
        </TabsContent>
      </Tabs>

      {/* Success Patterns */}
      {patterns.success_patterns.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-sm font-medium text-slate-400">Patterns de succès</h4>
          <div className="grid gap-2">
            {patterns.success_patterns.map((pattern, index) => (
              <div
                key={index}
                className={cn(
                  "flex items-center gap-2 p-3 rounded-lg",
                  "bg-success-500/5 border border-success-500/20"
                )}
              >
                <span className="text-success-400">✓</span>
                <span className="text-sm text-slate-300">{pattern}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PatternsList;
