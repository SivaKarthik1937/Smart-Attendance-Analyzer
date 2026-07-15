/**
 * types/index.ts
 * ================
 * TypeScript types mirroring the backend's Pydantic schemas (backend/models.py).
 * Keeping these in one file makes it easy to see the full API contract at a
 * glance and keep the frontend in sync with the backend.
 */

// ---------------------------------------------------------------------------
// Enums
// ---------------------------------------------------------------------------

export type Role = "student" | "faculty" | "admin";
export type RiskLevel = "Low Risk" | "Medium Risk" | "High Risk";
export type Trend = "improving" | "stable" | "declining";
export type Segment = "Excellent" | "Average" | "Critical";
export type ExportFormat = "pdf" | "csv";

// ---------------------------------------------------------------------------
// Auth
// ---------------------------------------------------------------------------

export interface UserRegisterPayload {
  username: string;
  email?: string;
  password: string;
  role: Role;
  name?: string;
  department?: string;
  semester?: number;
  gender?: string;
  distance_km?: number;
  designation?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
  role: Role;
  username: string;
  expires_in_minutes: number;
}

export interface CurrentUser {
  username: string;
  email: string | null;
  role: Role;
  profile_code: string | null;
  profile_name: string | null;
}

// ---------------------------------------------------------------------------
// Student
// ---------------------------------------------------------------------------

export interface StudentProfile {
  id: number;
  student_code: string;
  name: string;
  department: string;
  semester: number;
  gender?: string | null;
  distance_km?: number | null;
  overall_attendance_percentage?: number | null;
  trend?: Trend | null;
  created_at: string;
}

export interface SubjectAttendance {
  subject_name: string;
  total_classes: number;
  classes_attended: number;
  attendance_percentage: number;
  leaves_taken: number;
  internal_marks?: number | null;
  risk_label?: RiskLevel | null;
}

export interface MonthlyTrendPoint {
  month: string;
  attendance_percentage: number;
}

export interface PredictionOut {
  student_code: string | null;
  predicted_risk_level: RiskLevel;
  risk_model_used: string;
  risk_confidence: number | null;
  forecast_attendance_percentage: number;
  forecast_model_used: string;
  cluster_segment: Segment;
  ai_recommendations: string[];
  created_at: string | null;
}

export interface StudentDashboard {
  profile: StudentProfile;
  overall_attendance_percentage: number;
  subject_wise: SubjectAttendance[];
  monthly_trend: MonthlyTrendPoint[];
  total_leaves: number;
  average_internal_marks: number | null;
  latest_prediction: PredictionOut | null;
}

export interface AttendanceRecord {
  subject_name: string;
  total_classes: number;
  classes_attended: number;
  attendance_percentage: number;
  previous_attendance_percentage?: number | null;
  leaves_taken: number;
  internal_marks?: number | null;
  monthly_attendance?: number | null;
  risk_label?: RiskLevel | null;
}

export interface AttendanceHistory {
  student_code: string;
  records: AttendanceRecord[];
  monthly_trend: MonthlyTrendPoint[];
}

// ---------------------------------------------------------------------------
// Faculty
// ---------------------------------------------------------------------------

export interface StudentSummary {
  student_code: string;
  name: string;
  department: string;
  semester: number;
  overall_attendance_percentage: number | null;
  trend: Trend | null;
  risk_level: RiskLevel | null;
}

export interface DepartmentStat {
  department: string;
  average_attendance: number;
  total_students: number;
  below_75_count: number;
}

export interface SubjectStat {
  subject_name: string;
  average_attendance: number;
  total_enrolled: number;
}

export interface RiskDistribution {
  low_risk: number;
  medium_risk: number;
  high_risk: number;
}

export interface FacultyDashboard {
  total_students: number;
  students_below_75: number;
  highest_attendance: number;
  lowest_attendance: number;
  average_attendance: number;
  department_stats: DepartmentStat[];
  subject_stats: SubjectStat[];
  top_defaulters: StudentSummary[];
  students_improving: StudentSummary[];
  students_declining: StudentSummary[];
  risk_distribution: RiskDistribution;
}

// ---------------------------------------------------------------------------
// Prediction
// ---------------------------------------------------------------------------

export interface PredictionRequest {
  student_code?: string;
  current_attendance?: number;
  previous_attendance?: number;
  leaves_taken?: number;
  internal_marks?: number;
  distance_km?: number;
  monthly_attendance?: number;
}

export interface PredictionHistory {
  student_code: string;
  history: PredictionOut[];
}

export interface ModelComparisonEntry {
  model_name: string;
  accuracy?: number | null;
  precision?: number | null;
  recall?: number | null;
  f1_score?: number | null;
  mae?: number | null;
  rmse?: number | null;
  r2_score?: number | null;
}

export interface ModelInfo {
  risk_model: Record<string, unknown> | null;
  forecast_model: Record<string, unknown> | null;
  segmentation_model: Record<string, unknown> | null;
}

// ---------------------------------------------------------------------------
// Analytics
// ---------------------------------------------------------------------------

export interface CorrelationPair {
  feature_a: string;
  feature_b: string;
  correlation: number;
}

export interface FeatureImportanceEntry {
  feature: string;
  importance: number;
}

export interface AnalyticsOverview {
  attendance_distribution: number[];
  department_comparison: DepartmentStat[];
  semester_comparison: Record<string, number>;
  subject_comparison: SubjectStat[];
  monthly_trend_overall: MonthlyTrendPoint[];
  correlation_matrix: CorrelationPair[];
  feature_importance: FeatureImportanceEntry[];
  risk_model_comparison: ModelComparisonEntry[];
  forecast_model_comparison: ModelComparisonEntry[];
}

// ---------------------------------------------------------------------------
// Generic API error shape
// ---------------------------------------------------------------------------

export interface ApiErrorResponse {
  detail: string;
}
