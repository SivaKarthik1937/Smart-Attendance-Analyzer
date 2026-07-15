/**
 * components/RiskLedgerStrip.tsx
 * =================================
 * The app's signature visual element: a horizontal, proportionally-widthed
 * three-segment bar (Low / Medium / High risk) styled like a ledger
 * balance strip, with tabular mono numerals. Appears on both the Student
 * and Faculty dashboards to make risk distribution legible at a glance.
 */

interface RiskLedgerStripProps {
  low: number;
  medium: number;
  high: number;
}

export function RiskLedgerStrip({ low, medium, high }: RiskLedgerStripProps) {
  const total = Math.max(low + medium + high, 1);
  const lowPct = (low / total) * 100;
  const medPct = (medium / total) * 100;
  const highPct = (high / total) * 100;

  const segments = [
    { key: "low", label: "Low Risk", count: low, pct: lowPct, color: "bg-success" },
    { key: "medium", label: "Medium Risk", count: medium, pct: medPct, color: "bg-warning" },
    { key: "high", label: "High Risk", count: high, pct: highPct, color: "bg-danger" },
  ];

  return (
    <div>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-ink-100 dark:bg-ink-700">
        {segments.map(
          (segment) =>
            segment.pct > 0 && (
              <div
                key={segment.key}
                className={`${segment.color} h-full transition-all duration-500`}
                style={{ width: `${segment.pct}%` }}
                title={`${segment.label}: ${segment.count}`}
              />
            )
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-6 gap-y-2">
        {segments.map((segment) => (
          <div key={segment.key} className="flex items-center gap-2">
            <span className={`h-2.5 w-2.5 rounded-full ${segment.color}`} />
            <span className="text-xs text-slate">{segment.label}</span>
            <span className="font-mono text-sm font-semibold tabular-nums text-ink-900 dark:text-white">
              {segment.count}
            </span>
            <span className="font-mono text-xs text-slate">({segment.pct.toFixed(1)}%)</span>
          </div>
        ))}
      </div>
    </div>
  );
}
