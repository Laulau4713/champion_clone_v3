"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Mic,
  Brain,
  BarChart3,
  ArrowRight,
  CheckCircle2,
  Users,
  Trophy,
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
    title: "Entraînement Vocal",
    description:
      "Pratiquez avec des simulations vocales réalistes. L'IA adapte le prospect selon votre niveau.",
    gradient: "from-violet-500 to-purple-500",
  },
  {
    icon: Brain,
    title: "Analyse des Patterns",
    description:
      "Apprenez les techniques des meilleurs commerciaux grâce à notre système pédagogique structuré.",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    icon: BarChart3,
    title: "Feedback en Temps Réel",
    description:
      "Suivez votre progression avec la jauge émotionnelle et recevez des conseils personnalisés.",
    gradient: "from-emerald-500 to-teal-500",
  },
];

const stats = [
  { value: "15", label: "Cours structurés" },
  { value: "13", label: "Compétences clés" },
  { value: "3", label: "Niveaux de difficulté" },
];

const pricingPlans = [
  {
    name: "Essai Gratuit",
    price: "0",
    description: "Découvrez la plateforme",
    features: [
      "1 cours d'introduction",
      "1 quiz de compétence",
      "3 sessions d'entraînement",
      "Niveau facile uniquement",
    ],
  },
  {
    name: "Pro",
    price: "49",
    description: "Pour les commerciaux ambitieux",
    features: [
      "15 cours complets",
      "13 quiz de compétences",
      "Sessions illimitées",
      "Tous les niveaux",
      "Feedback avancé",
    ],
    popular: true,
  },
  {
    name: "Entreprise",
    price: "Sur mesure",
    description: "Pour les équipes commerciales",
    features: [
      "Tout le plan Pro",
      "Tableau de bord équipe",
      "Champions personnalisés",
      "Support dédié",
      "Formation sur site",
    ],
  },
];

