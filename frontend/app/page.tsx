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
    title: "Voice Cloning",
    description:
      "Train with your champion's actual voice. Our AI captures tone, pace, and personality.",
    gradient: "from-violet-500 to-purple-500",
  },
  {
    icon: Brain,
    title: "Pattern Analysis",
    description:
      "AI extracts proven sales techniques from your top performers automatically.",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    icon: BarChart3,
    title: "Real Feedback",
    description:
      "Improve with instant coaching. Get actionable insights after every practice session.",
    gradient: "from-emerald-500 to-teal-500",
  },
];

const stats = [
  { value: "1,250+", label: "Sales managers validated" },
  { value: "78/100", label: "Market validation score" },
  { value: "3x", label: "Faster onboarding" },
];

const pricingPlans = [
  {
    name: "Solo",
    price: "99",
    description: "Pour les commerciaux individuels",
    features: [
      "1 champion clone",
      "10 sessions/mois",
      "Feedback basique",
      "Support email",
    ],
  },
  {
    name: "Team",
    price: "249",
    description: "Pour les équipes commerciales",
    features: [
      "5 champion clones",
      "Sessions illimitées",
      "Analytics avancés",
      "Support prioritaire",
      "API access",
    ],
    popular: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    description: "Pour les grandes organisations",
    features: [
      "Champions illimités",
      "Sessions illimitées",
      "SSO & intégrations",
      "Account manager dédié",
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
            <motion.h1
              variants={fadeInUp}
              className="text-4xl sm:text-5xl lg:text-7xl font-bold tracking-tight mb-6"
            >
              Clone Your{" "}
              <span className="gradient-text">Sales Champions</span>
            </motion.h1>

            <motion.p
              variants={fadeInUp}
              className="text-xl text-muted-foreground mb-10 max-w-2xl mx-auto"
            >
              AI-Powered Training from Your Best Performers. Upload a video of
              your top salesperson and let AI teach their techniques to your
              entire team.
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
                <Link href="/upload" className="inline-flex items-center">
                  <span>Start Free Trial</span>
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="lg"
                className="text-lg px-8 py-6 rounded-xl border-white/20 hover:bg-white/5"
              >
                <Link href="#features">Learn More</Link>
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
              Everything you need to{" "}
              <span className="gradient-text">scale excellence</span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Our AI-powered platform captures what makes your best performers
              great and teaches it to everyone.
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
              How it <span className="gradient-text">works</span>
            </h2>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                title: "Upload",
                description:
                  "Upload a video of your best salesperson in action",
                icon: Users,
              },
              {
                step: "02",
                title: "Analyze",
                description:
                  "Our AI extracts patterns, techniques, and voice",
                icon: Brain,
              },
              {
                step: "03",
                title: "Train",
                description:
                  "Your team practices with an AI clone of your champion",
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
              Simple, transparent{" "}
              <span className="gradient-text">pricing</span>
            </h2>
            <p className="text-xl text-muted-foreground">
              Start free, upgrade when you need more
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
                        Popular
                      </Badge>
                    </div>
                  )}
                  <CardContent className="p-8">
                    <h3 className="text-xl font-semibold mb-2">{plan.name}</h3>
                    <p className="text-sm text-muted-foreground mb-6">
                      {plan.description}
                    </p>
                    <div className="mb-6">
                      <span className="text-4xl font-bold">{plan.price}</span>
                      {plan.price !== "Custom" && (
                        <span className="text-muted-foreground">/mois</span>
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
                      <Link href="/upload">
                        {plan.price === "Custom"
                          ? "Contact Sales"
                          : "Get Started"}
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
                  Ready to clone your champions?
                </h2>
                <p className="text-xl text-muted-foreground mb-8">
                  Start training your team with AI today. No credit card
                  required.
                </p>
                <Button
                  asChild
                  size="lg"
                  className="bg-gradient-primary hover:opacity-90 text-white text-lg px-8 py-6 rounded-xl"
                >
                  <Link href="/upload" className="inline-flex items-center">
                    <span>Start Free Trial</span>
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
