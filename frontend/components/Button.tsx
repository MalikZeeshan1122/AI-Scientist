import { ButtonHTMLAttributes, forwardRef, ReactNode } from "react";
import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";
type Size = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-gradient-to-b from-orange-500 to-orange-600 hover:from-orange-400 hover:to-orange-600 text-white shadow-glow border border-orange-400/30",
  secondary:
    "bg-[var(--bg-card)] text-ink-50 hover:bg-ink-800 border border-ink-700",
  ghost:
    "bg-transparent text-ink-300 hover:text-ink-50 hover:bg-ink-800 border border-transparent",
  danger:
    "bg-rose-500/90 hover:bg-rose-500 text-white border border-rose-400/30",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 px-3 text-xs gap-1.5 rounded-lg",
  md: "h-9 px-4 text-sm gap-2 rounded-xl",
  lg: "h-11 px-5 text-sm gap-2 rounded-xl",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    children,
    variant = "primary",
    size = "md",
    loading = false,
    leftIcon,
    rightIcon,
    className = "",
    disabled,
    ...rest
  },
  ref
) {
  const isDisabled = disabled || loading;
  return (
    <button
      ref={ref}
      disabled={isDisabled}
      className={cn(
        "inline-flex items-center justify-center font-medium tracking-tight transition-all duration-150 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:active:scale-100",
        VARIANTS[variant],
        SIZES[size],
        className
      )}
      {...rest}
    >
      {loading ? (
        <Spinner />
      ) : (
        leftIcon && <span className="shrink-0 -ml-0.5">{leftIcon}</span>
      )}
      <span className="truncate">{children}</span>
      {!loading && rightIcon && (
        <span className="shrink-0 -mr-0.5">{rightIcon}</span>
      )}
    </button>
  );
});

function Spinner() {
  return (
    <svg
      className="animate-spin h-3.5 w-3.5"
      viewBox="0 0 24 24"
      fill="none"
    >
      <circle
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeOpacity="0.25"
        strokeWidth="3"
      />
      <path
        d="M22 12a10 10 0 0 1-10 10"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
    </svg>
  );
}
