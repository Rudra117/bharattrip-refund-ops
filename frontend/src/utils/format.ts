export function formatINR(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return 'INR 0';
  return 'INR ' + new Intl.NumberFormat('en-IN').format(Math.round(val));
}

export function formatLakh(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '0.0';
  return (val / 100000).toFixed(1);
}

export function formatPct(val: number | null | undefined): string {
  if (val === null || val === undefined || isNaN(val)) return '0.0%';
  return val.toFixed(1) + '%';
}
