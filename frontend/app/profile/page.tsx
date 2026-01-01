'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  User,
  Mail,
  Lock,
  Save,
  Loader2,
  AlertCircle,
  CheckCircle2,
  CreditCard,
  BarChart3,
  Award,
  Calendar,
  ArrowLeft,
  Eye,
  EyeOff,
  LogOut,
  Shield,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { authAPI, learningAPI, paymentsAPI, PaymentStatus } from '@/lib/api';
import { useAuthStore } from '@/store/auth-store';
import type { User as UserType, UserProgress } from '@/types';

export default function ProfilePage() {
  const router = useRouter();
  const { user, logout, login } = useAuthStore();

  // Profile form state
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [profileLoading, setProfileLoading] = useState(false);
  const [profileSuccess, setProfileSuccess] = useState(false);
  const [profileError, setProfileError] = useState('');

  // Password form state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [passwordError, setPasswordError] = useState('');

  // Data state
  const [progress, setProgress] = useState<UserProgress | null>(null);
  const [paymentStatus, setPaymentStatus] = useState<PaymentStatus | null>(null);
  const [dataLoading, setDataLoading] = useState(true);

  // Initialize form with user data
  useEffect(() => {
    if (user) {
      setFullName(user.full_name || '');
      setEmail(user.email);
    }
  }, [user]);

  // Load additional data
  useEffect(() => {
    const loadData = async () => {
      try {
        const [progressRes, paymentRes] = await Promise.all([
          learningAPI.getProgress(),
          paymentsAPI.getStatus(),
        ]);
        setProgress(progressRes.data);
        setPaymentStatus(paymentRes.data);
      } catch (err) {
        console.error('Error loading profile data:', err);
      } finally {
        setDataLoading(false);
      }
    };

    loadData();
  }, []);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileLoading(true);
    setProfileError('');
    setProfileSuccess(false);

    try {
      const { data } = await authAPI.updateProfile({
        full_name: fullName,
        email: email !== user?.email ? email : undefined,
      });

      // Update local user state
      if (user) {
        login(data as UserType, localStorage.getItem('access_token') || '', localStorage.getItem('refresh_token') || '');
      }

      setProfileSuccess(true);
      setTimeout(() => setProfileSuccess(false), 3000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setProfileError(error.response?.data?.detail || 'Erreur lors de la mise à jour');
    } finally {
      setProfileLoading(false);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordLoading(true);
    setPasswordError('');
    setPasswordSuccess(false);

    if (newPassword !== confirmPassword) {
      setPasswordError('Les mots de passe ne correspondent pas');
      setPasswordLoading(false);
      return;
    }

    try {
      await authAPI.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });

      setPasswordSuccess(true);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setTimeout(() => setPasswordSuccess(false), 3000);
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setPasswordError(error.response?.data?.detail || 'Erreur lors du changement de mot de passe');
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (err) {
      console.error('Logout error:', err);
    }
    logout();
    router.push('/login');
  };

  const handleLogoutAll = async () => {
    try {
      await authAPI.logoutAll();
      logout();
      router.push('/login');
    } catch (err) {
      console.error('Logout all error:', err);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-gradient-dark flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-400" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-dark pt-28 pb-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push('/dashboard')}
              className="gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Retour
            </Button>
            <div>
              <h1 className="text-2xl font-bold gradient-text">Mon Profil</h1>
              <p className="text-sm text-muted-foreground">
                Gérez vos informations et préférences
              </p>
            </div>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Profile Info Card */}
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <User className="h-5 w-5 text-primary-400" />
                Informations Personnelles
              </CardTitle>
              <CardDescription>
                Modifiez votre nom et adresse email
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleUpdateProfile} className="space-y-4">
                <AnimatePresence>
                  {profileError && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2"
                    >
                      <AlertCircle className="h-4 w-4 flex-shrink-0" />
                      {profileError}
                    </motion.div>
                  )}
                  {profileSuccess && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-center gap-2"
                    >
                      <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                      Profil mis à jour avec succès
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Nom complet</label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      className="pl-10 bg-background/50 border-white/10"
                      placeholder="Votre nom"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="pl-10 bg-background/50 border-white/10"
                      placeholder="vous@exemple.com"
                      required
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full bg-gradient-primary"
                  disabled={profileLoading}
                >
                  {profileLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Enregistrement...
                    </>
                  ) : (
                    <>
                      <Save className="mr-2 h-4 w-4" />
                      Enregistrer
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Password Card */}
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="h-5 w-5 text-yellow-400" />
                Sécurité
              </CardTitle>
              <CardDescription>
                Changez votre mot de passe
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleChangePassword} className="space-y-4">
                <AnimatePresence>
                  {passwordError && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-3 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2"
                    >
                      <AlertCircle className="h-4 w-4 flex-shrink-0" />
                      {passwordError}
                    </motion.div>
                  )}
                  {passwordSuccess && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="p-3 rounded-lg bg-green-500/10 border border-green-500/20 text-green-400 text-sm flex items-center gap-2"
                    >
                      <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
                      Mot de passe changé avec succès
                    </motion.div>
                  )}
                </AnimatePresence>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Mot de passe actuel</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type={showCurrentPassword ? 'text' : 'password'}
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="pl-10 pr-10 bg-background/50 border-white/10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showCurrentPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Nouveau mot de passe</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type={showNewPassword ? 'text' : 'password'}
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="pl-10 pr-10 bg-background/50 border-white/10"
                      required
                      minLength={8}
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    >
                      {showNewPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Confirmer le mot de passe</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      type="password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="pl-10 bg-background/50 border-white/10"
                      required
                    />
                  </div>
                </div>

                <Button
                  type="submit"
                  variant="outline"
                  className="w-full border-yellow-500/30 text-yellow-400 hover:bg-yellow-500/10"
                  disabled={passwordLoading}
                >
                  {passwordLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Changement...
                    </>
                  ) : (
                    <>
                      <Shield className="mr-2 h-4 w-4" />
                      Changer le mot de passe
                    </>
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>

          {/* Stats Card */}
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-green-400" />
                Statistiques
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dataLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : progress ? (
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-white/5">
                    <p className="text-2xl font-bold text-primary-400">
                      {progress.total_scenarios_completed || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Scénarios complétés</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5">
                    <p className="text-2xl font-bold text-green-400">
                      {progress.total_training_minutes || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Minutes entraînement</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5">
                    <p className="text-2xl font-bold text-yellow-400">
                      {progress.skills_validated || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Skills validés</p>
                  </div>
                  <div className="p-4 rounded-xl bg-white/5">
                    <div className="flex items-center gap-1">
                      <Award className="h-5 w-5 text-purple-400" />
                      <p className="text-lg font-bold capitalize">
                        {progress.current_level || 'easy'}
                      </p>
                    </div>
                    <p className="text-sm text-muted-foreground">Niveau actuel</p>
                  </div>
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-4">
                  Aucune donnée disponible
                </p>
              )}
            </CardContent>
          </Card>

          {/* Subscription Card */}
          <Card className="glass border-white/10">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <CreditCard className="h-5 w-5 text-purple-400" />
                Abonnement
              </CardTitle>
            </CardHeader>
            <CardContent>
              {dataLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Plan</span>
                    <Badge className={cn(
                      paymentStatus?.plan === 'pro'
                        ? 'bg-purple-500/20 text-purple-400'
                        : 'bg-white/10 text-muted-foreground'
                    )}>
                      {paymentStatus?.plan === 'pro' ? 'Premium' : 'Gratuit'}
                    </Badge>
                  </div>

                  <div className="flex items-center justify-between">
                    <span className="text-muted-foreground">Statut</span>
                    <Badge className={cn(
                      paymentStatus?.status === 'active'
                        ? 'bg-green-500/20 text-green-400'
                        : 'bg-yellow-500/20 text-yellow-400'
                    )}>
                      {paymentStatus?.status === 'active' ? 'Actif' : 'Essai'}
                    </Badge>
                  </div>

                  {paymentStatus?.expires_at && (
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground">Expire le</span>
                      <span className="flex items-center gap-1">
                        <Calendar className="h-4 w-4 text-muted-foreground" />
                        {new Date(paymentStatus.expires_at).toLocaleDateString('fr-FR')}
                      </span>
                    </div>
                  )}

                  {user.subscription_plan === 'free' && (
                    <div className="pt-2">
                      <p className="text-sm text-muted-foreground mb-3">
                        Sessions utilisées : {user.trial_sessions_used || 0}/{user.trial_sessions_max || 3}
                      </p>
                      <Button
                        className="w-full bg-gradient-to-r from-purple-500 to-pink-500"
                        onClick={() => router.push('/pricing')}
                      >
                        Passer à Premium
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Danger Zone */}
        <Card className="glass border-red-500/20 mt-6">
          <CardHeader>
            <CardTitle className="text-red-400">Zone de danger</CardTitle>
            <CardDescription>
              Actions irréversibles
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-3">
              <Button
                variant="outline"
                className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                Déconnexion
              </Button>
              <Button
                variant="outline"
                className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                onClick={handleLogoutAll}
              >
                <Shield className="mr-2 h-4 w-4" />
                Déconnecter tous les appareils
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
