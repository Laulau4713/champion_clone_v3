'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Trophy, Star, Target, Clock, Award, Crown,
  BookOpen, GraduationCap, Flame, Dumbbell,
  CheckCircle, Shield, Phone, Ear, HelpCircle,
  ClipboardCheck, MessageCircle, Search, Scale,
  Zap, RefreshCw, Eye, Medal, Lock
} from 'lucide-react';
import { achievementsAPI } from '@/lib/api';
import { useAuthStore } from '@/store/auth-store';
import type { Achievement, UserXP, AchievementCategory } from '@/types';

// Map icon names to Lucide components
const iconMap: Record<string, React.ElementType> = {
  'book-open': BookOpen,
  'graduation-cap': GraduationCap,
  'award': Award,
  'trophy': Trophy,
  'flame': Flame,
  'dumbbell': Dumbbell,
  'target': Target,
  'check-circle': CheckCircle,
  'star': Star,
  'clock': Clock,
  'hourglass': Clock,
  'search': Search,
  'message-circle': MessageCircle,
  'phone': Phone,
  'ear': Ear,
  'help-circle': HelpCircle,
  'clipboard-check': ClipboardCheck,
  'shield': Shield,
  'scale': Scale,
  'crown': Crown,
  'zap': Zap,
  'refresh-cw': RefreshCw,
  'eye': Eye,
  'medal': Medal,
};

// Map colors to Tailwind classes
const colorMap: Record<string, { bg: string; text: string; border: string; ring: string }> = {
  blue: { bg: 'bg-blue-500/20', text: 'text-blue-400', border: 'border-blue-500/50', ring: 'ring-blue-500' },
  green: { bg: 'bg-green-500/20', text: 'text-green-400', border: 'border-green-500/50', ring: 'ring-green-500' },
  purple: { bg: 'bg-purple-500/20', text: 'text-purple-400', border: 'border-purple-500/50', ring: 'ring-purple-500' },
  gold: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/50', ring: 'ring-yellow-500' },
  orange: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/50', ring: 'ring-orange-500' },
  red: { bg: 'bg-red-500/20', text: 'text-red-400', border: 'border-red-500/50', ring: 'ring-red-500' },
  yellow: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', border: 'border-yellow-500/50', ring: 'ring-yellow-500' },
  cyan: { bg: 'bg-cyan-500/20', text: 'text-cyan-400', border: 'border-cyan-500/50', ring: 'ring-cyan-500' },
  teal: { bg: 'bg-teal-500/20', text: 'text-teal-400', border: 'border-teal-500/50', ring: 'ring-teal-500' },
  indigo: { bg: 'bg-indigo-500/20', text: 'text-indigo-400', border: 'border-indigo-500/50', ring: 'ring-indigo-500' },
};

const categoryLabels: Record<AchievementCategory, string> = {
  progression: 'Progression',
  skill: 'Compétences',
  special: 'Spécial',
};

const categoryIcons: Record<AchievementCategory, React.ElementType> = {
  progression: Target,
  skill: GraduationCap,
  special: Star,
};

