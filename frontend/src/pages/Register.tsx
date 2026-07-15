/**
 * pages/Register.tsx
 * ====================
 * Registration form. Shows different fields depending on the selected
 * role (student needs department + semester; faculty needs department +
 * designation), then auto-logs the user in and redirects to their
 * dashboard on success.
 */

import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { AuthLayout } from "@/layouts/AuthLayout";
import { Spinner } from "@/components/Loader";
import { getErrorMessage } from "@/services/api";
import { toast } from "@/lib/toast";
import { DEPARTMENTS, DESIGNATIONS, GENDERS, SEMESTERS } from "@/lib/constants";
import type { Role } from "@/types";

const inputClass =
  "w-full rounded-lg border border-ink-100 bg-white py-2.5 px-3 text-sm text-ink-900 outline-none transition-colors focus:border-gold focus:ring-1 focus:ring-gold dark:border-ink-700 dark:bg-ink-800 dark:text-white";
const labelClass = "mb-1 block text-sm font-medium text-ink-800 dark:text-ink-100";

export default function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();

  const [role, setRole] = useState<Role>("student");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [department, setDepartment] = useState<string>(DEPARTMENTS[0]);
  const [semester, setSemester] = useState<number>(1);
  const [gender, setGender] = useState<string>(GENDERS[0]);
  const [distanceKm, setDistanceKm] = useState<string>("5");
  const [designation, setDesignation] = useState<string>(DESIGNATIONS[0]);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !password || !name.trim()) {
      setError("Please fill in all required fields.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }
    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await register({
        username: username.trim().toLowerCase(),
        email: email.trim() || undefined,
        password,
        role,
        name: name.trim(),
        department,
        semester: role === "student" ? semester : undefined,
        gender: role === "student" ? gender : undefined,
        distance_km: role === "student" ? Number(distanceKm) || 0 : undefined,
        designation: role === "faculty" ? designation : undefined,
      });
      toast.success(`Account created! Welcome, ${user.profile_name ?? user.username}.`);
      navigate(user.role === "student" ? "/student/dashboard" : "/faculty/dashboard");
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Register as a student or faculty member.">
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {/* Role toggle */}
        <div className="grid grid-cols-2 gap-2 rounded-lg bg-ink-50 p-1 dark:bg-ink-800">
          {(["student", "faculty"] as Role[]).map((r) => (
            <button
              key={r}
              type="button"
              onClick={() => setRole(r)}
              className={
                role === r
                  ? "rounded-md bg-ink-900 py-2 text-sm font-semibold capitalize text-white dark:bg-gold dark:text-ink-900"
                  : "rounded-md py-2 text-sm font-medium capitalize text-slate hover:text-ink-900 dark:hover:text-white"
              }
            >
              {r}
            </button>
          ))}
        </div>

        <div>
          <label className={labelClass}>Full Name *</label>
          <input value={name} onChange={(e) => setName(e.target.value)} className={inputClass} placeholder="Jane Doe" />
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>Username *</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={inputClass}
              placeholder="janedoe"
              autoComplete="username"
            />
          </div>
          <div>
            <label className={labelClass}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              placeholder="optional"
            />
          </div>
        </div>

        <div>
          <label className={labelClass}>Department *</label>
          <select value={department} onChange={(e) => setDepartment(e.target.value)} className={inputClass}>
            {DEPARTMENTS.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        {role === "student" ? (
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className={labelClass}>Semester *</label>
              <select value={semester} onChange={(e) => setSemester(Number(e.target.value))} className={inputClass}>
                {SEMESTERS.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Gender</label>
              <select value={gender} onChange={(e) => setGender(e.target.value)} className={inputClass}>
                {GENDERS.map((g) => (
                  <option key={g} value={g}>
                    {g}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Distance (km)</label>
              <input
                type="number"
                min={0}
                value={distanceKm}
                onChange={(e) => setDistanceKm(e.target.value)}
                className={inputClass}
              />
            </div>
          </div>
        ) : (
          <div>
            <label className={labelClass}>Designation</label>
            <select value={designation} onChange={(e) => setDesignation(e.target.value)} className={inputClass}>
              {DESIGNATIONS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className={labelClass}>Password *</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
              placeholder="Min. 6 characters"
              autoComplete="new-password"
            />
          </div>
          <div>
            <label className={labelClass}>Confirm Password *</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClass}
              autoComplete="new-password"
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
          {isSubmitting ? <Spinner size={16} className="text-white dark:text-ink-900" /> : <UserPlus size={16} />}
          {isSubmitting ? "Creating account..." : "Create account"}
        </button>

        <p className="mt-2 text-center text-sm text-slate">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-gold-dark hover:underline dark:text-gold">
            Log in
          </Link>
        </p>
      </form>
    </AuthLayout>
  );
}
