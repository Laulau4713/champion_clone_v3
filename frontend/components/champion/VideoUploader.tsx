"use client";

import React, { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import { Upload, Video, X, Loader2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Progress } from "@/components/ui/progress";
import { cn, formatFileSize } from "@/lib/utils";

interface VideoUploaderProps {
  onUpload: (file: File, name: string, description?: string) => Promise<void>;
  isUploading: boolean;
  progress: number;
  status: "idle" | "uploading" | "processing" | "analyzing" | "complete" | "error";
  statusMessage: string;
}

const MAX_FILE_SIZE = 100 * 1024 * 1024; // 100MB
const ACCEPTED_TYPES = {
  "video/mp4": [".mp4"],
  "video/quicktime": [".mov"],
};

export const VideoUploader: React.FC<VideoUploaderProps> = ({
  onUpload,
  isUploading,
  progress,
  status,
  statusMessage,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: unknown[]) => {
    setError(null);

    if (rejectedFiles.length > 0) {
      setError("Format non supporté. Utilisez MP4 ou MOV (max 100MB).");
      return;
    }

    const videoFile = acceptedFiles[0];
    if (!videoFile) return;

    if (videoFile.size > MAX_FILE_SIZE) {
      setError(`Fichier trop volumineux (${formatFileSize(videoFile.size)}). Maximum: 100MB`);
      return;
    }

    setFile(videoFile);
    setName(videoFile.name.replace(/\.[^/.]+$/, "")); // Remove extension

    // Create video preview
    const url = URL.createObjectURL(videoFile);
    setPreview(url);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_TYPES,
    maxFiles: 1,
    disabled: isUploading || status === "complete",
  });

  const handleRemove = () => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }
    setFile(null);
    setPreview(null);
    setName("");
    setDescription("");
    setError(null);
  };

  const handleSubmit = async () => {
    if (!file || !name.trim()) {
      setError("Veuillez renseigner un nom pour le champion.");
      return;
    }

    try {
      await onUpload(file, name.trim(), description.trim() || undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur lors de l'upload");
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case "uploading":
      case "processing":
      case "analyzing":
        return <Loader2 className="h-5 w-5 animate-spin text-primary-400" />;
      case "complete":
        return <CheckCircle className="h-5 w-5 text-success-400" />;
      default:
        return null;
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={cn(
          "relative border-2 border-dashed rounded-xl p-8 transition-all cursor-pointer",
          "hover:border-primary-400 hover:bg-primary-500/5",
          isDragActive && "border-primary-400 bg-primary-500/10",
          file && "border-success-500/50 bg-success-500/5",
          error && "border-error-500/50",
          (isUploading || status === "complete") && "pointer-events-none opacity-75"
        )}
      >
        <input {...getInputProps()} />

        <AnimatePresence mode="wait">
          {!file ? (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex flex-col items-center justify-center text-center"
            >
              <div className="w-16 h-16 rounded-full bg-primary-500/10 flex items-center justify-center mb-4">
                <Upload className="h-8 w-8 text-primary-400" />
              </div>
              <h3 className="text-lg font-semibold text-white mb-2">
                {isDragActive ? "Déposez la vidéo ici" : "Glissez-déposez votre vidéo"}
              </h3>
              <p className="text-sm text-slate-400 mb-4">
                ou cliquez pour sélectionner un fichier
              </p>
              <p className="text-xs text-slate-500">
                Formats supportés: MP4, MOV • Taille max: 100MB
              </p>
            </motion.div>
          ) : (
            <motion.div
              key="preview"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="flex items-center gap-4"
            >
              {/* Video Preview */}
              <div className="relative w-32 h-20 rounded-lg overflow-hidden bg-slate-700 flex-shrink-0">
                {preview && (
                  <video
                    src={preview}
                    className="w-full h-full object-cover"
                    muted
                  />
                )}
                <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                  <Video className="h-6 w-6 text-white" />
                </div>
              </div>

              {/* File Info */}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{file.name}</p>
                <p className="text-xs text-slate-400">{formatFileSize(file.size)}</p>
              </div>

              {/* Remove Button */}
              {status === "idle" && (
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleRemove();
                  }}
                  className="flex-shrink-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Error Message */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-sm text-error-400 text-center"
        >
          {error}
        </motion.p>
      )}

      {/* Form Fields */}
      <AnimatePresence>
        {file && status === "idle" && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="space-y-4"
          >
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Nom du champion *
              </label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Ex: Marie Dupont - Meilleure vendeuse 2024"
                disabled={isUploading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Description (optionnel)
              </label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Ex: Spécialiste B2B, 15 ans d'expérience"
                disabled={isUploading}
              />
            </div>

            <Button
              onClick={handleSubmit}
              disabled={!name.trim() || isUploading}
              loading={isUploading}
              className="w-full"
              size="lg"
            >
              <Upload className="mr-2 h-4 w-4" />
              Uploader et analyser
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Progress Section */}
      <AnimatePresence>
        {status !== "idle" && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="space-y-4 p-4 rounded-lg bg-slate-800/50 border border-slate-700/50"
          >
            {/* Status */}
            <div className="flex items-center gap-3">
              {getStatusIcon()}
              <span className="text-sm text-slate-300">{statusMessage}</span>
            </div>

            {/* Progress Bar */}
            {status === "uploading" && (
              <Progress value={progress} className="h-2" />
            )}

            {/* Steps */}
            <div className="flex justify-between text-xs text-slate-500">
              <span className={cn(progress > 0 && "text-primary-400")}>
                1. Upload
              </span>
              <span className={cn(status === "processing" && "text-primary-400")}>
                2. Traitement
              </span>
              <span className={cn(status === "analyzing" && "text-primary-400")}>
                3. Analyse
              </span>
              <span className={cn(status === "complete" && "text-success-400")}>
                4. Terminé
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default VideoUploader;