export default function HomePage() {
  return (
    <div className="relative overflow-hidden">
      {/* Background gradient mesh */}
      <div className="absolute inset-0 gradient-mesh opacity-50" />

      {/* Hero Section */}
      <section className="relative py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center max-w-4xl mx-auto"
            initial="initial"
            animate="animate"
            variants={staggerContainer}
          >
            <motion.div variants={fadeInUp} className="mb-6">
              <Badge className="bg-primary-500/20 text-primary-400 border-primary-500/30 px-4 py-1">
                <Sparkles className="h-3 w-3 mr-1 inline" />
                Plateforme d&apos;entraînement IA
              </Badge>
            </motion.div>

            <motion.h1
              variants={fadeInUp}
              className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight mb-6"
            >
              Devenez un{" "}
              <span className="gradient-text">Champion de la Vente</span>
            </motion.h1>

            <motion.p
              variants={fadeInUp}
              className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto"
            >
              Maîtrisez l&apos;art de la vente grâce à notre programme de 15 jours.
              Cours structurés, quiz de validation et entraînements vocaux avec
              IA pour devenir un commercial d&apos;élite.
            </motion.p>

            <motion.div
              variants={fadeInUp}
              className="flex flex-col sm:flex-row gap-4 justify-center"
            >
              <Button
                asChild
                size="lg"
                className="bg-gradient-primary hover:opacity-90 text-white text-lg px-8 py-6 rounded-xl"
              >
                <Link href="/register" className="inline-flex items-center">
                  <span>Essai Gratuit</span>
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="text-lg px-8 py-6 rounded-xl border-white/20 hover:bg-white/5"
              >
                <Link href="/features">En savoir plus</Link>
              </Button>
            </motion.div>
          </motion.div>

          {/* Stats */}
          <motion.div
            className="mt-20 grid grid-cols-1 sm:grid-cols-3 gap-8 max-w-3xl mx-auto"
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <div className="text-3xl font-bold gradient-text">
                  {stat.value}
                </div>
                <div className="text-sm text-muted-foreground mt-1">
                  {stat.label}
                </div>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="relative py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Une méthode{" "}
              <span className="gradient-text">éprouvée</span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Notre programme combine théorie, pratique et feedback pour une
              progression rapide et mesurable.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="glass border-white/10 h-full hover:border-primary-500/50 transition-all duration-300 group">
                  <CardContent className="p-8">
                    <div
                      className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${feature.gradient} mb-6 group-hover:scale-110 transition-transform`}
                    >
                      <feature.icon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="text-xl font-semibold mb-3">
                      {feature.title}
                    </h3>
                    <p className="text-muted-foreground">
                      {feature.description}
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="relative py-20 lg:py-32 bg-white/[0.02]">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Comment ça <span className="gradient-text">marche</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Apprenez",
                description:
                  "Suivez nos cours quotidiens pour maîtriser les fondamentaux de la vente",
                icon: Users,
              },
              {
                step: "02",
                title: "Validez",
                description:
                  "Testez vos connaissances avec des quiz pour chaque compétence",
                icon: Brain,
              },
              {
                step: "03",
                title: "Pratiquez",
                description:
                  "Entraînez-vous avec notre IA qui simule des prospects réalistes",
                icon: Trophy,
              },
            ].map((item, index) => (
              <motion.div
                key={item.step}
                className="relative"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
              >
                <div className="text-8xl font-bold text-primary-500/10 absolute -top-8 left-0">
                  {item.step}
                </div>
                <div className="relative pt-12">
                  <div className="inline-flex p-3 rounded-xl bg-primary-500/20 mb-4">
                    <item.icon className="h-6 w-6 text-primary-400" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
                  <p className="text-muted-foreground">{item.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="relative py-20 lg:py-32">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <motion.div
            className="text-center mb-16"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-3xl lg:text-5xl font-bold mb-4">
              Tarifs{" "}
              <span className="gradient-text">simples et transparents</span>
            </h2>
            <p className="text-xl text-muted-foreground">
              Commencez gratuitement, passez à Pro quand vous êtes prêt
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {pricingPlans.map((plan, index) => (
              <motion.div
                key={plan.name}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card
                  className={`glass border-white/10 h-full relative ${
                    plan.popular ? "border-primary-500/50" : ""
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-gradient-primary text-white border-0">
                        Populaire
                      </Badge>
                    </div>
                  )}
                  <CardContent className="p-8">
                    <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      {plan.description}
                    </p>
                    <div className="mb-6">
                      {plan.price !== "Sur mesure" ? (
                        <>
                          <span className="text-4xl font-bold">{plan.price}€</span>
                          <span className="text-muted-foreground">/mois</span>
                        </>
                      ) : (
                        <span className="text-4xl font-bold">{plan.price}</span>
                      )}
                    </div>
                    <ul className="space-y-3 mb-8">
                      {plan.features.map((feature) => (
                        <li
                          key={feature}
                          className="flex items-center text-sm"
                        >
                          <CheckCircle2 className="h-4 w-4 text-primary-400 mr-3 flex-shrink-0" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <Button
                      asChild
                      className={`w-full ${
                        plan.popular
                          ? "bg-gradient-primary hover:opacity-90 text-white"
                          : "bg-white/10 hover:bg-white/20"
                      }`}
                    >
                      <Link href={plan.price === "0" ? "/register" : "/register"}>
                        {plan.price === "Sur mesure"
                          ? "Nous contacter"
                          : plan.price === "0"
                          ? "Commencer gratuitement"
                          : "Choisir ce plan"}
                      </Link>
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="relative py-20 lg:py-32">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <Card className="glass border-primary-500/30 overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 to-secondary-500/10" />
              <CardContent className="relative p-12">
                <h2 className="text-3xl lg:text-4xl font-bold mb-4">
                  Prêt à devenir un champion ?
                </h2>
                <p className="text-xl text-muted-foreground mb-8">
                  Commencez votre parcours dès aujourd&apos;hui. Aucune carte
                  bancaire requise.
                </p>
                <Button
                  asChild
                  size="lg"
                  className="bg-gradient-primary hover:opacity-90 text-white text-lg px-8 py-6 rounded-xl"
                >
                  <Link href="/register" className="inline-flex items-center">
                    <span>Démarrer l&apos;essai gratuit</span>
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
