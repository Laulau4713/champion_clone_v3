'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Mail, Lock, User, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { authAPI } from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';

const PASSWORD_REQUIREMENTS = [
  { id: 'length', label: '8 caractères minimum', test: (p: string) => p.length >= 8 },
  { id: 'uppercase', label: '1 majuscule', test: (p: string) => /[A-Z]/.test(p) },
  { id: 'lowercase', label: '1 minuscule', test: (p: string) => /[a-z]/.test(p) },
  { id: 'number', label: '1 chiffre', test: (p: string) => /[0-9]/.test(p) },
  { id: 'special', label: '1 caractère spécial', test: (p: string) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
];

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const passwordValid = PASSWORD_REQUIREMENTS.every((req) => req.test(password));
  const passwordsMatch = password === confirmPassword && password.length > 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!passwordValid) {
      setError('Le mot de passe ne respecte pas les critères requis');
      return;
    }

    if (!passwordsMatch) {
      setError('Les mots de passe ne correspondent pas');
      return;
    }

    setLoading(true);

    try {
      await authAPI.register({
        email,
        password,
        full_name: fullName || undefined,
      });

      router.push('/login?registered=true');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string | Array<{ msg: string }> } } };
      const detail = error.response?.data?.detail;
      // Handle Pydantic validation errors (array of objects with msg)
      if (Array.isArray(detail)) {
        setError(detail.map(e => e.msg).join(', '));
      } else {
        setError(detail || 'Erreur lors de l\'inscription');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-6rem)] flex items-center justify-center px-4 py-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <Card className="glass border-white/10">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl gradient-text">Inscription</CardTitle>
            <CardDescription>
              Créez votre compte pour commencer l&apos;entraînement
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <motion.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="bg-destructive/10 border border-destructive/20 text-destructive p-3 rounded-lg text-sm flex items-center gap-2"
                >
                  <AlertCircle className="h-4 w-4 flex-shrink-0" />
                  {error}
                </motion.div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Nom complet <span className="text-muted-foreground">(optionnel)</span>
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="text"
                    placeholder="Jean Dupont"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="pl-10 bg-background/50 border-white/10 focus:border-primary-500"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="email"
                    placeholder="vous@exemple.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="pl-10 bg-background/50 border-white/10 focus:border-primary-500"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Mot de passe
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="pl-10 bg-background/50 border-white/10 focus:border-primary-500"
                    required
                  />
                </div>
                {password.length > 0 && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-2 space-y-1"
                  >
                    {PASSWORD_REQUIREMENTS.map((req) => (
                      <div
                        key={req.id}
                        className={`flex items-center gap-2 text-xs ${
                          req.test(password) ? 'text-green-400' : 'text-muted-foreground'
                        }`}
                      >
                        <CheckCircle2
                          className={`h-3 w-3 ${
                            req.test(password) ? 'text-green-400' : 'text-muted-foreground/50'
                          }`}
                        />
                        {req.label}
                      </div>
                    ))}
                  </motion.div>
                )}
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-foreground">
                  Confirmer le mot de passe
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`pl-10 bg-background/50 border-white/10 focus:border-primary-500 ${
                      confirmPassword.length > 0 && !passwordsMatch
                        ? 'border-destructive/50'
                        : ''
                    }`}
                    required
                  />
                </div>
                {confirmPassword.length > 0 && !passwordsMatch && (
                  <p className="text-xs text-destructive">
                    Les mots de passe ne correspondent pas
                  </p>
                )}
              </div>

              <Button
                type="submit"
                className="w-full bg-gradient-primary hover:opacity-90 text-white border-0"
                disabled={loading || !passwordValid || !passwordsMatch}
              >
                {loading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Inscription...
                  </>
                ) : (
                  'Créer mon compte'
                )}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-muted-foreground">
                Déjà un compte ?{' '}
                <Link
                  href="/login"
                  className="text-primary-400 hover:text-primary-300 font-medium transition-colors"
                >
                  Se connecter
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
