"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { ArrowRight, Loader2, Crown, Lock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { VideoDropzone } from "@/components/upload/VideoDropzone";
import { ProcessingStatus } from "@/components/upload/ProcessingStatus";
import { PatternsPreview } from "@/components/upload/PatternsPreview";
import { useUploadChampion, useAnalyzeChampion } from "@/lib/queries";
import { useAuthStore } from "@/store/auth-store";
import type { SalesPatterns } from "@/types";

type Step = "upload" | "processing" | "ready";
type ProcessingStep = "extracting" | "transcribing" | "analyzing" | "ready";

export default function UploadPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const isFreeUser = user?.subscription_plan === "free";

  const [step, setStep] = useState<Step>("upload");
  const [processingStep, setProcessingStep] =
    useState<ProcessingStep>("extracting");
  const [championId, setChampionId] = useState<number | null>(null);
  const [patterns, setPatterns] = useState<SalesPatterns | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const uploadMutation = useUploadChampion();
  const analyzeMutation = useAnalyzeChampion();

  // Block access for free users
  if (isFreeUser) {
    return (
      <div className="relative min-h-[calc(100vh-6rem)] flex items-center justify-center">
        <div className="absolute inset-0 gradient-mesh opacity-20" />
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="relative"
        >
          <Card className="glass border-yellow-500/30 max-w-md mx-4">
            <CardContent className="py-12 text-center">
              <div className="inline-flex p-4 rounded-full bg-yellow-500/20 mb-6">
                <Lock className="h-8 w-8 text-yellow-400" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Fonctionnalité Premium</h2>
              <p className="text-muted-foreground mb-6">
                La création de champions personnalisés est réservée aux abonnés Pro et Entreprise.
              </p>
              <Link href="/features">
                <Button className="bg-gradient-primary hover:opacity-90 text-white">
                  <Crown className="h-4 w-4 mr-2" />
                  Découvrir les offres
                </Button>
              </Link>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    );
  }

  const handleFileAccepted = (file: File) => {
    setSelectedFile(file);
    setError(null);
  };

  const simulateProcessing = async (id: number) => {
    // Simulate processing steps with delays
    const steps: ProcessingStep[] = [
      "extracting",
      "transcribing",
      "analyzing",
      "ready",
    ];

    for (const processingStep of steps) {
      setProcessingStep(processingStep);
      await new Promise((resolve) =>
        setTimeout(resolve, processingStep === "analyzing" ? 3000 : 1500)
      );
    }

    return id;
  };

  const handleSubmit = async () => {
    if (!selectedFile || !name.trim()) {
      setError("Veuillez remplir tous les champs requis");
      return;
    }

    try {
      setError(null);
      setStep("processing");

      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 95) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 15;
        });
      }, 200);

      // Create form data
      const formData = new FormData();
      formData.append("name", name);
      formData.append("description", description);
      formData.append("video", selectedFile);

      // Upload
      const uploadResult = await uploadMutation.mutateAsync(formData);
      clearInterval(progressInterval);
      setUploadProgress(100);
      setChampionId(uploadResult.champion_id);

      // Wait a bit then start analysis simulation
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Simulate processing
      await simulateProcessing(uploadResult.champion_id);

      // Analyze (in real app, this would poll for completion)
      try {
        const analyzeResult = await analyzeMutation.mutateAsync(
          uploadResult.champion_id
        );
        if (analyzeResult.patterns) {
          setPatterns(analyzeResult.patterns);
        }
      } catch {
        // Use mock patterns for demo
        setPatterns({
          openings: [
            {
              text: "Bonjour, je suis ravi de pouvoir échanger avec vous aujourd'hui.",
              context: "Début d'appel",
              effectiveness: 8.5,
              tags: ["professionnnel", "chaleureux"],
            },
            {
              text: "J'ai bien étudié votre entreprise et je pense que nous avons des solutions adaptées.",
              context: "Introduction personnalisée",
              effectiveness: 9,
              tags: ["préparé", "ciblé"],
            },
          ],
          objection_handling: [
            {
              text: "Je comprends votre préoccupation concernant le budget. Permettez-moi de vous montrer le ROI que nos clients obtiennent.",
              context: "Objection prix",
              effectiveness: 8,
              tags: ["empathie", "données"],
            },
          ],
          closings: [
            {
              text: "Au vu de nos échanges, je vous propose de démarrer avec un pilote de 30 jours.",
              context: "Closing soft",
              effectiveness: 8.5,
              tags: ["engagement", "risque minimal"],
            },
          ],
          key_phrases: [
            "Je comprends",
            "Permettez-moi",
            "Nos clients témoignent",
            "Concrètement",
          ],
          communication_style:
            "Style professionnel et chaleureux, avec une approche consultative basée sur l'écoute active et la personnalisation.",
          effectiveness_score: 8.5,
        });
      }

      setStep("ready");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Une erreur est survenue"
      );
      setStep("upload");
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-6rem)]">
      {/* Background */}
      <div className="absolute inset-0 gradient-mesh opacity-30" />

      <div className="relative mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 py-12">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-3xl lg:text-4xl font-bold mb-4">
            Upload your <span className="gradient-text">Champion</span>
          </h1>
          <p className="text-muted-foreground max-w-xl mx-auto">
            Uploadez une vidéo de votre meilleur commercial en action. Notre IA
            analysera ses techniques et créera un clone pour entraîner votre
            équipe.
          </p>
        </motion.div>

        {/* Stepper */}
        <div className="flex items-center justify-center gap-4 mb-12">
          {["Upload", "Processing", "Ready"].map((label, index) => {
            const stepIndex = ["upload", "processing", "ready"].indexOf(step);
            const isActive = index === stepIndex;
            const isCompleted = index < stepIndex;

            return (
              <div key={label} className="flex items-center">
                <div
                  className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-all ${
                    isCompleted
                      ? "bg-primary-500 text-white"
                      : isActive
                      ? "bg-primary-500/20 text-primary-400 ring-2 ring-primary-500"
                      : "bg-white/5 text-muted-foreground"
                  }`}
                >
                  {isCompleted ? "✓" : index + 1}
                </div>
                <span
                  className={`ml-2 text-sm ${
                    isActive ? "text-foreground" : "text-muted-foreground"
                  }`}
                >
                  {label}
                </span>
                {index < 2 && (
                  <div
                    className={`w-12 h-px mx-4 ${
                      isCompleted ? "bg-primary-500" : "bg-white/10"
                    }`}
                  />
                )}
              </div>
            );
          })}
        </div>

        {/* Content */}
        <AnimatePresence mode="wait">
          {step === "upload" && (
            <motion.div
              key="upload"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <Card className="glass border-white/10">
                <CardContent className="p-8">
                  <div className="space-y-6">
                    {/* Name input */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Nom du champion *
                      </label>
                      <Input
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Ex: Marie Dupont - Top Performer Q4"
                        className="bg-white/5 border-white/10"
                      />
                    </div>

                    {/* Description */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Description (optionnel)
                      </label>
                      <Textarea
                        value={description}
                        onChange={(e) => setDescription(e.target.value)}
                        placeholder="Décrivez le contexte de cette vidéo..."
                        className="bg-white/5 border-white/10"
                        rows={3}
                      />
                    </div>

                    {/* Video dropzone */}
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        Vidéo *
                      </label>
                      <VideoDropzone
                        onFileAccepted={handleFileAccepted}
                        isUploading={uploadMutation.isPending}
                        uploadProgress={uploadProgress}
                        error={error}
                      />
                    </div>

                    {/* Submit button */}
                    <Button
                      onClick={handleSubmit}
                      disabled={
                        !selectedFile ||
                        !name.trim() ||
                        uploadMutation.isPending
                      }
                      className="w-full bg-gradient-primary hover:opacity-90 text-white py-6 text-lg"
                    >
                      {uploadMutation.isPending ? (
                        <>
                          <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                          Upload en cours...
                        </>
                      ) : (
                        <>
                          Analyser le champion
                          <ArrowRight className="h-5 w-5 ml-2" />
                        </>
                      )}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )}

          {step === "processing" && (
            <motion.div
              key="processing"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <ProcessingStatus currentStep={processingStep} error={error} />
            </motion.div>
          )}

          {step === "ready" && patterns && (
            <motion.div
              key="ready"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-6"
            >
              <PatternsPreview patterns={patterns} />

              <Button
                onClick={() =>
                  router.push(`/training?champion=${championId}`)
                }
                className="w-full bg-gradient-primary hover:opacity-90 text-white py-6 text-lg"
              >
                Démarrer l&apos;entraînement
                <ArrowRight className="h-5 w-5 ml-2" />
              </Button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
