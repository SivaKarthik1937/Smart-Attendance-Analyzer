/**
 * charts/SubjectRadarChart.tsx
 * ===============================
 * Radar chart plotting a student's attendance % across every enrolled
 * subject against the 75% requirement, making it easy to spot which
 * specific subjects are dragging the overall average down.
 */

import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import type { SubjectAttendance } from "@/types";

interface Props {
  subjects: SubjectAttendance[];
  height?: number;
}

export function SubjectRadarChart({ subjects, height = 300 }: Props) {
  const data = subjects.map((s) => ({
    subject: s.subject_name.length > 14 ? `${s.subject_name.slice(0, 14)}…` : s.subject_name,
    attendance: s.attendance_percentage,
    requirement: 75,
  }));

  return (
    <ResponsiveContainer width="100%" height={height}>
      <RadarChart data={data} outerRadius="75%">
        <PolarGrid stroke="currentColor" className="text-ink-100 dark:text-ink-700" />
        <PolarAngleAxis dataKey="subject" tick={{ fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} axisLine={false} />
        <Tooltip
          contentStyle={{ borderRadius: 10, border: "1px solid #E5E7EB", fontSize: 13, fontFamily: "Inter, sans-serif" }}
        />
        <Radar name="Requirement" dataKey="requirement" stroke="#B23A48" strokeDasharray="4 4" fill="#B23A48" fillOpacity={0.03} />
        <Radar name="Attendance %" dataKey="attendance" stroke="#C9A227" fill="#C9A227" fillOpacity={0.35} />
      </RadarChart>
    </ResponsiveContainer>
  );
}
