import { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function StatTile({
  label,
  value,
  icon,
  hint,
  trend,
  tone = "default",
  className = "",
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  hint?: ReactNode;
  trend?: { value: string; positive?: boolean };
  tone?: "default" | "accent" | "success" | "warn" | "danger";
  className?: string;
}) {
  const accentRing: Record<string, string> = {
    default: "from-ink-800 to-transparent",
    accent: "from-orange-500/20 to-orange-500/0",
    success: "from-emerald-500/30 to-emerald-500/0",
    warn: "from-amber-500/30 to-amber-500/0",
    danger: "from-rose-500/30 to-rose-500/0",
  };
  const iconBg: Record<string, string> = {
    default: "bg-ink-800 text-ink-300 border-ink-700",
    accent: "bg-orange-500/12 text-orange-500 border-orange-500/25",
    success: "bg-emerald-500/12 text-emerald-600 border-emerald-500/25",
    warn: "bg-amber-500/12 text-amber-600 border-amber-500/25",
    danger: "bg-rose-500/12 text-rose-600 border-rose-500/25",
  };
  return (
    <div
      className={cn(
        "relative overflow-hidden glass rounded-2xl p-5 hover-lift hover:border-ink-600",
        className
      )}
    >
      <div
        className={cn(
          "pointer-events-none absolute -top-12 -right-12 h-32 w-32 rounded-full bg-gradient-radial blur-2xl opacity-60 bg-gradient-to-br",
          accentRing[tone]
        )}
      />
      <div className="relative flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[11px] uppercase tracking-wider text-ink-400 font-medium">
            {label}
          </div>
          <div className="mt-1 text-2xl font-semibold tracking-tight text-ink-50 tabular-nums">
            {value}
          </div>
          {(hint || trend) && (
            <div className="mt-1.5 flex items-center gap-2 text-[11px]">
              {trend && (
                <span
                  className={cn(
                    "inline-flex items-center gap-0.5 font-medium",
                    trend.positive ? "text-emerald-600" : "text-rose-600"
                  )}
                >
                  {trend.positive ? "▲" : "▼"} {trend.value}
                </span>
              )}
              {hint && <span className="text-ink-500">{hint}</span>}
            </div>
          )}
        </div>
        {icon && (
          <div
            className={cn(
              "shrink-0 grid place-items-center h-10 w-10 rounded-xl border",
              iconBg[tone]
            )}
          >
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
