/**
 * lib/toast.ts
 * =============
 * Thin wrapper around react-hot-toast so every toast in the app shares the
 * same styling (Academic Ledger palette) without repeating options at
 * every call site. Import `toast` from here instead of "react-hot-toast".
 */

import hotToast, { Toaster } from "react-hot-toast";

const baseStyle = {
  borderRadius: "10px",
  background: "#14213D",
  color: "#F7F6F2",
  fontSize: "14px",
  fontFamily: "Inter, ui-sans-serif, sans-serif",
  padding: "10px 14px",
};

export const toast = {
  success(message: string) {
    hotToast.success(message, {
      style: baseStyle,
      iconTheme: { primary: "#2E7D5B", secondary: "#F7F6F2" },
    });
  },
  error(message: string) {
    hotToast.error(message, {
      style: baseStyle,
      iconTheme: { primary: "#B23A48", secondary: "#F7F6F2" },
    });
  },
  info(message: string) {
    hotToast(message, {
      style: baseStyle,
      icon: "ℹ️",
    });
  },
};

/** Mount once near the root of the app (see App.tsx). */
export function AppToaster() {
  return <Toaster position="top-right" toastOptions={{ duration: 4000 }} />;
}
