/**
 * components/Sidebar.tsx
 * ========================
 * Persistent left navigation rail. Link set adapts to the logged-in
 * user's role (student vs faculty/admin). Active links get a solid gold
 * left-border indicator instead of a filled pill, per the Academic
 * Ledger design language.
 */

import { NavLink } from "react-router-dom";
import clsx from "clsx";
import type { ElementType } from "react";
import {
  LayoutDashboard,
  LineChart,
  Sparkles,
  BarChart3,
  Settings,
  UserRound,
  Home,
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";

interface NavItem {
  to: string;
  label: string;
  icon: ElementType;
}

const studentLinks: NavItem[] = [
  { to: "/", label: "Home", icon: Home },
  { to: "/student/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/prediction", label: "Prediction", icon: Sparkles },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/profile", label: "Profile", icon: UserRound },
  { to: "/settings", label: "Settings", icon: Settings },
];

const facultyLinks: NavItem[] = [
  { to: "/", label: "Home", icon: Home },
  { to: "/faculty/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { to: "/prediction", label: "Prediction", icon: Sparkles },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/profile", label: "Profile", icon: UserRound },
  { to: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const { user } = useAuth();
  const links = user?.role === "student" ? studentLinks : facultyLinks;

  return (
    <aside className="hidden w-60 shrink-0 border-r border-ink-100 bg-white px-3 py-6 dark:border-ink-700 dark:bg-ink-900 md:block">
      <nav className="flex flex-col gap-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 rounded-lg border-l-4 px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "border-gold bg-gold/10 text-ink-900 dark:text-white"
                  : "border-transparent text-slate hover:bg-ink-50 hover:text-ink-900 dark:hover:bg-ink-800 dark:hover:text-white"
              )
            }
          >
            <Icon size={17} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-8 rounded-card bg-ink-900 p-4 text-white dark:bg-ink-800">
        <LineChart size={18} className="mb-2 text-gold" />
        <p className="font-display text-sm font-semibold">Stay on track</p>
        <p className="mt-1 text-xs text-ink-200">
          Consistent attendance is the strongest predictor of a healthy risk score.
        </p>
      </div>
    </aside>
  );
}
