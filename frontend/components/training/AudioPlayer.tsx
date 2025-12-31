"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Play, Pause, Volume2, VolumeX } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";

interface AudioPlayerProps {
  audioBase64?: string;
  audioUrl?: string;
  autoPlay?: boolean;
  onEnded?: () => void;
  className?: string;
}

export function AudioPlayer({
  audioBase64,
  audioUrl,
  autoPlay = false,
  onEnded,
  className,
}: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(1);

  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Create audio source
  const audioSrc = audioBase64
    ? `data:audio/mp3;base64,${audioBase64}`
    : audioUrl || "";

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;

    const handleLoadedMetadata = () => {
      setDuration(audio.duration);
    };

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime);
    };

    const handleEnded = () => {
      setIsPlaying(false);
      setCurrentTime(0);
      onEnded?.();
    };

    audio.addEventListener("loadedmetadata", handleLoadedMetadata);
    audio.addEventListener("timeupdate", handleTimeUpdate);
    audio.addEventListener("ended", handleEnded);

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata);
      audio.removeEventListener("timeupdate", handleTimeUpdate);
      audio.removeEventListener("ended", handleEnded);
    };
  }, [onEnded]);

  useEffect(() => {
    if (autoPlay && audioRef.current && audioSrc) {
      audioRef.current.play().catch(console.error);
      setIsPlaying(true);
    }
  }, [autoPlay, audioSrc]);

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(console.error);
    }
    setIsPlaying(!isPlaying);
  };

  const toggleMute = () => {
    if (!audioRef.current) return;
    audioRef.current.muted = !isMuted;
    setIsMuted(!isMuted);
  };

  const handleVolumeChange = (value: number[]) => {
    if (!audioRef.current) return;
    const newVolume = value[0];
    audioRef.current.volume = newVolume;
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
  };

  const handleSeek = (value: number[]) => {
    if (!audioRef.current) return;
    const newTime = value[0];
    audioRef.current.currentTime = newTime;
    setCurrentTime(newTime);
  };

  const formatTime = (seconds: number) => {
    if (!isFinite(seconds)) return "0:00";
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, "0")}`;
  };

  if (!audioSrc) return null;

  return (
    <div className={cn("glass rounded-xl p-3", className)}>
      <audio ref={audioRef} src={audioSrc} preload="metadata" />

      <div className="flex items-center gap-3">
        {/* Play/Pause button */}
        <Button
          onClick={togglePlay}
          variant="ghost"
          size="icon"
          className="h-10 w-10 rounded-full bg-primary-500/20 hover:bg-primary-500/30"
        >
          {isPlaying ? (
            <Pause className="h-5 w-5 text-primary-400" />
          ) : (
            <Play className="h-5 w-5 text-primary-400 ml-0.5" />
          )}
        </Button>

        {/* Progress bar */}
        <div className="flex-1 flex items-center gap-2">
          <span className="text-xs text-muted-foreground font-mono w-10">
            {formatTime(currentTime)}
          </span>

          <Slider
            value={[currentTime]}
            max={duration || 100}
            step={0.1}
            onValueChange={handleSeek}
            className="flex-1"
          />

          <span className="text-xs text-muted-foreground font-mono w-10">
            {formatTime(duration)}
          </span>
        </div>

        {/* Volume controls */}
        <div className="flex items-center gap-2">
          <Button
            onClick={toggleMute}
            variant="ghost"
            size="icon"
            className="h-8 w-8"
          >
            {isMuted || volume === 0 ? (
              <VolumeX className="h-4 w-4 text-muted-foreground" />
            ) : (
              <Volume2 className="h-4 w-4 text-muted-foreground" />
            )}
          </Button>

          <Slider
            value={[isMuted ? 0 : volume]}
            max={1}
            step={0.1}
            onValueChange={handleVolumeChange}
            className="w-20"
          />
        </div>
      </div>

      {/* Waveform visualization (simplified) */}
      <motion.div className="mt-2 flex items-center justify-center gap-0.5 h-8">
        {[...Array(30)].map((_, i) => (
          <motion.div
            key={i}
            animate={
              isPlaying
                ? {
                    height: ["20%", `${Math.random() * 100}%`, "20%"],
                  }
                : { height: "20%" }
            }
            transition={{
              repeat: isPlaying ? Infinity : 0,
              duration: 0.3 + Math.random() * 0.2,
              delay: i * 0.02,
            }}
            className="w-1 bg-primary-500/50 rounded-full"
          />
        ))}
      </motion.div>
    </div>
  );
}
