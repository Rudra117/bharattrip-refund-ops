import React, { useState, useEffect, useMemo } from 'react';
import {
  Search,
  Filter,
  Download,
  ArrowUpDown,
  AlertTriangle,
  FileSpreadsheet,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { GapsResponse, GapRecord } from '../types';
import { fetchGaps, getLedgerDownloadUrl } from '../api/client';
import { formatINR } from '../utils/format';

interface QueueSectionProps {
  externalAgentFilter?: string;
}

export const QueueSection: React.FC<QueueSectionProps> = ({ externalAgentFilter }) => {
  const [data, setData] = useState<GapsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState('');
  const [selectedGapClass, setSelectedGapClass] = useState('All');
  const [selectedAgent, setSelectedAgent] = useState('All');
  const [selectedTeam, setSelectedTeam] = useState('All');

  // Synchronize external agent filter if clicked from AgentExposure
  useEffect(() => {
    if (externalAgentFilter) {
      setSelectedAgent(externalAgentFilter);
    }
  }, [externalAgentFilter]);

  // Sorting
  const [sortField, setSortField] = useState<keyof GapRecord>('priority_score');
  const [sortAsc, setSortAsc] = useState(false);

  // Pagination
  const [page, setPage] = useState(1);
  const pageSize = 15;

  const loadData = async () => {
    try {
      setLoading(true);
      const res = await fetchGaps({
        gap_class: selectedGapClass,
        agent: selectedAgent,
        team: selectedTeam,
        limit: 300,
      });
      setData(res);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load action queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedGapClass, selectedAgent, selectedTeam]);

  const filteredAndSortedRecords = useMemo(() => {
    if (!data) return [];
    let list = [...data.records];

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(
        (r) =>
          r.clean_id.toLowerCase().includes(q) ||
          (r.raw_id && r.raw_id.toLowerCase().includes(q)) ||
          r.canonical_agent.toLowerCase().includes(q) ||
          r.route.toLowerCase().includes(q) ||
          (r.recommended_action || '').toLowerCase().includes(q)
      );
    }

    list.sort((a, b) => {
      let valA: any = a[sortField];
      let valB: any = b[sortField];

      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return sortAsc ? -1 : 1;
      if (valA > valB) return sortAsc ? 1 : -1;
      return 0;
    });

    return list;
  }, [data, search, sortField, sortAsc]);

  const paginatedRecords = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredAndSortedRecords.slice(start, start + pageSize);
  }, [filteredAndSortedRecords, page, pageSize]);

  const totalPages = Math.ceil(filteredAndSortedRecords.length / pageSize) || 1;

  const handleSort = (field: keyof GapRecord) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
    setPage(1);
  };

  const getGapBadgeClass = (gapClass: string) => {
    if (gapClass.includes('Gap B') || gapClass.includes('Gap D')) {
      return 'bg-signal-red-dim text-signal-red border border-signal-red-border';
    }
    if (gapClass.includes('Gap C') || gapClass.includes('Gap E')) {
      return 'bg-amber-dim text-amber border border-amber-border';
    }
    if (gapClass.includes('Gap A')) {
      return 'bg-signal-green-dim text-signal-green border border-signal-green-border';
    }
    return 'bg-ink-border/50 text-fg-muted border border-ink-border';
  };

  const getTeamBadgeClass = (team: string) => {
    switch (team) {
      case 'Support':
        return 'text-amber bg-amber-dim border border-amber-border/50';
      case 'Finance':
        return 'text-signal-blue bg-signal-blue-dim border border-signal-blue-border/50';
      case 'Joint':
        return 'text-signal-red bg-signal-red-dim border border-signal-red-border/50';
      default:
        return 'text-fg-faint bg-ink-border/40 border border-ink-border/40';
    }
  };

  return (
    <section
      id="queue"
      className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto border-b border-ink-border/50 dark:border-ink-border/50 light:border-paper-border"
    >
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-6">
        <div>
          <div className="flex items-center space-x-2 text-xs font-mono text-amber uppercase tracking-wider mb-2">
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>Prioritized Operational Remediation</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-heading font-bold text-fg-primary tracking-tight">
            The Action Queue
          </h2>
          <p className="mt-2 text-base text-fg-muted max-w-2xl">
            Ranked by priority score (Refund Amount &times; Age in Days). Reconciles tickets across Support and Finance with assigned team ownership and corrective steps.
          </p>
        </div>

        {/* Download Ledger Button */}
        <div>
          <a
            href={getLedgerDownloadUrl()}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-semibold bg-amber hover:bg-amber/90 text-ink transition-colors shadow-sm"
          >
            <Download className="w-4 h-4 text-ink" />
            <span>Download Ledger (.xlsx)</span>
          </a>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="p-4 rounded-lg border border-ink-border bg-ink-panel mb-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
          
          {/* Search Input */}
          <div className="relative md:col-span-1">
            <Search className="w-4 h-4 text-fg-muted absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search ID, agent, route..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full pl-9 pr-3 py-2 text-xs font-mono rounded border border-ink-border bg-ink-card text-fg-primary placeholder-fg-faint focus:outline-none focus:border-amber"
            />
          </div>

          {/* Gap Class Filter */}
          <div>
            <select
              value={selectedGapClass}
              onChange={(e) => {
                setSelectedGapClass(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by Gap Class"
              className="w-full px-3 py-2 text-xs font-mono rounded border border-ink-border bg-ink-card text-fg-primary focus:outline-none focus:border-amber"
            >
              <option value="All">All Gap Classes</option>
              {data?.filters.gap_classes.map((cls) => (
                <option key={cls} value={cls}>
                  {cls}
                </option>
              ))}
            </select>
          </div>

          {/* Team Filter */}
          <div>
            <select
              value={selectedTeam}
              onChange={(e) => {
                setSelectedTeam(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by Team"
              className="w-full px-3 py-2 text-xs font-mono rounded border border-ink-border bg-ink-card text-fg-primary focus:outline-none focus:border-amber"
            >
              <option value="All">All Owner Teams</option>
              {data?.filters.teams.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Agent Filter */}
          <div>
            <select
              value={selectedAgent}
              onChange={(e) => {
                setSelectedAgent(e.target.value);
                setPage(1);
              }}
              aria-label="Filter by Agent"
              className="w-full px-3 py-2 text-xs font-mono rounded border border-ink-border bg-ink-card text-fg-primary focus:outline-none focus:border-amber"
            >
              <option value="All">All Travel Agents</option>
              {data?.filters.agents.map((ag) => (
                <option key={ag} value={ag}>
                  {ag}
                </option>
              ))}
            </select>
          </div>

        </div>

        {/* Counter and Status */}
        <div className="flex items-center justify-between text-xs font-mono text-fg-muted pt-2 border-t border-ink-border/40">
          <div>
            Showing <span className="text-fg-primary font-bold">{filteredAndSortedRecords.length}</span> matching cases
            {data && <span> of {data.total_matching} in ledger</span>}
          </div>
          <div>
            Page {page} of {totalPages}
          </div>
        </div>
      </div>

      {/* Main Table */}
      <div className="rounded-lg border border-ink-border bg-ink-panel overflow-hidden shadow-sm">
        <div className="overflow-x-auto max-h-[580px] overflow-y-auto">
          <table className="w-full text-left text-xs font-mono whitespace-nowrap">
            <thead className="sticky top-0 z-20 bg-ink-card border-b border-ink-border text-fg-muted uppercase text-[10px]">
              <tr>
                <th
                  onClick={() => handleSort('clean_id')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Ticket ID</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('canonical_agent')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Agent</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th className="px-4 py-3.5">Route</th>
                <th
                  onClick={() => handleSort('gap_class')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Gap Class</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('owner_team')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none"
                >
                  <div className="flex items-center gap-1.5">
                    <span>Owner</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('Refund Amount (INR)')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none text-right"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <span>Refund Amt</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('Amount Paid (INR)')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none text-right"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <span>Paid Amt</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('effective_age_days')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none text-right"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <span>Age (d)</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th
                  onClick={() => handleSort('priority_score')}
                  className="px-4 py-3.5 cursor-pointer hover:text-fg-primary select-none text-right"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <span>Priority</span>
                    <ArrowUpDown className="w-3 h-3 text-fg-faint" />
                  </div>
                </th>
                <th className="px-4 py-3.5">Corrective Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ink-border/40 text-fg-primary">
              {loading && (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-fg-muted font-mono">
                    Loading action queue...
                  </td>
                </tr>
              )}
              {!loading && paginatedRecords.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-fg-muted font-mono">
                    No tickets match the selected criteria.
                  </td>
                </tr>
              )}
              {!loading &&
                paginatedRecords.map((row) => (
                  <tr key={row.clean_id} className="hover:bg-ink-hover/40 transition-colors">
                    <td className="px-4 py-2.5">
                      <div className="font-semibold text-amber">{row.clean_id}</div>
                      {row.raw_id && (
                        <div className="text-[10px] text-fg-faint" title={`Original Tracker Reference: ${row.raw_id}`}>
                          Raw: {row.raw_id}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-fg-primary font-medium">{row.canonical_agent}</td>
                    <td className="px-4 py-2.5 text-fg-muted">{row.route || '-'}</td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-semibold ${getGapBadgeClass(row.gap_class)}`}>
                        {row.gap_class.split(' ')[0]} {row.gap_class.split(' ')[1] || ''}
                      </span>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${getTeamBadgeClass(row.owner_team)}`}>
                        {row.owner_team}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums">
                      {row['Refund Amount (INR)'] > 0 ? formatINR(row['Refund Amount (INR)']) : '-'}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-fg-muted">
                      {row['Amount Paid (INR)'] > 0 ? formatINR(row['Amount Paid (INR)']) : '-'}
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums text-fg-muted">
                      {Math.round(row.effective_age_days)}d
                    </td>
                    <td className="px-4 py-2.5 text-right tabular-nums font-semibold text-amber">
                      {Math.round(row.priority_score).toLocaleString()}
                    </td>
                    <td className="px-4 py-2.5 text-fg-muted max-w-xs truncate" title={row.recommended_action}>
                      {row.recommended_action}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-ink-border bg-ink-card flex items-center justify-between text-xs font-mono text-fg-muted">
          <div>
            Showing {(page - 1) * pageSize + 1} to {Math.min(page * pageSize, filteredAndSortedRecords.length)} of {filteredAndSortedRecords.length}
          </div>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded border border-ink-border bg-ink-panel disabled:opacity-30 disabled:cursor-not-allowed hover:bg-ink-hover"
            >
              Previous
            </button>
            <span className="px-2">{page} / {totalPages}</span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded border border-ink-border bg-ink-panel disabled:opacity-30 disabled:cursor-not-allowed hover:bg-ink-hover"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
