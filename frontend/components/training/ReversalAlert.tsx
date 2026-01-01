'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { AlertTriangle, Bomb, DollarSign, Ghost, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

export type ReversalType =
  | 'last_minute_doubt'
  | 'last_minute_bomb'
  | 'price_attack_at_close'
  | 'ghost_decision_maker'
  | 'fake_competitor_offer';

interface ReversalAlertProps {
  type: ReversalType;
  message: string;
  jaugeDrop?: number;
  isVisible: boolean;
  onDismiss?: () => void;
}

const REVERSAL_CONFIG: Record<ReversalType, {
  icon: React.ElementType;
  title: string;
  color: string;
  bgColor: string;
  borderColor: string;
}> = {
  last_minute_doubt: {
    icon: AlertTriangle,
    title: 'Doute de dernière minute',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
  },
  last_minute_bomb: {
    icon: Bomb,
    title: 'Bombe de dernière minute !',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
  },
  price_attack_at_close: {
    icon: DollarSign,
    title: 'Attaque sur le prix',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
  },
  ghost_decision_maker: {
    icon: Ghost,
    title: 'Décideur fantôme',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
  },
  fake_competitor_offer: {
    icon: Users,
    title: 'Offre concurrente (bluff ?)',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
  },
};

export function ReversalAlert({
  type,
  message,
  jaugeDrop,
  isVisible,
  onDismiss,
}: ReversalAlertProps) {
  const config = REVERSAL_CONFIG[type];
  const Icon = config.icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -20, scale: 0.95 }}
          transition={{ type: 'spring', damping: 20, stiffness: 300 }}
          className={cn(
            'fixed top-24 left-1/2 -translate-x-1/2 z-50 max-w-lg w-full mx-4',
            'rounded-xl border-2 p-4 shadow-2xl',
            config.bgColor,
            config.borderColor
          )}
        >
          <div className="flex items-start gap-3">
            <motion.div
              initial={{ rotate: 0 }}
              animate={{ rotate: [0, -10, 10, -10, 10, 0] }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className={cn(
                'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                config.bgColor
              )}
            >
              <Icon className={cn('h-6 w-6', config.color)} />
            </motion.div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className={cn('font-bold', config.color)}>
                  {config.title}
                </h3>
                {jaugeDrop && jaugeDrop > 0 && (
                  <motion.span
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="text-xs px-2 py-0.5 rounded-full bg-red-500/20 text-red-400"
                  >
                    -{jaugeDrop} jauge
                  </motion.span>
                )}
              </div>
              <p className="text-sm text-muted-foreground line-clamp-2">
                {message}
              </p>
            </div>

            {onDismiss && (
              <button
                onClick={onDismiss}
                className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors"
              >
                <svg
                  className="h-5 w-5"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            )}
          </div>

          {/* Progress bar for auto-dismiss */}
          <motion.div
            initial={{ scaleX: 1 }}
            animate={{ scaleX: 0 }}
            transition={{ duration: 5, ease: 'linear' }}
            className={cn(
              'absolute bottom-0 left-0 right-0 h-1 origin-left rounded-b-xl',
              config.color.replace('text-', 'bg-')
            )}
            onAnimationComplete={onDismiss}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
