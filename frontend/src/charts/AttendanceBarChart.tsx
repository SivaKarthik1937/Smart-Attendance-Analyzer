/**
 * charts/AttendanceBarChart.tsx
 * ================================
 * Generic horizontal bar chart used for department-wise and subject-wise
 * attendance comparisons. Bars below the 75% requirement are tinted
 * danger-red; bars at/above are tinted the ink/gold brand color.
 */

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface BarDatum {
  label: string;
  value: number;
}

interface Props {
  data: BarDatum[];
  height?: number;
  valueSuffix?: string;
}

export function AttendanceBarChart({ data, height = 320, valueSuffix = "%" }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, bottom: 0, left: 8 }}>
        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="currentColor" className="text-ink-100 dark:text-ink-700" />
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate" />
        <YAxis type="category" dataKey="label" width={140} tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate" />
        <Tooltip
          contentStyle={{ borderRadius: 10, border: "1px solid #E5E7EB", fontSize: 13, fontFamily: "Inter, sans-serif" }}
          formatter={(value: number) => [`${value}${valueSuffix}`, "Average"]}
        />
        <ReferenceLine x={75} stroke="#B23A48" strokeDasharray="4 4" />
        <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={16}>
          {data.map((entry, index) => (
            <Cell key={index} fill={entry.value < 75 ? "#B23A48" : "#14213D"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
