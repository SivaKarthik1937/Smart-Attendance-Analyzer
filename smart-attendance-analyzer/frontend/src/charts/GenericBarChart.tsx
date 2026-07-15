/**
 * charts/GenericBarChart.tsx
 * =============================
 * Unlike <AttendanceBarChart> (which assumes a 0-100% domain and a 75%
 * reference line), this is a domain-agnostic horizontal bar chart used
 * for feature importance scores, histogram bin counts, and similar data
 * where the value range isn't a percentage.
 */

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export interface GenericBarDatum {
  label: string;
  value: number;
}

interface Props {
  data: GenericBarDatum[];
  height?: number;
  color?: string;
  valueFormatter?: (value: number) => string;
}

export function GenericBarChart({ data, height = 300, color = "#C9A227", valueFormatter = (v) => `${v}` }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" className="text-ink-100 dark:text-ink-700" />
        <XAxis type="number" tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate" />
        <YAxis type="category" dataKey="label" width={120} tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate" />
        <Tooltip
          contentStyle={{ borderRadius: 10, border: "1px solid #E5E7EB", fontSize: 13, fontFamily: "Inter, sans-serif" }}
          formatter={(value: number) => [valueFormatter(value), "Value"]}
        />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={16} fill={color} />
      </BarChart>
    </ResponsiveContainer>
  );
}
