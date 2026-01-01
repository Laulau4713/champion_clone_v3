'use client';

import { motion, AnimatePresence } from 'framer-motion';
import {
  Phone,
  Clock,
  AlertCircle,
  Users,
  MessageSquareWarning,
  Volume2,
  Zap,
  Target,
  Flame,
} from 'lucide-react';
import { cn } from '@/lib/utils';

export type EventType =
  | 'phone_interruption'
  | 'time_pressure'
  | 'distraction'
  | 'aggressive_interruption'
  | 'competitor_mention'
  | 'power_play'
  | 'phone_on_speaker'
  | 'sudden_time_pressure'
  | 'fake_objection_test'
  | 'emotional_bait';

interface EventNotificationProps {
  type: EventType;
  message: string;
  testDescription?: string;
  isVisible: boolean;
  onDismiss?: () => void;
  autoHide?: boolean;
  autoHideDuration?: number;
}

const EVENT_CONFIG: Record<EventType, {
  icon: React.ElementType;
  title: string;
  color: string;
  bgColor: string;
  borderColor: string;
  severity: 'low' | 'medium' | 'high';
}> = {
  phone_interruption: {
    icon: Phone,
    title: 'Interruption téléphonique',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    severity: 'low',
  },
  time_pressure: {
    icon: Clock,
    title: 'Pression temporelle',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    severity: 'medium',
  },
  distraction: {
    icon: AlertCircle,
    title: 'Distraction',
    color: 'text-gray-400',
    bgColor: 'bg-gray-500/10',
    borderColor: 'border-gray-500/30',
    severity: 'low',
  },
  aggressive_interruption: {
    icon: Flame,
    title: 'Interruption agressive',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    severity: 'high',
  },
  competitor_mention: {
    icon: Target,
    title: 'Mention concurrent',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/30',
    severity: 'high',
  },
  power_play: {
    icon: Zap,
    title: 'Rapport de force',
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    severity: 'medium',
  },
  phone_on_speaker: {
    icon: Volume2,
    title: 'Haut-parleur activé',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10',
    borderColor: 'border-cyan-500/30',
    severity: 'medium',
  },
  sudden_time_pressure: {
    icon: Clock,
    title: 'Urgence soudaine',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    severity: 'high',
  },
  fake_objection_test: {
    icon: MessageSquareWarning,
    title: 'Test du prospect',
    color: 'text-yellow-400',
    bgColor: 'bg-yellow-500/10',
    borderColor: 'border-yellow-500/30',
    severity: 'medium',
  },
  emotional_bait: {
    icon: Flame,
    title: 'Provocation émotionnelle',
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    severity: 'high',
  },
};

export function EventNotification({
  type,
  message,
  testDescription,
  isVisible,
  onDismiss,
  autoHide = true,
  autoHideDuration = 6000,
}: EventNotificationProps) {
  const config = EVENT_CONFIG[type];
  const Icon = config.icon;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, x: 100 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 100 }}
          transition={{ type: 'spring', damping: 25, stiffness: 200 }}
          className={cn(
            'fixed top-24 right-4 z-50 max-w-sm w-full',
            'rounded-xl border p-4 shadow-xl backdrop-blur-lg',
            config.bgColor,
            config.borderColor
          )}
        >
          <div className="flex items-start gap-3">
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ type: 'spring', delay: 0.1 }}
              className={cn(
                'flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center',
                config.bgColor
              )}
            >
              <Icon className={cn('h-5 w-5', config.color)} />
            </motion.div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className={cn('font-semibold text-sm', config.color)}>
                  {config.title}
                </h3>
                {config.severity === 'high' && (
                  <span className="text-xs px-1.5 py-0.5 rounded bg-red-500/20 text-red-400">
                    Critique
                  </span>
                )}
              </div>

              <p className="text-sm text-foreground/90 mb-2">
                {message}
              </p>

              {testDescription && (
                <div className="p-2 rounded-lg bg-white/5 border border-white/10">
                  <p className="text-xs text-muted-foreground">
                    <span className="font-medium">Test : </span>
                    {testDescription}
                  </p>
                </div>
              )}
            </div>

            {onDismiss && (
              <button
                onClick={onDismiss}
                className="flex-shrink-0 text-muted-foreground hover:text-foreground transition-colors"
              >
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>

          {/* Auto-hide progress bar */}
          {autoHide && (
            <motion.div
              initial={{ scaleX: 1 }}
              animate={{ scaleX: 0 }}
              transition={{ duration: autoHideDuration / 1000, ease: 'linear' }}
              className={cn(
                'absolute bottom-0 left-0 right-0 h-1 origin-left rounded-b-xl',
                config.color.replace('text-', 'bg-')
              )}
              onAnimationComplete={onDismiss}
            />
          )}
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Event result feedback shown after the user responds
 */
interface EventResultProps {
  handledWell: boolean;
  jaugeImpact: number;
  feedback: string;
  isVisible: boolean;
  onDismiss: () => void;
}

export function EventResult({
  handledWell,
  jaugeImpact,
  feedback,
  isVisible,
  onDismiss,
}: EventResultProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          className={cn(
            'fixed bottom-32 right-4 z-50 max-w-sm w-full',
            'rounded-xl border p-4 shadow-xl backdrop-blur-lg',
            handledWell
              ? 'bg-green-500/10 border-green-500/30'
              : 'bg-red-500/10 border-red-500/30'
          )}
        >
          <div className="flex items-start gap-3">
            <div className={cn(
              'flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center',
              handledWell ? 'bg-green-500/20' : 'bg-red-500/20'
            )}>
              {handledWell ? (
                <svg className="h-4 w-4 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              ) : (
                <svg className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              )}
            </div>

            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <h3 className={cn(
                  'font-semibold text-sm',
                  handledWell ? 'text-green-400' : 'text-red-400'
                )}>
                  {handledWell ? 'Bien géré !' : 'Attention'}
                </h3>
                <span className={cn(
                  'text-xs px-1.5 py-0.5 rounded',
                  jaugeImpact >= 0
                    ? 'bg-green-500/20 text-green-400'
                    : 'bg-red-500/20 text-red-400'
                )}>
                  {jaugeImpact >= 0 ? '+' : ''}{jaugeImpact}
                </span>
              </div>
              <p className="text-sm text-muted-foreground">
                {feedback}
              </p>
            </div>

            <button
              onClick={onDismiss}
              className="text-muted-foreground hover:text-foreground"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

/**
 * Interlocutor added notification
 */
interface NewInterlocutorProps {
  name: string;
  personality: string;
  isVisible: boolean;
  onDismiss: () => void;
}

export function NewInterlocutorNotification({
  name,
  personality,
  isVisible,
  onDismiss,
}: NewInterlocutorProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.9 }}
          className="fixed top-24 left-1/2 -translate-x-1/2 z-50 max-w-sm w-full mx-4"
        >
          <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-4 shadow-xl backdrop-blur-lg">
            <div className="flex items-center gap-3">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', delay: 0.1 }}
                className="w-12 h-12 rounded-full bg-cyan-500/20 flex items-center justify-center"
              >
                <Users className="h-6 w-6 text-cyan-400" />
              </motion.div>

              <div>
                <h3 className="font-bold text-cyan-400">
                  Nouvel interlocuteur
                </h3>
                <p className="text-sm">
                  <span className="font-medium">{name}</span> rejoint la conversation
                </p>
                <p className="text-xs text-muted-foreground">
                  Personnalité : {personality}
                </p>
              </div>

              <button onClick={onDismiss} className="ml-auto text-muted-foreground hover:text-foreground">
                <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
