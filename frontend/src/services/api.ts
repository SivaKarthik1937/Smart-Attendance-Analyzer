/**
 * services/api.ts
 * =================
 * Central Axios client + typed wrapper functions for every backend endpoint.
 * Components should never call axios directly -- they import the domain
 * objects exported here (authApi, studentApi, facultyApi, predictionApi,
 * analyticsApi, exportApi) so the request shape, error handling, and auth
 * header attachment stay consistent across the whole app.
 */

import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import type {
  AnalyticsOverview,
  AttendanceHistory,
  CurrentUser,
  FacultyDashboard,
  ModelInfo,
  PredictionHistory,
  PredictionOut,
  PredictionRequest,
  StudentDashboard,
  StudentProfile,
  StudentSummary,
  Token,
  UserRegisterPayload,
} from "@/types";

const TOKEN_KEY = "saa_access_token";
const ROLE_KEY = "saa_role";
const USERNAME_KEY = "saa_username";

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

const baseURL = (import.meta.env.VITE_API_BASE_URL as string | undefined) || "";

export const apiClient = axios.create({
  baseURL,
  timeout: 20000,
});

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Token missing/expired/invalid -- clear local session and let the
      // app's route guards redirect to /login on next render.
      clearSession();
    }
    return Promise.reject(error);
  }
);

/** Extract a human-readable message from any Axios error thrown by the API. */
export function getErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: string } | undefined)?.detail;
    if (detail) return detail;
    if (error.message) return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}

// ---------------------------------------------------------------------------
// Session storage helpers
// ---------------------------------------------------------------------------

export function saveSession(token: Token): void {
  localStorage.setItem(TOKEN_KEY, token.access_token);
  localStorage.setItem(ROLE_KEY, token.role);
  localStorage.setItem(USERNAME_KEY, token.username);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(ROLE_KEY);
  localStorage.removeItem(USERNAME_KEY);
}

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

// ---------------------------------------------------------------------------
// Auth API
// ---------------------------------------------------------------------------

export const authApi = {
  async login(username: string, password: string): Promise<Token> {
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    const { data } = await apiClient.post<Token>("/api/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return data;
  },

  async register(payload: UserRegisterPayload): Promise<Token> {
    const { data } = await apiClient.post<Token>("/api/auth/register", payload);
    return data;
  },

  async me(): Promise<CurrentUser> {
    const { data } = await apiClient.get<CurrentUser>("/api/auth/me");
    return data;
  },

  async logout(): Promise<void> {
    await apiClient.post("/api/auth/logout");
  },
};

// ---------------------------------------------------------------------------
// Student API
// ---------------------------------------------------------------------------

export const studentApi = {
  async getDashboard(): Promise<StudentDashboard> {
    const { data } = await apiClient.get<StudentDashboard>("/api/student/dashboard");
    return data;
  },

  async getProfile(): Promise<StudentProfile> {
    const { data } = await apiClient.get<StudentProfile>("/api/student/profile");
    return data;
  },

  async getAttendance(): Promise<AttendanceHistory> {
    const { data } = await apiClient.get<AttendanceHistory>("/api/student/attendance");
    return data;
  },
};

// ---------------------------------------------------------------------------
// Faculty API
// ---------------------------------------------------------------------------

export interface ListStudentsParams {
  department?: string;
  semester?: number;
  search?: string;
  skip?: number;
  limit?: number;
}

export const facultyApi = {
  async getDashboard(department?: string): Promise<FacultyDashboard> {
    const { data } = await apiClient.get<FacultyDashboard>("/api/faculty/dashboard", {
      params: department ? { department } : {},
    });
    return data;
  },

  async listStudents(params: ListStudentsParams = {}): Promise<StudentSummary[]> {
    const { data } = await apiClient.get<StudentSummary[]>("/api/faculty/students", { params });
    return data;
  },

  async getStudentDetail(studentCode: string): Promise<StudentDashboard> {
    const { data } = await apiClient.get<StudentDashboard>(`/api/faculty/students/${studentCode}`);
    return data;
  },

  async getBelow75(department?: string): Promise<StudentSummary[]> {
    const { data } = await apiClient.get<StudentSummary[]>("/api/faculty/below-75", {
      params: department ? { department } : {},
    });
    return data;
  },

  async getTopDefaulters(limit = 10, department?: string): Promise<StudentSummary[]> {
    const { data } = await apiClient.get<StudentSummary[]>("/api/faculty/top-defaulters", {
      params: { limit, ...(department ? { department } : {}) },
    });
    return data;
  },
};

// ---------------------------------------------------------------------------
// Prediction API
// ---------------------------------------------------------------------------

export const predictionApi = {
  async predict(payload: PredictionRequest): Promise<PredictionOut> {
    const { data } = await apiClient.post<PredictionOut>("/api/prediction/predict", payload);
    return data;
  },

  async getHistory(studentCode: string, limit = 20): Promise<PredictionHistory> {
    const { data } = await apiClient.get<PredictionHistory>(`/api/prediction/history/${studentCode}`, {
      params: { limit },
    });
    return data;
  },

  async getModelInfo(): Promise<ModelInfo> {
    const { data } = await apiClient.get<ModelInfo>("/api/prediction/model-info");
    return data;
  },
};

// ---------------------------------------------------------------------------
// Analytics API
// ---------------------------------------------------------------------------

export const analyticsApi = {
  async getOverview(): Promise<AnalyticsOverview> {
    const { data } = await apiClient.get<AnalyticsOverview>("/api/analytics/overview");
    return data;
  },
};

// ---------------------------------------------------------------------------
// Export API (returns raw Blobs for file download)
// ---------------------------------------------------------------------------

export const exportApi = {
  async studentReport(format: "pdf" | "csv", studentCode?: string): Promise<Blob> {
    const { data } = await apiClient.get("/api/export/student-report", {
      params: { format, ...(studentCode ? { student_code: studentCode } : {}) },
      responseType: "blob",
    });
    return data;
  },

  async facultyReport(format: "pdf" | "csv", department?: string): Promise<Blob> {
    const { data } = await apiClient.get("/api/export/faculty-report", {
      params: { format, ...(department ? { department } : {}) },
      responseType: "blob",
    });
    return data;
  },
};

/** Trigger a browser download for a Blob returned by the export endpoints. */
export function downloadBlob(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
