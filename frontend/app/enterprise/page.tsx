"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import {
  Building2,
  Video,
  Brain,
  Users,
  BarChart3,
  Shield,
  Headphones,
  ArrowRight,
  Check,
  Sparkles,
  Upload,
  Mic,
  Target,
  Award,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const championFeatures = [
  {
    icon: Video,
    title: "Analyse vidéo de vos champions",
    description: "Uploadez les appels de vos meilleurs commerciaux et laissez l'IA extraire leurs techniques gagnantes.",
  },
  {
    icon: Brain,
    title: "Extraction de patterns",
    description: "Notre IA Claude identifie les phrases d'accroche, techniques d'objection et closes qui convertissent.",
  },
  {
    icon: Mic,
    title: "Clonage de style",
    description: "Entraînez vos équipes à reproduire les patterns de vos champions avec des simulations personnalisées.",
  },
  {
    icon: Target,
    title: "Scénarios sur-mesure",
    description: "Créez des scénarios d'entraînement basés sur vos vrais appels clients.",
  },
];

const enterpriseBenefits = [
  {
    icon: Users,
    title: "Formation d'équipe",
    description: "Onboardez vos nouvelles recrues 3x plus vite avec les patterns de vos champions.",
  },
  {
    icon: BarChart3,
    title: "Analytics avancés",
    description: "Suivez la progression de chaque membre et identifiez les axes d'amélioration.",
  },
  {
    icon: Shield,
    title: "Données sécurisées",
    description: "Vos vidéos et données restent privées. Hébergement en France, conforme RGPD.",
  },
  {
    icon: Headphones,
    title: "Support dédié",
    description: "Un Customer Success Manager dédié pour accompagner le déploiement.",
  },
];

const pricingFeatures = [
  "Analyse illimitée de vidéos",
  "Extraction de patterns IA (Claude Opus)",
  "Scénarios d'entraînement personnalisés",
  "Tableau de bord équipe",
  "Analytics et reporting",
  "Intégration CRM (Salesforce, HubSpot)",
  "SSO / SAML",
  "Support prioritaire",
  "Customer Success Manager dédié",
  "Formation initiale incluse",
];

export default function EnterprisePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-primary-500/10 via-transparent to-transparent" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl" />

        <div className="container mx-auto px-4 relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center max-w-4xl mx-auto"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-sm font-medium mb-6">
              <Building2 className="h-4 w-4" />
              Offre Enterprise
            </div>

            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              <span className="gradient-text">Champion Clone</span>
              <br />
              <span className="text-foreground">pour votre équipe commerciale</span>
            </h1>

            <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Clonez les techniques de vos meilleurs vendeurs et formez toute votre équipe
              à reproduire leurs patterns gagnants.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                size="lg"
                className="bg-gradient-primary hover:opacity-90 text-white border-0 text-lg px-8"
                asChild
              >
                <Link href="mailto:enterprise@champion-clone.com?subject=Demande%20de%20démo%20Enterprise">
                  Demander une démo
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="text-lg px-8"
                asChild
              >
                <Link href="/training">
                  Essayer gratuitement
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Champion Features */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold mb-4">
              <Sparkles className="inline-block h-8 w-8 text-primary-500 mr-2" />
              Fonctionnalités Champion
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Analysez les appels de vos meilleurs commerciaux et créez des programmes
              d&apos;entraînement basés sur leurs techniques réelles.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {championFeatures.map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full bg-card/50 backdrop-blur border-white/10 hover:border-primary-500/50 transition-colors">
                  <CardHeader>
                    <div className="h-12 w-12 rounded-xl bg-primary-500/10 flex items-center justify-center mb-4">
                      <feature.icon className="h-6 w-6 text-primary-500" />
                    </div>
                    <CardTitle className="text-lg">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Enterprise Benefits */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="text-3xl font-bold mb-4">
              Pourquoi les équipes choisissent Enterprise
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Des outils conçus pour les équipes commerciales ambitieuses.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {enterpriseBenefits.map((benefit, index) => (
              <motion.div
                key={benefit.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
              >
                <Card className="h-full bg-card/50 backdrop-blur border-white/10">
                  <CardHeader>
                    <div className="h-12 w-12 rounded-xl bg-purple-500/10 flex items-center justify-center mb-4">
                      <benefit.icon className="h-6 w-6 text-purple-500" />
                    </div>
                    <CardTitle className="text-lg">{benefit.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{benefit.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="max-w-3xl mx-auto"
          >
            <Card className="bg-card border-primary-500/50 overflow-hidden">
              <div className="bg-gradient-primary p-6 text-center">
                <Award className="h-12 w-12 text-white mx-auto mb-4" />
                <h3 className="text-2xl font-bold text-white mb-2">Offre Enterprise</h3>
                <p className="text-white/80">Tarification sur mesure selon vos besoins</p>
              </div>

              <CardContent className="p-8">
                <div className="grid md:grid-cols-2 gap-4 mb-8">
                  {pricingFeatures.map((feature, index) => (
                    <div key={index} className="flex items-center gap-3">
                      <div className="h-5 w-5 rounded-full bg-green-500/10 flex items-center justify-center flex-shrink-0">
                        <Check className="h-3 w-3 text-green-500" />
                      </div>
                      <span className="text-sm">{feature}</span>
                    </div>
                  ))}
                </div>

                <div className="text-center space-y-4">
                  <p className="text-muted-foreground">
                    Contactez-nous pour obtenir un devis personnalisé adapté à la taille de votre équipe.
                  </p>
                  <Button
                    size="lg"
                    className="bg-gradient-primary hover:opacity-90 text-white border-0 px-8"
                    asChild
                  >
                    <Link href="mailto:enterprise@champion-clone.com?subject=Demande%20de%20devis%20Enterprise">
                      Demander un devis
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Link>
                  </Button>
                  <p className="text-sm text-muted-foreground">
                    ou appelez-nous au <strong>01 23 45 67 89</strong>
                  </p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="text-center max-w-2xl mx-auto"
          >
            <h2 className="text-3xl font-bold mb-4">
              Prêt à transformer votre équipe commerciale ?
            </h2>
            <p className="text-muted-foreground mb-8">
              Rejoignez les entreprises qui utilisent Champion Clone pour former
              leurs équipes aux meilleures techniques de vente.
            </p>
            <Button
              size="lg"
              className="bg-gradient-primary hover:opacity-90 text-white border-0 text-lg px-8"
              asChild
            >
              <Link href="mailto:enterprise@champion-clone.com?subject=Demande%20de%20démo%20Enterprise">
                Planifier une démo
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            </Button>
          </motion.div>
        </div>
      </section>
    </div>
  );
}
