/**
 * pages/Home.tsx
 * ================
 * Lightweight welcome hub shown at "/". Rather than duplicating the heavy
 * data-fetching that the Dashboard pages own, this page is an intentionally
 * fast-loading landing point with quick-access cards into the rest of the app.
 */

import { Link } from "react-router-dom";
import { BarChart3, LayoutDashboard, Sparkles, UserRound } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { Card } from "@/components/Card";

export default function Home() {
  const { user } = useAuth();
  const isStudent = user?.role === "student";

  const cards = [
    {
      to: isStudent ? "/student/dashboard" : "/faculty/dashboard",
      title: "Dashboard",
      description: isStudent
        ? "Your attendance, subject breakdown, and monthly trend."
        : "Institution-wide stats, defaulters, and department comparisons.",
      icon: LayoutDashboard,
    },
    {
      to: "/prediction",
      title: "Prediction",
      description: "Run the risk, forecast, and segmentation models on demand.",
      icon: Sparkles,
    },
    {
      to: "/analytics",
      title: "Analytics",
      description: "Correlation matrix, model comparisons, and deeper trends.",
      icon: BarChart3,
    },
    {
      to: "/profile",
      title: "Profile",
      description: "View and manage your account details.",
      icon: UserRound,
    },
  ];

  return (
    <div className="mx-auto max-w-4xl animate-fade-in py-6">
      <p className="text-sm font-medium uppercase tracking-wide text-gold-dark dark:text-gold">
        {isStudent ? "Student Portal" : "Faculty Portal"}
      </p>
      <h1 className="mt-1 font-display text-3xl font-semibold text-ink-900 dark:text-white">
        Welcome back, {user?.profile_name ?? user?.username}.
      </h1>
      <p className="mt-2 max-w-xl text-sm text-slate">
        {isStudent
          ? "Here's your quick path into attendance insights, risk prediction, and reports."
          : "Here's your quick path into institution-wide attendance analytics and student risk tracking."}
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2">
        {cards.map(({ to, title, description, icon: Icon }) => (
          <Link key={to} to={to}>
            <Card className="flex h-full items-start gap-4 p-5" hoverable>
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-ink-900 text-gold dark:bg-gold dark:text-ink-900">
                <Icon size={18} />
              </span>
              <div>
                <h3 className="font-display text-base font-semibold text-ink-900 dark:text-white">{title}</h3>
                <p className="mt-1 text-sm text-slate">{description}</p>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
