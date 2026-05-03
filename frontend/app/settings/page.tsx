"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Eye,
  EyeOff,
  Globe,
  KeyRound,
  Plus,
  Save,
  Shield,
  Sparkles,
  Trash2,
} from "lucide-react";
import { Badge, Card, CardHeader } from "@/components/Card";
import { Button } from "@/components/Button";
import { Input } from "@/components/Input";
import { PageHeader } from "@/components/PageHeader";
import { useToast } from "@/components/Toast";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";

type ProviderInfo = {
  configured: boolean;
  key_preview: string | null;
  model: string;
};

type SearchInfo = {
  configured: boolean;
  key_preview: string | null;
};

type CustomKeyEntry = {
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
    tavily: SearchInfo;
    semantic_scholar: SearchInfo;
  };
  custom_keys: CustomKeyEntry[];
  default_provider: "anthropic" | "google" | "groq" | "openai" | "openrouter";
  editable_keys: string[];
  custom_key_pattern: string;
};

type ProviderKey = keyof SettingsResponse["providers"];

const PROVIDER_META: Record<
  ProviderKey,
  {
    label: string;
    keyEnv: string;
    modelEnv: string;
    docs: string;
    notes: string;
    placeholderModel: string;
  }
> = {
  anthropic: {
    label: "Anthropic (Claude)",
    keyEnv: "ANTHROPIC_API_KEY",
    modelEnv: "AI_SCIENTIST_ANTHROPIC_MODEL",
    docs: "https://console.anthropic.com/settings/keys",
    notes: "Best long-form reasoning; paid tier.",
    placeholderModel: "claude-3-5-sonnet-latest",
  },
  google: {
    label: "Google (Gemini)",
    keyEnv: "GOOGLE_API_KEY",
    modelEnv: "AI_SCIENTIST_GOOGLE_MODEL",
    docs: "https://aistudio.google.com/app/apikey",
    notes: "Generous free tier; rate-limit hard.",
    placeholderModel: "gemini-2.0-flash",
  },
  groq: {
    label: "Groq",
    keyEnv: "GROQ_API_KEY",
    modelEnv: "AI_SCIENTIST_GROQ_MODEL",
    docs: "https://console.groq.com/keys",
    notes: "Very fast Llama-3.3 inference; free.",
    placeholderModel: "llama-3.3-70b-versatile",
  },
  openai: {
    label: "OpenAI",
    keyEnv: "OPENAI_API_KEY",
    modelEnv: "AI_SCIENTIST_OPENAI_MODEL",
    docs: "https://platform.openai.com/api-keys",
    notes: "Direct OpenAI API; pay-as-you-go.",
    placeholderModel: "gpt-4o-mini",
  },
  openrouter: {
    label: "OpenRouter",
    keyEnv: "OPENROUTER_API_KEY",
    modelEnv: "AI_SCIENTIST_OPENROUTER_MODEL",
    docs: "https://openrouter.ai/keys",
    notes: "Single key, many models; pay-as-you-go + free tier.",
    placeholderModel: "openai/gpt-4o-mini",
  },
};

const SEARCH_META = {
  tavily: {
    label: "Tavily web search",
    keyEnv: "TAVILY_API_KEY",
    docs: "https://app.tavily.com",
    notes: "Adds live web results to the Papers search.",
  },
  semantic_scholar: {
    label: "Semantic Scholar",
    keyEnv: "SEMANTIC_SCHOLAR_API_KEY",
    docs: "https://www.semanticscholar.org/product/api",
    notes: "Optional. Higher rate limits when set.",
  },
} as const;

