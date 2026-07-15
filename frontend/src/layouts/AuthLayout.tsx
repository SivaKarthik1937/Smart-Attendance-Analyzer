/**
 * layouts/AuthLayout.tsx
 * ========================
 * Centered, branded shell used by the Login and Register pages: a two-tone
 * split (ink brand panel + paper form panel on desktop, stacked on mobile).
 */

import type { ReactNode } from "react";
import { GraduationCap } from "lucide-react";

interface Props {
  title: string;
  subtitle: string;
  children: ReactNode;
}

export function AuthLayout({ title, subtitle, children }: Props) {
  return (
    <div className="flex min-h-screen bg-paper dark:bg-paper-dark">
      {/* Brand panel */}
      <div className="relative hidden w-1/2 flex-col justify-between bg-ink-900 p-10 text-white lg:flex">
        <div className="flex items-center gap-2">
          <GraduationCap size={22} className="text-gold" />
          <span className="font-display text-lg font-semibold">Smart Attendance Pattern Analyzer</span>
        </div>

        <div>
          <p className="font-display text-4xl font-medium leading-tight">
            Every class, <span className="text-gold">recorded.</span>
            <br />
            Every risk, <span className="text-gold">forecast.</span>
          </p>
          <p className="mt-4 max-w-md text-sm text-ink-200">
            AI-driven attendance analytics that help students stay on track and
            help faculty spot risk before it becomes a detention letter.
          </p>
        </div>

        <p className="text-xs text-ink-300">
          Risk classification &middot; Attendance forecasting &middot; Student segmentation
        </p>
      </div>

      {/* Form panel */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-md animate-fade-in">
          <div className="mb-8 flex items-center gap-2 lg:hidden">
            <GraduationCap size={22} className="text-gold" />
            <span className="font-display text-lg font-semibold text-ink-900">
              Smart Attendance Pattern Analyzer
            </span>
          </div>

          <h1 className="font-display text-2xl font-semibold text-ink-900 dark:text-white">{title}</h1>
          <p className="mt-1 text-sm text-slate">{subtitle}</p>

          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
