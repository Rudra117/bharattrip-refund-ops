import React, { useState, useEffect } from 'react';
import {
  Send,
  Sparkles,
  Bot,
  Copy,
  Check,
  AlertCircle,
  CheckCircle2,
  HelpCircle,
  FileText,
  User,
  Hash,
  MapPin,
  Calendar,
  Layers,
  ArrowRight,
} from 'lucide-react';
import { IntakeResponse, PresetsResponse, Preset } from '../types';
import { submitIntake, fetchPresets } from '../api/client';
import { formatINR } from '../utils/format';

export const IntakeSection: React.FC = () => {
  const [presets, setPresets] = useState<PresetsResponse | null>(null);
  const [message, setMessage] = useState('');
  const [channel, setChannel] = useState('Email');
  const [messageDate, setMessageDate] = useState<string>('2026-06-05');
  const [isTyping, setIsTyping] = useState(false);
  const [result, setResult] = useState<IntakeResponse | null>(null);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchPresets()
      .then((p) => {
        setPresets(p);
        // Default to preset A
        if (p?.preset_a) {
          setMessage(p.preset_a.text || '');
          setChannel(p.preset_a.channel || 'Email');
          setMessageDate(p.preset_a.date || '2026-06-05');
        }
      })
      .catch((err) => console.error('Presets error:', err));
  }, []);

  const handleApplyPreset = (preset: Preset) => {
    setMessage(preset.text || '');
    if (preset.channel) setChannel(preset.channel);
    if (preset.date) setMessageDate(preset.date);
    setResult(null);
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!message || !message.trim()) return;

    try {
      setIsTyping(true);
      setError(null);
      setResult(null);

      const res = await submitIntake({
        message,
        channel,
        date: messageDate || '2026-06-30',
      });

      // Typing animation delay for realistic agent feel
      setTimeout(() => {
        setResult(res);
        setIsTyping(false);
      }, 650);
    } catch (err: any) {
      setIsTyping(false);
      setError(err.message || 'Failed to process intake request');
    }
  };

  const handleCopy = () => {
    if (!result?.match.draft_reply) return;
    navigator.clipboard.writeText(result.match.draft_reply);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getMatchBadge = (matchObj?: any) => {
    const status = matchObj?.match_status || matchObj?.match_type;
    switch (status) {
      case 'UNIQUE_MATCH':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold bg-signal-green-dim text-signal-green border border-signal-green-border">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Unique Ledger Match
          </span>
        );
      case 'POSSIBLE_MATCH_LOW_CONFIDENCE':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold bg-amber-dim text-amber border border-amber-border">
            <HelpCircle className="w-3.5 h-3.5" />
            Possible Match (Low Confidence - Clarification Requested)
          </span>
        );
      case 'AMBIGUOUS':
      case 'MULTIPLE_MATCHES':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold bg-amber-dim text-amber border border-amber-border">
            <HelpCircle className="w-3.5 h-3.5" />
            Ambiguous Match ({matchObj?.candidates?.length || matchObj?.candidate_count || 0} candidates)
          </span>
        );
      case 'SUPPORT_CLOSED_NO_FINANCE':
      case 'INTERNAL_GAP_REPORT':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold bg-signal-red-dim text-signal-red border border-signal-red-border">
            <AlertCircle className="w-3.5 h-3.5" />
            Routed to Gap B Report (69 Tickets)
          </span>
        );
      case 'NO_MATCH':
      case 'NO_MATCH_NEW_CREATED':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-semibold bg-signal-blue-dim text-signal-blue border border-signal-blue-border">
            <Layers className="w-3.5 h-3.5" />
            New Entry Created ({matchObj?.new_ticket_id || matchObj?.new_ticket?.clean_id || 'RF-NEW-001'})
          </span>
        );
    }
  };

  return (
    <section
      id="intake"
      className="py-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto"
    >
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center space-x-2 text-xs font-mono text-amber uppercase tracking-wider mb-2">
          <Bot className="w-3.5 h-3.5" />
          <span>Automated Inbound Triage & Reconciled Matching</span>
        </div>
        <h2 className="text-3xl sm:text-4xl font-heading font-bold text-fg-primary tracking-tight">
          Intake Assistant
        </h2>
        <p className="mt-2 text-base text-fg-muted max-w-2xl">
          Paste an informal agent email, WhatsApp snippet, or internal note. The assistant extracts entities, matches against the reconciled ledger, and drafts grounded replies without hallucinated ETAs.
        </p>
      </div>

      {/* Runtime Banner */}
      {result?.llm_status && !result.llm_status.has_key && (
        <div className="p-3.5 rounded-lg border border-amber-border bg-amber-dim text-xs font-mono text-amber mb-6 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{result.llm_status.status_banner}</span>
          </div>
          <span className="hidden sm:inline-block text-[11px] opacity-80 uppercase">
            Deterministic Engine
          </span>
        </div>
      )}

      {/* Split Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column (5 cols): Chat-Style Input & Preset Chips */}
        <div className="lg:col-span-5 p-6 rounded-lg border border-ink-border bg-ink-panel space-y-5">
          <div>
            <label className="block text-xs font-mono text-fg-muted uppercase tracking-wider mb-2">
              Select Demo Scenario
            </label>
            <div className="flex flex-col gap-2">
              {presets?.preset_a && (
                <button
                  type="button"
                  onClick={() => handleApplyPreset(presets.preset_a)}
                  className="w-full text-left p-2.5 rounded border border-ink-border bg-ink-card hover:bg-ink-hover hover:border-amber-border transition-colors text-xs"
                >
                  <div className="font-semibold text-fg-primary flex items-center justify-between">
                    <span>{presets.preset_a.name}</span>
                    <span className="font-mono text-[10px] text-amber">{presets.preset_a.channel}</span>
                  </div>
                  <div className="text-[11px] text-fg-muted mt-0.5 truncate">
                    {presets.preset_a.text}
                  </div>
                </button>
              )}

              {presets?.preset_b && (
                <button
                  type="button"
                  onClick={() => handleApplyPreset(presets.preset_b)}
                  className="w-full text-left p-2.5 rounded border border-ink-border bg-ink-card hover:bg-ink-hover hover:border-amber-border transition-colors text-xs"
                >
                  <div className="font-semibold text-fg-primary flex items-center justify-between">
                    <span>{presets.preset_b.name}</span>
                    <span className="font-mono text-[10px] text-amber">{presets.preset_b.channel}</span>
                  </div>
                  <div className="text-[11px] text-fg-muted mt-0.5 truncate">
                    {presets.preset_b.text}
                  </div>
                </button>
              )}

              {presets?.preset_c && (
                <button
                  type="button"
                  onClick={() => handleApplyPreset(presets.preset_c)}
                  className="w-full text-left p-2.5 rounded border border-ink-border bg-ink-card hover:bg-ink-hover hover:border-amber-border transition-colors text-xs"
                >
                  <div className="font-semibold text-fg-primary flex items-center justify-between">
                    <span>{presets.preset_c.name}</span>
                    <span className="font-mono text-[10px] text-signal-red">Audit Link</span>
                  </div>
                  <div className="text-[11px] text-fg-muted mt-0.5 truncate">
                    {presets.preset_c.text}
                  </div>
                </button>
              )}
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4 pt-2 border-t border-ink-border/50">
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-xs font-mono text-fg-muted uppercase tracking-wider">
                  Informal Message Payload
                </label>
                <select
                  value={channel}
                  onChange={(e) => setChannel(e.target.value)}
                  aria-label="Message Channel"
                  className="px-2 py-1 text-xs font-mono rounded border border-ink-border bg-ink-card text-fg-primary focus:outline-none focus:border-amber"
                >
                  <option value="Email">Email</option>
                  <option value="WhatsApp">WhatsApp</option>
                  <option value="Portal">Portal</option>
                </select>
              </div>
              <textarea
                rows={6}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Paste inbound agent communication or internal refund note..."
                className="w-full p-3 text-xs font-mono rounded border border-ink-border bg-ink-card text-fg-primary placeholder-fg-faint focus:outline-none focus:border-amber leading-relaxed resize-none"
              />
            </div>

            <button
              type="submit"
              disabled={isTyping || !message.trim()}
              className="w-full py-2.5 px-4 rounded-lg text-sm font-semibold bg-amber hover:bg-amber/90 text-ink disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 shadow-sm"
            >
              {isTyping ? (
                <>
                  <div className="w-4 h-4 border-2 border-ink border-t-transparent rounded-full animate-spin" />
                  <span>Reconciling against ledger...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 text-ink" />
                  <span>Process Inbound Intake</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column (7 cols): Result Cards with Typing Indicator */}
        <div className="lg:col-span-7 space-y-4">

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-lg border border-signal-red-border bg-signal-red-dim text-signal-red text-xs font-mono flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>Error: {error}</span>
              </div>
              <button
                onClick={() => setError(null)}
                className="text-sm font-bold text-signal-red hover:underline ml-2"
              >
                &times;
              </button>
            </div>
          )}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="p-8 rounded-lg border border-ink-border bg-ink-panel flex flex-col items-center justify-center text-center space-y-3">
              <div className="flex items-center space-x-1.5">
                <div className="w-2.5 h-2.5 bg-amber rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2.5 h-2.5 bg-amber rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2.5 h-2.5 bg-amber rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
              <p className="text-xs font-mono text-fg-muted">
                Extracting entities and auditing cross-tracker ledger...
              </p>
            </div>
          )}

          {/* Empty State before any submission */}
          {!isTyping && !result && (
            <div className="p-12 rounded-lg border border-dashed border-ink-border bg-ink-panel/40 flex flex-col items-center justify-center text-center space-y-3">
              <Sparkles className="w-8 h-8 text-fg-faint" />
              <h3 className="font-heading font-semibold text-base text-fg-primary">
                Awaiting Intake Message
              </h3>
              <p className="text-xs text-fg-muted max-w-sm">
                Choose one of the demo chips on the left or type an inquiry to test entity normalization and deterministic ledger matching.
              </p>
            </div>
          )}

          {/* Result Cards */}
          {!isTyping && result && (
            <>
              {/* Card 1: Parsed Entities */}
              <div className="p-5 rounded-lg border border-ink-border bg-ink-panel">
                <div className="flex items-center justify-between pb-3 border-b border-ink-border/50 mb-3">
                  <span className="text-xs font-mono text-fg-muted uppercase tracking-wider flex items-center gap-1.5">
                    <FileText className="w-3.5 h-3.5 text-amber" />
                    Parsed Structured Entities
                  </span>
                  <div className="flex items-center gap-2">
                    <span
                      title={(result.parsed as any).fallback_reason ? `Fallback reason: ${(result.parsed as any).fallback_reason}` : undefined}
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-medium ${
                      (result.parsed as any).parser_engine === 'gemini' || (result.parsed as any).engine === 'gemini'
                        ? 'bg-signal-green-dim text-signal-green border border-signal-green-border'
                        : 'bg-amber-dim text-amber border border-amber-border'
                    }`}>
                      {(result.parsed as any).fallback_reason
                        ? `Rules fallback: ${(result.parsed as any).fallback_reason}`
                        : ((result.parsed as any).engine_chip ||
                            ((result.parsed as any).parser_engine === 'gemini' ? 'Parsed by Gemini' : 'Rules fallback'))}
                    </span>
                    <span className="text-xs font-mono text-fg-faint">
                      Channel: {result.parsed.channel}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 text-xs font-mono">
                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Agent</span>
                    <span className="font-semibold text-fg-primary truncate block mt-0.5">
                      {result.parsed.canonical_agent || (result.parsed as any).agent_name || 'Unrecognized'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Route</span>
                    <span className="font-semibold text-fg-primary truncate block mt-0.5">
                      {result.parsed.route || '-'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Ticket Ref</span>
                    <span className="font-semibold text-amber truncate block mt-0.5">
                      {result.parsed.ticket_number || (result.parsed as any).ticket_ref || '-'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Issue Type</span>
                    <span className="font-semibold text-fg-primary truncate block mt-0.5 capitalize">
                      {((result.parsed as any).issue_type || 'new_request').replace('_', ' ')}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Language</span>
                    <span className="font-semibold text-fg-primary truncate block mt-0.5">
                      {(result.parsed as any).language_detected || 'English'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Urgency</span>
                    <span className={`font-semibold truncate block mt-0.5 ${
                      (result.parsed as any).urgency === 'High' ? 'text-signal-red' : 'text-fg-primary'
                    }`}>
                      {(result.parsed as any).urgency || 'Medium'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Confidence</span>
                    <span className="font-semibold text-fg-primary truncate block mt-0.5">
                      {(result.parsed as any).confidence ? Math.round((result.parsed as any).confidence * 100) + '%' : '85%'}
                    </span>
                  </div>

                  <div className="p-2.5 rounded bg-ink-card border border-ink-border/60">
                    <span className="text-fg-faint block text-[10px] uppercase">Request Date</span>
                    <span className="font-semibold text-fg-primary truncate block mt-0.5">
                      {result.parsed.request_date || '2026-06-30'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Card 2: Reconciled Match Status */}
              <div className="p-5 rounded-lg border border-ink-border bg-ink-panel">
                <div className="flex items-center justify-between pb-3 border-b border-ink-border/50 mb-3">
                  <span className="text-xs font-mono text-fg-muted uppercase tracking-wider flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-amber" />
                    Ledger Cross-Reference
                  </span>
                  {getMatchBadge(result.match)}
                </div>

                {/* If Unique Match */}
                {((result.match.match_status === 'UNIQUE_MATCH') || (result.match.match_type === 'UNIQUE_MATCH')) && result.match.matched_ticket && (
                  <div className="p-3.5 rounded bg-ink-card border border-signal-green-border/40 text-xs font-mono space-y-2">
                    <div className="flex justify-between items-center pb-2 border-b border-ink-border/50">
                      <span className="text-fg-muted">Ticket ID:</span>
                      <span className="font-bold text-amber">{result.match.matched_ticket.clean_id}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-fg-muted">Agency / Sector:</span>
                      <span className="text-fg-primary">{result.match.matched_ticket.canonical_agent} ({result.match.matched_ticket.route})</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-fg-muted">Support Status:</span>
                      <span className="text-fg-primary">{result.match.matched_ticket.clean_status}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-fg-muted">Finance Payout Status:</span>
                      <span className="font-semibold text-signal-green">{result.match.matched_ticket.clean_payout_status}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-fg-muted">Reconciled Amount:</span>
                      <span className="font-bold text-fg-primary">
                        {result.match.matched_ticket['Amount Paid (INR)']
                          ? formatINR(result.match.matched_ticket['Amount Paid (INR)'])
                          : formatINR(result.match.matched_ticket['Refund Amount (INR)'])}
                      </span>
                    </div>
                    {result.match.matched_ticket.recommended_action && (
                      <div className="pt-2 border-t border-ink-border/50 text-[11px] text-fg-faint">
                        Recommended Action: {result.match.matched_ticket.recommended_action}
                      </div>
                    )}
                  </div>
                )}

                {/* If Ambiguous Match / Multiple Matches */}
                {((result.match.match_status === 'AMBIGUOUS') || (result.match.match_type === 'MULTIPLE_MATCHES')) && (
                  <div className="space-y-2">
                    <p className="text-xs text-amber font-mono">
                      Multiple candidate tickets detected for this agency and sector. Clarification requested from agent before asserting status:
                    </p>
                    <div className="space-y-1.5 max-h-48 overflow-y-auto">
                      {(result.match.candidates || []).map((cand: any, idx: number) => (
                        <div key={idx} className="p-2.5 rounded bg-ink-card border border-ink-border text-xs font-mono flex items-center justify-between">
                          <div>
                            <span className="font-semibold text-amber mr-2">{cand.clean_id}</span>
                            <span className="text-fg-muted">{cand.canonical_agent} ({cand.route})</span>
                          </div>
                          <div className="text-right">
                            <span className="font-semibold text-fg-primary mr-2">
                              {formatINR(cand['Refund Amount (INR)'] || 0)}
                            </span>
                            <span className="text-[10px] text-fg-faint px-1.5 py-0.5 rounded bg-ink-border">
                              {cand.clean_payout_status || cand.clean_status}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* If Preset C / Support Closed No Finance / Internal Gap Report */}
                {((result.match.match_status === 'SUPPORT_CLOSED_NO_FINANCE') || (result.match.match_type === 'INTERNAL_GAP_REPORT')) && (
                  <div className="p-4 rounded bg-signal-red-dim border border-signal-red-border text-xs font-mono text-signal-red space-y-2">
                    <div className="font-bold flex items-center gap-1.5 text-sm">
                      <AlertCircle className="w-4 h-4" />
                      Policy Route: No Individual Ticket Created
                    </div>
                    <p className="text-fg-muted text-xs leading-relaxed">
                      This communication describes a systemic operational discrepancy. Policy directs this immediately to the <strong>Gap Class B remediation queue</strong> (69 closed tickets unrecorded in Finance, totaling ₹10,80,700) rather than spawning redundant tickets.
                    </p>
                    <div className="pt-2 flex items-center justify-between">
                      <span className="text-[11px] text-fg-faint">Gap Class B Total: 69 tickets (₹10,80,700)</span>
                      <button
                        type="button"
                        onClick={() => {
                          const q = document.getElementById('queue');
                          if (q) q.scrollIntoView({ behavior: 'smooth' });
                        }}
                        className="px-2.5 py-1 rounded bg-amber-dim text-amber border border-amber-border hover:bg-amber hover:text-ink transition-colors font-medium text-xs"
                      >
                        View in Action Queue &darr;
                      </button>
                    </div>
                  </div>
                )}

                {/* If No Match (New Ticket Created) */}
                {((result.match.match_status === 'NO_MATCH') || (result.match.match_type === 'NO_MATCH_NEW_CREATED')) && (
                  <div className="p-3.5 rounded bg-signal-blue-dim border border-signal-blue-border text-xs font-mono text-signal-blue space-y-1.5">
                    <div className="font-bold flex items-center gap-1.5">
                      <Layers className="w-4 h-4" />
                      New Ticket Created: {result.match.new_ticket_id || (result.match as any).new_ticket?.clean_id || 'RF-NEW-001'}
                    </div>
                    <p className="text-fg-muted text-[11px] leading-relaxed">
                      No matching record found in either tracker. Ticket initialized with non-colliding <strong>RF-NEW-###</strong> prefix, assigned to Support triage queue with status <em>Working</em>.
                    </p>
                  </div>
                )}

                {/* If Possible Match (Low Confidence - Clarification Requested) */}
                {((result.match.match_status === 'POSSIBLE_MATCH_LOW_CONFIDENCE') || (result.match.match_type === 'POSSIBLE_MATCH_LOW_CONFIDENCE')) && (
                  <div className="space-y-3">
                    <div className="p-3.5 rounded bg-amber-dim/30 border border-amber/40 text-xs font-mono space-y-2">
                      <div className="font-bold text-amber flex items-center gap-1.5">
                        <HelpCircle className="w-4 h-4" />
                        Plausibility Guard: Clarification Requested
                      </div>
                      <p className="text-fg-muted text-[11px] leading-relaxed">
                        An earlier transaction was located on this sector, but due to elapsed time (&gt;45 days) or contradictory status, no status is asserted without agency confirmation.
                      </p>
                      {((result.match as any).candidate_note || (result.match.candidates?.[0] as any)?.plain_note) && (
                        <div className="p-2 rounded bg-ink-card border border-ink-border text-amber text-[11px]">
                          <strong>Observation:</strong> {(result.match as any).candidate_note || (result.match.candidates?.[0] as any)?.plain_note}
                        </div>
                      )}
                    </div>

                    <div className="p-3.5 rounded bg-signal-blue-dim border border-signal-blue-border text-xs font-mono text-signal-blue space-y-1">
                      <div className="font-bold flex items-center gap-1.5">
                        <Layers className="w-4 h-4" />
                        New Intake Ticket Created: {result.match.new_ticket_id || (result.match as any).new_ticket?.clean_id || 'RF-NEW-001'}
                      </div>
                      <p className="text-fg-muted text-[11px] leading-relaxed">
                        Ticket initialized with non-colliding <strong>RF-NEW-###</strong> prefix and marked <em>logged via intake</em>. Support will verify the exact PNR / booking reference with the agency.
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Card 3: Grounded Drafted Reply */}
              <div className="p-5 rounded-lg border border-ink-border bg-ink-panel">
                <div className="flex items-center justify-between pb-3 border-b border-ink-border/50 mb-3">
                  <span className="text-xs font-mono text-fg-muted uppercase tracking-wider flex items-center gap-1.5">
                    <Bot className="w-3.5 h-3.5 text-amber" />
                    Grounded Drafted Reply
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono text-fg-faint">
                      {(result.match as any).reply_engine === 'gemini' ? 'Engine: Gemini' : 'Engine: Template Guardrail'}
                    </span>
                    <button
                      onClick={handleCopy}
                      className="inline-flex items-center gap-1.5 text-xs font-mono px-2.5 py-1 rounded border border-ink-border bg-ink-card hover:bg-ink-hover text-fg-primary transition-colors"
                    >
                      {copied ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-signal-green" />
                          <span className="text-signal-green">Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-amber" />
                          <span>Copy Reply</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>

                <div className="p-3.5 rounded bg-ink-card border border-ink-border/60 text-xs font-mono text-fg-primary whitespace-pre-wrap leading-relaxed select-all">
                  {result.match.draft_reply}
                </div>

                <div className="mt-3 text-[10px] font-mono text-fg-faint flex items-center gap-1">
                  <span>Audit Assurance: Draft generated strictly from ledger records without hallucinated status or ETA.</span>
                </div>
              </div>
            </>
          )}

        </div>

      </div>
    </section>
  );
};
