import React from 'react';
import { ShieldCheck, Info, FileSpreadsheet } from 'lucide-react';
import { MonthlyResponse } from '../types';

interface FooterProps {
  monthly: MonthlyResponse | null;
}

export const Footer: React.FC<FooterProps> = ({ monthly }) => {
  const records = monthly?.records || [];
  const juneRecord = records.find((r) => r.Month.endsWith('-06')) || records[records.length - 1];
  const earlyRecords = records.filter((r) => !r.Month.endsWith('-06') && !r.Month.endsWith('-05'));

  const juneShareStr = juneRecord?.['Approval Share (%)'] != null
    ? `${juneRecord['Approval Share (%)']}%`
    : 'a recorded minority';

  const earlyShares = earlyRecords
    .map((r) => r['Approval Share (%)'])
    .filter((v): v is number => v != null);

  const minEarly = earlyShares.length > 0 ? Math.round(Math.min(...earlyShares)) : null;
  const maxEarly = earlyShares.length > 0 ? Math.round(Math.max(...earlyShares)) : null;
  const earlyRangeStr = minEarly !== null && maxEarly !== null
    ? `~${minEarly}-${maxEarly}%`
    : 'baseline levels';

  return (
    <footer className="border-t border-ink-border bg-ink-panel/70 dark:border-ink-border dark:bg-ink-panel/70 light:border-paper-border light:bg-paper-card py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-12 border-b border-ink-border/50">
          
          {/* Col 1: Reconciliation Methodology */}
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-amber uppercase font-semibold mb-3">
              <ShieldCheck className="w-4 h-4 text-amber" />
              <span>Duplicate Resolution Rule</span>
            </div>
            <p className="text-xs text-fg-muted leading-relaxed font-mono">
              In cases of duplicate ticket entries within the Support tracker, the engine retains the row with the latest <code className="text-fg-primary">Last Updated</code> timestamp. On a tie, it retains the row whose <code className="text-fg-primary">Refund Amount</code> matches Finance <code className="text-fg-primary">Amount Paid</code> or <code className="text-fg-primary">Amount Paid + Deduction</code>. If neither matches, the later row in the sheet is retained. All conflicting duplicate rows are isolated in a separate audit table.
            </p>
          </div>

          {/* Col 2: Turnaround Calculation Caveat */}
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-amber uppercase font-semibold mb-3">
              <Info className="w-4 h-4 text-amber" />
              <span>Survivorship Constraint</span>
            </div>
            <p className="text-xs text-fg-muted leading-relaxed font-mono">
              Turnaround duration (<code className="text-fg-primary">Processed On</code> minus <code className="text-fg-primary">Received On</code>) is calculated strictly on completed payouts. Unpaid and open refunds are excluded from this metric, introducing a survivorship constraint that reflects turnaround exclusively for finalized transactions.
            </p>
          </div>

          {/* Col 3: Field Governance & Audits */}
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-amber uppercase font-semibold mb-3">
              <FileSpreadsheet className="w-4 h-4 text-amber" />
              <span>Approval Field Documentation</span>
            </div>
            <p className="text-xs text-fg-muted leading-relaxed font-mono">
              Approver recorded on almost no June payouts because refunds above ~INR 20,000 (the inferred approval tier) were mostly still pending; cause not visible in the data. All observations reflect empirical cross-tracker reconciliations without speculation on internal organizational motivations.
            </p>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs font-mono text-fg-muted gap-4">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-signal-green" />
            <span>BharatTrip Reconciled Refund Platform</span>
            <span className="text-fg-faint">&bull;</span>
            <span>Snapshot: 30 June 2026</span>
          </div>

          <div className="text-fg-faint text-[11px]">
            Reconciled Operational Dataset &bull; Single Source of Truth
          </div>
        </div>
      </div>
    </footer>
  );
};
