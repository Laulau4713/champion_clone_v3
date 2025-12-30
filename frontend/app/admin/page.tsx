"use client";

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Users,
  Activity,
  AlertTriangle,
  Mail,
  Webhook,
  Bell,
  Shield,
} from 'lucide-react';
import { cn } from '@/lib/utils';

import OverviewTab from './components/OverviewTab';
import UsersTab from './components/UsersTab';
import ActivityTab from './components/ActivityTab';
import ErrorsTab from './components/ErrorsTab';
import EmailsTab from './components/EmailsTab';
import WebhooksTab from './components/WebhooksTab';
import AlertsTab from './components/AlertsTab';

const tabs = [
  { id: 'overview', label: 'Vue d\'ensemble', icon: LayoutDashboard },
  { id: 'users', label: 'Utilisateurs', icon: Users },
  { id: 'activity', label: 'Activité', icon: Activity },
  { id: 'errors', label: 'Erreurs', icon: AlertTriangle },
  { id: 'emails', label: 'Emails', icon: Mail },
  { id: 'webhooks', label: 'Webhooks', icon: Webhook },
  { id: 'alerts', label: 'Alertes', icon: Bell },
];

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('overview');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'users':
        return <UsersTab />;
      case 'activity':
        return <ActivityTab />;
      case 'errors':
        return <ErrorsTab />;
      case 'emails':
        return <EmailsTab />;
      case 'webhooks':
        return <WebhooksTab />;
      case 'alerts':
        return <AlertsTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-6rem)]">
      {/* Background */}
      <div className="absolute inset-0 gradient-mesh opacity-20" />

      <div className="relative container mx-auto px-4 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-primary/20">
              <Shield className="h-6 w-6 text-primary" />
            </div>
            <h1 className="text-3xl font-bold text-white">
              Panel <span className="gradient-text">Admin</span>
            </h1>
          </div>
          <p className="text-slate-400">
            Gérez votre plateforme Champion Clone
          </p>
        </motion.div>

        {/* Tabs Navigation */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="mb-6 overflow-x-auto"
        >
          <div className="flex gap-2 min-w-max pb-2">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "flex items-center gap-2 px-4 py-2.5 rounded-lg font-medium transition-all",
                    "border border-transparent",
                    isActive
                      ? "bg-primary text-white border-primary shadow-lg shadow-primary/25"
                      : "bg-slate-800/50 text-slate-400 hover:text-white hover:bg-slate-800 border-slate-700/50"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </motion.div>

        {/* Tab Content */}
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
        >
          {renderTabContent()}
        </motion.div>
      </div>
    </div>
  );
}
