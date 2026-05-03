import { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function Card({
  children,
  className = "",
  interactive = false,
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
}) {
  return (
    <div
      className={cn(
        "glass rounded-2xl p-5 shadow-card",
        interactive && "hover-lift hover:border-ink-600 cursor-pointer",
        className
      )}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  title,
  subtitle,
  right,
  icon,
}: {
  title: ReactNode;
  subtitle?: ReactNode;
  right?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3 mb-4">
      <div className="flex items-start gap-3 min-w-0">
        {icon && (
          <div className="mt-0.5 shrink-0 grid place-items-center h-9 w-9 rounded-xl bg-gradient-to-br from-orange-500/15 to-amber-500/8 border border-orange-500/20 text-orange-500">
            {icon}
          </div>
        )}
        <div className="min-w-0">
          <div className="text-sm font-semibold text-ink-50 tracking-tight truncate">
            {title}
          </div>
          {subtitle && (
            <div className="text-xs text-ink-400 mt-0.5 truncate">{subtitle}</div>
          )}
        </div>
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}

type Tone = "default" | "success" | "warn" | "danger" | "accent" | "info";

export function Badge({
  children,
  tone = "default",
  dot = false,
  className = "",
}: {
  children: ReactNode;
  tone?: Tone;
  dot?: boolean;
  className?: string;
}) {
  const toneClasses: Record<Tone, string> = {
    default: "bg-ink-800 text-ink-300 border border-ink-700",
    success:
      "bg-emerald-500/10 text-emerald-700 border border-emerald-500/25",
    warn: "bg-amber-500/10 text-amber-700 border border-amber-500/25",
    danger: "bg-rose-500/10 text-rose-700 border border-rose-500/25",
    accent:
      "bg-gradient-to-r from-orange-500/12 to-amber-500/8 text-orange-600 border border-orange-500/25",
    info: "bg-sky-500/10 text-sky-600 border border-sky-500/30",
  };
  const dotClasses: Record<Tone, string> = {
    default: "bg-ink-400",
    success: "bg-emerald-500 shadow-[0_0_6px] shadow-emerald-500/50",
    warn: "bg-amber-500 shadow-[0_0_6px] shadow-amber-500/50",
    danger: "bg-rose-500 shadow-[0_0_6px] shadow-rose-500/50",
    accent: "bg-orange-500 shadow-[0_0_6px] shadow-orange-500/50",
    info: "bg-sky-500 shadow-[0_0_6px] shadow-sky-500/50",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-[10.5px] uppercase tracking-wider font-medium px-2 py-0.5 rounded-full whitespace-nowrap",
        toneClasses[tone],
        className
      )}
    >
      {dot && <span className={cn("h-1.5 w-1.5 rounded-full", dotClasses[tone])} />}
      {children}
    </span>
  );
}
