"use client";

import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Beaker,
  Brain,
  ChevronDown,
  Lightbulb,
  Sparkles,
  Tag,
  Target,
} from "lucide-react";
import { Badge, Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { CircularScore, ScoreBar } from "@/components/ScoreBar";
import { EmptyState } from "@/components/EmptyState";
import { Input } from "@/components/Input";
import { PageHeader } from "@/components/PageHeader";
import { SkeletonList } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { api, type Idea } from "@/lib/api";
import { cn } from "@/lib/cn";

export default function IdeasPage() {
  const [topic, setTopic] = useState("efficient long-context inference");
  const [n, setN] = useState(5);
  const [generating, setGenerating] = useState(false);
  const [stored, setStored] = useState<Idea[] | null>(null);
  const [sortBy, setSortBy] = useState<"recent" | "score">("recent");
  const toast = useToast();

  const refresh = () => {
    api<Idea[]>("/ideas")
      .then(setStored)
      .catch((e) => toast.error(String(e), "Couldn't load ideas"));
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(refresh, []);

  const generate = async () => {
    if (!topic.trim()) return;
    setGenerating(true);
    try {
      const created = await api<Idea[]>("/ideate", {
        method: "POST",
        body: JSON.stringify({ topic, n }),
      });
      toast.success(`Generated ${created.length} ideas`, "Ideation complete");
      refresh();
    } catch (e) {
      toast.error(String(e), "Ideation failed");
    } finally {
      setGenerating(false);
    }
  };

  const sorted = useMemo(() => {
    if (!stored) return null;
    if (sortBy === "score") {
      return [...stored].sort((a, b) => scoreOf(b) - scoreOf(a));
    }
    return [...stored].sort(
      (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );
  }, [stored, sortBy]);

  const topScore = useMemo(() => {
    if (!stored || stored.length === 0) return null;
    return Math.max(...stored.map(scoreOf));
  }, [stored]);

  const avgScore = useMemo(() => {
    if (!stored || stored.length === 0) return null;
    const scored = stored.filter((i) => i.score);
    if (scored.length === 0) return null;
    return scored.reduce((acc, i) => acc + scoreOf(i), 0) / scored.length;
  }, [stored]);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Ideation"
        title="Ideas"
        description="Generate novel research ideas grounded in the indexed corpus, scored on novelty, feasibility, and impact by an automated peer reviewer."
      />

      <Card className="overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-orange-500/[0.04] via-transparent to-amber-500/[0.03]"
        />
        <div className="relative">
          <div className="flex items-center gap-2 mb-4">
            <div className="grid place-items-center h-9 w-9 rounded-xl bg-orange-500/10 border border-orange-500/30 text-orange-500">
              <Brain className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-semibold text-ink-50 tracking-tight">
                Generate ideas
              </div>
              <div className="text-xs text-ink-400">
                Novelty-aware idea generation over the indexed corpus
              </div>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-end">
            <Input
              containerClassName="flex-1"
              label="Topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              leftIcon={<Sparkles className="h-3.5 w-3.5" />}
            />
            <Input
              containerClassName="sm:w-24"
              label="Count"
              type="number"
              min={1}
              max={10}
              value={n}
              onChange={(e) => setN(Math.max(1, Math.min(10, Number(e.target.value))))}
            />
            <Button
              onClick={generate}
              disabled={!topic.trim()}
              loading={generating}
              size="lg"
              rightIcon={!generating ? <ArrowRight className="h-4 w-4" /> : undefined}
            >
              {generating ? "Generating…" : "Generate"}
            </Button>
          </div>
        </div>
      </Card>

      {stored && stored.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          <MiniStat label="Total" value={String(stored.length)} icon={<Lightbulb className="h-4 w-4" />} />
          <MiniStat
            label="Top score"
            value={topScore != null ? topScore.toFixed(2) : "—"}
            icon={<Target className="h-4 w-4" />}
            highlight
          />
          <MiniStat
            label="Average"
            value={avgScore != null ? avgScore.toFixed(2) : "—"}
            icon={<Beaker className="h-4 w-4" />}
          />
        </div>
      )}

      <div>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Lightbulb className="h-3.5 w-3.5 text-orange-500" />
            <h2 className="text-[11px] uppercase tracking-[0.18em] text-ink-300 font-medium">
              All ideas
            </h2>
            <Badge>{stored?.length ?? 0}</Badge>
          </div>
          {stored && stored.length > 1 && (
            <div className="flex items-center gap-1 text-xs">
              <span className="text-ink-400">Sort:</span>
              {(["recent", "score"] as const).map((opt) => (
                <button
                  key={opt}
                  onClick={() => setSortBy(opt)}
                  className={cn(
                    "px-2 py-1 rounded-md transition",
                    sortBy === opt
                      ? "bg-ink-800 text-ink-50 font-medium"
                      : "text-ink-400 hover:text-ink-50 hover:bg-ink-800"
                  )}
                >
                  {opt}
                </button>
              ))}
            </div>
          )}
        </div>

        {!stored ? (
          <SkeletonList rows={3} />
        ) : sorted && sorted.length === 0 ? (
          <EmptyState
            icon={<Lightbulb className="h-6 w-6" />}
            title="No ideas yet"
            description="Generate your first batch of ideas using the panel above."
          />
        ) : (
          <div className="space-y-3">
            {sorted?.map((idea) => <IdeaCard key={idea.id} idea={idea} />)}
          </div>
        )}
      </div>
    </div>
  );
}

function scoreOf(idea: Idea): number {
  const s = idea.score;
  if (!s) return 0;
  if (typeof s.overall === "number") return s.overall;
  return (s.novelty + s.feasibility + s.impact) / 3;
}

function MiniStat({
  label,
  value,
  icon,
  highlight = false,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div
      className={cn(
        "glass rounded-2xl p-4 flex items-center gap-3",
        highlight && "border-orange-500/40 bg-orange-500/[0.06]"
      )}
    >
      <div
        className={cn(
          "grid place-items-center h-9 w-9 rounded-xl border",
          highlight
            ? "bg-orange-500/15 text-orange-500 border-orange-500/40"
            : "bg-ink-850 text-ink-300 border-ink-700"
        )}
      >
        {icon}
      </div>
      <div>
        <div className="text-[10px] uppercase tracking-wider text-ink-400 font-medium">
          {label}
        </div>
        <div className="text-lg font-semibold tabular-nums text-ink-50">{value}</div>
      </div>
    </div>
  );
}

function IdeaCard({ idea }: { idea: Idea }) {
  const [expanded, setExpanded] = useState(false);
  const overall = scoreOf(idea);

  return (
    <Card className="hover-lift hover:border-ink-600">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="text-base font-semibold text-ink-50 tracking-tight leading-snug">
            {idea.title}
          </div>
          <div className="mt-1 text-[11px] text-ink-400 font-mono">
            topic · {idea.topic}
          </div>
        </div>
        {idea.score && (
          <CircularScore value={overall} max={5} label="overall" />
        )}
      </div>

      {idea.score && (
        <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <ScoreBar label="novelty" value={idea.score.novelty} />
          <ScoreBar label="feasibility" value={idea.score.feasibility} />
          <ScoreBar label="impact" value={idea.score.impact} />
        </div>
      )}

      <div className="mt-4">
        <button
          onClick={() => setExpanded((v) => !v)}
          className="inline-flex items-center gap-1 text-xs text-ink-400 hover:text-ink-50 transition"
        >
          <ChevronDown
            className={cn(
              "h-3.5 w-3.5 transition-transform",
              expanded && "rotate-180"
            )}
          />
          {expanded ? "Hide details" : "View hypothesis & method"}
        </button>
      </div>

      {expanded && (
        <div className="mt-3 grid grid-cols-1 md:grid-cols-2 gap-3">
          <Field label="Hypothesis">{idea.hypothesis}</Field>
          <Field label="Proposed method">{idea.proposed_method}</Field>
          <Field label="Motivation">{idea.motivation}</Field>
          <Field label="Expected outcome">{idea.expected_outcome}</Field>
          {idea.score?.rationale && (
            <Field label="Reviewer rationale" className="md:col-span-2">
              {idea.score.rationale}
            </Field>
          )}
        </div>
      )}

      {idea.keywords.length > 0 && (
        <div className="mt-4 pt-3 border-t border-ink-700 flex items-center gap-2 flex-wrap">
          <Tag className="h-3 w-3 text-ink-500" />
          {idea.keywords.map((k) => (
            <span
              key={k}
              className="text-[10.5px] text-ink-300 bg-ink-850 border border-ink-700 rounded-full px-2 py-0.5"
            >
              {k}
            </span>
          ))}
        </div>
      )}
    </Card>
  );
}

function Field({
  label,
  children,
  className = "",
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("rounded-xl bg-ink-850 border border-ink-700 px-3 py-2.5", className)}>
      <div className="text-[10px] uppercase tracking-wider text-ink-400 font-medium mb-1">
        {label}
      </div>
      <div className="text-sm text-ink-100 leading-relaxed">{children}</div>
    </div>
  );
}
