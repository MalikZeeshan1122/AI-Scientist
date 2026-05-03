import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        /* rgb(var(--ink-*)) works with Tailwind v3 opacity modifiers */
        ink: {
          50:  "rgb(var(--ink-50))",
          100: "rgb(var(--ink-100))",
          200: "rgb(var(--ink-200))",
          300: "rgb(var(--ink-300))",
          400: "rgb(var(--ink-400))",
          500: "rgb(var(--ink-500))",
          600: "rgb(var(--ink-600))",
          700: "rgb(var(--ink-700))",
          800: "rgb(var(--ink-800))",
          850: "rgb(var(--ink-850))",
          900: "rgb(var(--ink-900))",
          950: "rgb(var(--ink-950))",
        },
        accent: {
          DEFAULT: "#F97316",
          soft:    "#FB923C",
          deep:    "#EA6800",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "Inter", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(249,115,22,0.20)",
        soft: "0 1px 4px rgba(0,0,0,0.07)",
        card: "0 1px 4px rgba(0,0,0,0.07)",
      },
      animation: {
        shimmer:    "shimmer 1.6s linear infinite",
        "slide-up": "slide-up 0.2s ease-out",
      },
      keyframes: {
        shimmer:    { "0%": { backgroundPosition: "-400px 0" }, "100%": { backgroundPosition: "400px 0" } },
        "slide-up": { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
  plugins: [],
};

export default config;
