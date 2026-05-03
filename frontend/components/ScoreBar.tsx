import { cn } from "@/lib/cn";

export function ScoreBar({
  label,
  value,
  max = 5,
  className = "",
}: {
  label: string;
  value: number;
  max?: number;
  className?: string;
}) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  const tone =
    pct >= 80
      ? "from-emerald-400 to-emerald-500"
      : pct >= 60
        ? "from-orange-400 to-amber-500"
        : pct >= 40
          ? "from-amber-400 to-orange-500"
          : "from-rose-400 to-rose-500";
  return (
    <div className={cn("w-full", className)}>
      <div className="flex items-center justify-between mb-1">
        <div className="text-[11px] uppercase tracking-wider text-ink-400 font-medium">
          {label}
        </div>
        <div className="text-xs font-mono tabular-nums text-ink-100">
          {value.toFixed(1)}
          <span className="text-ink-500">/{max}</span>
        </div>
      </div>
      <div className="h-1.5 w-full rounded-full bg-ink-800 overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full bg-gradient-to-r transition-all duration-500",
            tone
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export function CircularScore({
  value,
  max = 5,
  size = 56,
  label = "score",
}: {
  value: number;
  max?: number;
  size?: number;
  label?: string;
}) {
  const pct = Math.max(0, Math.min(1, value / max));
  const r = size / 2 - 4;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - pct);
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <defs>
          <linearGradient id="scoreGrad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#fb923c" />
            <stop offset="100%" stopColor="#f59e0b" />
          </linearGradient>
        </defs>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          className="stroke-ink-700"
          strokeWidth="3"
          fill="none"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          stroke="url(#scoreGrad)"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 600ms ease" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center">
        <div className="text-center leading-none">
          <div className="text-base font-semibold tabular-nums text-ink-50">
            {value.toFixed(1)}
          </div>
          <div className="text-[8px] uppercase tracking-wider text-ink-500 mt-0.5">
            {label}
          </div>
        </div>
      </div>
    </div>
  );
}
