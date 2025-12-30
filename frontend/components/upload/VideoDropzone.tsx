"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload,
  Video,
  X,
  FileVideo,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { cn, formatFileSize } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";

interface VideoDropzoneProps {
  onFileAccepted: (file: File) => void;
  isUploading?: boolean;
  uploadProgress?: number;
  error?: string | null;
}

export function VideoDropzone({
  onFileAccepted,
  isUploading = false,
  uploadProgress = 0,
  error = null,
}: VideoDropzoneProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (file) {
        setSelectedFile(file);
        setPreviewUrl(URL.createObjectURL(file));
        onFileAccepted(file);
      }
    },
    [onFileAccepted]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } =
    useDropzone({
      onDrop,
      accept: {
        "video/mp4": [".mp4"],
        "video/quicktime": [".mov"],
        "video/x-msvideo": [".avi"],
      },
      maxSize: 100 * 1024 * 1024, // 100MB
      multiple: false,
      disabled: isUploading,
    });

  const clearFile = () => {
    setSelectedFile(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
  };

  return (
    <div className="w-full">
      <AnimatePresence mode="wait">
        {!selectedFile ? (
          <motion.div
            key="dropzone"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
          >
            <div
              {...getRootProps()}
              className={cn(
                "relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300",
                isDragActive && !isDragReject
                  ? "border-primary-500 bg-primary-500/10"
                  : isDragReject
                  ? "border-red-500 bg-red-500/10"
                  : "border-white/20 hover:border-primary-500/50 hover:bg-white/5"
              )}
            >
              <input {...getInputProps()} />

              <div className="flex flex-col items-center gap-4">
                <motion.div
                  animate={{
                    scale: isDragActive ? 1.1 : 1,
                    rotate: isDragActive ? 5 : 0,
                  }}
                  className={cn(
                    "p-4 rounded-2xl",
                    isDragActive
                      ? "bg-primary-500/20"
                      : "bg-white/5"
                  )}
                >
                  {isDragReject ? (
                    <AlertCircle className="h-12 w-12 text-red-400" />
                  ) : (
                    <Upload className="h-12 w-12 text-primary-400" />
                  )}
                </motion.div>

                <div>
                  <p className="text-lg font-medium mb-1">
                    {isDragActive
                      ? isDragReject
                        ? "Format non supporté"
                        : "Déposez votre vidéo ici"
                      : "Glissez-déposez votre vidéo"}
                  </p>
                  <p className="text-sm text-muted-foreground">
                    ou cliquez pour sélectionner un fichier
                  </p>
                </div>

                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <FileVideo className="h-3 w-3" />
                    MP4, MOV, AVI
                  </span>
                  <span>Max 100MB</span>
                </div>
              </div>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="glass rounded-2xl p-6"
          >
            <div className="flex items-start gap-4">
              {/* Video preview */}
              <div className="relative w-32 h-20 rounded-lg overflow-hidden bg-black flex-shrink-0">
                {previewUrl ? (
                  <video
                    src={previewUrl}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="flex items-center justify-center h-full">
                    <Video className="h-8 w-8 text-muted-foreground" />
                  </div>
                )}
              </div>

              {/* File info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="font-medium truncate">{selectedFile.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatFileSize(selectedFile.size)}
                    </p>
                  </div>
                  {!isUploading && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="flex-shrink-0"
                      onClick={clearFile}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>

                {/* Progress bar */}
                {isUploading && (
                  <div className="mt-4">
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-muted-foreground">
                        Upload en cours...
                      </span>
                      <span className="font-medium">{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} className="h-2" />
                  </div>
                )}

                {/* Success state */}
                {uploadProgress === 100 && !error && (
                  <div className="mt-4 flex items-center gap-2 text-sm text-green-400">
                    <CheckCircle2 className="h-4 w-4" />
                    Upload terminé
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error message */}
      {error && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30 flex items-center gap-3"
        >
          <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0" />
          <p className="text-sm text-red-400">{error}</p>
        </motion.div>
      )}
    </div>
  );
}
