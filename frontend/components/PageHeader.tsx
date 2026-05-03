import { ReactNode } from "react";
import { cn } from "@/lib/cn";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className = "",
}: {
  eyebrow?: ReactNode;
  title: ReactNode;
  description?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "mb-8 flex items-end justify-between gap-4 flex-wrap",
        className
      )}
    >
      <div>
        {eyebrow && (
          <div className="text-[11px] uppercase tracking-[0.18em] text-orange-500 mb-2 font-medium">
            {eyebrow}
          </div>
        )}
        <h1 className="text-[2.25rem] leading-[1.1] font-semibold tracking-tight text-gradient">
          {title}
        </h1>
        {description && (
          <p className="text-ink-400 mt-2 max-w-2xl text-sm leading-relaxed">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  );
}
