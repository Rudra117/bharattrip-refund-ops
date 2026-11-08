import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Area,
  AreaChart,
} from 'recharts';
import { ArrowUpRight, TrendingUp, ShieldAlert } from 'lucide-react';
import { SummaryResponse, MonthlyResponse } from '../types';
import { formatINR, formatLakh, formatPct } from '../utils/format';
import { useCountUp } from '../utils/useCountUp';

interface HeroSectionProps {
  summary: SummaryResponse | null;
  monthly: MonthlyResponse | null;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ summary, monthly }) => {
  const animatedCount = useCountUp(summary?.gap_b_count ?? 0, 1400);

  if (!summary || !monthly) {
    return (
      <section id="hero" className="min-h-screen flex items-center justify-center">
        <div className="flex items-center space-x-3 text-fg-muted font-mono text-sm">
          <div className="w-2 h-2 rounded-full bg-amber animate-ping" />
          <span>Synchronizing operational ledger...</span>
        </div>
      </section>
    );
  }

  const records = monthly.records || [];
  const firstMonth = records[0];
  const lastMonth = records[records.length - 1];

  const chartData = records.map((r) => ({
    month: r.Month,
    rate: r["Gap B Rate (%)"],
    count: r["Gap B (Closed, No Fin)"],
    closed: r["Support Closed"],
    total: r["Total Requests"],
  }));

  // Average monthly requests
  const avgRequests = records.length > 0
    ? Math.round(records.reduce((acc, curr) => acc + (curr["Total Requests"] || 0), 0) / records.length)
    : 145;

  return (
    <section
      id="hero"
      className="min-h-screen flex flex-col justify-between pt-16 pb-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-ink-border/50 dark:border-ink-border/50 light:border-paper-border"
    >
      {/* Top Meta Tag */}
      <div className="flex items-center justify-between text-xs font-mono text-fg-muted uppercase tracking-wider mb-6">
        <span className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-signal-red" />
          Operational Reconciled Finding | Feb - Jun 2026
        </span>
        <span className="text-fg-faint">Single Source of Truth</span>
      </div>

      {/* Main Impact Number Display */}
      <div className="my-auto">
        <div className="flex flex-col lg:flex-row lg:items-end gap-6 lg:gap-12 mb-8">
          {/* Huge Stat Counter */}
          <div className="flex items-baseline">
            <span className="text-[96px] sm:text-[130px] md:text-[160px] font-heading font-bold text-signal-red leading-none tabular-nums tracking-tighter">
              {animatedCount}
            </span>
          </div>

          {/* Rupee Amount & Observation Details */}
          <div className="flex flex-col justify-end pb-2 sm:pb-4 space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-2xl sm:text-4xl font-heading font-semibold text-fg-primary dark:text-fg-primary light:text-fg-primary-light tabular-nums">
                {formatINR(summary.gap_b_amount)}
              </span>
              <span className="text-xs font-mono px-2 py-1 rounded bg-signal-red-dim text-signal-red border border-signal-red-border uppercase">
                Gap Class B
              </span>
            </div>
            <p className="text-base sm:text-lg text-fg-muted dark:text-fg-muted light:text-fg-muted-light max-w-xl font-normal leading-relaxed">
              <span className="text-fg-primary dark:text-fg-primary light:text-fg-primary-light font-medium">
                {summary.gap_b_count} refunds worth INR {formatLakh(summary.gap_b_amount)} lakh
              </span>{' '}
              were marked closed in Support but never reached Finance.
            </p>
          </div>
        </div>

        {/* Supporting Context Banner */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 rounded-lg border border-ink-border bg-ink-panel/60 dark:border-ink-border dark:bg-ink-panel/60 light:border-paper-border light:bg-paper-panel mb-8">
          <div>
            <div className="text-xs font-mono text-fg-muted uppercase mb-1">Volume Stability</div>
            <div className="text-sm text-fg-primary font-medium">
              Volume flat: ~{avgRequests} requests a month
            </div>
          </div>
          <div>
            <div className="text-xs font-mono text-fg-muted uppercase mb-1">Gap Rate Shift</div>
            <div className="text-sm text-signal-red font-medium flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-signal-red" />
              <span>
                {formatPct(firstMonth?.["Gap B Rate (%)"])} in {firstMonth?.Month} &rarr; {formatPct(lastMonth?.["Gap B Rate (%)"])} in {lastMonth?.Month}
              </span>
            </div>
          </div>
          <div>
            <div className="text-xs font-mono text-fg-muted uppercase mb-1">Finance Turnaround</div>
            <div className="text-sm text-fg-primary font-medium">
              {records[records.length - 2]?.["Avg Finance Proc Days"] ?? '-'}d in May (excluding unpaid)
            </div>
          </div>
        </div>

        {/* Monthly Gap Rate Chart Line drawing in beneath */}
        <div className="p-6 rounded-lg border border-ink-border bg-ink-panel dark:border-ink-border dark:bg-ink-panel light:border-paper-border light:bg-paper-panel">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-ink-border/50 mb-4 gap-2">
            <div>
              <h3 className="text-sm font-heading font-semibold text-fg-primary uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-signal-red" />
                Monthly Gap Rate Trend (% of Support-Closed Tickets Unrecorded in Finance)
              </h3>
              <p className="text-xs text-fg-muted mt-0.5">
                Steep divergence emerged in May and June while inbound customer request volume remained steady.
              </p>
            </div>
            <div className="text-right font-mono text-xs text-fg-muted">
              {records.length} Recorded Cohorts
            </div>
          </div>

          <div className="h-56 sm:h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="gapRateGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FF5C5C" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#FF5C5C" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2630" vertical={false} />
                <XAxis
                  dataKey="month"
                  stroke="#8A94A3"
                  fontSize={12}
                  tickLine={false}
                  axisLine={{ stroke: '#1E2630' }}
                />
                <YAxis
                  stroke="#8A94A3"
                  fontSize={12}
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={(val) => `${val}%`}
                />
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="p-3 rounded border border-ink-border bg-ink-card text-xs font-mono shadow-xl">
                          <div className="text-fg-muted mb-1">{data.month}</div>
                          <div className="text-signal-red font-semibold text-sm">
                            Gap Rate: {data.rate}%
                          </div>
                          <div className="text-fg-primary mt-1">
                            Unrecorded: {data.count} of {data.closed} closed
                          </div>
                          <div className="text-fg-faint text-[10px] mt-0.5">
                            Total Inbound: {data.total}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Area
                  type="monotone"
                  dataKey="rate"
                  stroke="#FF5C5C"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#gapRateGradient)"
                  isAnimationActive={true}
                  animationDuration={1500}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Bottom Footnote */}
      <div className="mt-8 flex flex-col sm:flex-row items-start sm:items-center justify-between text-[11px] font-mono text-fg-muted border-t border-ink-border/40 pt-4 gap-2">
        <div className="flex items-center gap-1.5">
          <ShieldAlert className="w-3.5 h-3.5 text-amber" />
          <span>Caveat: Turnaround calculations exclude unpaid refunds (survivorship constraint).</span>
        </div>
        <div>
          Snapshot: 30 June 2026
        </div>
      </div>
    </section>
  );
};
