import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { AlertCircle, Filter, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { EscalationsResponse } from '../types';

interface EscalationsSectionProps {
  escalations: EscalationsResponse | null;
}

const ROOT_CAUSE_COLORS: Record<string, string> = {
  'paid and matched': '#3DD6A3',
  'Support closed/no Finance': '#FF5C5C',
  'never logged': '#A855F7',
  'paid but amount differs': '#FFB547',
  'Finance pending/Support not closed': '#38BDF8',
  'declined': '#991B1B',
  'Support closed/Finance pending': '#F97316',
  'Finance-only': '#EC4899',
};

const getRootCauseLabel = (cause: string): string => {
  if (cause === 'Support closed/Finance pending') return 'Premature closure (Support closed / Finance pending)';
  if (cause === 'declined') return 'Decline recorded in Finance';
  return cause;
};

export const EscalationsSection: React.FC<EscalationsSectionProps> = ({ escalations }) => {
  const [selectedCause, setSelectedCause] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;

  const { monthlyTotals, rootCauses, trendData, paidMatchedCount, supportClosedCount } = useMemo(() => {
    if (!escalations) {
      return { monthlyTotals: [], rootCauses: [], trendData: [], paidMatchedCount: 0, supportClosedCount: 0 };
    }

    const trend = escalations.monthly_trend || [];
    const causes = escalations.root_causes.map((c) => c.root_cause);

    const totals = trend.map((row) => {
      const month = String(row.raised_month);
      let sum = 0;
      Object.entries(row).forEach(([key, val]) => {
        if (key !== 'raised_month' && typeof val === 'number') {
          sum += val;
        }
      });
      return { month, total: sum };
    });

    const paidCount = escalations.root_causes.find((c) => c.root_cause === 'paid and matched')?.count ?? 0;
    const closedCount = escalations.root_causes.find((c) => c.root_cause === 'Support closed/no Finance')?.count ?? 0;

    return {
      monthlyTotals: totals,
      rootCauses: causes,
      trendData: trend,
      paidMatchedCount: paidCount,
      supportClosedCount: closedCount,
    };
  }, [escalations]);

  if (!escalations) return null;

  // Filtered escalation records if user clicks a root cause
  const allFilteredRecords = selectedCause
    ? escalations.records.filter((r) => r.root_cause === selectedCause)
    : escalations.records;

  const totalPages = Math.ceil(allFilteredRecords.length / pageSize) || 1;
  const paginatedRecords = allFilteredRecords.slice((page - 1) * pageSize, page * pageSize);

  const handleSelectCause = (cause: string | null) => {
    setSelectedCause(cause);
    setPage(1);
  };

  return (
    <section
      id="escalations"
      className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-ink-border/50 dark:border-ink-border/50 light:border-paper-border"
    >
      {/* Section Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-amber uppercase tracking-wider mb-2">
            <AlertCircle className="w-3.5 h-3.5" />
            <span>Customer Friction & Audit Investigation</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-heading font-bold text-fg-primary tracking-tight">
            Escalation Root Causes
          </h2>
          <p className="mt-2 text-base text-fg-muted max-w-2xl">
            Audit of all {escalations.total} agent escalations. Root causes classified by cross-referencing Support and Finance operational data.
          </p>
        </div>

        {/* Monthly Volume Progression badges derived strictly from API */}
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {monthlyTotals.map((mt, idx) => {
            const isLast = idx === monthlyTotals.length - 1;
            return (
              <div
                key={mt.month}
                className={`px-3 py-2 rounded border font-mono text-xs flex flex-col min-w-[76px] ${
                  isLast
                    ? 'border-signal-red-border bg-signal-red-dim text-signal-red'
                    : 'border-ink-border bg-ink-panel text-fg-muted'
                }`}
              >
                <span className="text-[10px] uppercase text-fg-faint">{mt.month.replace('2026-', '')}</span>
                <span className="text-base font-bold tabular-nums mt-0.5">{mt.total}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Stacked Bar Chart & Root Cause Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-10">
        
        {/* Left 2 Cols: Stacked Bar Chart */}
        <div className="lg:col-span-2 p-6 rounded-lg border border-ink-border bg-ink-panel">
          <div className="flex items-center justify-between mb-6 pb-3 border-b border-ink-border/50">
            <div>
              <h3 className="text-sm font-heading font-semibold text-fg-primary uppercase tracking-wider">
                Monthly Root-Cause Composition
              </h3>
              <p className="text-xs text-fg-muted mt-0.5">
                Click any cause below to isolate specific tickets.
              </p>
            </div>
            {selectedCause && (
              <button
                onClick={() => setSelectedCause(null)}
                className="text-xs font-mono text-amber hover:underline flex items-center gap-1"
              >
                Clear filter &times;
              </button>
            )}
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1E2630" vertical={false} />
                <XAxis
                  dataKey="raised_month"
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
                />
                <Tooltip
                  cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }}
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const totalForMonth = payload.reduce((acc, p) => acc + (Number(p.value) || 0), 0);
                      return (
                        <div className="p-3 rounded border border-ink-border bg-ink-card text-xs font-mono shadow-xl max-w-xs">
                          <div className="text-fg-primary font-bold mb-2 pb-1 border-b border-ink-border flex justify-between">
                            <span>{label}</span>
                            <span className="text-amber">{totalForMonth} Total</span>
                          </div>
                          <div className="space-y-1">
                            {payload.map((p) => {
                              const val = Number(p.value) || 0;
                              if (val === 0) return null;
                              return (
                                <div key={p.name} className="flex items-center justify-between gap-4">
                                  <div className="flex items-center gap-1.5 truncate">
                                    <span
                                      className="w-2 h-2 rounded-full flex-shrink-0"
                                      style={{ backgroundColor: p.color }}
                                    />
                                    <span className="text-fg-muted truncate">{p.name}</span>
                                  </div>
                                  <span className="font-semibold text-fg-primary tabular-nums">{val}</span>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                {rootCauses.map((cause) => (
                  <Bar
                    key={cause}
                    dataKey={cause}
                    stackId="a"
                    fill={ROOT_CAUSE_COLORS[cause] || '#8A94A3'}
                    opacity={selectedCause === null || selectedCause === cause ? 1 : 0.25}
                    onClick={() => setSelectedCause(selectedCause === cause ? null : cause)}
                    className="cursor-pointer transition-opacity"
                  />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right 1 Col: Root Cause Breakdown List with Click-to-Filter */}
        <div className="p-6 rounded-lg border border-ink-border bg-ink-panel flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-ink-border/50">
              <h3 className="text-sm font-heading font-semibold text-fg-primary uppercase tracking-wider">
                Root Cause Breakdown
              </h3>
              <span className="text-xs font-mono text-fg-muted">{escalations.total} Cases</span>
            </div>

            <div className="space-y-2">
              {escalations.root_causes.map((item) => {
                const isSelected = selectedCause === item.root_cause;
                const color = ROOT_CAUSE_COLORS[item.root_cause] || '#8A94A3';
                return (
                  <button
                    key={item.root_cause}
                    onClick={() => handleSelectCause(isSelected ? null : item.root_cause)}
                    className={`w-full text-left p-2.5 rounded border transition-all flex items-center justify-between text-xs ${
                      isSelected
                        ? 'border-amber bg-amber-dim text-fg-primary'
                        : 'border-ink-border/60 bg-ink-card/50 hover:bg-ink-hover text-fg-muted'
                    }`}
                  >
                    <div className="flex items-center gap-2 truncate pr-2">
                      <span
                        className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                        style={{ backgroundColor: color }}
                      />
                      <span className="truncate font-medium text-fg-primary">{getRootCauseLabel(item.root_cause)}</span>
                    </div>
                    <div className="flex items-center gap-2 font-mono tabular-nums flex-shrink-0">
                      <span className="font-semibold text-fg-primary">{item.count}</span>
                      <span className="text-[10px] text-fg-faint">({item.share}%)</span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-ink-border/50 text-[11px] font-mono text-fg-faint">
            Observation: {paidMatchedCount} cases were already paid; {supportClosedCount} were closed in Support with zero Finance record.
          </div>
        </div>

      </div>

      {/* Estimated Addressable Escalations Callout */}
      <div className="p-5 rounded-lg border border-amber/30 bg-amber-dim/20 mb-8 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber uppercase tracking-wider mb-1">
            <CheckCircle2 className="w-4 h-4 text-amber" />
            <span>Estimated Addressable: 141 of {escalations.total} (91.0%)</span>
          </div>
          <p className="text-xs text-fg-muted max-w-3xl leading-relaxed">
            <strong className="text-fg-primary">Grouping Rule:</strong> 84 structural discrepancies (31 Support closed/no Finance + 29 never logged off-tracker + 18 amount differences + 6 declines recorded in Finance) + 57 status chases on completed payouts = 141 of {escalations.total} (91.0%). Expands to 147 (94.8%) when 6 premature closures (Support closed / Finance pending) are grouped as structural.
          </p>
        </div>
        <div className="flex items-center gap-2 font-mono text-xs flex-shrink-0">
          <span className="px-2.5 py-1 rounded bg-amber-dim border border-amber-border text-amber font-semibold">
            84 Structural
          </span>
          <span className="text-fg-faint">+</span>
          <span className="px-2.5 py-1 rounded bg-signal-green-dim border border-signal-green-border text-signal-green font-semibold">
            57 Paid Chases
          </span>
        </div>
      </div>

      {/* Escalation Drilldown Table */}
      <div className="rounded-lg border border-ink-border bg-ink-panel overflow-hidden">
        <div className="p-4 border-b border-ink-border flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-ink-border text-fg-muted">
              Audit Drilldown
            </span>
            <span className="text-xs text-fg-muted">
              {selectedCause ? `Showing tickets for: "${selectedCause}"` : 'All escalation records'}
            </span>
          </div>
          <span className="text-xs font-mono text-fg-faint">
            {allFilteredRecords.length} records total
          </span>
        </div>

        <div className="overflow-x-auto max-h-80 overflow-y-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="sticky top-0 bg-ink-card border-b border-ink-border text-fg-muted uppercase text-[10px]">
              <tr>
                <th className="px-4 py-3">Escalation ID</th>
                <th className="px-4 py-3">Raised On</th>
                <th className="px-4 py-3">Ticket ID</th>
                <th className="px-4 py-3">Agent</th>
                <th className="px-4 py-3">Root Cause</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Days Open</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-border/40 text-fg-primary">
              {paginatedRecords.map((row) => (
                <tr key={row.clean_escalation_id} className="hover:bg-ink-hover/50 transition-colors">
                  <td className="px-4 py-2.5 font-semibold text-amber">{row.clean_escalation_id}</td>
                  <td className="px-4 py-2.5 text-fg-muted">{row.parsed_raised_on}</td>
                  <td className="px-4 py-2.5">{row.clean_ticket_id || '-'}</td>
                  <td className="px-4 py-2.5">{row.canonical_agent}</td>
                  <td className="px-4 py-2.5">
                    <span
                      className="px-2 py-0.5 rounded text-[10px] font-semibold"
                      style={{
                        backgroundColor: `${ROOT_CAUSE_COLORS[row.root_cause] || '#8A94A3'}1A`,
                        color: ROOT_CAUSE_COLORS[row.root_cause] || '#8A94A3',
                      }}
                    >
                      {getRootCauseLabel(row.root_cause)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`px-2 py-0.5 rounded text-[10px] ${
                      row.clean_status === 'Open' ? 'bg-signal-red-dim text-signal-red' : 'bg-signal-green-dim text-signal-green'
                    }`}>
                      {row.clean_status}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 tabular-nums text-fg-muted">{row['Days Open']}d</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        {totalPages > 1 && (
          <div className="p-3 border-t border-ink-border/60 bg-ink-card/50 flex items-center justify-between text-xs font-mono">
            <span className="text-fg-muted">
              Page {page} of {totalPages} ({allFilteredRecords.length} records)
            </span>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-2.5 py-1 rounded border border-ink-border bg-ink-card text-fg-muted hover:text-fg-primary disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-2.5 py-1 rounded border border-ink-border bg-ink-card text-fg-muted hover:text-fg-primary disabled:opacity-40 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
