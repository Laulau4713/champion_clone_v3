"use client";

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield } from 'lucide-react';

import OverviewTab from './components/OverviewTab';
import UsersTab from './components/UsersTab';
import ActivityTab from './components/ActivityTab';
import ErrorsTab from './components/ErrorsTab';
import EmailsTab from './components/EmailsTab';
import WebhooksTab from './components/WebhooksTab';
import AlertsTab from './components/AlertsTab';
import SessionsTab from './components/SessionsTab';
import AuditTab from './components/AuditTab';
import AdminSidebar from './components/AdminSidebar';

export default function AdminPage() {
  const [activeTab, setActiveTab] = useState('overview');

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return <OverviewTab />;
      case 'users':
        return <UsersTab />;
      case 'sessions':
        return <SessionsTab />;
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
      case 'audit':
        return <AuditTab />;
      default:
        return <OverviewTab />;
    }
  };

  return (
    <div className="relative min-h-[calc(100vh-6rem)]">
      {/* Background */}
      <div className="absolute inset-0 gradient-mesh opacity-20" />

      {/* Sidebar */}
      <AdminSidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Main Content */}
      <div className="pl-[240px] transition-all">
        <div className="relative container mx-auto px-6 py-8 max-w-7xl">
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
    </div>
  );
}
