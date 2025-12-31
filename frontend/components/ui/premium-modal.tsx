"use client";

import Link from "next/link";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Crown, CheckCircle2, ArrowRight, Sparkles } from "lucide-react";

interface PremiumModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const premiumFeatures = [
  "Sessions illimit\u00e9es",
  "Acc\u00e8s au niveau Expert",
  "Secteurs sp\u00e9cialis\u00e9s",
  "Analytics avanc\u00e9s",
  "Support prioritaire",
];

export function PremiumModal({ open, onOpenChange }: PremiumModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md bg-gray-900 border-gray-800">
        <DialogHeader className="text-center">
          <div className="mx-auto w-16 h-16 rounded-full bg-gradient-to-br from-amber-500 to-yellow-500 flex items-center justify-center mb-4">
            <Crown className="w-8 h-8 text-white" />
          </div>
          <DialogTitle className="text-2xl font-bold text-white">
            Passez \u00e0 Premium
          </DialogTitle>
          <DialogDescription className="text-gray-400 text-base">
            Votre essai gratuit de 3 sessions est termin\u00e9.
            <br />
            Continuez votre progression avec Premium.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <span className="font-semibold text-white">
                Avantages Premium
              </span>
            </div>
            <ul className="space-y-2">
              {premiumFeatures.map((feature) => (
                <li key={feature} className="flex items-center gap-2 text-gray-300">
                  <CheckCircle2 className="w-4 h-4 text-green-500 flex-shrink-0" />
                  <span>{feature}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>

        <DialogFooter className="flex-col gap-3 sm:flex-col">
          <Button
            className="w-full bg-gradient-to-r from-amber-500 to-yellow-500 hover:from-amber-600 hover:to-yellow-600 text-gray-900 font-semibold"
            size="lg"
          >
            Passer \u00e0 Premium
            <ArrowRight className="ml-2 h-5 w-5" />
          </Button>
          <Button
            variant="ghost"
            className="w-full text-gray-400 hover:text-white"
            onClick={() => onOpenChange(false)}
          >
            Plus tard
          </Button>
        </DialogFooter>

        <div className="text-center text-sm text-gray-500">
          <Link href="/features" className="hover:text-gray-300 underline">
            En savoir plus sur nos offres
          </Link>
        </div>
      </DialogContent>
    </Dialog>
  );
}
