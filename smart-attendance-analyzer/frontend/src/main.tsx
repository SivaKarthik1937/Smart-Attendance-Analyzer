/**
 * main.tsx
 * ==========
 * Application entry point. Mounts <App /> (which itself wraps
 * ThemeProvider/AuthProvider/BrowserRouter) into the DOM.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element '#root' not found in index.html");
}

createRoot(rootElement).render(
  <StrictMode>
    <App />
  </StrictMode>
);
