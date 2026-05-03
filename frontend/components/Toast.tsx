"use client";

import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import { cn } from "@/lib/cn";

export type ToastTone = "info" | "success" | "warn" | "danger";

type Toast = {
  id: string;
  title?: string;
  message: string;
  tone: ToastTone;
};

type ToastContextValue = {
  push: (t: Omit<Toast, "id">) => string;
  success: (msg: string, title?: string) => string;
  error: (msg: string, title?: string) => string;
  info: (msg: string, title?: string) => string;
  warn: (msg: string, title?: string) => string;
  dismiss: (id: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used inside <ToastProvider>");
  }
  return ctx;
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((ts) => ts.filter((t) => t.id !== id));
  }, []);

  const push: ToastContextValue["push"] = useCallback((t) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((ts) => [...ts, { id, ...t }]);
    return id;
  }, []);

  const value: ToastContextValue = {
    push,
    dismiss,
    success: (message, title) => push({ message, title, tone: "success" }),
    error: (message, title) => push({ message, title, tone: "danger" }),
    info: (message, title) => push({ message, title, tone: "info" }),
    warn: (message, title) => push({ message, title, tone: "warn" }),
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} dismiss={dismiss} />
    </ToastContext.Provider>
  );
}

function ToastViewport({
  toasts,
  dismiss,
}: {
  toasts: Toast[];
  dismiss: (id: string) => void;
}) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-full max-w-sm flex-col gap-2">
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} dismiss={dismiss} />
      ))}
    </div>
  );
}

const TONE_STYLE: Record<ToastTone, { border: string; icon: ReactNode; iconColor: string }> = {
  info: {
    border: "border-sky-500/30 bg-sky-500/[0.06]",
    icon: <Info className="h-4 w-4" />,
    iconColor: "text-sky-600",
  },
  success: {
    border: "border-emerald-500/30 bg-emerald-500/[0.06]",
    icon: <CheckCircle2 className="h-4 w-4" />,
    iconColor: "text-emerald-600",
  },
  warn: {
    border: "border-amber-500/30 bg-amber-500/[0.06]",
    icon: <AlertTriangle className="h-4 w-4" />,
    iconColor: "text-amber-600",
  },
  danger: {
    border: "border-rose-500/30 bg-rose-500/[0.06]",
    icon: <XCircle className="h-4 w-4" />,
    iconColor: "text-rose-600",
  },
};

function ToastItem({
  toast,
  dismiss,
}: {
  toast: Toast;
  dismiss: (id: string) => void;
}) {
  const style = TONE_STYLE[toast.tone];

  useEffect(() => {
    const ms = toast.tone === "danger" ? 8000 : 4500;
    const timer = setTimeout(() => dismiss(toast.id), ms);
    return () => clearTimeout(timer);
  }, [toast.id, toast.tone, dismiss]);

  return (
    <div
      role="status"
      className={cn(
        "pointer-events-auto animate-slide-up rounded-xl p-3.5 pr-3 border bg-[var(--bg-card)]",
        "shadow-[0_8px_24px_rgba(0,0,0,0.10)]",
        style.border
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn("mt-0.5 shrink-0", style.iconColor)}>{style.icon}</div>
        <div className="min-w-0 flex-1">
          {toast.title && (
            <div className="text-sm font-semibold text-ink-50 tracking-tight">
              {toast.title}
            </div>
          )}
          <div className="text-xs text-ink-300 leading-relaxed break-words">
            {toast.message}
          </div>
        </div>
        <button
          onClick={() => dismiss(toast.id)}
          className="shrink-0 -mr-1 -mt-1 p-1 text-ink-400 hover:text-ink-50 rounded hover:bg-ink-800 transition"
          aria-label="Dismiss"
        >
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
