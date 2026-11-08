import React, { useState, useEffect } from 'react';
import { ShieldCheck, Clock, AlertTriangle, FileSpreadsheet, ChevronRight, UserCheck } from 'lucide-react';
import { ApprovalTierResponse, StalledRecord } from '../types';
import { fetchApprovalTier, getLedgerDownloadUrl } from '../api/client';
import { formatINR } from '../utils/format';

export const ApprovalTierSection: React.FC = () => {
  const [data, setData] = useState<ApprovalTierResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const pageSize = 5;

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const res = await fetchApprovalTier();
        setData(res);
      } catch (err: any) {
        console.error('Failed to load approval tier metrics:', err);
        setError(err.message || 'Error loading approval tier metrics');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading || !data) return null;

  const totalPages = Math.ceil((data.pending_records?.length || 0) / pageSize) || 1;
  const paginatedRecords = (data.pending_records || []).slice((page - 1) * pageSize, page * pageSize);

  return (
    <section id="approvals" className="py-12 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-ink-border/50">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-8 pb-4 border-b border-ink-border gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-amber uppercase tracking-wider mb-2">
            <ShieldCheck className="w-4 h-4 text-amber" />
            <span>Governance & Policy Architecture</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-fg-primary tracking-tight">
            Large refunds waiting on approval
          </h2>
          <p className="mt-1 text-sm text-fg-muted max-w-3xl">
            Inferred approval tier above {formatINR(data.threshold)}: all recorded manager approvals in the dataset occur on payouts exceeding this threshold (two unapproved refunds sit at exactly {formatINR(data.threshold)}; smallest approved is INR 20,100). Refunds below this tier proceed through straight-through processing.
          </p>
        </div>

        <a
          href={getLedgerDownloadUrl()}
          download
          className="inline-flex items-center space-x-2 px-3 py-2 rounded border border-amber/40 bg-amber/10 text-amber text-xs font-mono hover:bg-amber/20 transition-colors flex-shrink-0"
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          <span>Sheet 9: Stalled_Approvals</span>
        </a>
      </div>

      {/* KPI 4-Card Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="p-5 rounded-lg border border-signal-red-border/50 bg-signal-red-dim/20">
          <div className="flex items-center justify-between text-xs font-mono text-signal-red mb-1">
            <span>STALLED APPROVALS</span>
            <AlertTriangle className="w-3.5 h-3.5 text-signal-red" />
          </div>
          <div className="text-2xl sm:text-3xl font-mono font-bold text-fg-primary">
            {data.pending_large_count} tickets
          </div>
          <div className="mt-1 text-xs text-fg-muted">
            Pending payout awaiting approval
          </div>
        </div>

        <div className="p-5 rounded-lg border border-amber-border/40 bg-ink-card">
          <div className="flex items-center justify-between text-xs font-mono text-amber mb-1">
            <span>PENDING VALUE</span>
            <ShieldCheck className="w-3.5 h-3.5 text-amber" />
          </div>
          <div className="text-2xl sm:text-3xl font-mono font-bold text-fg-primary">
            {formatINR(data.pending_large_amount)}
          </div>
          <div className="mt-1 text-xs text-fg-muted">
            Cumulative stalled capital
          </div>
        </div>

        <div className="p-5 rounded-lg border border-ink-border bg-ink-card">
          <div className="flex items-center justify-between text-xs font-mono text-fg-muted mb-1">
            <span>MEAN WAITING TIME</span>
            <Clock className="w-3.5 h-3.5 text-fg-muted" />
          </div>
          <div className="text-2xl sm:text-3xl font-mono font-bold text-fg-primary">
            {data.mean_wait_days} days
          </div>
          <div className="mt-1 text-xs text-fg-muted">
            Max waiting duration: {data.max_wait_days} days
          </div>
        </div>

        <div className="p-5 rounded-lg border border-ink-border bg-ink-card">
          <div className="flex items-center justify-between text-xs font-mono text-fg-muted mb-1">
            <span>INFERRED TIER THRESHOLD</span>
            <UserCheck className="w-3.5 h-3.5 text-fg-muted" />
          </div>
          <div className="text-2xl sm:text-3xl font-mono font-bold text-fg-primary">
            &gt; {formatINR(data.threshold)}
          </div>
          <div className="mt-1 text-xs text-fg-muted">
            All approved payouts &gt; INR 20,000 (smallest: INR 20,100)
          </div>
        </div>
      </div>

      {/* Observation Banner */}
      <div className="mb-8 p-4 rounded border border-ink-border bg-ink-panel/70">
        <div className="flex items-start space-x-3">
          <div className="p-1 rounded bg-amber/10 border border-amber/30 text-amber flex-shrink-0 mt-0.5">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div className="text-xs text-fg-secondary leading-relaxed">
            <strong className="text-fg-primary font-mono uppercase tracking-wide mr-1.5">Empirical Finding:</strong>
            {data.observation_note}
          </div>
        </div>
      </div>

      {/* Dual Analysis Grids: Turnaround Trend + Approver Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Turnaround Line / Table */}
        <div className="p-5 rounded-lg border border-ink-border bg-ink-card">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-ink-border/50">
            <div>
              <div className="text-xs font-mono text-amber uppercase tracking-wider">
                Turnaround Trajectory
              </div>
              <h4 className="text-base font-heading font-semibold text-fg-primary">
                Turnaround on Completed Tier Refunds (&gt; {formatINR(data.threshold)})
              </h4>
            </div>
            <span className="text-xs font-mono text-fg-muted">By Received Month</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono text-left">
              <thead>
                <tr className="border-b border-ink-border text-fg-muted uppercase">
                  <th className="py-2 px-3">Received Month</th>
                  <th className="py-2 px-3 text-right">Completed</th>
                  <th className="py-2 px-3 text-right">Avg Turnaround</th>
                  <th className="py-2 px-3 text-right">Velocity Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-border/30">
                {data.monthly_turnaround?.map((item, idx) => {
                  const isElevated = item.avg_proc_days > 10;
                  return (
                    <tr key={item.month} className="hover:bg-ink-panel/50">
                      <td className="py-2.5 px-3 font-semibold text-fg-primary">{item.month}</td>
                      <td className="py-2.5 px-3 text-right text-fg-secondary">{item.completed_count}</td>
                      <td className={`py-2.5 px-3 text-right font-bold ${isElevated ? 'text-signal-red' : 'text-fg-primary'}`}>
                        {item.avg_proc_days} days
                      </td>
                      <td className="py-2.5 px-3 text-right text-fg-muted">
                        {idx === 0 ? 'Baseline' : `${item.avg_proc_days > data.monthly_turnaround[idx - 1].avg_proc_days ? '+' : ''}${(item.avg_proc_days - data.monthly_turnaround[idx - 1].avg_proc_days).toFixed(1)}d`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-3 text-[11px] text-fg-muted leading-relaxed">
            Note: 1 large refund completed in June ({data.monthly_turnaround?.find((m) => m.month === '2026-06')?.avg_proc_days || 0}d), while {data.pending_large_count} large refunds remain in Pending Payout status.
          </div>
        </div>

        {/* Approver Documentation Matrix */}
        <div className="p-5 rounded-lg border border-ink-border bg-ink-card">
          <div className="flex items-center justify-between mb-4 pb-2 border-b border-ink-border/50">
            <div>
              <div className="text-xs font-mono text-amber uppercase tracking-wider">
                Approver Documentation
              </div>
              <h4 className="text-base font-heading font-semibold text-fg-primary">
                Approvals per Approver by Received Month
              </h4>
            </div>
            <span className="text-xs font-mono text-fg-muted">Finance Distribution</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs font-mono text-left">
              <thead>
                <tr className="border-b border-ink-border text-fg-muted uppercase">
                  <th className="py-2 px-3">Month</th>
                  <th className="py-2 px-3 text-right">N. Iyer</th>
                  <th className="py-2 px-3 text-right">R. Menon</th>
                  <th className="py-2 px-3 text-right">S. Bhatt</th>
                  <th className="py-2 px-3 text-right">Approved</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ink-border/30">
                {data.approver_breakdown?.map((row) => {
                  const isJune = row.month === '2026-06';
                  return (
                    <tr key={row.month} className={`hover:bg-ink-panel/50 ${isJune ? 'bg-amber/5' : ''}`}>
                      <td className="py-2.5 px-3 font-semibold text-fg-primary">
                        {row.month}
                        {isJune && <span className="ml-1.5 px-1.5 py-0.5 rounded text-[10px] bg-amber/20 text-amber">June</span>}
                      </td>
                      <td className={`py-2.5 px-3 text-right ${isJune && row['N. Iyer'] === 0 ? 'text-fg-muted' : 'text-fg-secondary'}`}>
                        {row['N. Iyer']}
                      </td>
                      <td className={`py-2.5 px-3 text-right ${isJune && row['R. Menon'] === 0 ? 'text-fg-muted' : 'text-fg-secondary'}`}>
                        {row['R. Menon']}
                      </td>
                      <td className={`py-2.5 px-3 text-right ${isJune && row['S. Bhatt'] > 0 ? 'text-amber font-bold' : 'text-fg-secondary'}`}>
                        {row['S. Bhatt']}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-fg-primary">
                        {row.total_approved}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="mt-3 text-[11px] text-fg-muted leading-relaxed">
            In June: 0 for N. Iyer, 0 for R. Menon, 1 for S. Bhatt (total 1 approved payout).
          </div>
        </div>
      </div>

      {/* Stalled Large Refunds Table */}
      <div className="p-5 rounded-lg border border-ink-border bg-ink-card">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-4 pb-2 border-b border-ink-border/50 gap-2">
          <div>
            <h4 className="text-base font-heading font-semibold text-fg-primary">
              Pending Large Refund Queue ({data.pending_large_count} Cases)
            </h4>
            <p className="text-xs text-fg-muted">
              Individual transactions awaiting managerial sign-off and payout release.
            </p>
          </div>
          <div className="flex items-center space-x-2 text-xs font-mono">
            <span className="text-fg-muted">Page {page} of {totalPages}</span>
            <div className="flex space-x-1">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-2 py-1 rounded bg-ink border border-ink-border disabled:opacity-40 hover:bg-ink-panel"
              >
                &larr;
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="px-2 py-1 rounded bg-ink border border-ink-border disabled:opacity-40 hover:bg-ink-panel"
              >
                &rarr;
              </button>
            </div>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs font-mono text-left">
            <thead>
              <tr className="border-b border-ink-border text-fg-muted uppercase">
                <th className="py-2 px-3">Ticket ID</th>
                <th className="py-2 px-3">Partner Agency</th>
                <th className="py-2 px-3">Sector</th>
                <th className="py-2 px-3 text-right">Amount</th>
                <th className="py-2 px-3">Received On</th>
                <th className="py-2 px-3 text-right">Age (Days)</th>
                <th className="py-2 px-3 text-right">Priority Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-border/30">
              {paginatedRecords.map((r: StalledRecord) => (
                <tr key={r.clean_id} className="hover:bg-ink-panel/50">
                  <td className="py-2.5 px-3 font-bold text-amber">{r.clean_id}</td>
                  <td className="py-2.5 px-3 text-fg-primary font-sans">{r.canonical_agent}</td>
                  <td className="py-2.5 px-3 text-fg-secondary">{r.route || 'N/A'}</td>
                  <td className="py-2.5 px-3 text-right font-bold text-fg-primary">
                    {formatINR(r['Refund Amount (INR)'])}
                  </td>
                  <td className="py-2.5 px-3 text-fg-muted">{r.parsed_received_on}</td>
                  <td className="py-2.5 px-3 text-right text-signal-red font-semibold">
                    {Math.round(r.effective_age_days)}d
                  </td>
                  <td className="py-2.5 px-3 text-right text-fg-secondary">
                    {Math.round(r.priority_score).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};
