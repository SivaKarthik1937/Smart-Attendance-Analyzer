/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // --- Academic Ledger design system ---
        ink: {
          DEFAULT: "#14213D",
          50: "#EEF1F6",
          100: "#D6DCE8",
          200: "#AEB9D1",
          300: "#8695B9",
          400: "#5E71A1",
          500: "#3C4E7F",
          600: "#2C3B62",
          700: "#1F2C4A",
          800: "#182238",
          900: "#14213D",
          950: "#0C1526",
        },
        paper: {
          DEFAULT: "#F7F6F2",
          dark: "#0F1219",
        },
        slate: {
          DEFAULT: "#5B6472",
        },
        gold: {
          DEFAULT: "#C9A227",
          light: "#E4C866",
          dark: "#9C7D1B",
        },
        success: {
          DEFAULT: "#2E7D5B",
          light: "#DCEFE6",
          dark: "#1F5A40",
        },
        warning: {
          DEFAULT: "#C9822E",
          light: "#F6E6D2",
          dark: "#9C621F",
        },
        danger: {
          DEFAULT: "#B23A48",
          light: "#F6DCDF",
          dark: "#8A2732",
        },
      },
      fontFamily: {
        display: ["Fraunces", "ui-serif", "Georgia", "serif"],
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        card: "10px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(20, 33, 61, 0.04), 0 4px 12px rgba(20, 33, 61, 0.06)",
        "card-hover": "0 2px 4px rgba(20, 33, 61, 0.06), 0 8px 24px rgba(20, 33, 61, 0.10)",
      },
      keyframes: {
        "fade-in": {
          "0%": { opacity: "0", transform: "translateY(4px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.25s ease-out",
      },
    },
  },
  plugins: [],
};
