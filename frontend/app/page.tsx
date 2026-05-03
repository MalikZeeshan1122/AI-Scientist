"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  CheckCircle2,
  ClipboardCopy,
  FileText,
  FlaskConical,
  History,
  KeyRound,
  Lightbulb,
  Microscope,
  Play,
  Sparkles,
  TrendingUp,
  X,
} from "lucide-react";
import Link from "next/link";
import { Badge, Card, CardHeader } from "@/components/Card";
import { Button } from "@/components/Button";
import { CategoryFilter } from "@/components/CategoryFilter";
import { EmptyState } from "@/components/EmptyState";
import { Input } from "@/components/Input";
import { PageHeader } from "@/components/PageHeader";
import { ScoreBar } from "@/components/ScoreBar";
import { SkeletonList } from "@/components/Skeleton";
import { StatTile } from "@/components/StatTile";
import { Stepper, type Step, type StepStatus } from "@/components/Stepper";
import { useToast } from "@/components/Toast";
import { api, type Project } from "@/lib/api";

type RunResult = {
  project: Project;
  papers: { id: string; title: string }[];
  ideas: { id: string; title: string; score?: { overall?: number } | null }[];
  chosen_idea: { id: string; title: string };
  experiment: {
    id: string;
    title: string;
    result?: { status: string; metrics: Record<string, number> } | null;
  };
  draft: { id: string; title: string; rendered_path: string | null };
  improvement: {
    iterations: number;
    history: { soundness: number; clarity: number; novelty: number; significance: number }[];
  } | null;
};

