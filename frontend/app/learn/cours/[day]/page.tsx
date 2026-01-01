"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Clock,
  CheckCircle2,
  Lightbulb,
  AlertTriangle,
  Heart,
  Sparkles,
  Lock,
  ChevronDown,
  ChevronUp,
  Target,
  MessageSquare,
  FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { learningAPI, authAPI } from "@/lib/api";
import { useAuthStore } from "@/store/auth-store";
import { PremiumModal } from "@/components/ui/premium-modal";
import type { User, Cours } from "@/types";

const levelConfig = {
  easy: { label: "Facile", color: "bg-green-500/20 text-green-400" },
  medium: { label: "Moyen", color: "bg-yellow-500/20 text-yellow-400" },
  expert: { label: "Expert", color: "bg-red-500/20 text-red-400" },
};

// Composant pour afficher le contenu markdown
function MarkdownContent({ content }: { content: string }) {
  // Parse markdown-like content
  const lines = content.split('\n\n');

  return (
    <div className="prose prose-invert max-w-none">
      {lines.map((block, i) => {
        // Headers
        if (block.startsWith('# ')) {
          return <h2 key={i} className="text-2xl font-bold mt-8 mb-4 text-white">{block.slice(2)}</h2>;
        }
        if (block.startsWith('## ')) {
          return <h3 key={i} className="text-xl font-semibold mt-6 mb-3 text-primary-400">{block.slice(3)}</h3>;
        }

        // Bold text processing
        const processText = (text: string) => {
          const parts = text.split(/(\*\*[^*]+\*\*)/g);
          return parts.map((part, j) => {
            if (part.startsWith('**') && part.endsWith('**')) {
              return <strong key={j} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
            }
            return part;
          });
        };

        // Bullet points
        if (block.includes('\n• ') || block.startsWith('• ')) {
          const items = block.split('\n').filter(line => line.trim());
          const title = items[0].startsWith('• ') ? null : items.shift();
          return (
            <div key={i} className="my-4">
              {title && <p className="font-medium mb-2">{processText(title)}</p>}
              <ul className="space-y-2 ml-4">
                {items.map((item, j) => (
                  <li key={j} className="flex items-start gap-2">
                    <span className="text-primary-400 mt-1">•</span>
                    <span>{processText(item.replace(/^[•\-]\s*/, ''))}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        }

        // Regular paragraph
        if (block.trim()) {
          return <p key={i} className="my-4 leading-relaxed text-gray-300">{processText(block)}</p>;
        }

        return null;
      })}
    </div>
  );
}

// Composant pour afficher le contenu structuré d'un key_point
function KeyPointContent({ content }: { content: Record<string, unknown> }) {
  if (!content || typeof content !== "object") return null;

  return (
    <div className="space-y-4 mt-4">
      {Object.entries(content).map(([key, value]) => {
        const title = key.replace(/_/g, " ").replace(/niveau \d+ /, "");

        if (typeof value === "object" && value !== null && !Array.isArray(value)) {
          const obj = value as Record<string, unknown>;
          return (
            <div key={key} className="p-4 rounded-lg bg-white/5 border border-white/10">
              <h5 className="font-medium text-primary-400 mb-3 capitalize">{title}</h5>
              <div className="space-y-2 text-sm">
                {Object.entries(obj).map(([subKey, subValue]) => (
                  <div key={subKey}>
                    <span className="text-muted-foreground capitalize">
                      {subKey.replace(/_/g, " ")}:
                    </span>{" "}
                    {Array.isArray(subValue) ? (
                      <ul className="mt-1 ml-4 space-y-1">
                        {subValue.map((item, i) => (
                          <li key={i} className="flex items-start gap-2">
                            <span className="text-primary-400">•</span>
                            <span>{String(item)}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <span>{String(subValue)}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          );
        }

        if (Array.isArray(value)) {
          return (
            <div key={key} className="p-4 rounded-lg bg-white/5 border border-white/10">
              <h5 className="font-medium text-primary-400 mb-2 capitalize">{title}</h5>
              <ul className="space-y-1 text-sm">
                {value.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-primary-400">•</span>
                    <span>{String(item)}</span>
                  </li>
                ))}
              </ul>
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}

export default function CoursePage() {
  const params = useParams();
  const router = useRouter();
  // The route param is still "day" for URL compatibility, but we use it as module order
  const moduleOrder = Number(params.day);

  const [course, setCourse] = useState<Cours | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [showPremiumModal, setShowPremiumModal] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set([0]));

  const isFreeUser = user?.subscription_plan === "free";
  const isLocked = isFreeUser && moduleOrder > 1;

  const loadUser = useCallback(async () => {
    try {
      const res = await authAPI.me();
      if (res.data) {
        setUser(res.data);
      }
    } catch {
      // Not logged in
    }
  }, []);

  const loadCourse = useCallback(async () => {
    try {
      setLoading(true);
      const res = await learningAPI.getCourseByDay(moduleOrder);
      setCourse(res.data);
    } catch {
      setError("Module non trouvé");
    } finally {
      setLoading(false);
    }
  }, [moduleOrder]);

  useEffect(() => {
    loadCourse();
    loadUser();
  }, [loadCourse, loadUser]);

  const toggleSection = (index: number) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedSections(newExpanded);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
        >
          <Sparkles className="h-8 w-8 text-primary-400" />
        </motion.div>
      </div>
    );
  }

  if (isLocked) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
        <div className="max-w-3xl mx-auto px-4">
          <Card className="glass border-yellow-500/30">
            <CardContent className="py-12 text-center">
              <div className="inline-flex p-4 rounded-full bg-yellow-500/20 mb-6">
                <Lock className="h-8 w-8 text-yellow-400" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Contenu Premium</h2>
              <p className="text-muted-foreground mb-6">
                Ce cours est réservé aux abonnés Pro et Entreprise.
              </p>
              <div className="flex gap-4 justify-center">
                <Button variant="outline" onClick={() => router.back()}>
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Retour
                </Button>
                <Button
                  className="bg-gradient-primary hover:opacity-90 text-white"
                  onClick={() => setShowPremiumModal(true)}
                >
                  Passer à Pro
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
        <PremiumModal open={showPremiumModal} onOpenChange={setShowPremiumModal} />
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h1 className="text-2xl font-bold text-red-400 mb-4">{error}</h1>
          <Button variant="outline" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour
          </Button>
        </div>
      </div>
    );
  }

  const config = levelConfig[course.level as keyof typeof levelConfig] || levelConfig.easy;
  const keyPoints = course.key_points || [];
  const commonMistakes = course.common_mistakes || [];
  const emotionalTips = course.emotional_tips || [];
  const takeaways = course.takeaways || [];

  return (
    <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Button
            variant="ghost"
            className="mb-4"
            onClick={() => router.push("/learn?tab=courses")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour aux cours
          </Button>

          <div className="flex items-center gap-3 mb-4">
            <Badge variant="outline" className="bg-slate-800/50">
              Module {course.order ?? moduleOrder}
            </Badge>
            <Badge className={config.color}>{config.label}</Badge>
            <span className="flex items-center text-sm text-muted-foreground">
              <Clock className="h-4 w-4 mr-1" />
              {course.duration_minutes} min
            </span>
          </div>

          <h1 className="text-3xl font-bold mb-4">{course.title}</h1>

          <div className="p-4 rounded-lg bg-primary-500/10 border border-primary-500/20">
            <div className="flex items-start gap-3">
              <Target className="h-5 w-5 text-primary-400 mt-0.5 shrink-0" />
              <div>
                <p className="font-medium text-primary-400 mb-1">Objectif du cours</p>
                <p className="text-lg">{course.objective}</p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Contenu de lecture complet */}
        {course.full_content && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-8"
          >
            <Card className="glass">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-primary-400" />
                  Contenu du cours
                </CardTitle>
              </CardHeader>
              <CardContent>
                <MarkdownContent content={course.full_content} />
              </CardContent>
            </Card>
          </motion.div>
        )}

        {/* Résumé et points clés */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <BookOpen className="h-6 w-6 text-primary-400" />
            Résumé et points clés
          </h2>
          {/* Points clés */}
          {keyPoints.map((kp, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card className="glass overflow-hidden">
                <CardHeader
                  className="cursor-pointer hover:bg-white/5 transition-colors"
                  onClick={() => toggleSection(index)}
                >
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary-500/20 text-primary-400 font-bold text-sm">
                        {index + 1}
                      </div>
                      <Lightbulb className="h-5 w-5 text-yellow-400" />
                      {kp.title}
                    </CardTitle>
                    {expandedSections.has(index) ? (
                      <ChevronUp className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                </CardHeader>

                {expandedSections.has(index) && (
                  <CardContent className="space-y-6 pt-0">
                    {/* Résumé */}
                    <p className="text-lg leading-relaxed">{kp.summary}</p>

                    {/* Template si présent */}
                    {kp.template && (
                      <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20">
                        <p className="text-sm font-medium text-blue-400 mb-2">Template</p>
                        <p className="font-mono text-sm">{kp.template}</p>
                      </div>
                    )}

                    {/* Contenu structuré */}
                    {kp.content && (
                      <KeyPointContent content={kp.content as Record<string, unknown>} />
                    )}

                    {/* Checklist si présente */}
                    {kp.checklist && (
                      <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                        <p className="text-sm font-medium text-green-400 mb-3">Checklist</p>
                        <ul className="space-y-2">
                          {kp.checklist.map((item: string, i: number) => (
                            <li key={i} className="flex items-start gap-2">
                              <CheckCircle2 className="h-4 w-4 text-green-400 mt-0.5 shrink-0" />
                              <span className="text-sm">{item}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Warning si présent */}
                    {kp.warning && (
                      <div className="p-4 rounded-lg bg-orange-500/10 border border-orange-500/20">
                        <div className="flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 text-orange-400 mt-0.5 shrink-0" />
                          <p className="text-sm">{kp.warning}</p>
                        </div>
                      </div>
                    )}

                    {/* Exemple de dialogue */}
                    {kp.example_dialogue && (
                      <div className="space-y-4">
                        <h4 className="font-semibold flex items-center gap-2">
                          <MessageSquare className="h-4 w-4" />
                          Exemple de dialogue
                        </h4>

                        {kp.example_dialogue.context && (
                          <p className="text-sm text-muted-foreground italic">
                            Contexte : {kp.example_dialogue.context}
                          </p>
                        )}

                        {kp.example_dialogue.bad && (
                          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                            <p className="text-sm font-medium text-red-400 mb-1">
                              Ce qu&apos;il ne faut PAS faire :
                            </p>
                            <p className="text-sm">{kp.example_dialogue.bad}</p>
                            {kp.example_dialogue.why_bad && (
                              <p className="text-xs text-muted-foreground mt-2">
                                → {kp.example_dialogue.why_bad}
                              </p>
                            )}
                          </div>
                        )}

                        {kp.example_dialogue.good && (
                          <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                            <p className="text-sm font-medium text-green-400 mb-1">
                              Ce qu&apos;il faut faire :
                            </p>
                            <p className="text-sm">{kp.example_dialogue.good}</p>
                            {kp.example_dialogue.why_good && (
                              <p className="text-xs text-muted-foreground mt-2">
                                → {kp.example_dialogue.why_good}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            </motion.div>
          ))}

          {/* Erreurs courantes */}
          {commonMistakes.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: keyPoints.length * 0.1 }}
            >
              <Card className="glass border-orange-500/30">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5 text-orange-400" />
                    Erreurs courantes à éviter
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {commonMistakes.map((mistake, i) => (
                      <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-orange-500/10">
                        <span className="text-orange-400 font-bold shrink-0">{i + 1}.</span>
                        <span>{mistake}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Conseils émotionnels */}
          {emotionalTips.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: (keyPoints.length + 1) * 0.1 }}
            >
              <Card className="glass border-purple-500/30">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Heart className="h-5 w-5 text-purple-400" />
                    Conseils pour gérer vos émotions
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {emotionalTips.map((tip, i) => (
                      <li key={i} className="flex items-start gap-3 p-4 rounded-lg bg-purple-500/10 border border-purple-500/20">
                        <Sparkles className="h-5 w-5 text-purple-400 shrink-0 mt-0.5" />
                        <span>{tip}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Ce qu'il faut retenir */}
          {takeaways.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: (keyPoints.length + 2) * 0.1 }}
            >
              <Card className="glass border-green-500/30">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CheckCircle2 className="h-5 w-5 text-green-400" />
                    Ce qu&apos;il faut retenir
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {takeaways.map((takeaway, i) => (
                      <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-green-500/10 border border-green-500/20">
                        <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                        <span>{takeaway}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {/* Stat clé si présente */}
          {course.stat_cle && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: (keyPoints.length + 3) * 0.1 }}
            >
              <div className="p-6 rounded-2xl bg-gradient-to-r from-primary-500/20 to-purple-500/20 border border-primary-500/30 text-center">
                <p className="text-sm text-muted-foreground mb-2">Statistique clé</p>
                <p className="text-2xl font-bold gradient-text">{course.stat_cle}</p>
              </div>
            </motion.div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex justify-between mt-12 pt-8 border-t border-white/10">
          <Button
            variant="outline"
            onClick={() => router.push(moduleOrder > 1 ? `/learn/cours/${moduleOrder - 1}` : "/learn?tab=courses")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            {moduleOrder > 1 ? `Module ${moduleOrder - 1}` : "Retour"}
          </Button>

          <Button
            className="bg-gradient-primary hover:opacity-90 text-white"
            onClick={() => router.push(moduleOrder < 17 ? `/learn/cours/${moduleOrder + 1}` : "/learn?tab=courses")}
          >
            {moduleOrder < 17 ? `Module ${moduleOrder + 1}` : "Terminer"}
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  );
}
