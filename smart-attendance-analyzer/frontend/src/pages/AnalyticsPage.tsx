/**
 * pages/AnalyticsPage.tsx
 * ==========================
 * Deeper analytics: attendance distribution, department/subject/semester
 * comparisons, monthly trend, correlation matrix, feature importance, and
 * side-by-side ML model comparison tables (accuracy/F1 for risk,
 * MAE/RMSE/R2 for forecast).
 */

import { useEffect, useState } from "react";
import { analyticsApi, getErrorMessage } from "@/services/api";
import type { AnalyticsOverview } from "@/types";
import { PageLoader } from "@/components/Loader";
import { ErrorState } from "@/components/EmptyState";
import { SectionCard } from "@/components/Card";
import { AttendanceBarChart, type BarDatum } from "@/charts/AttendanceBarChart";
import { AttendanceLineChart } from "@/charts/AttendanceLineChart";
import { GenericBarChart } from "@/charts/GenericBarChart";
import { Heatmap } from "@/charts/Heatmap";

const DISTRIBUTION_BIN_LABELS = ["0-10", "10-20", "20-30", "30-40", "40-50", "50-60", "60-70", "70-80", "80-90", "90-100"];

/** Reconstruct a full symmetric correlation matrix (with diagonal = 1) from the upper-triangle pairs the API returns. */
function buildCorrelationMatrix(pairs: AnalyticsOverview["correlation_matrix"]) {
  const features: string[] = [];
  pairs.forEach((p) => {
    if (!features.includes(p.feature_a)) features.push(p.feature_a);
    if (!features.includes(p.feature_b)) features.push(p.feature_b);
  });

  const matrix: number[][] = features.map((rowFeature) =>
    features.map((colFeature) => {
      if (rowFeature === colFeature) return 1;
      const pair = pairs.find(
        (p) =>
          (p.feature_a === rowFeature && p.feature_b === colFeature) ||
          (p.feature_a === colFeature && p.feature_b === rowFeature)
      );
      return pair ? pair.correlation : 0;
    })
  );

  return { features, matrix };
}

function ModelComparisonTable({
  title,
  rows,
  columns,
  bestKey,
}: {
  title: string;
  rows: Record<string, unknown>[];
  columns: { key: string; label: string; format?: (v: number) => string }[];
  bestKey: string;
}) {
  const bestValue = Math.max(...rows.map((r) => Number(r[bestKey] ?? -Infinity)));

  return (
    <SectionCard title={title}>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-ink-100 text-xs uppercase tracking-wide text-slate dark:border-ink-700">
              <th className="py-2 pr-4">Model</th>
              {columns.map((c) => (
                <th key={c.key} className="py-2 pr-4">
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const isBest = Number(row[bestKey]) === bestValue;
              return (
                <tr key={String(row.model_name)} className="border-b border-ink-50 dark:border-ink-800">
                  <td className="py-2.5 pr-4 font-medium text-ink-800 dark:text-ink-100">
                    {String(row.model_name)}
                    {isBest && (
                      <span className="ml-2 rounded-full bg-gold/20 px-2 py-0.5 text-xs font-semibold text-gold-dark dark:text-gold">
                        Best
                      </span>
                    )}
                  </td>
                  {columns.map((c) => {
                    const raw = row[c.key];
                    const value = typeof raw === "number" ? raw : null;
                    return (
                      <td key={c.key} className="py-2.5 pr-4 font-mono text-slate">
                        {value !== null ? (c.format ? c.format(value) : value) : "-"}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}

export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyticsApi.getOverview();
      setData(result);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  if (isLoading) return <PageLoader label="Crunching the numbers..." />;
  if (error || !data) return <ErrorState message={error ?? "No analytics data available."} onRetry={load} />;

  const distributionData = data.attendance_distribution.map((count, i) => ({
    label: `${DISTRIBUTION_BIN_LABELS[i]}%`,
    value: count,
  }));

  const departmentBars: BarDatum[] = data.department_comparison.map((d) => ({ label: d.department, value: d.average_attendance }));
  const subjectBars: BarDatum[] = data.subject_comparison.map((s) => ({ label: s.subject_name, value: s.average_attendance }));
  const semesterBars: BarDatum[] = Object.entries(data.semester_comparison)
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .map(([sem, avg]) => ({ label: `Semester ${sem}`, value: avg }));

  const featureImportanceBars = data.feature_importance.map((f) => ({
    label: f.feature.replace(/_/g, " "),
    value: f.importance,
  }));

  const { features, matrix } = buildCorrelationMatrix(data.correlation_matrix);
  const correlationLabels = features.map((f) => f.replace(/_/g, " "));

  return (
    <div className="animate-fade-in space-y-6 pb-10">
      <div>
        <p className="text-sm font-medium uppercase tracking-wide text-gold-dark dark:text-gold">Analytics</p>
        <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">
          Deeper Attendance Insights
        </h1>
        <p className="mt-1 text-sm text-slate">
          Distribution, comparisons, correlation, and the machine learning models behind the predictions.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Attendance Distribution" description="Number of records in each 10% attendance band.">
          <GenericBarChart data={distributionData} color="#14213D" valueFormatter={(v) => `${v} records`} />
        </SectionCard>
        <SectionCard title="Overall Monthly Trend" description="Average attendance % across all students, by month.">
          <AttendanceLineChart data={data.monthly_trend_overall} />
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Department Comparison">
          <AttendanceBarChart data={departmentBars} height={Math.max(220, departmentBars.length * 45)} />
        </SectionCard>
        <SectionCard title="Semester Comparison">
          <AttendanceBarChart data={semesterBars} height={Math.max(220, semesterBars.length * 40)} />
        </SectionCard>
      </div>

      <SectionCard title="Subject Comparison">
        <AttendanceBarChart data={subjectBars} height={Math.max(260, subjectBars.length * 32)} />
      </SectionCard>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Correlation Matrix" description="Pairwise correlation between attendance-related features.">
          <Heatmap rows={correlationLabels} cols={correlationLabels} values={matrix} colorScale="diverging" valueFormatter={(v) => v.toFixed(2)} />
        </SectionCard>
        <SectionCard title="Feature Importance" description="Which features drive the risk classification model's predictions.">
          <GenericBarChart data={featureImportanceBars} valueFormatter={(v) => v.toFixed(3)} />
        </SectionCard>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ModelComparisonTable
          title="Risk Classification Models"
          rows={data.risk_model_comparison}
          bestKey="f1_score"
          columns={[
            { key: "accuracy", label: "Accuracy", format: (v) => `${(v * 100).toFixed(1)}%` },
            { key: "precision", label: "Precision", format: (v) => `${(v * 100).toFixed(1)}%` },
            { key: "recall", label: "Recall", format: (v) => `${(v * 100).toFixed(1)}%` },
            { key: "f1_score", label: "F1 Score", format: (v) => `${(v * 100).toFixed(1)}%` },
          ]}
        />
        <ModelComparisonTable
          title="Forecast Regression Models"
          rows={data.forecast_model_comparison}
          bestKey="r2_score"
          columns={[
            { key: "mae", label: "MAE", format: (v) => v.toFixed(2) },
            { key: "rmse", label: "RMSE", format: (v) => v.toFixed(2) },
            { key: "r2_score", label: "R²", format: (v) => v.toFixed(3) },
          ]}
        />
      </div>
    </div>
  );
}
