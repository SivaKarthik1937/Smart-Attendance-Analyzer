/**
 * pages/FacultyDashboard.tsx
 * =============================
 * The primary faculty-facing page: totals, below-75% count, department
 * filter, department/subject comparisons, top defaulters, improving vs.
 * declining students, risk distribution, and PDF/CSV report export.
 */

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  Download,
  Percent,
  TrendingUp,
  Users,
} from "lucide-react";
import { downloadBlob, exportApi, facultyApi, getErrorMessage } from "@/services/api";
import type { FacultyDashboard as FacultyDashboardType, StudentSummary } from "@/types";
import { PageLoader } from "@/components/Loader";
import { ErrorState } from "@/components/EmptyState";
import { SectionCard, StatCard } from "@/components/Card";
import { RiskBadge } from "@/components/Badge";
import { RiskLedgerStrip } from "@/components/RiskLedgerStrip";
import { AttendanceBarChart, type BarDatum } from "@/charts/AttendanceBarChart";
import { DEPARTMENTS } from "@/lib/constants";
import { toast } from "@/lib/toast";

function StudentMiniTable({ students, emptyLabel }: { students: StudentSummary[]; emptyLabel: string }) {
  if (students.length === 0) {
    return <p className="py-4 text-center text-sm text-slate">{emptyLabel}</p>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-ink-100 text-xs uppercase tracking-wide text-slate dark:border-ink-700">
            <th className="py-2 pr-4">Code</th>
            <th className="py-2 pr-4">Name</th>
            <th className="py-2 pr-4">Dept</th>
            <th className="py-2 pr-4">Attendance</th>
            <th className="py-2 pr-4">Risk</th>
          </tr>
        </thead>
        <tbody>
          {students.map((s) => (
            <tr key={s.student_code} className="border-b border-ink-50 dark:border-ink-800">
              <td className="py-2 pr-4 font-mono text-xs text-slate">{s.student_code}</td>
              <td className="py-2 pr-4 font-medium text-ink-800 dark:text-ink-100">{s.name}</td>
              <td className="py-2 pr-4 text-slate">{s.department}</td>
              <td
                className={`py-2 pr-4 font-mono font-semibold ${
                  (s.overall_attendance_percentage ?? 0) < 75 ? "text-danger" : "text-success"
                }`}
              >
                {s.overall_attendance_percentage}%
              </td>
              <td className="py-2 pr-4">
                <RiskBadge level={s.risk_level} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function FacultyDashboard() {
  const [data, setData] = useState<FacultyDashboardType | null>(null);
  const [department, setDepartment] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState<"pdf" | "csv" | null>(null);

  async function loadDashboard(dept: string) {
    setIsLoading(true);
    setError(null);
    try {
      const result = await facultyApi.getDashboard(dept || undefined);
      setData(result);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadDashboard(department);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [department]);

  async function handleDownload(format: "pdf" | "csv") {
    setDownloading(format);
    try {
      const blob = await exportApi.facultyReport(format, department || undefined);
      downloadBlob(blob, `faculty_report.${format}`);
      toast.success(`Report downloaded as ${format.toUpperCase()}.`);
    } catch (err) {
      toast.error(getErrorMessage(err));
    } finally {
      setDownloading(null);
    }
  }

  if (isLoading && !data) return <PageLoader label="Loading faculty dashboard..." />;
  if (error && !data) return <ErrorState message={error} onRetry={() => loadDashboard(department)} />;
  if (!data) return null;

  const departmentBars: BarDatum[] = data.department_stats.map((d) => ({ label: d.department, value: d.average_attendance }));
  const subjectBars: BarDatum[] = data.subject_stats.map((s) => ({ label: s.subject_name, value: s.average_attendance }));

  return (
    <div className="animate-fade-in space-y-6 pb-10">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <p className="text-sm font-medium uppercase tracking-wide text-gold-dark dark:text-gold">
            Faculty Dashboard
          </p>
          <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">
            Institution Attendance Overview
          </h1>
        </div>
        <div className="flex gap-2">
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="rounded-lg border border-ink-100 bg-white px-3 py-2 text-sm text-ink-800 outline-none focus:border-gold dark:border-ink-700 dark:bg-ink-800 dark:text-white"
          >
            <option value="">All Departments</option>
            {DEPARTMENTS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
          <button
            onClick={() => handleDownload("csv")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg border border-ink-100 px-3 py-2 text-sm font-medium text-ink-700 transition-colors hover:bg-ink-50 disabled:opacity-60 dark:border-ink-700 dark:text-ink-100 dark:hover:bg-ink-800"
          >
            <Download size={14} /> CSV
          </button>
          <button
            onClick={() => handleDownload("pdf")}
            disabled={downloading !== null}
            className="flex items-center gap-1.5 rounded-lg bg-ink-900 px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-ink-700 disabled:opacity-60 dark:bg-gold dark:text-ink-900 dark:hover:bg-gold-light"
          >
            <Download size={14} /> {downloading === "pdf" ? "Preparing..." : "Export PDF"}
          </button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard label="Total Students" value={data.total_students} icon={<Users size={16} />} accent="ink" />
        <StatCard
          label="Below 75%"
          value={data.students_below_75}
          icon={<AlertTriangle size={16} />}
          accent="danger"
          sublabel={`${((data.students_below_75 / Math.max(data.total_students, 1)) * 100).toFixed(1)}% of total`}
        />
        <StatCard label="Average Attendance" value={`${data.average_attendance}%`} icon={<Percent size={16} />} accent="ink" />
        <StatCard
          label="Highest / Lowest"
          value={`${data.highest_attendance}% / ${data.lowest_attendance}%`}
          icon={<TrendingUp size={16} />}
          accent="ink"
        />
      </div>

      {/* Risk distribution */}
      <SectionCard title="Risk Distribution" description="Worst-case risk level across each student's enrolled subjects.">
        <RiskLedgerStrip
          low={data.risk_distribution.low_risk}
          medium={data.risk_distribution.medium_risk}
          high={data.risk_distribution.high_risk}
        />
      </SectionCard>

      {/* Comparisons */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard title="Department Comparison" description="Average attendance % by department.">
          <AttendanceBarChart data={departmentBars} height={Math.max(220, departmentBars.length * 45)} />
        </SectionCard>
        <SectionCard title="Subject Comparison" description="Average attendance % by subject.">
          <AttendanceBarChart data={subjectBars} height={Math.max(220, subjectBars.length * 32)} />
        </SectionCard>
      </div>

      {/* Defaulters */}
      <SectionCard title="Top Defaulters" description="Students with the lowest overall attendance.">
        <StudentMiniTable students={data.top_defaulters} emptyLabel="No defaulters found for this filter." />
      </SectionCard>

      {/* Improving / Declining */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <SectionCard
          title="Students Improving"
          description="Trending upward compared to last semester."
          action={<ArrowUpRight size={16} className="text-success" />}
        >
          <StudentMiniTable students={data.students_improving} emptyLabel="No improving students found." />
        </SectionCard>
        <SectionCard
          title="Students Declining"
          description="Trending downward compared to last semester."
          action={<ArrowDownRight size={16} className="text-danger" />}
        >
          <StudentMiniTable students={data.students_declining} emptyLabel="No declining students found." />
        </SectionCard>
      </div>
    </div>
  );
}
