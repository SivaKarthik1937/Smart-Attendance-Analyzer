/**
 * charts/RiskPieChart.tsx
 * =========================
 * Pie chart visualizing the Low/Medium/High risk distribution, using the
 * same semantic success/warning/danger colors as <RiskBadge>.
 */

import { Cell, Legend, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { RiskDistribution } from "@/types";

interface Props {
  distribution: RiskDistribution;
  height?: number;
}

const COLORS = { "Low Risk": "#2E7D5B", "Medium Risk": "#C9822E", "High Risk": "#B23A48" };

export function RiskPieChart({ distribution, height = 260 }: Props) {
  const data = [
    { name: "Low Risk", value: distribution.low_risk },
    { name: "Medium Risk", value: distribution.medium_risk },
    { name: "High Risk", value: distribution.high_risk },
  ].filter((d) => d.value > 0);

  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={55} outerRadius={90} paddingAngle={2}>
          {data.map((entry) => (
            <Cell key={entry.name} fill={COLORS[entry.name as keyof typeof COLORS]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{ borderRadius: 10, border: "1px solid #E5E7EB", fontSize: 13, fontFamily: "Inter, sans-serif" }}
        />
        <Legend verticalAlign="bottom" height={30} wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
