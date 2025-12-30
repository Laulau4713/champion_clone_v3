"use client";

import { motion } from "framer-motion";
import {
  Loader2,
  AudioWaveform,
  Brain,
  FileText,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

type ProcessingStep = "extracting" | "transcribing" | "analyzing" | "ready";
type StepStatus = "pending" | "processing" | "completed" | "error";

interface ProcessingStatusProps {
  currentStep: ProcessingStep;
  error?: string | null;
}

const steps = [
  {
    id: "extracting" as const,
    label: "Extraction audio",
    description: "Extraction de la piste audio de la vidéo...",
    icon: AudioWaveform,
  },
  {
    id: "transcribing" as const,
    label: "Transcription",
    description: "Transcription avec Whisper AI...",
    icon: FileText,
  },
  {
    id: "analyzing" as const,
    label: "Analyse patterns",
    description: "Extraction des techniques de vente avec Claude...",
    icon: Brain,
  },
  {
    id: "ready" as const,
    label: "Prêt",
    description: "Votre champion est prêt pour l'entraînement!",
    icon: CheckCircle2,
  },
];

export function ProcessingStatus({
  currentStep,
  error,
}: ProcessingStatusProps) {
  const getStepStatus = (stepId: ProcessingStep): StepStatus => {
    const currentIndex = steps.findIndex((s) => s.id === currentStep);
    const stepIndex = steps.findIndex((s) => s.id === stepId);

    if (error && stepId === currentStep) return "error";
    if (stepIndex < currentIndex) return "completed";
    if (stepIndex === currentIndex) return "processing";
    return "pending";
  };

  return (
    <div className="glass rounded-2xl p-8">
      <div className="space-y-6">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id);
          const isLast = index === steps.length - 1;

          return (
            <div key={step.id} className="relative">
              <div className="flex items-start gap-4">
                {/* Step icon */}
                <div
                  className={cn(
                    "relative flex items-center justify-center w-10 h-10 rounded-full flex-shrink-0 transition-all duration-300",
                    status === "completed" &&
                      "bg-green-500/20 text-green-400",
                    status === "processing" &&
                      "bg-primary-500/20 text-primary-400",
                    status === "pending" &&
                      "bg-white/5 text-muted-foreground",
                    status === "error" && "bg-red-500/20 text-red-400"
                  )}
                >
                  {status === "processing" ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : status === "completed" ? (
                    <CheckCircle2 className="h-5 w-5" />
                  ) : status === "error" ? (
                    <AlertCircle className="h-5 w-5" />
                  ) : (
                    <step.icon className="h-5 w-5" />
                  )}

                  {/* Pulse animation for processing */}
                  {status === "processing" && (
                    <motion.div
                      className="absolute inset-0 rounded-full bg-primary-500/30"
                      animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                      transition={{
                        duration: 1.5,
                        repeat: Infinity,
                        ease: "easeOut",
                      }}
                    />
                  )}
                </div>

                {/* Step content */}
                <div className="flex-1 min-w-0">
                  <h3
                    className={cn(
                      "font-medium mb-1 transition-colors",
                      status === "completed" && "text-green-400",
                      status === "processing" && "text-foreground",
                      status === "pending" && "text-muted-foreground",
                      status === "error" && "text-red-400"
                    )}
                  >
                    {step.label}
                  </h3>
                  <p
                    className={cn(
                      "text-sm",
                      status === "processing"
                        ? "text-muted-foreground"
                        : "text-muted-foreground/50"
                    )}
                  >
                    {status === "error" ? error : step.description}
                  </p>
                </div>
              </div>

              {/* Connector line */}
              {!isLast && (
                <div
                  className={cn(
                    "absolute left-5 top-12 w-px h-6 transition-colors",
                    status === "completed"
                      ? "bg-green-500/50"
                      : "bg-white/10"
                  )}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
