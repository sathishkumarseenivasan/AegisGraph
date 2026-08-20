'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  Map, 
  AlertTriangle, 
  Network, 
  Bot, 
  Shield, 
  Menu, 
  X,
  Activity,
  Layers
} from 'lucide-react';
import { Entity } from '@/types';
import { EntityDetailPanel } from '@/components/ui/EntityDetailPanel';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [selectedEntity, setSelectedEntity] = useState<Entity | null>(null);

  const pathname = usePathname();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: Map },
    { href: '/anomalies', label: 'Anomalies', icon: AlertTriangle },
    { href: '/graph', label: 'Graph View', icon: Network },
    { href: '/analyst', label: 'AI Analyst', icon: Bot },
    { href: '/audit', label: 'Audit Log', icon: Shield },
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-16'
        } flex-shrink-0 bg-surface border-r border-border transition-all duration-300 flex flex-col`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center gap-3">
            <Layers className="w-8 h-8 text-primary flex-shrink-0" />
            {sidebarOpen && (
              <div>
                <h1 className="text-lg font-bold text-text">AegisGraph</h1>
                <p className="text-xs text-textMuted">Decision Intelligence</p>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-primary/20 text-primary'
                    : 'text-textMuted hover:bg-surfaceHighlight hover:text-text'
                }`}
              >
                <Icon className="w-5 h-5 flex-shrink-0" />
                {sidebarOpen && <span className="text-sm">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Toggle Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-3 border-t border-border text-textMuted hover:text-text transition-colors"
        >
          {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden relative">
        {children}
        
        {/* Entity Detail Panel */}
        {selectedEntity && (
          <EntityDetailPanel
            entity={selectedEntity}
            onClose={() => setSelectedEntity(null)}
          />
        )}
      </main>
    </div>
  );
}
