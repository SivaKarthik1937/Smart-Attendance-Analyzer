/**
 * components/Badge.tsx
 * ======================
 * Small pill labels. `RiskBadge` maps a RiskLevel/Trend/Segment string to
 * the semantic success/warning/danger tokens so risk is always
 * color-coded consistently across the app.
 */

import clsx from "clsx";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";
import type { ReactNode } from "react";
import type { RiskLevel, Segment, Trend } from "@/types";

interface BadgeProps {
  children: ReactNode;
  className?: string;
}

export function Badge({ children, className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        className
      )}
    >
      {children}
    </span>
  );
}

const riskStyles: Record<RiskLevel, string> = {
  "Low Risk": "bg-success-light text-success-dark dark:bg-success-dark/20 dark:text-success",
  "Medium Risk": "bg-warning-light text-warning-dark dark:bg-warning-dark/20 dark:text-warning",
  "High Risk": "bg-danger-light text-danger-dark dark:bg-danger-dark/20 dark:text-danger",
};

export function RiskBadge({ level }: { level: RiskLevel | null | undefined }) {
  if (!level) return <Badge className="bg-ink-100 text-slate dark:bg-ink-700">Unknown</Badge>;
  return <Badge className={riskStyles[level]}>{level}</Badge>;
}

const segmentStyles: Record<Segment, string> = {
  Excellent: "bg-success-light text-success-dark dark:bg-success-dark/20 dark:text-success",
  Average: "bg-warning-light text-warning-dark dark:bg-warning-dark/20 dark:text-warning",
  Critical: "bg-danger-light text-danger-dark dark:bg-danger-dark/20 dark:text-danger",
};

export function SegmentBadge({ segment }: { segment: Segment | null | undefined }) {
  if (!segment) return <Badge className="bg-ink-100 text-slate dark:bg-ink-700">Unknown</Badge>;
  return <Badge className={segmentStyles[segment]}>{segment}</Badge>;
}

export function TrendBadge({ trend }: { trend: Trend | null | undefined }) {
  if (!trend) return null;
  if (trend === "improving") {
    return (
      <Badge className="bg-success-light text-success-dark dark:bg-success-dark/20 dark:text-success">
        <ArrowUpRight size={12} /> Improving
      </Badge>
    );
  }
  if (trend === "declining") {
    return (
      <Badge className="bg-danger-light text-danger-dark dark:bg-danger-dark/20 dark:text-danger">
        <ArrowDownRight size={12} /> Declining
      </Badge>
    );
  }
  return (
    <Badge className="bg-ink-100 text-slate dark:bg-ink-700">
      <Minus size={12} /> Stable
    </Badge>
  );
}
