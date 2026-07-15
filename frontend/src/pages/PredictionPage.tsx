/**
 * pages/PredictionPage.tsx
 * ===========================
 * Lets a student run a prediction for themselves, or lets faculty either
 * look up a specific student by code or run a manual "what-if" scenario
 * with hand-entered feature values.
 */

import { useEffect, useState, type FormEvent } from "react";
import { Clock, Search, Sparkles, SlidersHorizontal } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage, predictionApi, studentApi } from "@/services/api";
import type { PredictionOut } from "@/types";
import { SectionCard } from "@/components/Card";
import { RiskBadge, SegmentBadge } from "@/components/Badge";
import { Spinner } from "@/components/Loader";
import { EmptyState } from "@/components/EmptyState";
import { toast } from "@/lib/toast";

const inputClass =
  "w-full rounded-lg border border-ink-100 bg-white py-2.5 px-3 text-sm text-ink-900 outline-none transition-colors focus:border-gold focus:ring-1 focus:ring-gold dark:border-ink-700 dark:bg-ink-800 dark:text-white";
const labelClass = "mb-1 block text-xs font-medium uppercase tracking-wide text-slate";

function PredictionResultCard({ result }: { result: PredictionOut }) {
  return (
    <SectionCard
      title="Prediction Result"
      description={`${result.risk_model_used} (risk) + ${result.forecast_model_used} (forecast)`}
    >
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <RiskBadge level={result.predicted_risk_level} />
        <SegmentBadge segment={result.cluster_segment} />
        {result.risk_confidence !== null && (
          <span className="text-sm text-slate">
            Confidence:{" "}
            <span className="font-mono font-semibold text-ink-900 dark:text-white">
              {(result.risk_confidence * 100).toFixed(1)}%
            </span>
          </span>
        )}
        <span className="text-sm text-slate">
          Forecasted attendance:{" "}
          <span className="font-mono font-semibold text-ink-900 dark:text-white">
            {result.forecast_attendance_percentage}%
          </span>
        </span>
      </div>
      <ul className="space-y-2">
        {result.ai_recommendations.map((tip, i) => (
          <li
            key={i}
            className="flex items-start gap-2 rounded-lg bg-ink-50 px-3 py-2 text-sm text-ink-800 dark:bg-ink-800 dark:text-ink-100"
          >
            <Sparkles size={14} className="mt-0.5 shrink-0 text-gold" />
            {tip}
          </li>
        ))}
      </ul>
    </SectionCard>
  );
}