export default function AchievementsPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();
  const [achievements, setAchievements] = useState<Achievement[]>([]);
  const [userXP, setUserXP] = useState<UserXP | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<AchievementCategory | 'all'>('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check auth on mount
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    if (!token && !isAuthenticated) {
      router.push('/login');
      return;
    }
    loadData();
  }, [isAuthenticated, router]);

  const loadData = async () => {
    try {
      const [achRes, xpRes] = await Promise.all([
        achievementsAPI.getAll(),
        achievementsAPI.getXP(),
      ]);
      setAchievements(achRes.data);
      setUserXP(xpRes.data);
    } catch (error) {
      console.error('Failed to load achievements:', error);
      // If unauthorized, redirect to login
      if ((error as { response?: { status: number } }).response?.status === 401) {
        router.push('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const filteredAchievements = selectedCategory === 'all'
    ? achievements
    : achievements.filter(a => a.category === selectedCategory);

  const unlockedCount = achievements.filter(a => a.unlocked).length;
  const totalXPFromUnlocked = achievements
    .filter(a => a.unlocked)
    .reduce((sum, a) => sum + a.xp_reward, 0);

  const categories: (AchievementCategory | 'all')[] = ['all', 'progression', 'skill', 'special'];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 pb-20">
      {/* Header */}
      <div className="bg-gradient-to-b from-slate-900 to-slate-950 border-b border-slate-800">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="flex items-center gap-3 mb-6">
            <Trophy className="w-8 h-8 text-yellow-500" />
            <h1 className="text-3xl font-bold text-white">Achievements</h1>
          </div>

          {/* XP & Level Card */}
          {userXP && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700"
            >
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">{userXP.level}</span>
                  </div>
                  <div>
                    <p className="text-slate-400 text-sm">Niveau actuel</p>
                    <p className="text-2xl font-bold text-white">{userXP.total_xp} XP</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-slate-400 text-sm">Achievements débloqués</p>
                  <p className="text-xl font-semibold text-white">
                    {unlockedCount} / {achievements.length}
                  </p>
                </div>
              </div>

              {/* XP Progress Bar */}
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-slate-400">Progression vers niveau {userXP.level + 1}</span>
                  <span className="text-yellow-500">{Math.round(userXP.xp_progress * 100)}%</span>
                </div>
                <div className="h-3 bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${userXP.xp_progress * 100}%` }}
                    transition={{ duration: 1, ease: 'easeOut' }}
                    className="h-full bg-gradient-to-r from-yellow-500 to-orange-500"
                  />
                </div>
                <p className="text-xs text-slate-500 text-right">
                  {userXP.xp_for_next_level - userXP.total_xp} XP restants
                </p>
              </div>
            </motion.div>
          )}

          {/* Category Tabs */}
          <div className="flex gap-2 mt-6 overflow-x-auto pb-2">
            {categories.map((cat) => {
              const Icon = cat === 'all' ? Trophy : categoryIcons[cat];
              const isActive = selectedCategory === cat;
              return (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all whitespace-nowrap
                    ${isActive
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-white'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {cat === 'all' ? 'Tous' : categoryLabels[cat]}
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    isActive ? 'bg-white/20' : 'bg-slate-700'
                  }`}>
                    {cat === 'all'
                      ? achievements.length
                      : achievements.filter(a => a.category === cat).length
                    }
                  </span>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* Achievements Grid */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <AnimatePresence mode="popLayout">
          <motion.div
            key={selectedCategory}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {filteredAchievements.map((achievement, index) => {
              const Icon = iconMap[achievement.icon] || Trophy;
              const colors = colorMap[achievement.color] || colorMap.blue;

              return (
                <motion.div
                  key={achievement.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                  className={`
                    relative rounded-xl p-5 border transition-all duration-300
                    ${achievement.unlocked
                      ? `${colors.bg} ${colors.border} hover:ring-2 ${colors.ring}`
                      : 'bg-slate-800/30 border-slate-700/50 opacity-60'
                    }
                  `}
                >
                  {/* Lock overlay for locked achievements */}
                  {!achievement.unlocked && (
                    <div className="absolute inset-0 flex items-center justify-center z-10">
                      <Lock className="w-8 h-8 text-slate-600" />
                    </div>
                  )}

                  <div className={`flex items-start gap-4 ${!achievement.unlocked ? 'blur-sm' : ''}`}>
                    <div className={`
                      w-14 h-14 rounded-xl flex items-center justify-center shrink-0
                      ${achievement.unlocked ? colors.bg : 'bg-slate-700/50'}
                    `}>
                      <Icon className={`w-7 h-7 ${achievement.unlocked ? colors.text : 'text-slate-500'}`} />
                    </div>

                    <div className="flex-1 min-w-0">
                      <h3 className={`font-semibold mb-1 ${
                        achievement.unlocked ? 'text-white' : 'text-slate-400'
                      }`}>
                        {achievement.name}
                      </h3>
                      <p className="text-sm text-slate-400 mb-2">
                        {achievement.description}
                      </p>
                      <div className="flex items-center justify-between">
                        <span className={`text-sm font-medium ${colors.text}`}>
                          +{achievement.xp_reward} XP
                        </span>
                        {achievement.unlocked && achievement.unlocked_at && (
                          <span className="text-xs text-slate-500">
                            {new Date(achievement.unlocked_at).toLocaleDateString('fr-FR')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Unlocked badge */}
                  {achievement.unlocked && (
                    <div className="absolute -top-2 -right-2">
                      <div className="w-6 h-6 rounded-full bg-green-500 flex items-center justify-center shadow-lg">
                        <CheckCircle className="w-4 h-4 text-white" />
                      </div>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </motion.div>
        </AnimatePresence>

        {/* Empty state */}
        {filteredAchievements.length === 0 && (
          <div className="text-center py-12">
            <Trophy className="w-16 h-16 text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">Aucun achievement dans cette catégorie</p>
          </div>
        )}
      </div>
    </div>
  );
}
