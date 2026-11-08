import React, { useState, useEffect } from 'react';
import { SummaryResponse, MonthlyResponse, EscalationsResponse } from './types';
import { fetchSummary, fetchMonthly, fetchEscalations } from './api/client';
import { Navbar } from './components/Navbar';
import { HeroSection } from './components/HeroSection';
import { LeakFlowSection } from './components/LeakFlowSection';
import { EscalationsSection } from './components/EscalationsSection';
import { AgentExposureSection } from './components/AgentExposureSection';
import { LatentSection } from './components/LatentSection';
import { ApprovalTierSection } from './components/ApprovalTierSection';
import { QueueSection } from './components/QueueSection';
import { IntakeSection } from './components/IntakeSection';
import { Footer } from './components/Footer';

export function App() {
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('theme');
      if (saved) return saved === 'dark';
    } catch (e) {
      // ignore
    }
    return true;
  });
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [monthly, setMonthly] = useState<MonthlyResponse | null>(null);
  const [escalations, setEscalations] = useState<EscalationsResponse | null>(null);
  const [activeSection, setActiveSection] = useState<string>('hero');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [filterAgent, setFilterAgent] = useState<string>('All');

  const handleSelectAgent = (agent: string) => {
    setFilterAgent(agent);
    const qEl = document.getElementById('queue');
    if (qEl) {
      qEl.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Sync dark mode class on document element
  useEffect(() => {
    try {
      localStorage.setItem('theme', darkMode ? 'dark' : 'light');
    } catch (e) {
      // ignore
    }
    if (darkMode) {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.add('light');
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Load core data from API
  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        const [sumRes, monRes, escRes] = await Promise.all([
          fetchSummary(),
          fetchMonthly(),
          fetchEscalations(),
        ]);
        setSummary(sumRes);
        setMonthly(monRes);
        setEscalations(escRes);
        setError(null);
      } catch (err: any) {
        console.error('Failed to load API data:', err);
        setError(err.message || 'Error connecting to API server');
      } finally {
        setLoading(false);
      }
    }

    loadInitialData();
  }, []);

  // Track active section on scroll
  useEffect(() => {
    const handleScroll = () => {
      const sections = ['hero', 'leaks', 'escalations', 'approvals', 'queue', 'intake'];
      const scrollPos = window.scrollY + 200;

      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const top = el.offsetTop;
          const height = el.offsetHeight;
          if (scrollPos >= top && scrollPos < top + height) {
            setActiveSection(sectionId);
            break;
          }
        }
      }
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div className="min-h-screen bg-ink text-fg-primary dark:bg-ink dark:text-fg-primary light:bg-paper light:text-fg-primary-light transition-colors duration-200">
      {/* Sticky Top Navigation */}
      <Navbar
        darkMode={darkMode}
        setDarkMode={setDarkMode}
        activeSection={activeSection}
        hasKey={summary?.has_key ?? false}
      />

      {/* Global Error Banner if API connection fails */}
      {error && (
        <div className="bg-signal-red-dim border-b border-signal-red-border text-signal-red px-4 py-3 text-center text-xs font-mono">
          API Connection Alert: {error}. Ensure FastAPI is running on port 8000.
        </div>
      )}

      {/* Main Single-Scrolling Story Flow */}
      <main>
        {/* Section 1: Hero Impact Viewport */}
        <HeroSection summary={summary} monthly={monthly} />

        {/* Section 2: How the Process Leaks */}
        <LeakFlowSection summary={summary} escalations={escalations} />

        {/* Section 3: Escalation Root Causes */}
        <EscalationsSection escalations={escalations} />

        {/* Section 4: Proactive Intelligence & Partner Risk */}
        <section className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-ink-border/50">
          <AgentExposureSection onSelectAgent={handleSelectAgent} />
          <LatentSection />
        </section>

        {/* Section 5: Governance & Approval Tier Policy */}
        <ApprovalTierSection />

        {/* Section 6: Prioritized Action Queue */}
        <QueueSection externalAgentFilter={filterAgent} />

        {/* Section 6: Grounded Intake Assistant */}
        <IntakeSection />
      </main>

      {/* Footnotes and Governance */}
      <Footer monthly={monthly} />
    </div>
  );
}

export default App;
