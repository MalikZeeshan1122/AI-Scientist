import { ReactNode } from "react";
import { Check } from "lucide-react";
import { cn } from "@/lib/cn";

export type StepStatus = "pending" | "active" | "complete" | "error";

export type Step = {
  id: string;
  label: string;
  description?: string;
  icon?: ReactNode;
  status: StepStatus;
};

export function Stepper({ steps }: { steps: Step[] }) {
  return (
    <ol className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
      {steps.map((s, i) => (
        <li key={s.id} className="relative">
          <div
          className={cn(
            "h-full rounded-xl border p-4 transition-colors duration-200",
            s.status === "complete" &&
              "border-emerald-500/30 bg-emerald-500/[0.06]",
            s.status === "active" &&
              "border-orange-500/40 bg-orange-500/[0.08] shadow-glow",
            s.status === "pending" &&
              "border-ink-700 bg-ink-850",
            s.status === "error" &&
              "border-rose-500/30 bg-rose-500/[0.06]"
          )}
          >
            <div className="flex items-center gap-2 mb-2">
              <StepIndicator index={i + 1} status={s.status} icon={s.icon} />
              <div
                className={cn(
                  "text-[10px] uppercase tracking-wider font-medium",
                  s.status === "complete" && "text-emerald-600",
                  s.status === "active" && "text-orange-600",
                  s.status === "pending" && "text-ink-400",
                  s.status === "error" && "text-rose-600"
                )}
              >
                Step {i + 1}
              </div>
            </div>
            <div className="text-sm font-semibold text-ink-50 tracking-tight">
              {s.label}
            </div>
            {s.description && (
              <div className="text-xs text-ink-300 mt-1 leading-relaxed line-clamp-2">
                {s.description}
              </div>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}

function StepIndicator({
  index,
  status,
  icon,
}: {
  index: number;
  status: StepStatus;
  icon?: ReactNode;
}) {
  if (status === "complete") {
    return (
      <div className="h-6 w-6 rounded-full bg-emerald-500/15 border border-emerald-500/40 grid place-items-center text-emerald-600">
        <Check className="h-3.5 w-3.5" strokeWidth={3} />
      </div>
    );
  }
  if (status === "active") {
    return (
      <div className="relative h-6 w-6 rounded-full border border-orange-500/50 bg-orange-500/15 grid place-items-center text-orange-600 text-[11px] font-semibold">
        {icon ?? index}
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="h-6 w-6 rounded-full bg-rose-500/15 border border-rose-500/40 grid place-items-center text-rose-600 text-[11px] font-semibold">
        !
      </div>
    );
  }
  return (
    <div className="h-6 w-6 rounded-full bg-ink-800 border border-ink-700 grid place-items-center text-ink-400 text-[11px] font-semibold">
      {icon ?? index}
    </div>
  );
}
