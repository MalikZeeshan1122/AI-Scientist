"use client";

import { useEffect, useState } from "react";
import {
  Check,
  ChevronDown,
  ChevronUp,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { useToast } from "@/components/Toast";
import { cn } from "@/lib/cn";

type ProviderInfo = {
  configured: boolean;
  key_preview: string | null;
  model?: string;
};

type CustomKey = {
  name: string;
  configured: boolean;
  key_preview: string | null;
};

type SettingsResponse = {
  providers: {
    anthropic: ProviderInfo;
    google: ProviderInfo;
    groq: ProviderInfo;
    openai: ProviderInfo;
    openrouter: ProviderInfo;
  };
  search: {
    tavily: ProviderInfo;
    semantic_scholar: ProviderInfo;
  };
  custom_keys: CustomKey[];
  default_provider: string;
  custom_key_pattern: string;
};

type Slot = {
  envKey: string;
  label: string;
  shortLabel: string;
  hint: string;
  group: keyof SettingsResponse["providers"] | keyof SettingsResponse["search"] | "__custom__";
  category: "llm" | "search" | "custom";
};

const CUSTOM_SLOT_KEY = "__custom__";

const SLOTS: Slot[] = [
  {
    envKey: "OPENAI_API_KEY",
    label: "OpenAI",
    shortLabel: "openai",
    hint: "sk-…",
    group: "openai",
    category: "llm",
  },
  {
    envKey: "OPENROUTER_API_KEY",
    label: "OpenRouter",
    shortLabel: "openrouter",
    hint: "sk-or-…",
    group: "openrouter",
    category: "llm",
  },
  {
    envKey: "ANTHROPIC_API_KEY",
    label: "Anthropic (Claude)",
    shortLabel: "anthropic",
    hint: "sk-ant-…",
    group: "anthropic",
    category: "llm",
  },
  {
    envKey: "GOOGLE_API_KEY",
    label: "Google (Gemini)",
    shortLabel: "google",
    hint: "AIza…",
    group: "google",
    category: "llm",
  },
  {
    envKey: "GROQ_API_KEY",
    label: "Groq",
    shortLabel: "groq",
    hint: "gsk_…",
    group: "groq",
    category: "llm",
  },
  {
    envKey: "TAVILY_API_KEY",
    label: "Tavily web search",
    shortLabel: "tavily",
    hint: "tvly-…",
    group: "tavily",
    category: "search",
  },
  {
    envKey: "SEMANTIC_SCHOLAR_API_KEY",
    label: "Semantic Scholar",
    shortLabel: "s2",
    hint: "optional",
    group: "semantic_scholar",
    category: "search",
  },
  {
    envKey: CUSTOM_SLOT_KEY,
    label: "Custom key",
    shortLabel: "custom",
    hint: "MY_PROVIDER_API_KEY",
    group: "__custom__",
    category: "custom",
  },
];

const CUSTOM_NAME_PATTERN = /^[A-Z][A-Z0-9_]{1,64}_API_KEY$/;

export function SidebarApiKeys() {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState<SettingsResponse | null>(null);
  const [slot, setSlot] = useState<string>("OPENAI_API_KEY");
  const [customName, setCustomName] = useState("");
  const [value, setValue] = useState("");
  const [reveal, setReveal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [justSaved, setJustSaved] = useState(false);
  const toast = useToast();

  const refresh = async () => {
    try {
      const s = await api<SettingsResponse>("/settings");
      setData(s);
    } catch {
      // Ignore — backend may be down; the rest of the UI handles that.
    }
  };

  useEffect(() => {
    if (open && !data) refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // Refresh status dots even when collapsed so the user sees what's configured.
  useEffect(() => {
    refresh();
  }, []);

  const isConfigured = (s: Slot): boolean => {
    if (!data) return false;
    if (s.category === "llm") {
      return Boolean(data.providers[s.group as keyof typeof data.providers]?.configured);
    }
    if (s.category === "search") {
      return Boolean(data.search[s.group as keyof typeof data.search]?.configured);
    }
    // custom slot is "configured" when at least one custom key exists
    return (data.custom_keys?.length ?? 0) > 0;
  };

  const configuredCount = data
    ? SLOTS.filter((s) => s.category !== "custom" && isConfigured(s)).length +
      (data.custom_keys?.length ?? 0)
    : 0;

  const isCustom = slot === CUSTOM_SLOT_KEY;
  const targetEnvKey = isCustom ? customName.trim().toUpperCase() : slot;
  const customNameValid = !isCustom || CUSTOM_NAME_PATTERN.test(targetEnvKey);
  const canSave =
    Boolean(value.trim()) && customNameValid && (!isCustom || targetEnvKey.length > 0);

  const save = async () => {
    if (!canSave) return;
    setSaving(true);
    try {
      const next = await api<SettingsResponse>("/settings", {
        method: "POST",
        body: JSON.stringify({ updates: { [targetEnvKey]: value.trim() } }),
      });
      setData(next);
      setValue("");
      if (isCustom) setCustomName("");
      setReveal(false);
      setJustSaved(true);
      toast.success(
        isCustom ? `${targetEnvKey} saved` : `${slotLabel(slot)} key saved`,
        "Updated .env"
      );
      setTimeout(() => setJustSaved(false), 1800);
    } catch (e) {
      toast.error(String(e), "Couldn't save key");
    } finally {
      setSaving(false);
    }
  };

  const removeCustom = async (name: string) => {
    setSaving(true);
    try {
      const next = await api<SettingsResponse>("/settings", {
        method: "POST",
        body: JSON.stringify({ updates: { [name]: "" } }),
      });
      setData(next);
      toast.success(`${name} cleared`);
    } catch (e) {
      toast.error(String(e), "Couldn't clear key");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="rounded-xl border border-ink-700 bg-[var(--bg-card)] overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between gap-2 px-3 py-2 text-left hover:bg-ink-800 transition-colors"
        aria-expanded={open}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="grid place-items-center h-6 w-6 rounded-md bg-orange-500/10 border border-orange-500/30 text-orange-600 shrink-0">
            <KeyRound className="h-3 w-3" />
          </div>
          <div className="min-w-0">
            <div className="text-[12px] font-semibold text-ink-50 leading-tight tracking-tight">
              API keys
            </div>
            <div className="text-[10px] text-ink-400 leading-tight">
              {data ? `${configuredCount}/${SLOTS.length} configured` : "Loading…"}
            </div>
          </div>
        </div>
        {open ? (
          <ChevronUp className="h-3.5 w-3.5 text-ink-400 shrink-0" />
        ) : (
          <ChevronDown className="h-3.5 w-3.5 text-ink-400 shrink-0" />
        )}
      </button>

      {open && (
        <div className="px-3 pb-3 pt-1 space-y-2 border-t border-ink-700">
          <div className="flex flex-wrap gap-1 mt-2">
            {SLOTS.map((s) => {
              const ok = isConfigured(s);
              const active = slot === s.envKey;
              return (
                <button
                  key={s.envKey}
                  type="button"
                  onClick={() => setSlot(s.envKey)}
                  title={s.label}
                  className={cn(
                    "inline-flex items-center gap-1 text-[10px] font-mono px-1.5 py-0.5 rounded border transition",
                    active
                      ? "bg-orange-500/15 text-orange-700 border-orange-500/40"
                      : "bg-ink-850 text-ink-300 border-ink-700 hover:border-ink-600 hover:text-ink-50"
                  )}
                >
                  <span
                    className={cn(
                      "h-1.5 w-1.5 rounded-full",
                      ok ? "bg-emerald-500" : "bg-ink-500"
                    )}
                  />
                  {s.shortLabel}
                </button>
              );
            })}
          </div>

          {isCustom && (
            <div>
              <label
                htmlFor="sidebar-api-key-name"
                className="block text-[10px] uppercase tracking-wider text-ink-400 font-medium mb-1"
              >
                Env-var name
              </label>
              <input
                id="sidebar-api-key-name"
                type="text"
                value={customName}
                onChange={(e) => setCustomName(e.target.value.toUpperCase())}
                placeholder="MY_PROVIDER_API_KEY"
                autoComplete="off"
                spellCheck={false}
                className={cn(
                  "w-full h-8 bg-[var(--bg-page)] border rounded-md text-[12px] font-mono text-ink-50 placeholder:text-ink-500",
                  "px-2 outline-none transition-colors",
                  customName && !customNameValid
                    ? "border-rose-500/60 focus:shadow-[0_0_0_2px_rgba(244,63,94,0.18)]"
                    : "border-ink-700 focus:border-orange-400/70 focus:shadow-[0_0_0_2px_rgba(249,115,22,0.18)]"
                )}
                style={{
                  color: "rgb(var(--ink-50))",
                  caretColor: "rgb(var(--ink-50))",
                }}
              />
              <div
                className={cn(
                  "text-[10px] mt-1",
                  customName && !customNameValid
                    ? "text-rose-600"
                    : "text-ink-400"
                )}
              >
                {customName && !customNameValid
                  ? "Must be uppercase, end in _API_KEY (e.g. COHERE_API_KEY)."
                  : "Use UPPER_SNAKE_CASE ending in _API_KEY."}
              </div>
            </div>
          )}

          <div>
            <label
              htmlFor="sidebar-api-key"
              className="block text-[10px] uppercase tracking-wider text-ink-400 font-medium mb-1"
            >
              {isCustom
                ? targetEnvKey || "Custom key"
                : `${slotLabel(slot)} key`}
            </label>
            <div className="relative">
              <input
                id="sidebar-api-key"
                type={reveal ? "text" : "password"}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && canSave) save();
                }}
                placeholder={hintForSlot(slot)}
                autoComplete="off"
                spellCheck={false}
                className={cn(
                  "w-full h-8 bg-[var(--bg-page)] border border-ink-700 rounded-md text-[12px] text-ink-50 placeholder:text-ink-500",
                  "px-2 pr-7 outline-none transition-colors",
                  "focus:border-orange-400/70 focus:shadow-[0_0_0_2px_rgba(249,115,22,0.18)]"
                )}
                style={{
                  color: "rgb(var(--ink-50))",
                  caretColor: "rgb(var(--ink-50))",
                }}
              />
              <button
                type="button"
                onClick={() => setReveal((r) => !r)}
                aria-label={reveal ? "Hide key" : "Reveal key"}
                className="absolute right-1.5 top-1/2 -translate-y-1/2 text-ink-400 hover:text-ink-50 p-0.5 rounded"
              >
                {reveal ? (
                  <EyeOff className="h-3 w-3" />
                ) : (
                  <Eye className="h-3 w-3" />
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={save}
              disabled={!canSave || saving}
              className={cn(
                "flex-1 inline-flex items-center justify-center gap-1 h-8 rounded-md text-[12px] font-semibold transition",
                canSave && !saving
                  ? "bg-orange-500 text-white hover:bg-orange-600"
                  : "bg-ink-800 text-ink-500 cursor-not-allowed"
              )}
            >
              {saving ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : justSaved ? (
                <Check className="h-3 w-3" />
              ) : (
                <Plus className="h-3 w-3" />
              )}
              {saving ? "Saving…" : justSaved ? "Saved" : "Save key"}
            </button>
          </div>

          {/* Live "current value" preview for the selected slot */}
          {!isCustom && (() => {
            const s = SLOTS.find((x) => x.envKey === slot);
            if (!s || !data) return null;
            const info =
              s.category === "llm"
                ? data.providers[s.group as keyof typeof data.providers]
                : data.search[s.group as keyof typeof data.search];
            if (!info?.key_preview) return null;
            return (
              <div className="text-[10px] text-ink-400 font-mono truncate">
                current: {info.key_preview}
              </div>
            );
          })()}

          {/* Existing custom keys list (auto-detected from .env) */}
          {data && data.custom_keys && data.custom_keys.length > 0 && (
            <div className="space-y-1 pt-1 border-t border-ink-700">
              <div className="text-[10px] uppercase tracking-wider text-ink-400 font-medium pt-1">
                Custom keys
              </div>
              {data.custom_keys.map((c) => (
                <div
                  key={c.name}
                  className="flex items-center gap-1.5 text-[10px]"
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
                  <span className="font-mono text-ink-200 truncate">
                    {c.name}
                  </span>
                  <span className="font-mono text-ink-400 truncate">
                    {c.key_preview ?? ""}
                  </span>
                  <button
                    type="button"
                    onClick={() => removeCustom(c.name)}
                    title={`Clear ${c.name}`}
                    className="ml-auto text-ink-400 hover:text-rose-600 transition shrink-0 p-0.5"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <Link
            href="/settings"
            className="block text-center text-[10px] text-ink-400 hover:text-orange-600 underline-offset-2 hover:underline pt-1"
          >
            Manage all keys & providers →
          </Link>
        </div>
      )}
    </div>
  );
}

function slotLabel(key: string): string {
  return SLOTS.find((s) => s.envKey === key)?.label ?? key;
}

function hintForSlot(key: string): string {
  return SLOTS.find((s) => s.envKey === key)?.hint ?? "";
}
