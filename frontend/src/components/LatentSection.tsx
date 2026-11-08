import React, { useState, useEffect } from 'react';
import { ShieldAlert, Clock, Copy, Check, Send, ChevronDown, ChevronUp } from 'lucide-react';
import { LatentResponse, LatentRecord } from '../types';
import { fetchLatent } from '../api/client';
import { formatINR } from '../utils/format';

export const LatentSection: React.FC = () => {
  const [data, setData] = useState<LatentResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [page, setPage] = useState<number>(1);
  const pageSize = 6;

  useEffect(() => {
    async function loadLatent() {
      try {
        setLoading(true);
        const res = await fetchLatent();
        setData(res);
      } catch (err) {
        console.error('Failed to load latent escalations:', err);
      } finally {
        setLoading(false);
      }
    }
    loadLatent();
  }, []);

  if (loading || !data) return null;

  const totalPages = Math.ceil(data.records.length / pageSize) || 1;
  const paginatedRecords = data.records.slice((page - 1) * pageSize, page * pageSize);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2500);
  };

  return (
    <div className="mb-12 p-6 rounded-lg border border-signal-red-border/60 bg-signal-red-dim/15">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-6 pb-4 border-b border-signal-red-border/30 gap-4">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-signal-red uppercase tracking-wider mb-1">
            <ShieldAlert className="w-3.5 h-3.5 text-signal-red" />
            <span>Chase First: Latent Escalation Discovery</span>
          </div>
          <h3 className="text-xl sm:text-2xl font-heading font-bold text-fg-primary tracking-tight">
            Latent Escalation Candidates ({data.count} Tickets)
          </h3>
          <p className="mt-1 text-xs text-fg-muted max-w-2xl">
            {data.count} tickets closed in Support with zero Finance record and <strong>zero agent complaints logged yet</strong>. Total unprompted exposure: <strong>{formatINR(data.total_amount)}</strong> (mean age {data.mean_age_days}d; {data.over_30_days_count} over 30d). Proactive outreach resolves these before partner escalations occur.
          </p>
        </div>

        {/* Badges */}
        <div className="flex items-center gap-2 font-mono text-xs flex-shrink-0">
          <div className="px-3 py-2 rounded bg-ink-card border border-signal-red-border/50 text-right">
            <div className="text-[10px] uppercase text-fg-faint">At-Risk Value</div>
            <div className="text-sm font-bold text-signal-red">{formatINR(data.total_amount)}</div>
          </div>
          <div className="px-3 py-2 rounded bg-ink-card border border-ink-border text-right">
            <div className="text-[10px] uppercase text-fg-faint">Mean Age</div>
            <div className="text-sm font-bold text-fg-primary">{data.mean_age_days}d</div>
          </div>
        </div>
      </div>

      {/* Latent Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-4">
        {paginatedRecords.map((item) => {
          const isExpanded = expandedId === item.clean_id;
          const isCopied = copiedId === item.clean_id;

          return (
            <div
              key={item.clean_id}
              className="p-4 rounded border border-ink-border bg-ink-panel flex flex-col justify-between space-y-3"
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-mono text-xs font-bold text-amber">
                    {item.clean_id}
                    {item.raw_id && item.raw_id !== item.clean_id && (
                      <span className="text-[10px] text-fg-faint font-normal ml-1">({item.raw_id})</span>
                    )}
                  </span>
                  <span className="font-mono text-xs font-semibold text-fg-primary tabular-nums">
                    {formatINR(item['Refund Amount (INR)'])}
                  </span>
                </div>

                <div className="text-xs text-fg-muted flex items-center justify-between">
                  <span className="font-medium text-fg-primary truncate pr-2">{item.canonical_agent}</span>
                  <span className="font-mono text-[11px] text-fg-faint">{item.route}</span>
                </div>

                <div className="mt-2 flex items-center gap-1.5 text-[11px] font-mono text-signal-red">
                  <Clock className="w-3 h-3 flex-shrink-0" />
                  <span>{item.effective_age_days} days since request without payout</span>
                </div>
              </div>

              {/* Proactive draft button and drawer */}
              <div className="pt-2 border-t border-ink-border/50">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => setExpandedId(isExpanded ? null : item.clean_id)}
                    className="text-[11px] font-mono text-fg-muted hover:text-fg-primary flex items-center gap-1"
                  >
                    <span>{isExpanded ? 'Hide Draft' : 'Preview Outreach'}</span>
                    {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  </button>

                  <button
                    onClick={() => handleCopy(item.clean_id, item.proactive_draft)}
                    className={`inline-flex items-center gap-1 px-2.5 py-1 rounded text-xs font-mono font-medium transition-colors ${
                      isCopied
                        ? 'bg-signal-green-dim text-signal-green border border-signal-green-border'
                        : 'bg-amber-dim text-amber border border-amber-border hover:bg-amber hover:text-ink'
                    }`}
                  >
                    {isCopied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                    <span>{isCopied ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>

                {isExpanded && (
                  <div className="mt-2.5 p-2.5 rounded bg-ink-card border border-ink-border text-[11px] font-mono text-fg-muted leading-relaxed select-all">
                    {item.proactive_draft}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination Bar */}
      {totalPages > 1 && (
        <div className="pt-3 border-t border-signal-red-border/30 flex items-center justify-between text-xs font-mono">
          <span className="text-fg-muted">
            Page {page} of {totalPages} ({data.records.length} latent candidates)
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
  );
};
