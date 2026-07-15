/**
 * charts/Heatmap.tsx
 * ====================
 * Recharts has no built-in heatmap primitive, so this is a small custom
 * CSS-grid heatmap. Supports two color scales:
 *   - "sequential": low (pale) -> high (deep gold/ink), for attendance %
 *   - "diverging": negative (danger red) <-> 0 (neutral) <-> positive
 *     (success green), for correlation matrices (-1 to 1)
 * Used on the Analytics page for the correlation matrix and the
 * Department x Semester attendance breakdown.
 */

interface HeatmapProps {
  rows: string[];
  cols: string[];
  values: (number | null)[][]; // values[rowIndex][colIndex]
  colorScale?: "sequential" | "diverging";
  valueFormatter?: (value: number) => string;
  min?: number;
  max?: number;
}

function sequentialColor(t: number): string {
  // t in [0,1] -> pale paper to deep ink/gold
  const r = Math.round(247 - t * (247 - 20));
  const g = Math.round(246 - t * (246 - 33));
  const b = Math.round(242 - t * (242 - 61));
  return `rgb(${r}, ${g}, ${b})`;
}

function divergingColor(t: number): string {
  // t in [-1, 1] -> danger red <-> white <-> success green
  if (t >= 0) {
    const amount = Math.round(t * 255);
    return `rgb(${255 - amount * 0.31}, ${255 - amount * 0.03}, ${255 - amount * 0.63})`;
  }
  const amount = Math.round(-t * 255);
  return `rgb(${255 - amount * 0.09}, ${255 - amount * 0.65}, ${255 - amount * 0.66})`;
}

export function Heatmap({
  rows,
  cols,
  values,
  colorScale = "sequential",
  valueFormatter = (v) => v.toFixed(1),
  min,
  max,
}: HeatmapProps) {
  const flat = values.flat().filter((v): v is number => v !== null);
  const dataMin = min ?? Math.min(...flat);
  const dataMax = max ?? Math.max(...flat);

  function getColor(value: number | null): string {
    if (value === null) return "transparent";
    if (colorScale === "diverging") {
      return divergingColor(Math.max(-1, Math.min(1, value)));
    }
    const t = dataMax === dataMin ? 0.5 : (value - dataMin) / (dataMax - dataMin);
    return sequentialColor(t);
  }

  function getTextColor(value: number | null): string {
    if (value === null) return "transparent";
    const t = colorScale === "diverging" ? Math.abs(value) : (value - dataMin) / (dataMax - dataMin || 1);
    return t > 0.55 ? "#F7F6F2" : "#14213D";
  }

  return (
    <div className="overflow-x-auto">
      <table className="border-collapse text-xs">
        <thead>
          <tr>
            <th className="p-2" />
            {cols.map((col) => (
              <th key={col} className="whitespace-nowrap p-2 text-center font-medium text-slate">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={row}>
              <th className="whitespace-nowrap p-2 text-right font-medium text-slate">{row}</th>
              {cols.map((col, colIndex) => {
                const value = values[rowIndex]?.[colIndex] ?? null;
                return (
                  <td
                    key={col}
                    className="min-w-[56px] rounded p-2 text-center font-mono tabular-nums"
                    style={{ backgroundColor: getColor(value), color: getTextColor(value) }}
                  >
                    {value !== null ? valueFormatter(value) : "—"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
