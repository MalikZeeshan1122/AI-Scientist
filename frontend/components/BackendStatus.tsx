"use client";

import { useEffect, useState } from "react";
import { API_BASE } from "@/lib/api";
import { cn } from "@/lib/cn";

type Status = "checking" | "online" | "offline";

export function BackendStatus() {
  const [status, setStatus] = useState<Status>("checking");

  useEffect(() => {
    let alive = true;

    const ping = async () => {
      try {
        const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
        if (!alive) return;
        setStatus(res.ok ? "online" : "offline");
      } catch {
        if (!alive) return;
        setStatus("offline");
      }
    };

    ping();
    const id = setInterval(ping, 15000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  const dot =
    status === "online"
      ? "bg-emerald-500"
      : status === "offline"
        ? "bg-rose-500"
        : "bg-amber-500";

  const label =
    status === "online" ? "Online" : status === "offline" ? "Offline" : "Checking…";

  return (
    <div className="rounded-lg border border-ink-700 bg-ink-850 px-3 py-2 flex items-center justify-between gap-2">
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-ink-500 font-medium">
          Backend
        </div>
        <div className="text-[11px] font-mono text-ink-200 truncate mt-0.5">{API_BASE}</div>
      </div>
      <div className="flex items-center gap-1.5 shrink-0">
        <span className={cn("h-2 w-2 rounded-full", dot)} />
        <span className="text-[11px] text-ink-300 font-medium">{label}</span>
      </div>
    </div>
  );
}