const STAGES = [
  { id: "ingest", label: "Ingest", description: "Search arXiv, S2, OpenAlex", icon: <BookOpen className="h-3.5 w-3.5" /> },
  { id: "ideate", label: "Ideate", description: "Novelty-aware generation", icon: <Lightbulb className="h-3.5 w-3.5" /> },
  { id: "experiment", label: "Experiment", description: "Sandboxed Python run", icon: <FlaskConical className="h-3.5 w-3.5" /> },
  { id: "draft", label: "Draft", description: "Markdown / LaTeX output", icon: <FileText className="h-3.5 w-3.5" /> },
  { id: "refine", label: "Refine", description: "Critique & revise loop", icon: <Sparkles className="h-3.5 w-3.5" /> },
];

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [topic, setTopic] = useState("sparse mixture-of-experts inference");
  const [nPapers, setNPapers] = useState(3);
  const [nIdeas, setNIdeas] = useState(3);
  const [refine, setRefine] = useState(1);
  const [categories, setCategories] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<RunResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeStage, setActiveStage] = useState<number>(-1);
  const toast = useToast();

  const refresh = async () => {
    try {
      const ps = await api<Project[]>("/projects");
      setProjects(ps);
    } catch (e) {
      toast.error(String(e), "Couldn't load projects");
    }
  };

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Animate the stepper while a run is in flight (visual heuristic only).
  useEffect(() => {
    if (!running) {
      setActiveStage(-1);
      return;
    }
    setActiveStage(0);
    const timers: ReturnType<typeof setTimeout>[] = [];
    [4500, 11000, 22000, 32000].forEach((ms, i) => {
      timers.push(setTimeout(() => setActiveStage((s) => Math.max(s, i + 1)), ms));
    });
    return () => timers.forEach(clearTimeout);
  }, [running]);

  const runPipeline = async () => {
    setRunning(true);
    setResult(null);
    setError(null);
    try {
      const r = await api<RunResult>("/run", {
        method: "POST",
        body: JSON.stringify({
          topic,
          n_papers: nPapers,
          n_ideas: nIdeas,
          refine_iters: refine,
          fmt: "markdown",
          categories: categories.length ? categories : null,
        }),
      });
      setResult(r);
      toast.success(
        `Drafted "${r.draft.title.slice(0, 60)}${r.draft.title.length > 60 ? "…" : ""}"`,
        "Pipeline complete"
      );
      await refresh();
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      setError(msg);
      toast.error(msg, "Pipeline failed");
    } finally {
      setRunning(false);
    }
  };

  const steps: Step[] = useMemo(() => {
    return STAGES.map((s, i) => {
      let status: StepStatus = "pending";
      if (result) status = "complete";
      else if (running) {
        if (i < activeStage) status = "complete";
        else if (i === activeStage) status = "active";
      }
      return { ...s, status };
    });
  }, [running, activeStage, result]);

  const expStatus = result?.experiment.result?.status;
  const improvementHistory = result?.improvement?.history ?? [];
  const improvementScores = improvementHistory.map(
    (s) => (s.soundness + s.clarity + s.novelty + s.significance) / 4
  );
  const trend =
    improvementScores.length >= 2
      ? improvementScores[improvementScores.length - 1] - improvementScores[0]
      : null;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Workspace"
        title="Run an autonomous research pipeline"
        description="Search papers, propose novel ideas, execute experiments in a sandbox, draft a paper, and iterate — all from a single topic."
        actions={
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<History className="h-3.5 w-3.5" />}
            onClick={refresh}
          >
            Refresh
          </Button>
        }
      />

      {/* Stat tiles */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <StatTile
          label="Projects"
          value={projects?.length ?? "—"}
          icon={<Microscope className="h-4 w-4" />}
          tone="default"
        />
        <StatTile
          label="Papers ingested"
          value={result?.papers.length ?? "—"}
          icon={<BookOpen className="h-4 w-4" />}
          tone="accent"
          hint={result ? "this run" : undefined}
        />
        <StatTile
          label="Ideas generated"
          value={result?.ideas.length ?? "—"}
          icon={<Lightbulb className="h-4 w-4" />}
          tone="accent"
          hint={result ? "this run" : undefined}
        />
        <StatTile
          label="Last experiment"
          value={
            expStatus
              ? expStatus.replace("_", " ")
              : "—"
          }
          icon={<FlaskConical className="h-4 w-4" />}
          tone={
            expStatus === "succeeded"
              ? "success"
              : expStatus === "failed"
                ? "danger"
                : expStatus
                  ? "warn"
                  : "default"
          }
        />
      </div>

      {/* Run pipeline */}
      <Card className="overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-orange-500/[0.04] via-transparent to-amber-500/[0.03]"
        />
        <div className="relative">
          <CardHeader
            icon={<Play className="h-4 w-4" />}
            title="New pipeline run"
            subtitle="search → ideate → experiment → draft → refine"
            right={
              running ? (
                <Badge tone="accent" dot>
                  Running…
                </Badge>
              ) : (
                <Badge tone="default" dot>
                  Idle
                </Badge>
              )
            }
          />

          <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
            <Input
              containerClassName="md:col-span-6"
              label="Research topic"
              placeholder="e.g. sparse mixture-of-experts inference"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              leftIcon={<Sparkles className="h-3.5 w-3.5" />}
            />
            <NumInput
              label="Papers"
              value={nPapers}
              onChange={setNPapers}
              hint="3 ≈ free-tier safe"
              className="md:col-span-2"
            />
            <NumInput
              label="Ideas"
              value={nIdeas}
              onChange={setNIdeas}
              className="md:col-span-2"
            />
            <NumInput
              label="Refine"
              value={refine}
              onChange={setRefine}
              hint="critique iters"
              className="md:col-span-2"
            />
          </div>

          <div className="mt-4">
            <CategoryFilter
              value={categories}
              onChange={setCategories}
              label="Restrict to categories"
              hint="Optional. arXiv search will be filtered; other sources are filtered post-hoc when categories are reported."
            />
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button
              onClick={runPipeline}
              disabled={!topic.trim()}
              loading={running}
              size="lg"
              leftIcon={<Play className="h-4 w-4" fill="currentColor" />}
              rightIcon={!running ? <ArrowRight className="h-4 w-4" /> : undefined}
            >
              {running ? "Pipeline running…" : "Run autonomous pipeline"}
            </Button>
            <div className="text-xs text-ink-400">
              Tip: small numbers run faster and stay inside Gemini free-tier limits.
            </div>
          </div>

          <div className="mt-6">
            <Stepper steps={steps} />
          </div>
        </div>
      </Card>

      {/* Error panel — persists last failure so the user can read it */}
      {error && !result && <PipelineErrorCard message={error} onDismiss={() => setError(null)} />}

      {/* Result panel */}
      {result && (
        <Card>
          <CardHeader
            icon={<CheckCircle2 className="h-4 w-4" />}
            title={result.project.topic}
            subtitle={`Project ${result.project.id}`}
            right={
              <div className="flex flex-wrap gap-1.5">
                <Badge tone="accent">{result.papers.length} papers</Badge>
                <Badge tone="accent">{result.ideas.length} ideas</Badge>
                {expStatus && (
                  <Badge
                    tone={
                      expStatus === "succeeded"
                        ? "success"
                        : expStatus === "failed"
                          ? "danger"
                          : "warn"
                    }
                    dot
                  >
                    {expStatus.replace("_", " ")}
                  </Badge>
                )}
              </div>
            }
          />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            <ResultRow
              icon={<Lightbulb className="h-3.5 w-3.5" />}
              label="Chosen idea"
              value={result.chosen_idea.title}
            />
            <ResultRow
              icon={<FlaskConical className="h-3.5 w-3.5" />}
              label="Experiment"
              value={result.experiment.title}
            />
            <ResultRow
              icon={<FileText className="h-3.5 w-3.5" />}
              label="Draft"
              value={result.draft.title}
              hint={result.draft.rendered_path ?? undefined}
              copy={result.draft.rendered_path ?? undefined}
            />
            {improvementScores.length > 0 && (
              <ResultRow
                icon={<TrendingUp className="h-3.5 w-3.5" />}
                label={`Self-improvement · ${improvementScores.length} iterations`}
                value={improvementScores.map((s) => s.toFixed(2)).join("  →  ")}
                hint={
                  trend !== null
                    ? `${trend > 0 ? "+" : ""}${trend.toFixed(2)} overall`
                    : undefined
                }
              />
            )}
          </div>

          {result.experiment.result?.metrics &&
            Object.keys(result.experiment.result.metrics).length > 0 && (
              <div className="mt-4">
                <div className="text-[11px] uppercase tracking-wider text-ink-400 font-medium mb-2">
                  Metrics
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {Object.entries(result.experiment.result.metrics).map(([k, v]) => (
                    <div
                      key={k}
                      className="rounded-xl bg-ink-850 border border-ink-700 px-3 py-2"
                    >
                      <div className="text-[10px] uppercase tracking-wider text-ink-500">
                        {k}
                      </div>
                      <div className="text-base font-semibold text-orange-600 tabular-nums mt-0.5">
                        {typeof v === "number" ? v.toPrecision(4) : v}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

          {improvementHistory.length > 0 && (
            <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {(["soundness", "clarity", "novelty", "significance"] as const).map((k) => {
                const last = improvementHistory[improvementHistory.length - 1][k];
                return <ScoreBar key={k} label={k} value={last} max={5} />;
              })}
            </div>
          )}
        </Card>
      )}

      {/* Recent projects */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-[11px] uppercase tracking-[0.18em] text-ink-400 font-medium">
            Recent projects
          </h2>
          <Badge>{projects?.length ?? 0}</Badge>
        </div>
        {!projects ? (
          <SkeletonList rows={3} />
        ) : projects.length === 0 ? (
          <EmptyState
            icon={<Microscope className="h-6 w-6" />}
            title="No projects yet"
            description="Run the autonomous pipeline above to create your first research project."
          />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {projects.map((p) => (
              <Card key={p.id} interactive>
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 grid place-items-center h-9 w-9 rounded-xl bg-gradient-to-br from-orange-500/15 to-amber-500/5 border border-orange-500/20 text-orange-500 shrink-0">
                    <Microscope className="h-4 w-4" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-semibold text-ink-50 tracking-tight truncate">
                      {p.topic}
                    </div>
                    <div className="text-[11px] text-ink-500 mt-0.5 font-mono">
                      {p.id}
                    </div>
                    <div className="text-[11px] text-ink-500 mt-2">
                      {new Date(p.created_at).toLocaleString()}
                    </div>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ResultRow({
  icon,
  label,
  value,
  hint,
  copy,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  hint?: string;
  copy?: string;
}) {
  const toast = useToast();
  return (
      <div className="rounded-xl bg-ink-850 border border-ink-700 px-4 py-3 hover:border-ink-600 transition">
      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-ink-400 font-medium">
        <span className="text-orange-500">{icon}</span>
        {label}
      </div>
      <div className="mt-1 text-sm text-ink-50 leading-snug font-mono break-words">
        {value}
      </div>
      {(hint || copy) && (
        <div className="mt-1.5 flex items-center gap-2">
          {hint && (
            <span className="text-[11px] text-ink-500 font-mono truncate">
              {hint}
            </span>
          )}
          {copy && (
            <button
              onClick={() => {
                navigator.clipboard.writeText(copy);
                toast.success("Copied to clipboard");
              }}
              className="text-ink-500 hover:text-ink-50 p-1 rounded hover:bg-ink-800 transition"
              aria-label="Copy"
            >
              <ClipboardCopy className="h-3 w-3" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function NumInput({
  label,
  value,
  onChange,
  hint,
  className = "",
}: {
  label: string;
  value: number;
  onChange: (v: number) => void;
  hint?: string;
  className?: string;
}) {
  return (
    <Input
      containerClassName={className}
      label={label}
      hint={hint}
      type="number"
      min={0}
      value={value}
      onChange={(e) => onChange(Math.max(0, Number(e.target.value)))}
    />
  );
}

function PipelineErrorCard({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  // Heuristic: detect the common Gemini-quota / missing-key cases and surface
  // an actionable hint rather than just the raw error text.
  const hint = useMemo(() => {
    const m = message.toLowerCase();
    const isOpenAIRpm =
      (m.includes("openai api 429") || m.includes("rate_limit_exceeded")) &&
      (m.includes("requests per min") || m.includes("rpm") || m.includes("rate limit"));
    if (isOpenAIRpm) {
      return {
        kind: "openai-rpm",
        title: "OpenAI rate limit (RPM)",
        body: "Your OpenAI org allows very few requests per minute (often ~3 RPM). This build serializes chat requests inside each backend process and spaces them (**~35s** apart by default — hard-refresh the page if this card still mentions ~30s). Ensure `AI_SCIENTIST_OPENAI_MIN_INTERVAL_S` is not `0` in `.env`, restart the backend after changes, and confirm **GET /health** reports **version 0.1.1** so you are not on an older API build. Other apps or extra uvicorn workers using the same key share that RPM. Wait ~1 minute after errors, add billing at platform.openai.com/account/billing for higher RPM, or switch Active LLM to Groq / OpenRouter.",
      } as const;
    }
    if (
      m.includes("gemini quota") ||
      (m.includes("429") && m.includes("gemini"))
    ) {
      return {
        kind: "quota",
        title: "Gemini hit its rate limit",
        body: "Switch the active LLM provider to OpenAI, OpenRouter, Groq, or Anthropic in the sidebar API keys card. The pipeline will use that provider on the next run.",
      } as const;
    }
    if (m.includes("api_key") || m.includes("not configured")) {
      return {
        kind: "missing-key",
        title: "Missing or invalid API key",
        body: "Open the API keys card in the sidebar (or the Settings page) and paste the key for whichever provider you want to use. Then click that provider in the 'Active LLM' row.",
      } as const;
    }
    if (m.includes("openai api 401") || m.includes("openai api 403")) {
      return {
        kind: "openai-auth",
        title: "OpenAI rejected the key",
        body: "The OPENAI_API_KEY is invalid or revoked. Generate a fresh one at platform.openai.com/api-keys and re-save it in the sidebar.",
      } as const;
    }
    return null;
  }, [message]);

  return (
    <Card className="border-rose-500/40 bg-rose-500/[0.04]">
      <div className="flex items-start gap-3">
        <div className="grid place-items-center h-9 w-9 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-600 shrink-0">
          <AlertTriangle className="h-4 w-4" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-3">
            <div className="text-sm font-semibold text-ink-50">
              {hint?.title ?? "Pipeline failed"}
            </div>
            <button
              type="button"
              onClick={onDismiss}
              className="text-ink-400 hover:text-ink-50 transition shrink-0 p-0.5"
              aria-label="Dismiss"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          </div>
          {hint && (
            <p className="text-[13px] text-ink-200 leading-relaxed mt-1">
              {hint.body}
            </p>
          )}
          <div className="mt-3 rounded-lg bg-[var(--bg-card)] border border-ink-700 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wider text-ink-400 font-medium mb-1">
              Server message
            </div>
            <code className="text-[12px] text-ink-200 leading-relaxed font-mono break-words whitespace-pre-wrap block">
              {message}
            </code>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link
              href="/settings"
              className="inline-flex items-center gap-1.5 text-[12px] font-medium text-orange-700 hover:text-orange-800 underline-offset-2 hover:underline"
            >
              <KeyRound className="h-3 w-3" />
              Open Settings
            </Link>
          </div>
        </div>
      </div>
    </Card>
  );
}
