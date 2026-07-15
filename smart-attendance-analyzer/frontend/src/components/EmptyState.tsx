/**
 * components/EmptyState.tsx
 * ============================
 * Consistent empty-state and error-state UI, used whenever an API call
 * fails or returns no data, so the app never shows a blank white area.
 */

import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";

interface EmptyStateProps {
  title?: string;
  message?: string;
}

export function EmptyState({ title = "Nothing here yet", message = "There's no data to display." }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 rounded-card border border-dashed border-ink-200 py-12 text-center dark:border-ink-700">
      <Inbox size={28} className="text-ink-300 dark:text-ink-500" />
      <p className="font-medium text-ink-700 dark:text-ink-200">{title}</p>
      <p className="max-w-sm text-sm text-slate">{message}</p>
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-card border border-danger-light bg-danger-light/40 py-12 text-center dark:border-danger-dark/30 dark:bg-danger-dark/10">
      <AlertTriangle size={28} className="text-danger" />
      <p className="font-medium text-ink-900 dark:text-white">Something went wrong</p>
      <p className="max-w-sm text-sm text-slate">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-1 inline-flex items-center gap-1.5 rounded-full bg-ink-900 px-4 py-1.5 text-sm font-medium text-white transition-colors hover:bg-ink-700 dark:bg-white dark:text-ink-900 dark:hover:bg-ink-100"
        >
          <RefreshCw size={14} /> Try again
        </button>
      )}
    </div>
  );
}
