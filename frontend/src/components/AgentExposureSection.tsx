import React, { useState, useEffect } from 'react';
import { Users, TrendingUp, AlertTriangle, ArrowUpDown, ArrowRight } from 'lucide-react';
import { AgentExposureResponse, AgentExposureItem } from '../types';
import { fetchAgentExposure } from '../api/client';
import { formatINR } from '../utils/format';

interface AgentExposureSectionProps {
  onSelectAgent?: (agentName: string) => void;
}

export const AgentExposureSection: React.FC<AgentExposureSectionProps> = ({ onSelectAgent }) => {
  const [data, setData] = useState<AgentExposureResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [sortBy, setSortBy] = useState<'stuck_amount' | 'stuck_tickets'>('stuck_amount');

  useEffect(() => {
    async function loadExposure() {
      try {
        setLoading(true);
        const res = await fetchAgentExposure();
        setData(res);
      } catch (err) {
        console.error('Failed to load agent exposure:', err);
      } finally {
        setLoading(false);
      }
    }
    loadExposure();
  }, []);

  if (loading || !data) return null;

  const sortedAgents = [...data.agents].sort((a, b) => b[sortBy] - a[sortBy]);
  const maxAmount = Math.max(...data.agents.map((a) => a.stuck_amount), 1);

  return (
    <div className="mb-12 p-6 rounded-lg border border-ink-border bg-ink-panel">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-6 pb-4 border-b border-ink-border/50 gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-amber uppercase tracking-wider mb-1">
            <Users className="w-3.5 h-3.5" />
            <span>Concentration & Partner Risk (Classes B, C, D)</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-heading font-bold text-fg-primary tracking-tight">
            Agent Exposure Concentration
          </h3>
          <p className="mt-1 text-xs text-fg-muted max-w-xl">
            {data.total_agents} travel partners hold {formatINR(data.total_stuck_value)} across stuck classes. Top 5 agencies account for {data.top5_share_pct}% of total exposure.
          </p>
        </div>

        {/* KPI Chips */}
        <div className="flex items-center gap-3">
          <div className="px-3 py-2 rounded bg-ink-card border border-amber/30 text-right font-mono">
            <div className="text-[10px] uppercase text-fg-faint">Top 5 Concentration</div>
            <div className="text-base font-bold text-amber">{data.top5_share_pct}%</div>
          </div>
          <div className="px-3 py-2 rounded bg-ink-card border border-ink-border text-right font-mono">
            <div className="text-[10px] uppercase text-fg-faint">Total Stuck Value</div>
            <div className="text-base font-bold text-fg-primary">{formatINR(data.total_stuck_value)}</div>
          </div>
        </div>
      </div>

      {/* Sort toggle */}
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs font-mono text-fg-muted">
          Showing all {sortedAgents.length} agents &bull; Click any agent to filter Action Queue below
        </span>
        <div className="flex items-center gap-1 text-xs font-mono">
          <span className="text-fg-faint text-[10px] mr-1">Sort by:</span>
          <button
            onClick={() => setSortBy('stuck_amount')}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              sortBy === 'stuck_amount'
                ? 'bg-amber text-ink font-semibold'
                : 'bg-ink-card text-fg-muted hover:text-fg-primary border border-ink-border'
            }`}
          >
            Amount
          </button>
          <button
            onClick={() => setSortBy('stuck_tickets')}
            className={`px-2 py-1 rounded text-xs transition-colors ${
              sortBy === 'stuck_tickets'
                ? 'bg-amber text-ink font-semibold'
                : 'bg-ink-card text-fg-muted hover:text-fg-primary border border-ink-border'
            }`}
          >
            Tickets
          </button>
        </div>
      </div>

      {/* Grid of Agent Bars */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {sortedAgents.slice(0, 9).map((agent, index) => {
          const pct = Math.round((agent.stuck_amount / maxAmount) * 100);
          return (
            <div
              key={agent.canonical_agent}
              onClick={() => onSelectAgent && onSelectAgent(agent.canonical_agent)}
              className="p-3 rounded border border-ink-border/70 bg-ink-card/60 hover:bg-ink-hover hover:border-amber/50 cursor-pointer transition-all flex flex-col justify-between group"
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-semibold text-fg-primary group-hover:text-amber transition-colors truncate pr-2">
                    {index + 1}. {agent.canonical_agent}
                  </span>
                  <span className="text-xs font-mono font-bold text-fg-primary tabular-nums">
                    {formatINR(agent.stuck_amount)}
                  </span>
                </div>
                
                {/* Visual share bar */}
                <div className="w-full h-1.5 rounded-full bg-ink-border overflow-hidden mb-2">
                  <div
                    className="h-full bg-amber transition-all duration-300"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>

              <div className="flex items-center justify-between text-[10px] font-mono text-fg-faint pt-1 border-t border-ink-border/40">
                <div className="flex items-center gap-1.5">
                  <span className="text-signal-red">B:{agent.gap_b_count}</span>
                  <span className="text-amber">C:{agent.gap_c_count}</span>
                  <span className="text-fg-muted">D:{agent.gap_d_count}</span>
                </div>
                <span className="group-hover:text-amber flex items-center gap-0.5 transition-colors">
                  {agent.stuck_tickets} tickets <ArrowRight className="w-2.5 h-2.5" />
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Definition Footnote */}
      <div className="mt-4 pt-3 border-t border-ink-border/40 text-[11px] font-mono text-fg-muted">
        Definition: Closed in Support but unpaid (classes B, C, D: Support Closed with No Finance Record, Support Closed with Finance Pending, Support Closed with Finance Declined). Total exposure: {formatINR(data.total_stuck_value)} across {data.total_stuck_tickets} tickets. Top 5 partners hold {data.top5_share_pct}% of total stuck capital.
      </div>
    </div>
  );
};
