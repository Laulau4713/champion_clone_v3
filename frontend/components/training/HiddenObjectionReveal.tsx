'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Eye, EyeOff, HelpCircle, ChevronDown, ChevronUp, Lightbulb } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

export interface HiddenObjection {
  id: string;
  expressed: string;       // Ce que le prospect dit
  hidden: string;          // La vraie objection
  discoveryQuestions: string[];  // Questions pour la découvrir
  discovered: boolean;
  discoveredAt?: Date;
}

interface HiddenObjectionRevealProps {
  objections: HiddenObjection[];
  showHints?: boolean;
  onRequestHint?: (objectionId: string) => void;
}

export function HiddenObjectionReveal({
  objections,
  showHints = false,
  onRequestHint,
}: HiddenObjectionRevealProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const discoveredCount = objections.filter(o => o.discovered).length;
  const totalCount = objections.length;

  if (totalCount === 0) return null;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Eye className="h-4 w-4 text-purple-400" />
          Objections Cachées
        </h3>
        <span className="text-xs px-2 py-1 rounded-full bg-purple-500/20 text-purple-400">
          {discoveredCount}/{totalCount} découvertes
        </span>
      </div>

      {/* Objections list */}
      <div className="space-y-2">
        {objections.map((objection) => (
          <motion.div
            key={objection.id}
            layout
            className={cn(
              'rounded-lg border transition-all',
              objection.discovered
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-white/5 border-white/10'
            )}
          >
            {/* Expressed objection */}
            <button
              onClick={() => setExpandedId(expandedId === objection.id ? null : objection.id)}
              className="w-full p-3 flex items-start gap-3 text-left"
            >
              <div className={cn(
                'flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center mt-0.5',
                objection.discovered
                  ? 'bg-green-500/20'
                  : 'bg-white/10'
              )}>
                {objection.discovered ? (
                  <Eye className="h-3.5 w-3.5 text-green-400" />
                ) : (
                  <EyeOff className="h-3.5 w-3.5 text-muted-foreground" />
                )}
              </div>

              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium">
                  &quot;{objection.expressed}&quot;
                </p>
                {objection.discovered && objection.discoveredAt && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Découverte à {objection.discoveredAt.toLocaleTimeString('fr-FR', {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </p>
                )}
              </div>

              <div className="flex-shrink-0">
                {expandedId === objection.id ? (
                  <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </button>

            {/* Expanded content */}
            <AnimatePresence>
              {expandedId === objection.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="px-3 pb-3 pt-1 border-t border-white/10 ml-9">
                    {objection.discovered ? (
                      /* Revealed content */
                      <div className="space-y-3">
                        <div className="p-2 rounded-lg bg-green-500/10">
                          <p className="text-xs text-green-400 font-medium mb-1">
                            Vraie objection :
                          </p>
                          <p className="text-sm">{objection.hidden}</p>
                        </div>

                        <div>
                          <p className="text-xs text-muted-foreground font-medium mb-1">
                            Questions qui auraient pu la révéler :
                          </p>
                          <ul className="space-y-1">
                            {objection.discoveryQuestions.map((q, i) => (
                              <li key={i} className="text-xs text-muted-foreground flex items-start gap-1">
                                <HelpCircle className="h-3 w-3 mt-0.5 text-purple-400 flex-shrink-0" />
                                {q}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ) : (
                      /* Hidden content with hint option */
                      <div className="space-y-3">
                        <div className="p-2 rounded-lg bg-white/5 flex items-center gap-2">
                          <EyeOff className="h-4 w-4 text-muted-foreground" />
                          <p className="text-sm text-muted-foreground italic">
                            Objection non découverte...
                          </p>
                        </div>

                        {showHints && onRequestHint && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => onRequestHint(objection.id)}
                            className="w-full gap-2 text-yellow-400 border-yellow-500/30 hover:bg-yellow-500/10"
                          >
                            <Lightbulb className="h-4 w-4" />
                            Demander un indice
                          </Button>
                        )}
                      </div>
                    )}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>

      {/* Progress bar */}
      <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${(discoveredCount / totalCount) * 100}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
          className="h-full bg-gradient-to-r from-purple-500 to-green-500 rounded-full"
        />
      </div>
    </div>
  );
}

/**
 * Notification popup when an objection is discovered
 */
interface ObjectionDiscoveredPopupProps {
  objection: HiddenObjection;
  isVisible: boolean;
  onDismiss: () => void;
}

export function ObjectionDiscoveredPopup({
  objection,
  isVisible,
  onDismiss,
}: ObjectionDiscoveredPopupProps) {
  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          transition={{ type: 'spring', damping: 20, stiffness: 300 }}
          className="fixed bottom-32 left-1/2 -translate-x-1/2 z-50 max-w-md w-full mx-4"
        >
          <div className="rounded-xl border-2 border-green-500/30 bg-green-500/10 p-4 shadow-2xl backdrop-blur-lg">
            <div className="flex items-start gap-3">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: 'spring', delay: 0.1 }}
                className="flex-shrink-0 w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center"
              >
                <Eye className="h-5 w-5 text-green-400" />
              </motion.div>

              <div className="flex-1">
                <h3 className="font-bold text-green-400 mb-1">
                  Objection cachée découverte !
                </h3>
                <p className="text-sm text-muted-foreground mb-2">
                  &quot;{objection.expressed}&quot;
                </p>
                <p className="text-sm">
                  <span className="text-green-400 font-medium">Vraie raison :</span>{' '}
                  {objection.hidden}
                </p>
              </div>

              <button
                onClick={onDismiss}
                className="flex-shrink-0 text-muted-foreground hover:text-foreground"
              >
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
