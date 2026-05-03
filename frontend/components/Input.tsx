import { forwardRef, InputHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  hint?: string;
  leftIcon?: ReactNode;
  rightSlot?: ReactNode;
  containerClassName?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
  {
    label,
    hint,
    leftIcon,
    rightSlot,
    className = "",
    containerClassName = "",
    id,
    ...rest
  },
  ref
) {
  const inputId = id || rest.name;
  return (
    <div className={cn("w-full", containerClassName)}>
      {label && (
        <label
          htmlFor={inputId}
          className="block text-[11px] uppercase tracking-wider text-ink-400 font-medium mb-1.5"
        >
          {label}
        </label>
      )}
      <div className="relative group">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-400 group-focus-within:text-orange-500 transition-colors pointer-events-none">
            {leftIcon}
          </div>
        )}
        <input
          ref={ref}
          id={inputId}
          className={cn(
            "w-full h-10 bg-[var(--bg-card)] border border-ink-700 rounded-xl text-sm text-ink-50 placeholder:text-ink-500",
            "px-3.5 py-2 outline-none transition-colors duration-150",
            "hover:border-ink-600 hover:bg-ink-800",
            "focus:border-orange-400/70 focus:bg-[var(--bg-card)] focus:shadow-[0_0_0_3px_rgba(249,115,22,0.18)]",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            leftIcon && "pl-9",
            rightSlot && "pr-9",
            className
          )}
          style={{ color: "rgb(var(--ink-50))", caretColor: "rgb(var(--ink-50))" }}
          {...rest}
        />
        {rightSlot && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-500">
            {rightSlot}
          </div>
        )}
      </div>
      {hint && <div className="text-[11px] text-ink-400 mt-1.5">{hint}</div>}
    </div>
  );
});
