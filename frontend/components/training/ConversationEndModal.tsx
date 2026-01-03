"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { CheckCircle2, MessageSquareOff, Clock, ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

type EndType = "mutual_goodbye" | "prospect_ending" | "user_ending";

interface ConversationEndModalProps {
  isVisible: boolean;
  endType: EndType;
  redirectUrl: string | null;
  sessionId: number;
  autoRedirectDelay?: number; // in ms, default 3000
}

const END_TYPE_INFO: Record<EndType, { icon: typeof CheckCircle2; title: string; description: string; color: string }> = {
  mutual_goodbye: {
    icon: CheckCircle2,
    title: "Conversation terminee",
    description: "Vous avez tous les deux conclu la conversation.",
    color: "text-green-400",
  },
  prospect_ending: {
    icon: MessageSquareOff,
    title: "Le prospect met fin",
    description: "Le prospect a signale qu'il devait partir.",
    color: "text-yellow-400",
  },
  user_ending: {
    icon: CheckCircle2,
    title: "Vous avez conclu",
    description: "Vous avez pris conge du prospect.",
    color: "text-blue-400",
  },
};

export function ConversationEndModal({
  isVisible,
  endType,
  redirectUrl,
  sessionId,
  autoRedirectDelay = 3000,
}: ConversationEndModalProps) {
  const router = useRouter();
  const [countdown, setCountdown] = useState(Math.ceil(autoRedirectDelay / 1000));
  const [isRedirecting, setIsRedirecting] = useState(false);

  const info = END_TYPE_INFO[endType];
  const Icon = info.icon;

  // Countdown and auto-redirect
  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    // Auto-redirect after delay
    const timeout = setTimeout(() => {
      setIsRedirecting(true);
      const url = redirectUrl || `/training/report/${sessionId}`;
      router.push(url);
    }, autoRedirectDelay);

    return () => {
      clearInterval(interval);
      clearTimeout(timeout);
    };
  }, [isVisible, autoRedirectDelay, redirectUrl, sessionId, router]);

  const handleRedirect = () => {
    setIsRedirecting(true);
    const url = redirectUrl || `/training/report/${sessionId}`;
    router.push(url);
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            className="glass rounded-2xl p-8 max-w-md mx-4 text-center"
          >
            {/* Icon */}
            <div className={cn(
              "w-20 h-20 rounded-full mx-auto mb-6 flex items-center justify-center",
              endType === "mutual_goodbye" && "bg-green-500/20",
              endType === "prospect_ending" && "bg-yellow-500/20",
              endType === "user_ending" && "bg-blue-500/20"
            )}>
              <Icon className={cn("h-10 w-10", info.color)} />
            </div>

            {/* Title */}
            <h2 className="text-2xl font-bold mb-2">{info.title}</h2>
            <p className="text-muted-foreground mb-6">{info.description}</p>

            {/* Countdown */}
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground mb-6">
              <Clock className="h-4 w-4" />
              <span>
                Redirection vers le rapport dans <span className="font-bold text-primary-400">{countdown}s</span>
              </span>
            </div>

            {/* Progress bar */}
            <div className="w-full h-1 bg-white/10 rounded-full mb-6 overflow-hidden">
              <motion.div
                initial={{ width: "100%" }}
                animate={{ width: "0%" }}
                transition={{ duration: autoRedirectDelay / 1000, ease: "linear" }}
                className="h-full bg-gradient-primary"
              />
            </div>

            {/* Button */}
            <Button
              onClick={handleRedirect}
              disabled={isRedirecting}
              className="bg-gradient-primary"
            >
              {isRedirecting ? (
                "Redirection..."
              ) : (
                <>
                  Voir le rapport maintenant
                  <ArrowRight className="h-4 w-4 ml-2" />
                </>
              )}
            </Button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
