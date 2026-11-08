import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight, ArrowDown, AlertTriangle, CheckCircle2, Clock, HelpCircle, GitCommit } from 'lucide-react';
import { SummaryResponse, EscalationsResponse } from '../types';
import { formatINR, formatLakh } from '../utils/format';

interface LeakFlowProps {
  summary: SummaryResponse | null;
  escalations: EscalationsResponse | null;
}

export const LeakFlowSection: React.FC<LeakFlowProps> = ({ summary, escalations }) => {
  const sectionRef = useRef<HTMLDivElement>(null);
  const [hasAnimated, setHasAnimated] = useState(true);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setHasAnimated(true);
        }
      },
      { threshold: 0.2 }
    );

    if (sectionRef.current) {
      observer.observe(sectionRef.current);
    }

    return () => observer.disconnect();
  }, []);

  if (!summary) return null;

  // Never logged count from escalations API
  const neverLoggedCount = escalations?.root_causes.find(
    (r) => r.root_cause.toLowerCase() === 'never logged'
  )?.count ?? 0;

  return (
    <section
      id="leaks"
      ref={sectionRef}
      className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-ink-border/50 dark:border-ink-border/50 light:border-paper-border"
    >
      {/* Section Header */}
      <div className="mb-14">
        <div className="flex items-center space-x-2 text-xs font-mono text-amber uppercase tracking-wider mb-2">
          <GitCommit className="w-3.5 h-3.5" />
          <span>Operational Architecture & Leakage Analysis</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-heading font-bold text-fg-primary dark:text-fg-primary light:text-fg-primary-light tracking-tight">
          How the Refund Process Leaks
        </h2>
        <p className="mt-2 text-base text-fg-muted max-w-2xl">
          Tracing the lifecycle of a refund from B2B Travel Agent intake through Support tracking to Finance payout. Three empirical divergence points prevent resolution.
        </p>
      </div>

      {/* Process Flow Interactive Container */}
      <div className={`transition-all duration-1000 ${hasAnimated ? 'opacity-100 translate-y-0' : 'opacity-20 translate-y-8'}`}>
        
        {/* Horizontal Pipeline Steps with Connected Directional Flow */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
          
          {/* Step 1: Agent Request */}
          <div className="p-5 rounded-lg border border-ink-border bg-ink-panel relative flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-ink-border/60 text-fg-muted">01 / Inbound</span>
                <span className="text-xs font-mono text-fg-muted">{summary.canonical_agents_count} Agents</span>
              </div>
              <h3 className="font-heading font-semibold text-lg text-fg-primary mb-1">
                Travel Agent
              </h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Agent submits refund request via Email, WhatsApp, or Portal.
              </p>
            </div>
            <div className="mt-6 pt-3 border-t border-ink-border/40 font-mono text-xs text-fg-faint">
              Intake Trigger
            </div>
            {/* Connector Arrow to Step 2 */}
            <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-ink-card border border-ink-border items-center justify-center text-fg-muted shadow-sm">
              <ArrowRight className="w-3.5 h-3.5 text-amber" />
            </div>
          </div>

          {/* Mobile down arrow */}
          <div className="flex md:hidden justify-center items-center -my-1 text-fg-muted">
            <ArrowDown className="w-4 h-4 text-amber" />
          </div>

          {/* Step 2: Support Tracker */}
          <div className="p-5 rounded-lg border border-ink-border bg-ink-panel relative flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-ink-border/60 text-fg-muted">02 / Triage</span>
                <span className="text-xs font-mono text-fg-muted">{summary.total_support_tickets} Logged</span>
              </div>
              <h3 className="font-heading font-semibold text-lg text-fg-primary mb-1">
                Support Tracker
              </h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Support logs request and updates ticket status.
              </p>
            </div>
            <div className="mt-6 pt-3 border-t border-ink-border/40 font-mono text-xs text-fg-faint">
              Support Ownership
            </div>
            {/* Connector Arrow to Step 3 */}
            <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-ink-card border border-ink-border items-center justify-center text-fg-muted shadow-sm">
              <ArrowRight className="w-3.5 h-3.5 text-amber" />
            </div>
          </div>

          {/* Mobile down arrow */}
          <div className="flex md:hidden justify-center items-center -my-1 text-fg-muted">
            <ArrowDown className="w-4 h-4 text-amber" />
          </div>

          {/* Step 3: Finance Processing */}
          <div className="p-5 rounded-lg border border-ink-border bg-ink-panel relative flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-ink-border/60 text-fg-muted">03 / Execution</span>
                <span className="text-xs font-mono text-fg-muted">{summary.total_finance_payouts} Recorded</span>
              </div>
              <h3 className="font-heading font-semibold text-lg text-fg-primary mb-1">
                Finance Tracker
              </h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Finance records receipt and updates payout status.
              </p>
            </div>
            <div className="mt-6 pt-3 border-t border-ink-border/40 font-mono text-xs text-fg-faint">
              Finance Ownership
            </div>
            {/* Connector Arrow to Step 4 */}
            <div className="hidden md:flex absolute -right-3 top-1/2 -translate-y-1/2 z-10 w-6 h-6 rounded-full bg-ink-card border border-ink-border items-center justify-center text-fg-muted shadow-sm">
              <ArrowRight className="w-3.5 h-3.5 text-signal-green" />
            </div>
          </div>

          {/* Mobile down arrow */}
          <div className="flex md:hidden justify-center items-center -my-1 text-fg-muted">
            <ArrowDown className="w-4 h-4 text-signal-green" />
          </div>

          {/* Step 4: Settled Payout in Support */}
          <div className="p-5 rounded-lg border border-signal-green-border bg-signal-green-dim/20 relative flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-signal-green-dim text-signal-green">04 / Settled</span>
                <CheckCircle2 className="w-4 h-4 text-signal-green" />
              </div>
              <h3 className="font-heading font-semibold text-lg text-signal-green mb-1">
                Agent Credited
              </h3>
              <p className="text-xs text-fg-muted leading-relaxed">
                Payout recorded as Refund Done in Finance and identified in Support.
              </p>
            </div>
            <div className="mt-6 pt-3 border-t border-signal-green-border/30 font-mono text-xs text-signal-green font-semibold">
              {summary.paid_in_support} Payouts Completed in Support
            </div>
          </div>

        </div>

        {/* Downward Connector Header */}
        <div className="mt-10 mb-4 flex items-center gap-3">
          <div className="h-[1px] flex-1 bg-ink-border/60" />
          <div className="flex items-center gap-2 text-[11px] font-mono uppercase tracking-wider text-fg-muted">
            <ArrowDown className="w-3.5 h-3.5 text-amber" />
            <span>Process Leak Points Identified in Cross-Tracker Reconciliation</span>
          </div>
          <div className="h-[1px] flex-1 bg-ink-border/60" />
        </div>

        {/* SVG Flow Connectors and Leak Annotations */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Leak 1: Never Logged / Off-tracker */}
          <div className="p-5 rounded-lg border border-ink-border bg-ink-card relative overflow-hidden group hover:border-amber-border transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-amber" />
                <span className="text-xs font-mono text-amber uppercase font-semibold">Leak Point 1</span>
              </div>
              <span className="font-mono text-2xl font-bold text-fg-primary tabular-nums">
                {neverLoggedCount}
              </span>
            </div>
            <h4 className="mt-3 text-sm font-semibold text-fg-primary">
              Escalations With No Usable Reference
            </h4>
            <p className="mt-1 text-xs text-fg-muted leading-relaxed">
              Inquiries escalated by travel agents where no usable ticket reference was provided or found in operational trackers.
            </p>
            <div className="mt-4 pt-3 border-t border-ink-border/60 flex items-center justify-between text-[11px] font-mono text-fg-faint">
              <span>Location: Intake &rarr; Support</span>
              <span className="text-amber">Off-Tracker Escalations</span>
            </div>
          </div>

          {/* Leak 2: Gap Class B (Closed, No Finance) */}
          <div className="p-5 rounded-lg border border-signal-red-border bg-signal-red-dim/20 relative overflow-hidden group hover:border-signal-red transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-signal-red animate-pulse" />
                <span className="text-xs font-mono text-signal-red uppercase font-semibold">Leak Point 2 (Primary)</span>
              </div>
              <div className="text-right">
                <div className="font-mono text-2xl font-bold text-signal-red tabular-nums">
                  {summary.gap_b_count}
                </div>
                <div className="font-mono text-xs text-signal-red">
                  {formatINR(summary.gap_b_amount)}
                </div>
              </div>
            </div>
            <h4 className="mt-3 text-sm font-semibold text-fg-primary">
              Support Closed, No Finance Record
            </h4>
            <p className="mt-1 text-xs text-fg-muted leading-relaxed">
              Tickets marked &ldquo;Closed&rdquo; in Support that have zero corresponding entry in the Finance payout tracker.
            </p>
            <div className="mt-4 pt-3 border-t border-signal-red-border/40 flex items-center justify-between text-[11px] font-mono">
              <span className="text-fg-muted">Location: Support &rarr; Finance Handoff</span>
              <span className="text-signal-red font-semibold">Gap Class B</span>
            </div>
          </div>

          {/* Leak 3: Gap Class C (Pending in Finance) */}
          <div className="p-5 rounded-lg border border-ink-border bg-ink-card relative overflow-hidden group hover:border-amber-border transition-colors">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-amber" />
                <span className="text-xs font-mono text-amber uppercase font-semibold">Leak Point 3</span>
              </div>
              <div className="text-right">
                <div className="font-mono text-2xl font-bold text-fg-primary tabular-nums">
                  {summary.gap_c_count}
                </div>
                <div className="font-mono text-xs text-fg-muted">
                  {formatINR(summary.gap_c_amount)}
                </div>
              </div>
            </div>
            <h4 className="mt-3 text-sm font-semibold text-fg-primary">
              Closed in Support, Pending in Finance
            </h4>
            <p className="mt-1 text-xs text-fg-muted leading-relaxed">
              Tickets closed in Support where Finance received the item but payout status remains Pending Payout.
            </p>
            <div className="mt-4 pt-3 border-t border-ink-border/60 flex items-center justify-between text-[11px] font-mono text-fg-faint">
              <span>Location: Finance Execution</span>
              <span className="text-amber">Gap Class C</span>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
