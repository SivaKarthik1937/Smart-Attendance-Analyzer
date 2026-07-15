/**
 * components/Loader.tsx
 * =======================
 * Loading indicators used while API requests are in flight.
 */

import clsx from "clsx";

export function Spinner({ size = 20, className }: { size?: number; className?: string }) {
  return (
    <svg
      className={clsx("animate-spin text-gold", className)}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-label="Loading"
      role="status"
    >
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
      <path
        className="opacity-90"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

export function PageLoader({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3">
      <Spinner size={32} />
      <p className="text-sm text-slate">{label}</p>
    </div>
  );
}

export function SkeletonBlock({ className }: { className?: string }) {
  return (
    <div
      className={clsx(
        "animate-pulse rounded-card bg-ink-100 dark:bg-ink-700",
        className
      )}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="rounded-card border border-ink-100 bg-white p-5 shadow-card dark:border-ink-700 dark:bg-ink-800">
      <SkeletonBlock className="mb-3 h-3 w-24" />
      <SkeletonBlock className="mb-2 h-8 w-32" />
      <SkeletonBlock className="h-3 w-20" />
    </div>
  );
}
