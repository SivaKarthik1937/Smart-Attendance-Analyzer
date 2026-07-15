/**
 * pages/Profile.tsx
 * ===================
 * Displays profile details for the logged-in user. Students get the full
 * profile (department, semester, distance, trend, overall attendance);
 * faculty/admin see the identity fields exposed by /api/auth/me, since
 * there's currently no dedicated "my faculty profile" endpoint.
 */

import { useEffect, useState, type ReactNode } from "react";
import { CalendarDays, GraduationCap, Mail, MapPin, User as UserIcon } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { getErrorMessage, studentApi } from "@/services/api";
import type { StudentProfile } from "@/types";
import { Card } from "@/components/Card";
import { TrendBadge } from "@/components/Badge";
import { PageLoader } from "@/components/Loader";
import { ErrorState } from "@/components/EmptyState";

function InfoRow({ icon, label, value }: { icon: ReactNode; label: string; value: ReactNode }) {
  return (
    <div className="flex items-center gap-3 border-b border-ink-50 py-3 last:border-0 dark:border-ink-800">
      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-ink-50 text-ink-500 dark:bg-ink-800 dark:text-ink-300">
        {icon}
      </span>
      <div>
        <p className="text-xs uppercase tracking-wide text-slate">{label}</p>
        <p className="text-sm font-medium text-ink-900 dark:text-white">{value}</p>
      </div>
    </div>
  );
}

export default function Profile() {
  const { user } = useAuth();
  const isStudent = user?.role === "student";

  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [isLoading, setIsLoading] = useState(isStudent);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isStudent) return;
    setIsLoading(true);
    studentApi
      .getProfile()
      .then(setProfile)
      .catch((err) => setError(getErrorMessage(err)))
      .finally(() => setIsLoading(false));
  }, [isStudent]);

  if (isStudent && isLoading) return <PageLoader label="Loading profile..." />;
  if (isStudent && error) return <ErrorState message={error} />;

  const initial = (user?.profile_name ?? user?.username ?? "?")[0]?.toUpperCase();

  return (
    <div className="mx-auto max-w-2xl animate-fade-in space-y-6 pb-10">
      <div>
        <p className="text-sm font-medium uppercase tracking-wide text-gold-dark dark:text-gold">Account</p>
        <h1 className="mt-1 font-display text-2xl font-semibold text-ink-900 dark:text-white">Your Profile</h1>
      </div>

      <Card className="p-6">
        <div className="mb-6 flex items-center gap-4">
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-ink-900 text-2xl font-semibold text-white dark:bg-gold dark:text-ink-900">
            {initial}
          </span>
          <div>
            <h2 className="font-display text-xl font-semibold text-ink-900 dark:text-white">
              {user?.profile_name ?? user?.username}
            </h2>
            <p className="text-sm capitalize text-slate">{user?.role}</p>
            {isStudent && profile?.trend && (
              <div className="mt-1">
                <TrendBadge trend={profile.trend} />
              </div>
            )}
          </div>
        </div>

        <InfoRow icon={<UserIcon size={15} />} label="Username" value={user?.username} />
        <InfoRow icon={<Mail size={15} />} label="Email" value={user?.email ?? "Not provided"} />

        {isStudent && profile && (
          <>
            <InfoRow icon={<GraduationCap size={15} />} label="Department" value={profile.department} />
            <InfoRow icon={<GraduationCap size={15} />} label="Semester" value={profile.semester} />
            <InfoRow icon={<MapPin size={15} />} label="Distance from College" value={`${profile.distance_km ?? 0} km`} />
            <InfoRow
              icon={<GraduationCap size={15} />}
              label="Overall Attendance"
              value={`${profile.overall_attendance_percentage ?? 0}%`}
            />
            <InfoRow
              icon={<CalendarDays size={15} />}
              label="Member Since"
              value={new Date(profile.created_at).toLocaleDateString()}
            />
          </>
        )}
      </Card>
    </div>
  );
}
