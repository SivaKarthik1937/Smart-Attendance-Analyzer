/**
 * components/Card.tsx
 * =====================
 * Generic card primitives used throughout both dashboards. `Card` is the
 * base surface; `StatCard` renders a single metric (label + big mono
 * number + optional trend/sublabel); `SectionCard` wraps a titled block
 * of content (tables, charts, lists).
 */

import type { ReactNode } from "react";
import clsx from "clsx";
import { TrendingDown, TrendingUp, Minus } from "lucide-react";

// ---------------------------------------------------------------------------
// Base Card
// ---------------------------------------------------------------------------

interface CardProps {
  children: ReactNode;
  className?: string;
  hoverable?: boolean;
}

export function Card({ children, className, hoverable = false }: CardProps) {
  return (
    <div
      className={clsx(
        "rounded-card border border-ink-100 bg-white shadow-card dark:border-ink-700 dark:bg-ink-800",
        hoverable && "transition-shadow duration-200 hover:shadow-card-hover",
        className
      )}
    >
      {children}
    </div>
  );
}

// ---------------------------------------------------------------------------
// StatCard — a single headline metric
// ---------------------------------------------------------------------------

type TrendDirection = "up" | "down" | "flat";

interface StatCardProps {
  label: string;
  value: string | number;
  sublabel?: string;
  icon?: ReactNode;
  trend?: TrendDirection;
  trendLabel?: string;
  accent?: "ink" | "gold" | "success" | "warning" | "danger";
}

const accentTextClass: Record<NonNullable<StatCardProps["accent"]>, string> = {
  ink: "text-ink-900 dark:text-white",
  gold: "text-gold-dark dark:text-gold-light",
  success: "text-success dark:text-success",
  warning: "text-warning dark:text-warning",
  danger: "text-danger dark:text-danger",
};

const trendIcon: Record<TrendDirection, ReactNode> = {
  up: <TrendingUp size={14} />,
  down: <TrendingDown size={14} />,
  flat: <Minus size={14} />,
};

const trendClass: Record<TrendDirection, string> = {
  up: "text-success",
  down: "text-danger",
  flat: "text-slate",
};

export function StatCard({ label, value, sublabel, icon, trend, trendLabel, accent = "ink" }: StatCardProps) {
  return (
    <Card className="p-5" hoverable>
      <div className="flex items-start justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate">{label}</p>
        {icon && <span className="text-ink-300 dark:text-ink-400">{icon}</span>}
      </div>
      <p className={clsx("mt-2 font-mono text-3xl font-semibold tabular-nums", accentTextClass[accent])}>
        {value}
      </p>
      {(sublabel || trend) && (
        <div className="mt-1.5 flex items-center gap-1.5 text-xs">
          {trend && (
            <span className={clsx("inline-flex items-center gap-0.5", trendClass[trend])}>
              {trendIcon[trend]}
              {trendLabel}
            </span>
          )}
          {sublabel && <span className="text-slate">{sublabel}</span>}
        </div>
      )}
    </Card>
  );
}

// ---------------------------------------------------------------------------
// SectionCard — titled content block
// ---------------------------------------------------------------------------

interface SectionCardProps {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function SectionCard({ title, description, action, children, className }: SectionCardProps) {
  return (
    <Card className={clsx("p-5", className)}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <h3 className="font-display text-lg font-semibold text-ink-900 dark:text-white">{title}</h3>
          {description && <p className="mt-0.5 text-sm text-slate">{description}</p>}
        </div>
        {action}
      </div>
      {children}
    </Card>
  );
}
