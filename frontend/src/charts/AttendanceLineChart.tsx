/**
 * charts/AttendanceLineChart.tsx
 * =================================
 * Monthly attendance trend line chart with a 75% requirement reference
 * line. Used on the Student Dashboard and the Analytics page.
 */

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { MonthlyTrendPoint } from "@/types";

interface Props {
  data: MonthlyTrendPoint[];
  height?: number;
}

export function AttendanceLineChart({ data, height = 260 }: Props) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: -16 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="text-ink-100 dark:text-ink-700" />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate" />
        <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} stroke="currentColor" className="text-slate" />
        <Tooltip
          contentStyle={{
            borderRadius: 10,
            border: "1px solid #E5E7EB",
            fontSize: 13,
            fontFamily: "Inter, sans-serif",
          }}
          formatter={(value: number) => [`${value}%`, "Attendance"]}
        />
        <ReferenceLine y={75} stroke="#B23A48" strokeDasharray="4 4" label={{ value: "75% req.", fontSize: 11, fill: "#B23A48" }} />
        <Line
          type="monotone"
          dataKey="attendance_percentage"
          name="Attendance %"
          stroke="#C9A227"
          strokeWidth={2.5}
          dot={{ r: 3, fill: "#14213D" }}
          activeDot={{ r: 5 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
