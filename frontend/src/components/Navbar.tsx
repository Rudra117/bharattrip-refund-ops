import React from 'react';
import { Download, Sun, Moon, AlertCircle } from 'lucide-react';
import { getLedgerDownloadUrl } from '../api/client';

interface NavbarProps {
  darkMode: boolean;
  setDarkMode: (val: boolean) => void;
  activeSection: string;
  hasKey?: boolean;
}

export const Navbar: React.FC<NavbarProps> = ({
  darkMode,
  setDarkMode,
  activeSection,
  hasKey = false,
}) => {
  const navItems = [
    { id: 'hero', label: 'Overview' },
    { id: 'leaks', label: 'Process Leaks' },
    { id: 'escalations', label: 'Root Causes' },
    { id: 'approvals', label: 'Approvals' },
    { id: 'queue', label: 'Action Queue' },
    { id: 'intake', label: 'Intake Assistant' },
  ];

  const scrollTo = (id: string) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <nav className="sticky top-0 z-50 w-full border-b backdrop-blur-md transition-colors duration-200 border-ink-border/80 bg-ink/80 dark:border-ink-border/80 dark:bg-ink/85 light:border-paper-border light:bg-paper/85">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2 cursor-pointer" onClick={() => scrollTo('hero')}>
            <div className="w-2.5 h-2.5 rounded-full bg-amber animate-pulse" />
            <span className="font-heading font-bold text-base sm:text-lg tracking-tight text-fg-primary dark:text-fg-primary light:text-fg-primary-light">
              BharatTrip <span className="font-normal text-xs uppercase px-1.5 py-0.5 rounded border border-ink-border text-fg-muted dark:border-ink-border light:border-paper-border">Ops</span>
            </span>
          </div>

          {!hasKey && (
            <span className="hidden md:inline-flex items-center gap-1 text-[11px] font-mono px-2 py-0.5 rounded bg-amber-dim text-amber border border-amber-border">
              <AlertCircle className="w-3 h-3" />
              Running without LLM
            </span>
          )}
        </div>

        {/* Section Links */}
        <div className="hidden lg:flex items-center space-x-1">
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => scrollTo(item.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
                  isActive
                    ? 'text-amber bg-amber-dim border border-amber-border'
                    : 'text-fg-muted hover:text-fg-primary dark:text-fg-muted dark:hover:text-fg-primary light:text-fg-muted-light light:hover:text-fg-primary-light'
                }`}
              >
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Right actions */}
        <div className="flex items-center space-x-3">
          <a
            href={getLedgerDownloadUrl()}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded border transition-colors bg-ink-panel hover:bg-ink-hover border-ink-border text-fg-primary dark:bg-ink-panel dark:hover:bg-ink-hover dark:border-ink-border light:bg-paper-panel light:hover:bg-paper-hover light:border-paper-border light:text-fg-primary-light"
            title="Download unified reconciled ledger in Excel format"
          >
            <Download className="w-3.5 h-3.5 text-amber" />
            <span className="hidden sm:inline">Ledger (.xlsx)</span>
          </a>

          <button
            onClick={() => setDarkMode(!darkMode)}
            aria-label="Toggle theme"
            className="p-1.5 rounded border border-ink-border bg-ink-panel hover:bg-ink-hover text-fg-muted hover:text-fg-primary dark:border-ink-border dark:bg-ink-panel dark:hover:bg-ink-hover light:border-paper-border light:bg-paper-panel light:hover:bg-paper-hover transition-colors"
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber" /> : <Moon className="w-4 h-4 text-amber" />}
          </button>
        </div>
      </div>
    </nav>
  );
};
