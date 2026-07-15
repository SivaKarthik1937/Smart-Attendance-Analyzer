/**
 * layouts/AppLayout.tsx
 * =======================
 * Shell for every authenticated page: sticky Navbar, left Sidebar, and a
 * content area rendered via React Router's <Outlet>. Also mounts the
 * global toast portal once for the whole authenticated section of the app.
 */

import { Outlet } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { Sidebar } from "@/components/Sidebar";
import { AppToaster } from "@/lib/toast";

export function AppLayout() {
  return (
    <div className="min-h-screen bg-paper dark:bg-paper-dark">
      <Navbar />
      <div className="mx-auto flex max-w-[1440px]">
        <Sidebar />
        <main className="min-w-0 flex-1 px-4 py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
      <AppToaster />
    </div>
  );
}
