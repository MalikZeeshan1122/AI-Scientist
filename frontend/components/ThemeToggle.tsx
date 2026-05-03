"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Moon, Sun } from "lucide-react";
import { cn } from "@/lib/cn";

export function ThemeToggle() {
  const { theme, setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return (
      <div
        aria-hidden
        className="h-8 rounded-lg border border-ink-700 bg-ink-850"
      />
    );
  }

  const current = (theme === "system" ? resolvedTheme : theme) ?? "light";

  return (
    <div
      role="group"
      aria-label="Theme"
      className="relative grid grid-cols-2 h-8 rounded-lg border border-ink-700 bg-ink-850 p-0.5"
    >
      <span
        aria-hidden
        className={cn(
          "absolute top-0.5 bottom-0.5 left-0.5 w-[calc(50%-2px)] rounded-md bg-[var(--bg-card)] border border-ink-700 transition-transform duration-200 ease-out",
          current === "dark" && "translate-x-full"
        )}
      />
      <button
        type="button"
        onClick={() => setTheme("light")}
        aria-pressed={current === "light"}
        className={cn(
          "relative z-10 inline-flex items-center justify-center gap-1.5 text-[11px] font-medium tracking-tight rounded-md transition-colors",
          current === "light" ? "text-ink-50" : "text-ink-400 hover:text-ink-200"
        )}
      >
        <Sun className="h-3.5 w-3.5" strokeWidth={2.2} />
        Light
      </button>
      <button
        type="button"
        onClick={() => setTheme("dark")}
        aria-pressed={current === "dark"}
        className={cn(
          "relative z-10 inline-flex items-center justify-center gap-1.5 text-[11px] font-medium tracking-tight rounded-md transition-colors",
          current === "dark" ? "text-ink-50" : "text-ink-400 hover:text-ink-200"
        )}
      >
        <Moon className="h-3.5 w-3.5" strokeWidth={2.2} />
        Dark
      </button>
    </div>
  );
}
