/**
 * pages/Settings.tsx
 * ====================
 * Appearance (dark mode) control, read-only account info, and an
 * "About the Models" panel that surfaces the real training metrics for
 * transparency (which algorithm won, and its headline score).
 */

import { useEffect, useState } from "react";
import { Moon, Sun, Info } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/hooks/useTheme";
import { getErrorMessage, predictionApi } from "@/services/api";
import type { ModelInfo } from "@/types";
import { SectionCard } from "@/components/Card";
import { Spinner } from "@/components/Loader";

interface RiskModelMetrics {
  best_model?: string;
  models?: { model_name: string; accuracy?: number; f1_score?: number }[];
}

interface ForecastModelMetrics {
  best_model?: string;
  models?: { model_name: string; r2_score?: number; mae?: number }[];
}

interface SegmentationModelMetrics {
  silhouette_score?: number;
  segment_counts?: Record<string, number>;
}

export default function Settings() {
  const { user } = useAuth();
  const { theme, setTheme } = useTheme();

  const [modelInfo, setModelInfo] = useState<ModelInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    predictionApi
      .getModelInfo()
      .then(setModelInfo)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, []);

  const riskMetrics = modelInfo?.risk_model as RiskModelMetrics | null;
  const forecastMetrics = modelInfo?.forecast_model as ForecastModelMetrics | null;
  const segmentationMetrics = modelInfo?.segmentation_model as SegmentationModelMetrics | null;

  const bestRisk = riskMetrics?.models?.find((m) => m.model_name === riskMetrics.best_model);
  const bestForecast = forecastMetrics?.models?.find((m) => m.model_name === forecastMetrics.best_model);

  return (
    <div className="mx-auto max-w-2xl animate-fade-in space-y-6 pb-10">
      <div>
        <p className="text-sm font-medium uppercase tracking-wide text-gold-dark dark:text-gold">Preferences</p>
        <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">Settings</h1>
      </div>

      <SectionCard title="Appearance" description="Choose how the app looks on your device.">
        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={() => setTheme("light")}
            className={
              theme === "light"
                ? "flex items-center justify-center gap-2 rounded-lg border-2 border-gold bg-gold/10 py-3 text-sm font-semibold text-ink-900"
                : "flex items-center justify-center gap-2 rounded-lg border border-ink-100 py-3 text-sm font-medium text-slate hover:bg-ink-50 dark:border-ink-700 dark:hover:bg-ink-800"
            }
          >
            <Sun size={16} /> Light Mode
          </button>
          <button
            onClick={() => setTheme("dark")}
            className={
              theme === "dark"
                ? "flex items-center justify-center gap-2 rounded-lg border-2 border-gold bg-gold/10 py-3 text-sm font-semibold text-white"
                : "flex items-center justify-center gap-2 rounded-lg border border-ink-100 py-3 text-sm font-medium text-slate hover:bg-ink-50 dark:border-ink-700 dark:hover:bg-ink-800"
            }
          >
            <Moon size={16} /> Dark Mode
          </button>
        </div>
      </SectionCard>

      <SectionCard title="Account" description="Your login details.">
        <div className="space-y-3 text-sm">
          <div className="flex justify-between border-b border-ink-50 pb-2 dark:border-ink-800">
            <span className="text-slate">Username</span>
            <span className="font-medium text-ink-900 dark:text-white">{user?.username}</span>
          </div>
          <div className="flex justify-between border-b border-ink-50 pb-2 dark:border-ink-800">
            <span className="text-slate">Email</span>
            <span className="font-medium text-ink-900 dark:text-white">{user?.email ?? "Not provided"}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate">Role</span>
            <span className="font-medium capitalize text-ink-900 dark:text-white">{user?.role}</span>
          </div>
        </div>
      </SectionCard>

      <SectionCard
        title="About the Models"
        description="Transparency into the ML models powering your predictions."
      >
        {isLoading ? (
          <div className="flex justify-center py-6">
            <Spinner size={22} />
          </div>
        ) : error ? (
          <p className="text-sm text-danger">{error}</p>
        ) : (
          <div className="space-y-4 text-sm">
            <div className="flex items-start gap-2 rounded-lg bg-ink-50 p-3 dark:bg-ink-800">
              <Info size={15} className="mt-0.5 shrink-0 text-gold" />
              <p className="text-ink-700 dark:text-ink-200">
                Three models work together: a risk classifier, an attendance forecaster, and a K-Means
                segmentation model. The best-performing algorithm is automatically selected during training.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-ink-100 p-3 dark:border-ink-700">
                <p className="text-xs uppercase tracking-wide text-slate">Risk Model</p>
                <p className="mt-1 font-display text-base font-semibold text-ink-900 dark:text-white">
                  {riskMetrics?.best_model ?? "-"}
                </p>
                <p className="mt-1 font-mono text-xs text-slate">
                  Accuracy: {bestRisk?.accuracy ? `${(bestRisk.accuracy * 100).toFixed(1)}%` : "-"}
                </p>
              </div>
              <div className="rounded-lg border border-ink-100 p-3 dark:border-ink-700">
                <p className="text-xs uppercase tracking-wide text-slate">Forecast Model</p>
                <p className="mt-1 font-display text-base font-semibold text-ink-900 dark:text-white">
                  {forecastMetrics?.best_model ?? "-"}
                </p>
                <p className="mt-1 font-mono text-xs text-slate">R²: {bestForecast?.r2_score?.toFixed(3) ?? "-"}</p>
              </div>
              <div className="rounded-lg border border-ink-100 p-3 dark:border-ink-700">
                <p className="text-xs uppercase tracking-wide text-slate">Segmentation</p>
                <p className="mt-1 font-display text-base font-semibold text-ink-900 dark:text-white">K-Means</p>
                <p className="mt-1 font-mono text-xs text-slate">
                  Silhouette: {segmentationMetrics?.silhouette_score?.toFixed(3) ?? "-"}
                </p>
              </div>
            </div>
          </div>
        )}
      </SectionCard>
    </div>
  );
}