export default function SettingsPage() {
  const [data, setData] = useState<SettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [updates, setUpdates] = useState<Record<string, string>>({});
  const [reveal, setReveal] = useState<Record<string, boolean>>({});
  const toast = useToast();

  const refresh = async () => {
    setLoading(true);
    try {
      const s = await api<SettingsResponse>("/settings");
      setData(s);
      setUpdates({});
    } catch (e) {
      toast.error(String(e), "Couldn't load settings");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setUpdate = (key: string, value: string) => {
    setUpdates((u) => ({ ...u, [key]: value }));
  };

  const clearKey = (envKey: string) => {
    setUpdate(envKey, "");
  };

  const dirty = useMemo(
    () => Object.keys(updates).filter((k) => updates[k] !== undefined).length,
    [updates]
  );

  const save = async () => {
    if (!dirty) return;
    setSaving(true);
    try {
      const next = await api<SettingsResponse>("/settings", {
        method: "POST",
        body: JSON.stringify({ updates }),
      });
      setData(next);
      setUpdates({});
      toast.success("Settings saved", `${dirty} key${dirty === 1 ? "" : "s"} updated`);
    } catch (e) {
      toast.error(String(e), "Couldn't save settings");
    } finally {
      setSaving(false);
    }
  };

  const setDefaultProvider = (provider: ProviderKey) => {
    setUpdate("AI_SCIENTIST_DEFAULT_PROVIDER", provider);
  };

  const stagedDefaultProvider =
    (updates["AI_SCIENTIST_DEFAULT_PROVIDER"] as ProviderKey | undefined) ??
    data?.default_provider;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Settings"
        title="API keys & providers"
        description="Add or rotate API keys without leaving the app. Values are written to your local .env and never displayed in full."
        actions={
          <Button
            onClick={save}
            disabled={!dirty || saving}
            loading={saving}
            leftIcon={<Save className="h-4 w-4" />}
          >
            {dirty ? `Save ${dirty} change${dirty === 1 ? "" : "s"}` : "Saved"}
          </Button>
        }
      />

      <SecurityNotice />

      <Card>
        <CardHeader
          icon={<Sparkles className="h-4 w-4" />}
          title="Default LLM provider"
          subtitle="Used by ideation, experiments, drafting, and refinement."
        />
        {loading || !data ? (
          <div className="text-sm text-ink-400">Loading…</div>
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
            {(Object.keys(PROVIDER_META) as ProviderKey[]).map((p) => {
              const info = data.providers[p];
              const active = stagedDefaultProvider === p;
              return (
                <button
                  key={p}
                  onClick={() => setDefaultProvider(p)}
                  className={cn(
                    "text-left rounded-xl border p-3 transition",
                    active
                      ? "border-orange-500/60 bg-orange-500/[0.06]"
                      : "border-ink-700 bg-[var(--bg-card)] hover:border-ink-600"
                  )}
                >
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <div className="text-sm font-semibold text-ink-50 tracking-tight">
                      {PROVIDER_META[p].label}
                    </div>
                    {info.configured ? (
                      <Badge tone="success" dot>
                        ready
                      </Badge>
                    ) : (
                      <Badge tone="default">no key</Badge>
                    )}
                  </div>
                  <div className="text-[11px] text-ink-400 font-mono truncate">
                    {info.model}
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </Card>

      <Card>
        <CardHeader
          icon={<KeyRound className="h-4 w-4" />}
          title="LLM provider keys"
          subtitle="Paste a key, hit Save. Leave blank to keep what's already on disk; clear to remove."
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {(Object.keys(PROVIDER_META) as ProviderKey[]).map((p) => (
            <ProviderRow
              key={p}
              provider={p}
              info={data?.providers[p]}
              modelOverride={updates[PROVIDER_META[p].modelEnv]}
              keyOverride={updates[PROVIDER_META[p].keyEnv]}
              revealed={reveal[PROVIDER_META[p].keyEnv]}
              onToggleReveal={() =>
                setReveal((r) => ({
                  ...r,
                  [PROVIDER_META[p].keyEnv]: !r[PROVIDER_META[p].keyEnv],
                }))
              }
              onKeyChange={(v) => setUpdate(PROVIDER_META[p].keyEnv, v)}
              onModelChange={(v) => setUpdate(PROVIDER_META[p].modelEnv, v)}
              onClear={() => clearKey(PROVIDER_META[p].keyEnv)}
            />
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader
          icon={<Globe className="h-4 w-4" />}
          title="Search providers"
          subtitle="Optional integrations that enrich the Papers search."
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {(Object.keys(SEARCH_META) as (keyof typeof SEARCH_META)[]).map((s) => (
            <SearchRow
              key={s}
              name={s}
              info={data?.search[s]}
              keyOverride={updates[SEARCH_META[s].keyEnv]}
              revealed={reveal[SEARCH_META[s].keyEnv]}
              onToggleReveal={() =>
                setReveal((r) => ({
                  ...r,
                  [SEARCH_META[s].keyEnv]: !r[SEARCH_META[s].keyEnv],
                }))
              }
              onKeyChange={(v) => setUpdate(SEARCH_META[s].keyEnv, v)}
              onClear={() => clearKey(SEARCH_META[s].keyEnv)}
            />
          ))}
        </div>
      </Card>

      <CustomKeysSection
        existing={data?.custom_keys ?? []}
        onAdd={async (name, val) => {
          if (!val.trim()) return;
          setSaving(true);
          try {
            const next = await api<SettingsResponse>("/settings", {
              method: "POST",
              body: JSON.stringify({ updates: { [name]: val.trim() } }),
            });
            setData(next);
            toast.success(`${name} added`, "Updated .env");
          } catch (e) {
            toast.error(String(e), "Couldn't save key");
          } finally {
            setSaving(false);
          }
        }}
        onRemove={async (name) => {
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
        }}
      />

      <div className="text-[11px] text-ink-400">
        Keys are written to <span className="font-mono">backend/.env</span> on this
        machine. The backend reloads them in-process on save — no restart needed.
      </div>
    </div>
  );
}

function SecurityNotice() {
  return (
    <Card className="border-amber-500/40 bg-amber-500/[0.04]">
      <div className="flex gap-3">
        <div className="grid place-items-center h-9 w-9 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-600 shrink-0">
          <Shield className="h-4 w-4" />
        </div>
        <div className="text-[13px] text-ink-200 leading-relaxed">
          <div className="font-semibold text-ink-50 mb-1">
            Treat keys like passwords
          </div>
          API keys grant billable access to your accounts. Never paste them into
          chat, screenshots, or version control. If you suspect a key has
          leaked, rotate it at the provider's dashboard immediately.
        </div>
      </div>
    </Card>
  );
}

function ProviderRow({
  provider,
  info,
  keyOverride,
  modelOverride,
  revealed,
  onToggleReveal,
  onKeyChange,
  onModelChange,
  onClear,
}: {
  provider: ProviderKey;
  info: ProviderInfo | undefined;
  keyOverride: string | undefined;
  modelOverride: string | undefined;
  revealed: boolean | undefined;
  onToggleReveal: () => void;
  onKeyChange: (v: string) => void;
  onModelChange: (v: string) => void;
  onClear: () => void;
}) {
  const meta = PROVIDER_META[provider];
  const status = info?.configured;
  const cleared = keyOverride === "";
  return (
    <div className="rounded-xl border border-ink-700 bg-[var(--bg-card)] p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="text-sm font-semibold text-ink-50 tracking-tight">
              {meta.label}
            </div>
            {status ? (
              <Badge tone="success" dot>
                configured
              </Badge>
            ) : (
              <Badge tone="default">not set</Badge>
            )}
          </div>
          <p className="text-[11px] text-ink-400 mt-0.5">{meta.notes}</p>
        </div>
        <a
          href={meta.docs}
          target="_blank"
          rel="noreferrer"
          className="text-[11px] text-orange-600 hover:text-orange-700 underline-offset-2 hover:underline shrink-0"
        >
          Get key
        </a>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-[11px] uppercase tracking-wider text-ink-400 font-medium">
            API key
          </label>
          {info?.key_preview && !keyOverride && (
            <span className="text-[11px] text-ink-400 font-mono">
              current: {info.key_preview}
            </span>
          )}
        </div>
        <div className="flex gap-1.5">
          <Input
            containerClassName="flex-1"
            type={revealed ? "text" : "password"}
            value={keyOverride ?? ""}
            onChange={(e) => onKeyChange(e.target.value)}
            placeholder={
              status
                ? "Paste a new value to replace…"
                : `${meta.keyEnv} (e.g. sk-…)`
            }
            autoComplete="off"
            spellCheck={false}
            rightSlot={
              <button
                type="button"
                onClick={onToggleReveal}
                aria-label={revealed ? "Hide" : "Reveal"}
                className="text-ink-400 hover:text-ink-50 transition"
              >
                {revealed ? (
                  <EyeOff className="h-3.5 w-3.5" />
                ) : (
                  <Eye className="h-3.5 w-3.5" />
                )}
              </button>
            }
          />
          {info?.configured && (
            <button
              type="button"
              onClick={onClear}
              title="Clear this key on save"
              className={cn(
                "h-10 w-10 rounded-xl border grid place-items-center transition",
                cleared
                  ? "border-rose-500/50 bg-rose-500/10 text-rose-600"
                  : "border-ink-700 text-ink-400 hover:border-ink-600 hover:text-ink-50"
              )}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        {cleared && (
          <div className="flex items-center gap-1.5 text-[11px] text-rose-600">
            <AlertTriangle className="h-3 w-3" />
            Will be cleared on save.
          </div>
        )}
      </div>

      <div>
        <Input
          label="Model"
          value={modelOverride ?? info?.model ?? ""}
          onChange={(e) => onModelChange(e.target.value)}
          placeholder={meta.placeholderModel}
        />
      </div>
    </div>
  );
}

function SearchRow({
  name,
  info,
  keyOverride,
  revealed,
  onToggleReveal,
  onKeyChange,
  onClear,
}: {
  name: keyof typeof SEARCH_META;
  info: SearchInfo | undefined;
  keyOverride: string | undefined;
  revealed: boolean | undefined;
  onToggleReveal: () => void;
  onKeyChange: (v: string) => void;
  onClear: () => void;
}) {
  const meta = SEARCH_META[name];
  const cleared = keyOverride === "";
  return (
    <div className="rounded-xl border border-ink-700 bg-[var(--bg-card)] p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <div className="text-sm font-semibold text-ink-50 tracking-tight">
              {meta.label}
            </div>
            {info?.configured ? (
              <Badge tone="success" dot>
                configured
              </Badge>
            ) : (
              <Badge tone="default">optional</Badge>
            )}
          </div>
          <p className="text-[11px] text-ink-400 mt-0.5">{meta.notes}</p>
        </div>
        <a
          href={meta.docs}
          target="_blank"
          rel="noreferrer"
          className="text-[11px] text-orange-600 hover:text-orange-700 underline-offset-2 hover:underline shrink-0"
        >
          Get key
        </a>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label className="text-[11px] uppercase tracking-wider text-ink-400 font-medium">
            API key
          </label>
          {info?.key_preview && !keyOverride && (
            <span className="text-[11px] text-ink-400 font-mono">
              current: {info.key_preview}
            </span>
          )}
        </div>
        <div className="flex gap-1.5">
          <Input
            containerClassName="flex-1"
            type={revealed ? "text" : "password"}
            value={keyOverride ?? ""}
            onChange={(e) => onKeyChange(e.target.value)}
            placeholder={info?.configured ? "Paste a new value…" : meta.keyEnv}
            autoComplete="off"
            spellCheck={false}
            rightSlot={
              <button
                type="button"
                onClick={onToggleReveal}
                aria-label={revealed ? "Hide" : "Reveal"}
                className="text-ink-400 hover:text-ink-50 transition"
              >
                {revealed ? (
                  <EyeOff className="h-3.5 w-3.5" />
                ) : (
                  <Eye className="h-3.5 w-3.5" />
                )}
              </button>
            }
          />
          {info?.configured && (
            <button
              type="button"
              onClick={onClear}
              title="Clear this key on save"
              className={cn(
                "h-10 w-10 rounded-xl border grid place-items-center transition",
                cleared
                  ? "border-rose-500/50 bg-rose-500/10 text-rose-600"
                  : "border-ink-700 text-ink-400 hover:border-ink-600 hover:text-ink-50"
              )}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        {cleared && (
          <div className="flex items-center gap-1.5 text-[11px] text-rose-600">
            <AlertTriangle className="h-3 w-3" />
            Will be cleared on save.
          </div>
        )}
      </div>
    </div>
  );
}

const CUSTOM_PATTERN = /^[A-Z][A-Z0-9_]{1,64}_API_KEY$/;

function CustomKeysSection({
  existing,
  onAdd,
  onRemove,
}: {
  existing: CustomKeyEntry[];
  onAdd: (name: string, value: string) => Promise<void> | void;
  onRemove: (name: string) => Promise<void> | void;
}) {
  const [name, setName] = useState("");
  const [val, setVal] = useState("");
  const [reveal, setReveal] = useState(false);
  const target = name.trim().toUpperCase();
  const valid = CUSTOM_PATTERN.test(target);
  const canSave = Boolean(val.trim()) && valid;

  return (
    <Card>
      <CardHeader
        icon={<KeyRound className="h-4 w-4" />}
        title="Custom keys"
        subtitle="Add any extra provider key your scripts or experiments expect — e.g. COHERE_API_KEY, MISTRAL_API_KEY, DEEPSEEK_API_KEY."
      />

      {existing.length > 0 && (
        <div className="mb-4 rounded-xl border border-ink-700 bg-[var(--bg-card)] divide-y divide-ink-700">
          {existing.map((c) => (
            <div
              key={c.name}
              className="flex items-center gap-3 px-3 py-2"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 shrink-0" />
              <div className="font-mono text-sm text-ink-50 truncate flex-1">
                {c.name}
              </div>
              <span className="font-mono text-[11px] text-ink-400">
                {c.key_preview ?? ""}
              </span>
              <button
                type="button"
                onClick={() => onRemove(c.name)}
                title={`Clear ${c.name}`}
                className="text-ink-400 hover:text-rose-600 transition p-1"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-2 items-start">
        <div className="lg:col-span-5">
          <Input
            label="Env-var name"
            value={name}
            onChange={(e) => setName(e.target.value.toUpperCase())}
            placeholder="MY_PROVIDER_API_KEY"
            spellCheck={false}
            autoComplete="off"
          />
          {name && !valid && (
            <div className="text-[11px] text-rose-600 mt-1">
              Must be UPPER_SNAKE_CASE and end in <span className="font-mono">_API_KEY</span>.
            </div>
          )}
        </div>
        <div className="lg:col-span-5">
          <Input
            label="Value"
            type={reveal ? "text" : "password"}
            value={val}
            onChange={(e) => setVal(e.target.value)}
            placeholder="paste the secret here"
            spellCheck={false}
            autoComplete="off"
            rightSlot={
              <button
                type="button"
                onClick={() => setReveal((r) => !r)}
                aria-label={reveal ? "Hide" : "Reveal"}
                className="text-ink-400 hover:text-ink-50 transition"
              >
                {reveal ? (
                  <EyeOff className="h-3.5 w-3.5" />
                ) : (
                  <Eye className="h-3.5 w-3.5" />
                )}
              </button>
            }
          />
        </div>
        <div className="lg:col-span-2 lg:pt-[26px]">
          <Button
            onClick={async () => {
              await onAdd(target, val);
              if (canSave) {
                setName("");
                setVal("");
                setReveal(false);
              }
            }}
            disabled={!canSave}
            leftIcon={<Plus className="h-4 w-4" />}
            className="w-full"
          >
            Add
          </Button>
        </div>
      </div>
    </Card>
  );
}
