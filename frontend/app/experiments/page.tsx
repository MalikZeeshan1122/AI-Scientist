"use client";

import { useEffect, useState } from "react";
import {
  AlertOctagon,
  Check,
  ChevronDown,
  Clock,
  Code2,
  FlaskConical,
  Loader2,
  Terminal,
  Timer,
  X,
} from "lucide-react";
import { Badge, Card, CardHeader } from "@/components/Card";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { PageHeader } from "@/components/PageHeader";
import { SkeletonList } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { api, type Experiment } from "@/lib/api";
import { cn } from "@/lib/cn";

const STATUS_TONE: Record<string, "success" | "danger" | "warn" | "default"> = {
  succeeded: "success",
  failed: "danger",
  timed_out: "warn",
  running: "warn",
  pending: "default",
};

const STATUS_ICON: Record<string, React.ReactNode> = {
  succeeded: <Check className="h-3 w-3" />,
  failed: <X className="h-3 w-3" />,
  timed_out: <Timer className="h-3 w-3" />,
  running: <Loader2 className="h-3 w-3 animate-spin" />,
  pending: <Clock className="h-3 w-3" />,
};

export default function ExperimentsPage() {
  const [experiments, setExperiments] = useState<Experiment[] | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    api<Experiment[]>("/experiments")
      .then(setExperiments)
      .catch((e) => toast.error(String(e), "Couldn't load experiments"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const succeeded = experiments?.filter((e) => e.result?.status === "succeeded").length ?? 0;
  const failed = experiments?.filter((e) => e.result?.status === "failed").length ?? 0;

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Sandbox"
        title="Experiments"
        description="LLM-generated Python experiments executed in a sandboxed subprocess. Inspect code, captured output, and parsed metrics."
        actions={
          experiments && experiments.length > 0 ? (
            <div className="flex items-center gap-2">
              <Badge tone="success" dot>
                {succeeded} succeeded
              </Badge>
              {failed > 0 && (
                <Badge tone="danger" dot>
                  {failed} failed
                </Badge>
              )}
            </div>
          ) : undefined
        }
      />

      {!experiments ? (
        <SkeletonList rows={3} />
      ) : experiments.length === 0 ? (
        <EmptyState
          icon={<FlaskConical className="h-6 w-6" />}
          title="No experiments yet"
          description="Run the autonomous pipeline to generate and execute your first experiment."
        />
      ) : (
        <div className="space-y-3">
          {experiments.map((e) => {
            const status = e.result?.status ?? "pending";
            const isOpen = open === e.id;
            return (
              <Card key={e.id} className="overflow-hidden">
                <CardHeader
                  icon={<FlaskConical className="h-4 w-4" />}
                  title={e.title}
                  subtitle={
                    <span className="font-mono">
                      {e.id}
                      {e.idea_id && ` · idea ${e.idea_id}`}
                    </span>
                  }
                  right={
                    <div className="flex items-center gap-2">
                      {e.result && (
                        <span className="text-[11px] text-ink-400 font-mono inline-flex items-center gap-1">
                          <Timer className="h-3 w-3" />
                          {e.result.duration_s.toFixed(1)}s
                        </span>
                      )}
                      <Badge tone={STATUS_TONE[status] || "default"} dot>
                        <span className="inline-flex items-center gap-1">
                          {STATUS_ICON[status]}
                          {status.replace("_", " ")}
                        </span>
                      </Badge>
                    </div>
                  }
                />
                <p className="text-sm text-ink-200 leading-relaxed">
                  {e.description}
                </p>

                {e.result?.metrics && Object.keys(e.result.metrics).length > 0 && (
                  <div className="mt-4 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                    {Object.entries(e.result.metrics).map(([k, v]) => (
                      <MetricTile key={k} label={k} value={v} />
                    ))}
                  </div>
                )}

                {e.requirements?.length > 0 && (
                  <div className="mt-3 flex items-center gap-2 flex-wrap">
                    <span className="text-[10px] uppercase tracking-wider text-ink-400 font-medium">
                      requires
                    </span>
                    {e.requirements.map((r) => (
                      <span
                        key={r}
                        className="text-[11px] font-mono text-orange-600 bg-orange-500/10 border border-orange-500/30 rounded-md px-1.5 py-0.5"
                      >
                        {r}
                      </span>
                    ))}
                  </div>
                )}

                <div className="mt-4">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setOpen(isOpen ? null : e.id)}
                    leftIcon={
                      <ChevronDown
                        className={cn(
                          "h-3.5 w-3.5 transition-transform",
                          isOpen && "rotate-180"
                        )}
                      />
                    }
                  >
                    {isOpen ? "Hide" : "Show"} code & output
                  </Button>
                </div>

                {isOpen && (
                  <div className="mt-4 space-y-3">
                    <CodeBlock
                      icon={<Code2 className="h-3.5 w-3.5" />}
                      title="experiment.py"
                      content={e.code}
                    />
                    {e.result?.stdout && (
                      <CodeBlock
                        icon={<Terminal className="h-3.5 w-3.5" />}
                        title="stdout"
                        content={e.result.stdout}
                      />
                    )}
                    {e.result?.stderr && (
                      <CodeBlock
                        icon={<AlertOctagon className="h-3.5 w-3.5" />}
                        title="stderr"
                        content={e.result.stderr}
                        tone="danger"
                      />
                    )}
                  </div>
                )}
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

function MetricTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl bg-ink-850 border border-ink-700 px-3 py-2 hover:border-orange-500/40 transition">
      <div className="text-[10px] uppercase tracking-wider text-ink-400 font-medium truncate">
        {label}
      </div>
      <div className="text-base font-semibold text-orange-600 tabular-nums mt-0.5 truncate">
        {typeof value === "number" ? value.toPrecision(4) : value}
      </div>
    </div>
  );
}

function CodeBlock({
  icon,
  title,
  content,
  tone = "default",
}: {
  icon?: React.ReactNode;
  title: string;
  content: string;
  tone?: "default" | "danger";
}) {
  const toast = useToast();
  return (
    <div className="rounded-xl border border-ink-700 bg-ink-850 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-ink-700 bg-ink-900">
        <div
          className={cn(
            "flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-medium",
            tone === "danger" ? "text-rose-600" : "text-ink-300"
          )}
        >
          {icon}
          {title}
        </div>
        <button
          onClick={() => {
            navigator.clipboard.writeText(content);
            toast.success("Copied");
          }}
          className="text-[11px] text-ink-400 hover:text-ink-50 px-2 py-0.5 rounded hover:bg-ink-800 transition"
        >
          Copy
        </button>
      </div>
      <pre className="p-3 text-[12px] font-mono overflow-x-auto max-h-[28rem] leading-[1.55] text-ink-100">
        {content}
      </pre>
    </div>
  );
}
