import { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function EmptyState({
  icon,
  title,
  description,
  action,
  className = "",
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "glass rounded-2xl p-10 text-center flex flex-col items-center justify-center",
        className
      )}
    >
      {icon && (
        <div className="mb-4 grid place-items-center h-14 w-14 rounded-2xl bg-gradient-to-br from-orange-500/12 to-amber-500/6 border border-orange-500/20 text-orange-500">
          {icon}
        </div>
      )}
      <div className="text-base font-semibold text-ink-50 tracking-tight">
        {title}
      </div>
      {description && (
        <div className="text-sm text-ink-400 mt-1 max-w-md">{description}</div>
      )}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
