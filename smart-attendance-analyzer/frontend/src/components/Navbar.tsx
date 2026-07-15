/**
 * components/Navbar.tsx
 * =======================
 * Persistent top bar: brand mark, dark-mode toggle, and a user menu with
 * role badge + logout. Sits alongside <Sidebar> in the app shell layout.
 */

import { useState } from "react";
import { LogOut, Moon, Sun, UserCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useTheme } from "@/hooks/useTheme";
import { Badge } from "@/components/Badge";
import { useNavigate } from "react-router-dom";

export function Navbar() {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-ink-100 bg-white/90 px-6 backdrop-blur dark:border-ink-700 dark:bg-ink-900/90">
      <div className="flex items-center gap-2">
        <span className="font-display text-lg font-semibold tracking-tight text-ink-900 dark:text-white">
          Smart Attendance
        </span>
        <span className="hidden font-display text-lg text-gold sm:inline">Pattern Analyzer</span>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={toggleTheme}
          aria-label="Toggle dark mode"
          className="rounded-full p-2 text-ink-500 transition-colors hover:bg-ink-50 dark:text-ink-200 dark:hover:bg-ink-800"
        >
          {theme === "dark" ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <div className="relative">
          <button
            onClick={() => setMenuOpen((prev) => !prev)}
            className="flex items-center gap-2 rounded-full border border-ink-100 py-1 pl-1 pr-3 transition-colors hover:bg-ink-50 dark:border-ink-700 dark:hover:bg-ink-800"
          >
            <span className="flex h-7 w-7 items-center justify-center rounded-full bg-ink-900 text-xs font-semibold text-white dark:bg-gold dark:text-ink-900">
              {user?.profile_name?.[0]?.toUpperCase() ?? user?.username?.[0]?.toUpperCase() ?? <UserCircle size={16} />}
            </span>
            <span className="hidden text-sm font-medium text-ink-800 dark:text-ink-100 sm:inline">
              {user?.profile_name ?? user?.username}
            </span>
          </button>

          {menuOpen && (
            <div
              className="absolute right-0 mt-2 w-56 animate-fade-in rounded-card border border-ink-100 bg-white p-3 shadow-card-hover dark:border-ink-700 dark:bg-ink-800"
              onMouseLeave={() => setMenuOpen(false)}
            >
              <div className="mb-2 border-b border-ink-100 pb-2 dark:border-ink-700">
                <p className="text-sm font-semibold text-ink-900 dark:text-white">
                  {user?.profile_name ?? user?.username}
                </p>
                <p className="text-xs text-slate">{user?.email ?? user?.username}</p>
                {user?.role && (
                  <div className="mt-1.5">
                    <Badge className="bg-ink-100 capitalize text-ink-700 dark:bg-ink-700 dark:text-ink-100">
                      {user.role}
                    </Badge>
                  </div>
                )}
              </div>
              <button
                onClick={handleLogout}
                className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm text-danger transition-colors hover:bg-danger-light dark:hover:bg-danger-dark/10"
              >
                <LogOut size={15} /> Log out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
