/**
 * pages/Login.tsx
 * =================
 * Username/password login. Redirects to the role-appropriate dashboard on
 * success (student -> /student/dashboard, faculty/admin -> /faculty/dashboard).
 */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Lock, LogIn, User } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Spinner } from "@/components/Loader";
import { getErrorMessage } from "@/services/api";
import { toast } from "@/lib/toast";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password) {
      setError("Please enter both username and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await login(username.trim().toLowerCase(), password);
      toast.success(`Welcome back, ${user.profile_name ?? user.username}!`);
      navigate(user.role === "student" ? "/student/dashboard" : "/faculty/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to view your attendance insights.">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-ink-800 dark:text-ink-100">Username</label>
          <div className="relative">
            <User size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate" />
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. stu00001"
              autoComplete="username"
              className="w-full rounded-lg border border-ink-100 bg-white py-2.5 pl-9 pr-3 text-sm text-ink-900 outline-none transition-colors focus:border-gold focus:ring-1 focus:ring-gold dark:border-ink-700 dark:bg-ink-800 dark:text-white"
            />
          </div>
        </div>

        <div>
          <label className="mb-1 block text-sm font-medium text-ink-800 dark:text-ink-100">Password</label>
          <div className="relative">
            <Lock size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              className="w-full rounded-lg border border-ink-100 bg-white py-2.5 pl-9 pr-3 text-sm text-ink-900 outline-none transition-colors focus:border-gold focus:ring-1 focus:ring-gold dark:border-ink-700 dark:bg-ink-800 dark:text-white"
            />
          </div>
        </div>

        {error && (
          <p className="rounded-lg bg-danger-light px-3 py-2 text-sm text-danger-dark dark:bg-danger-dark/10 dark:text-danger">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="mt-2 flex items-center justify-center gap-2 rounded-lg bg-ink-900 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-ink-700 disabled:cursor-not-allowed disabled:opacity-70 dark:bg-gold dark:text-ink-900 dark:hover:bg-gold-light"
        >
          {isSubmitting ? <Spinner size={16} className="text-white dark:text-ink-900" /> : <LogIn size={16} />}
          {isSubmitting ? "Logging in..." : "Log in"}
        </button>

        <p className="mt-2 text-center text-sm text-slate">
          Don&apos;t have an account?{" "}
          <Link to="/register" className="font-medium text-gold-dark hover:underline dark:text-gold">
            Register here
          </Link>
        </p>

        <div className="mt-4 rounded-lg bg-ink-50 p-3 text-xs text-slate dark:bg-ink-800">
          <p className="mb-1 font-medium text-ink-700 dark:text-ink-200">Demo credentials</p>
          <p>Student: <span className="font-mono">stu00001</span> / <span className="font-mono">student123</span></p>
          <p>Faculty: <span className="font-mono">fac0001</span> / <span className="font-mono">faculty123</span></p>
        </div>
      </form>
    </AuthLayout>
  );
}
