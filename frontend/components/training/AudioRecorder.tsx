"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, Square, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface AudioRecorderProps {
  onRecordingComplete: (audioBase64: string) => void;
  disabled?: boolean;
  className?: string;
}

export function AudioRecorder({
  onRecordingComplete,
  disabled = false,
  className,
}: AudioRecorderProps) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isRecordingRef = useRef(false);

  // Keep ref in sync with state for keyboard handler
  useEffect(() => {
    isRecordingRef.current = isRecording;
  }, [isRecording]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startRecording = useCallback(async () => {
    if (disabled || isProcessing) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: "audio/webm;codecs=opus",
      });

      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        setIsProcessing(true);

        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        const reader = new FileReader();

        reader.onloadend = () => {
          const base64Audio = reader.result as string;
          // Remove the data URL prefix
          const base64Data = base64Audio.split(",")[1];
          onRecordingComplete(base64Data);
          setIsProcessing(false);
        };

        reader.readAsDataURL(audioBlob);

        // Stop all tracks
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(100); // Collect data every 100ms
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error("Error starting recording:", error);
    }
  }, [onRecordingComplete, disabled, isProcessing]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecordingRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, []);

  // Keyboard shortcut: Space to toggle recording
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Only handle Space key
      if (e.code !== "Space") return;

      // Don't trigger if user is typing in an input/textarea
      const target = e.target as HTMLElement;
      if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") return;

      // Don't trigger if disabled or processing
      if (disabled || isProcessing) return;

      // Prevent default space behavior (scrolling)
      e.preventDefault();

      // Toggle recording
      if (isRecordingRef.current) {
        stopRecording();
      } else {
        startRecording();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [disabled, isProcessing, startRecording, stopRecording]);

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className={cn("flex flex-col items-center gap-2", className)}>
      <AnimatePresence mode="wait">
        {isProcessing ? (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex items-center gap-2 text-muted-foreground"
          >
            <Loader2 className="h-5 w-5 animate-spin" />
            <span className="text-sm">Traitement...</span>
          </motion.div>
        ) : isRecording ? (
          <motion.div
            key="recording"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex items-center gap-3"
          >
            {/* Recording indicator */}
            <div className="flex items-center gap-2">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 1 }}
                className="w-3 h-3 bg-red-500 rounded-full"
              />
              <span className="text-sm font-mono text-red-400">
                {formatTime(recordingTime)}
              </span>
            </div>

            {/* Waveform animation */}
            <div className="flex items-center gap-0.5 h-8">
              {[...Array(5)].map((_, i) => (
                <motion.div
                  key={i}
                  animate={{
                    height: ["40%", "100%", "40%"],
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 0.5,
                    delay: i * 0.1,
                  }}
                  className="w-1 bg-red-500 rounded-full"
                />
              ))}
            </div>

            {/* Stop button */}
            <Button
              onClick={stopRecording}
              variant="destructive"
              size="icon"
              className="h-12 w-12 rounded-full"
              title="Arrêter (Espace)"
            >
              <Square className="h-5 w-5" />
            </Button>
          </motion.div>
        ) : (
          <motion.div
            key="idle"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="flex flex-col items-center gap-1"
          >
            <Button
              onClick={startRecording}
              disabled={disabled}
              className={cn(
                "h-14 w-14 rounded-full",
                "bg-gradient-primary hover:opacity-90",
                "shadow-lg shadow-primary-500/25"
              )}
              title="Enregistrer (Espace)"
            >
              <Mic className="h-6 w-6" />
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Keyboard shortcut hint */}
      {!isProcessing && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs text-muted-foreground"
        >
          {isRecording ? "Espace pour arrêter" : "Espace pour parler"}
        </motion.p>
      )}
    </div>
  );
}
