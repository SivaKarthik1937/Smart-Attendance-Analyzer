/**
 * pages/StudentDashboard.tsx
 * =============================
 * The primary student-facing page: overall + subject-wise attendance,
 * monthly trend, latest risk/forecast/segment prediction with AI
 * recommendations, and PDF/CSV report download.
 */

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BookOpen,
  CalendarX,
  Download,
  GraduationCap,
  Percent,
  Sparkles,
} from "lucide-react";
import { downloadBlob, exportApi, getErrorMessage, studentApi } from "@/services/api";
import type { StudentDashboard as StudentDashboardType } from "@/types";
import { PageLoader } from "@/components/Loader";
import { ErrorState } from "@/components/EmptyState";
import { Card, SectionCard, StatCard } from "@/components/Card";
import { RiskBadge, SegmentBadge, TrendBadge } from "@/components/Badge";
import { AttendanceLineChart } from "@/charts/AttendanceLineChart";
import { SubjectRadarChart } from "@/charts/SubjectRadarChart";
import { toast } from "@/lib/toast";

export default function StudentDashboard() {
  const [data, setData] = useState<StudentDashboardType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<"pdf" | "csv" | null>(null);

  async function loadDashboard() {
    setIsLoading(true);
    setError(null);
    try {
      const result = await studentApi.getDashboard();
      setData(result);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard();
  }, []);

  async function handleDownload(format: "pdf" | "csv") {
    setDownloading(format);
    try {
      const blob = await exportApi.studentReport(format);
      downloadBlob(blob, `attendance_report.${format}`);
      toast.success(`Report downloaded as ${format.toUpperCase()}.`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setDownloading(null);
    }
  }

  if (isLoading) return <PageLoader label="Loading your dashboard..." />;
  if (error || !data) return <ErrorState message={error ?? "No data available."} onRetry={loadDashboard} />;

  const { profile, overall_attendance_percentage, subject_wise, monthly_trend, total_leaves, average_internal_marks, latest_prediction } = data;

  return (
    <div className="animate-fade-in space-y-6 pb-10">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-gold-dark dark:text-gold">
            Student Dashboard
          </p>
          <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">
            {profile.name} <span className="font-mono text-lg text-slate">· {profile.student_code}</span>
          </h1>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-slate">
            <GraduationCap size={14} /> {profile.department} · Semester {profile.semester}
            <TrendBadge trend={profile.trend} />
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleDownload("csv")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg border border-ink-100 px-3 py-2 text-sm font-medium text-ink-700 transition-colors hover:bg-ink-50 disabled:opacity-60 dark:border-ink-700 dark:text-ink-100 dark:hover:bg-ink-800"
          >
            <Download size={14} /> {downloading === "csv" ? "Preparing..." : "CSV"}
          </button>
          <button
            onClick={() => handleDownload("pdf")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg bg-ink-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-ink-700 disabled:opacity-60 dark:bg-gold dark:text-ink-900 dark:hover:bg-gold-light"
          >
            <Download size={14} /> {downloading === "pdf" ? "Preparing..." : "Download PDF"}
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="Overall Attendance"
          value={`${overall_attendance_percentage}%`}
          icon={<Percent size={16} />}
          accent={overall_attendance_percentage < 75 ? "danger" : "success"}
          sublabel={overall_attendance_percentage < 75 ? "Below requirement" : "Meets requirement"}
        />
        <StatCard label="Total Leaves" value={total_leaves} icon={<CalendarX size={16} />} accent="ink" />
        <StatCard
          label="Avg. Internal Marks"
          value={average_internal_marks ?? "-"}
          icon={<BookOpen size={16} />}
          accent="ink"
        />
        <StatCard
          label="Risk Level"
          value={latest_prediction?.predicted_risk_level ?? "Not predicted"}
          icon={<Sparkles size={16} />}
          accent={
            latest_prediction?.predicted_risk_level === "High Risk"
              ? "danger"
              : latest_prediction?.predicted_risk_level === "Medium Risk"
              ? "warning"
              : "success"
          }
        />
      </div>

      {/* Prediction summary */}
      {latest_prediction ? (
        <SectionCard
          title="Latest AI Prediction"
          description={`Generated using ${latest_prediction.risk_model_used} + ${latest_prediction.forecast_model_used}`}
          action={
            <Link to="/prediction" className="text-sm font-medium text-gold-dark hover:underline dark:text-gold">
              Run new prediction
            </Link>
          }
        >
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <RiskBadge level={latest_prediction.predicted_risk_level} />
            <SegmentBadge segment={latest_prediction.cluster_segment} />
            <span className="text-sm text-slate">
              Forecasted semester-end attendance:{" "}
              <span className="font-mono font-semibold text-ink-900 dark:text-white">
                {latest_prediction.forecast_attendance_percentage}%
              </span>
            </span>
          </div>
          <ul className="space-y-2">
            {latest_prediction.ai_recommendations.map((tip, i) => (
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
      ) : (
        <Card className="flex flex-col items-center gap-3 p-6 text-center">
          <Sparkles size={24} className="text-gold" />
          <p className="text-sm text-slate">
            No prediction has been generated yet. Run the model to see your risk level, forecast, and personalized
            recommendations.
          </p>
          <Link
            to="/prediction"
            className="rounded-lg bg-ink-900 px-4 py-2 text-sm font-medium text-white hover:bg-ink-700 dark:bg-gold dark:text-ink-900"
          >
            Run Prediction
          </Link>
        </Card>
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Monthly Attendance Trend" description="Your average attendance across all subjects, by month.">
          <AttendanceLineChart data={monthly_trend} />
        </SectionCard>
        <SectionCard title="Subject-wise Attendance" description="Attendance % per subject vs. the 75% requirement.">
          <SubjectRadarChart subjects={subject_wise} />
        </SectionCard>
      </div>

      {/* Subject table */}
      <SectionCard title="Subject Details">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-ink-100 text-xs uppercase tracking-wide text-slate dark:border-ink-700">
                <th className="py-2 pr-4">Subject</th>
                <th className="py-2 pr-4">Classes</th>
                <th className="py-2 pr-4">Attendance</th>
                <th className="py-2 pr-4">Leaves</th>
                <th className="py-2 pr-4">Marks</th>
                <th className="py-2 pr-4">Risk</th>
              </tr>
            </thead>
            <tbody>
              {subject_wise.map((s) => (
                <tr key={s.subject_name} className="border-b border-ink-50 dark:border-ink-800">
                  <td className="py-2.5 pr-4 font-medium text-ink-800 dark:text-ink-100">{s.subject_name}</td>
                  <td className="py-2.5 pr-4 font-mono text-slate">
                    {s.classes_attended}/{s.total_classes}
                  </td>
                  <td
                    className={`py-2.5 pr-4 font-mono font-semibold ${
                      s.attendance_percentage < 75 ? "text-danger" : "text-success"
                    }`}
                  >
                    {s.attendance_percentage}%
                  </td>
                  <td className="py-2.5 pr-4 font-mono text-slate">{s.leaves_taken}</td>
                  <td className="py-2.5 pr-4 font-mono text-slate">{s.internal_marks ?? "-"}</td>
                  <td className="py-2.5 pr-4">
                    <RiskBadge level={s.risk_label} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SectionCard>
    </div>
  );
}
