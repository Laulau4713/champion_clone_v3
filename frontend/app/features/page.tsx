"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Mic,
  Brain,
  BarChart3,
  ArrowRight,
  CheckCircle2,
  Target,
  TrendingUp,
  MessageSquare,
  Gauge,
  Shield,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.5 },
};

const staggerContainer = {
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const features = [
  {
    icon: Mic,
    title: "Entraînement Vocal Réaliste",
    description:
      "Pratiquez avec un prospect IA qui réagit naturellement à votre voix. Transcription automatique et feedback en temps réel.",
    gradient: "from-violet-500 to-purple-500",
  },
  {
    icon: Gauge,
    title: "Jauge Émotionnelle",
    description:
      "Suivez l'humeur du prospect en temps réel. Apprenez à identifier les signaux d'achat et à éviter les erreurs fatales.",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    icon: Brain,
    title: "Analyse Comportementale",
    description:
      "Notre IA détecte vos patterns positifs et négatifs. Recevez des conseils personnalisés pour progresser rapidement.",
    gradient: "from-emerald-500 to-teal-500",
  },
];

const howItWorks = [
  {
    step: "01",
    title: "Choisissez votre compétence",
    description:
      "Écoute active, gestion des objections, closing... Sélectionnez la compétence à travailler parmi notre programme structuré.",
  },
  {
    step: "02",
    title: "Lancez une session",
    description:
      "Un prospect IA réaliste vous appelle. Répondez par la voix ou par texte. Le prospect réagit à vos arguments en temps réel.",
  },
  {
    step: "03",
    title: "Progressez avec le feedback",
    description:
      "Analysez votre performance avec des métriques précises. Identifiez vos points forts et vos axes d'amélioration.",
  },
];

const benefits = [
  {
    icon: Target,
    title: "Scénarios réalistes",
    description: "Adaptés à votre secteur : immobilier, SaaS, assurance...",
  },
  {
    icon: TrendingUp,
    title: "Progression mesurable",
    description: "Suivez votre évolution avec des scores détaillés.",
  },
  {
    icon: MessageSquare,
    title: "Feedback instantané",
    description: "Corrigez vos erreurs immédiatement, pas après le deal perdu.",
  },
  {
    icon: Shield,
    title: "Environnement sécurisé",
    description: "Faites vos erreurs ici, pas devant vos vrais prospects.",
  },
];

export default function FeaturesPage() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-950 via-gray-900 to-gray-950">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Background gradient effects */}
        <div className="absolute inset-0 bg-gradient-to-r from-violet-600/10 via-transparent to-cyan-600/10" />
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-cyan-500/20 rounded-full blur-3xl" />

        <div className="relative container mx-auto px-4 py-24 sm:py-32">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="text-center max-w-4xl mx-auto"
          >
            <Badge className="mb-6 bg-violet-500/10 text-violet-400 border-violet-500/20 px-4 py-1.5">
              <Sparkles className="w-4 h-4 mr-2" />
              Essai gratuit - 3 sessions offertes
            </Badge>

            <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold text-white mb-6 leading-tight">
              Devenez un{" "}
              <span className="bg-gradient-to-r from-violet-400 to-cyan-400 bg-clip-text text-transparent">
                champion de la vente
              </span>
            </h1>

            <p className="text-xl text-gray-400 mb-8 max-w-2xl mx-auto">
              Entraînez-vous avec un prospect IA ultra-réaliste. Maîtrisez
              l&apos;écoute active, gérez les objections, et closez plus de
              deals.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/register">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-xl"
                >
                  Commencer gratuitement
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link href="/login">
                <Button
                  size="lg"
                  variant="outline"
                  className="border-gray-700 text-white hover:bg-gray-800 px-8 py-6 text-lg rounded-xl"
                >
                  Se connecter
                </Button>
              </Link>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 relative">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              3 piliers pour votre progression
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              Une approche complète pour transformer votre technique de vente
            </p>
          </motion.div>

          <motion.div
            variants={staggerContainer}
            initial="initial"
            whileInView="animate"
            viewport={{ once: true }}
            className="grid md:grid-cols-3 gap-8"
          >
            {features.map((feature, index) => (
              <motion.div key={feature.title} variants={fadeInUp}>
                <Card className="bg-gray-900/50 border-gray-800 h-full hover:border-gray-700 transition-colors group">
                  <CardContent className="p-8">
                    <div
                      className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform`}
                    >
                      <feature.icon className="h-7 w-7 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold text-white mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-gray-400">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-24 bg-gray-900/50">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Comment ça marche ?
            </h2>
            <p className="text-gray-400 text-lg max-w-2xl mx-auto">
              3 étapes simples pour commencer votre entraînement
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {howItWorks.map((step, index) => (
              <motion.div
                key={step.step}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                {/* Connector line */}
                {index < howItWorks.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[60%] w-full h-0.5 bg-gradient-to-r from-violet-500/50 to-transparent" />
                )}

                <div className="text-center">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-violet-600 to-purple-600 flex items-center justify-center mx-auto mb-6">
                    <span className="text-2xl font-bold text-white">
                      {step.step}
                    </span>
                  </div>
                  <h3 className="text-xl font-semibold text-white mb-3">
                    {step.title}
                  </h3>
                  <p className="text-gray-400">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-24">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              Pourquoi les commerciaux nous choisissent
            </h2>
          </motion.div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
            {benefits.map((benefit, index) => (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="text-center p-6"
              >
                <div className="w-12 h-12 rounded-lg bg-gray-800 flex items-center justify-center mx-auto mb-4">
                  <benefit.icon className="h-6 w-6 text-violet-400" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {benefit.title}
                </h3>
                <p className="text-gray-400 text-sm">{benefit.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-600/20 via-transparent to-cyan-600/20" />

        <div className="relative container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-3xl mx-auto"
          >
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
              Prêt à devenir un champion ?
            </h2>
            <p className="text-xl text-gray-400 mb-8">
              Commencez avec 3 sessions gratuites. Aucune carte bancaire
              requise.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/register">
                <Button
                  size="lg"
                  className="bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-xl"
                >
                  Commencer gratuitement
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            </div>

            <div className="mt-8 flex items-center justify-center gap-8 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>3 sessions offertes</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Sans engagement</span>
              </div>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span>Résultats immédiats</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-gray-800">
        <div className="container mx-auto px-4 text-center text-gray-500 text-sm">
          <p>Champion Clone - Plateforme d&apos;entraînement commercial</p>
        </div>
      </footer>
    </div>
  );
}