export default function PredictionPage() {
  const { user } = useAuth();
  const isStudent = user?.role === "student";

  const [mode, setMode] = useState<"lookup" | "manual">("lookup");
  const [studentCode, setStudentCode] = useState("");
  const [manual, setManual] = useState({
    current_attendance: "72",
    previous_attendance: "78",
    leaves_taken: "8",
    internal_marks: "60",
    distance_km: "10",
    monthly_attendance: "70",
  });

  const [result, setResult] = useState<PredictionOut | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [history, setHistory] = useState<PredictionOut[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [ownCode, setOwnCode] = useState<string | null>(null);

  // Students: fetch their own profile so we know the code for history lookups.
  useEffect(() => {
    if (!isStudent) return;
    studentApi
      .getProfile()
      .then((profile) => setOwnCode(profile.student_code))
      .catch(() => {
        /* silently ignore -- the student may not have a linked profile yet */
      });
  }, [isStudent]);

  async function loadHistory(code: string) {
    setHistoryLoading(true);
    try {
      const data = await predictionApi.getHistory(code);
      setHistory(data.history);
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }

  useEffect(() => {
    if (ownCode) loadHistory(ownCode);
  }, [ownCode]);

  async function handleStudentPredict() {
    setIsSubmitting(true);
    setError(null);
    try {
      const prediction = await predictionApi.predict({});
      setResult(prediction);
      toast.success("Prediction complete.");
      if (ownCode) loadHistory(ownCode);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleLookupSubmit(e: FormEvent) {
    e.preventDefault();
    if (!studentCode.trim()) {
      setError("Please enter a student code.");
      return;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const prediction = await predictionApi.predict({ student_code: studentCode.trim().toUpperCase() });
      setResult(prediction);
      toast.success(`Prediction complete for ${prediction.student_code}.`);
      loadHistory(studentCode.trim().toUpperCase());
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleManualSubmit(e: FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      const prediction = await predictionApi.predict({
        current_attendance: Number(manual.current_attendance),
        previous_attendance: Number(manual.previous_attendance),
        leaves_taken: Number(manual.leaves_taken),
        internal_marks: Number(manual.internal_marks),
        distance_km: Number(manual.distance_km),
        monthly_attendance: Number(manual.monthly_attendance),
      });
      setResult(prediction);
      setHistory([]);
      toast.success("What-if prediction complete.");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="animate-fade-in space-y-6 pb-10">
      <div>
        <p className="text-sm font-medium uppercase tracking-wide text-gold-dark dark:text-gold">AI Prediction</p>
        <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">
          Risk, Forecast &amp; Segmentation
        </h1>
        <p className="mt-1 text-sm text-slate">
          {isStudent
            ? "Run the models on your latest attendance data to see your risk level, forecast, and personalized advice."
            : "Look up a student by code, or test a hypothetical scenario with manual feature values."}
        </p>
      </div>

      {isStudent ? (
        <SectionCard title="Run Your Prediction">
          <button
            onClick={handleStudentPredict}
            disabled={isSubmitting}
            className="flex items-center gap-2 rounded-lg bg-ink-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-ink-700 disabled:opacity-60 dark:bg-gold dark:text-ink-900 dark:hover:bg-gold-light"
          >
            {isSubmitting ? <Spinner size={16} className="text-white dark:text-ink-900" /> : <Sparkles size={16} />}
            {isSubmitting ? "Running models..." : "Run Prediction"}
          </button>
          {error && <p className="mt-3 text-sm text-danger">{error}</p>}
        </SectionCard>
      ) : (
        <SectionCard title="Choose Prediction Mode">
          <div className="mb-4 grid grid-cols-2 gap-2 rounded-lg bg-ink-50 p-1 dark:bg-ink-800">
            <button
              onClick={() => setMode("lookup")}
              className={
                mode === "lookup"
                  ? "flex items-center justify-center gap-1.5 rounded-md bg-ink-900 py-2 text-sm font-semibold text-white dark:bg-gold dark:text-ink-900"
                  : "flex items-center justify-center gap-1.5 rounded-md py-2 text-sm font-medium text-slate hover:text-ink-900 dark:hover:text-white"
              }
            >
              <Search size={14} /> Lookup Student
            </button>
            <button
              onClick={() => setMode("manual")}
              className={
                mode === "manual"
                  ? "flex items-center justify-center gap-1.5 rounded-md bg-ink-900 py-2 text-sm font-semibold text-white dark:bg-gold dark:text-ink-900"
                  : "flex items-center justify-center gap-1.5 rounded-md py-2 text-sm font-medium text-slate hover:text-ink-900 dark:hover:text-white"
              }
            >
              <SlidersHorizontal size={14} /> Manual What-If
            </button>
          </div>

          {mode === "lookup" ? (
            <form onSubmit={handleLookupSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
              <div className="flex-1">
                <label className={labelClass}>Student Code</label>
                <input
                  value={studentCode}
                  onChange={(e) => setStudentCode(e.target.value)}
                  placeholder="e.g. STU00001"
                  className={inputClass}
                />
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center justify-center gap-2 rounded-lg bg-ink-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-ink-700 disabled:opacity-60 dark:bg-gold dark:text-ink-900 dark:hover:bg-gold-light"
              >
                {isSubmitting ? <Spinner size={16} className="text-white dark:text-ink-900" /> : <Sparkles size={16} />}
                Predict
              </button>
            </form>
          ) : (
            <form onSubmit={handleManualSubmit} className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {(
                [
                  ["current_attendance", "Current Attendance %"],
                  ["previous_attendance", "Previous Semester %"],
                  ["leaves_taken", "Leaves Taken"],
                  ["internal_marks", "Internal Marks"],
                  ["distance_km", "Distance (km)"],
                  ["monthly_attendance", "Last Month %"],
                ] as const
              ).map(([key, label]) => (
                <div key={key}>
                  <label className={labelClass}>{label}</label>
                  <input
                    type="number"
                    value={manual[key]}
                    onChange={(e) => setManual((prev) => ({ ...prev, [key]: e.target.value }))}
                    className={inputClass}
                  />
                </div>
              ))}
              <div className="col-span-2 sm:col-span-3">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex items-center justify-center gap-2 rounded-lg bg-ink-900 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-ink-700 disabled:opacity-60 dark:bg-gold dark:text-ink-900 dark:hover:bg-gold-light"
                >
                  {isSubmitting ? <Spinner size={16} className="text-white dark:text-ink-900" /> : <Sparkles size={16} />}
                  Run What-If Prediction
                </button>
              </div>
            </form>
          )}
          {error && <p className="mt-3 text-sm text-danger">{error}</p>}
        </SectionCard>
      )}

      {result && <PredictionResultCard result={result} />}

      {(isStudent || (mode === "lookup" && result)) && (
        <SectionCard title="Prediction History" description="Most recent predictions, newest first.">
          {historyLoading ? (
            <div className="flex justify-center py-6">
              <Spinner size={22} />
            </div>
          ) : history.length === 0 ? (
            <EmptyState title="No prediction history yet" message="Run a prediction to start building history." />
          ) : (
            <ul className="divide-y divide-ink-50 dark:divide-ink-800">
              {history.map((h, i) => (
                <li key={i} className="flex flex-wrap items-center justify-between gap-2 py-3 text-sm">
                  <div className="flex items-center gap-2 text-slate">
                    <Clock size={13} />
                    {h.created_at ? new Date(h.created_at).toLocaleString() : "-"}
                  </div>
                  <div className="flex items-center gap-2">
                    <RiskBadge level={h.predicted_risk_level} />
                    <SegmentBadge segment={h.cluster_segment} />
                    <span className="font-mono text-ink-900 dark:text-white">{h.forecast_attendance_percentage}%</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </SectionCard>
      )}
    </div>
  );
}
