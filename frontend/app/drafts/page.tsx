"use client";

import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  ClipboardCopy,
  FileCode2,
  FileText,
  Hash,
  ListTree,
  Search,
} from "lucide-react";
import { Badge, Card, CardHeader } from "@/components/Card";
import { Button } from "@/components/Button";
import { EmptyState } from "@/components/EmptyState";
import { Input } from "@/components/Input";
import { PageHeader } from "@/components/PageHeader";
import { SkeletonList } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { api, type Draft } from "@/lib/api";
import { cn } from "@/lib/cn";

export default function DraftsPage() {
  const [drafts, setDrafts] = useState<Draft[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [filter, setFilter] = useState("");
  const toast = useToast();

  useEffect(() => {
    api<Draft[]>("/drafts")
      .then((d) => {
        setDrafts(d);
        if (d.length > 0) setSelectedId(d[0].id);
      })
      .catch((e) => toast.error(String(e), "Couldn't load drafts"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = useMemo(
    () => drafts?.find((d) => d.id === selectedId) || null,
    [drafts, selectedId]
  );

  const markdown = useMemo(() => {
    if (!selected) return "";
    const sec = selected.sections
      .map((s) => `## ${s.name}\n\n${s.content}`)
      .join("\n\n");
    const refs = selected.references.length
      ? "\n\n## References\n" +
        selected.references.map((r, i) => `${i + 1}. ${r}`).join("\n")
      : "";
    return `# ${selected.title}\n\n## Abstract\n\n${selected.abstract}\n\n${sec}${refs}`;
  }, [selected]);

  const filteredDrafts = useMemo(() => {
    if (!drafts) return null;
    const q = filter.trim().toLowerCase();
    if (!q) return drafts;
    return drafts.filter((d) => d.title.toLowerCase().includes(q));
  }, [drafts, filter]);

  const wordCount = useMemo(() => {
    if (!selected) return 0;
    const text =
      selected.abstract +
      " " +
      selected.sections.map((s) => s.content).join(" ");
    return text.split(/\s+/).filter(Boolean).length;
  }, [selected]);

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Writing"
        title="Drafts"
        description="Auto-drafted papers (Markdown / LaTeX) produced by the writing pipeline, optionally refined by the self-critique loop."
      />

      {!drafts ? (
        <SkeletonList rows={3} />
      ) : drafts.length === 0 ? (
        <EmptyState
          icon={<FileText className="h-6 w-6" />}
          title="No drafts yet"
          description="Run the autonomous pipeline to produce your first paper draft."
        />
      ) : (
        <div className="grid grid-cols-12 gap-5">
          {/* Draft list sidebar */}
          <aside className="col-span-12 lg:col-span-4 xl:col-span-3 space-y-3 lg:sticky lg:top-6 lg:self-start">
            <Input
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              placeholder="Filter drafts…"
              leftIcon={<Search className="h-3.5 w-3.5" />}
            />
            <div className="space-y-1.5 max-h-[calc(100vh-12rem)] overflow-y-auto pr-1 -mr-1">
              {filteredDrafts?.map((d) => {
                const active = d.id === selectedId;
                return (
                  <button
                    key={d.id}
                    onClick={() => setSelectedId(d.id)}
                    className={cn(
                      "w-full text-left rounded-xl border px-3 py-2.5 transition group relative",
                      active
                        ? "border-orange-500/40 bg-orange-500/[0.08]"
                        : "border-ink-700 bg-[var(--bg-card)] hover:bg-ink-850 hover:border-ink-600"
                    )}
                  >
                    {active && (
                      <span className="absolute left-0 top-2 bottom-2 w-[2px] bg-gradient-to-b from-orange-400 to-amber-400 rounded-r-full" />
                    )}
                    <div className="flex items-start justify-between gap-2">
                      <div className="text-sm font-medium text-ink-50 truncate tracking-tight">
                        {d.title}
                      </div>
                      <Badge tone={d.format === "latex" ? "info" : "accent"} className="shrink-0">
                        {d.format}
                      </Badge>
                    </div>
                    <div className="text-[11px] text-ink-400 mt-1 font-mono truncate">
                      {new Date(d.created_at).toLocaleString()}
                    </div>
                  </button>
                );
              })}
              {filteredDrafts?.length === 0 && (
                <div className="text-xs text-ink-400 text-center py-4">
                  No matches.
                </div>
              )}
            </div>
          </aside>

          {/* Selected draft viewer */}
          <section className="col-span-12 lg:col-span-8 xl:col-span-9">
            {selected ? (
              <Card>
                <CardHeader
                  icon={
                    selected.format === "latex" ? (
                      <FileCode2 className="h-4 w-4" />
                    ) : (
                      <FileText className="h-4 w-4" />
                    )
                  }
                  title={selected.title}
                  subtitle={
                    <span className="font-mono">
                      {selected.id} · {wordCount.toLocaleString()} words ·{" "}
                      {selected.sections.length} sections
                    </span>
                  }
                  right={
                    <div className="flex items-center gap-2">
                      <Button
                        variant="secondary"
                        size="sm"
                        leftIcon={<ClipboardCopy className="h-3.5 w-3.5" />}
                        onClick={() => {
                          navigator.clipboard.writeText(markdown);
                          toast.success("Markdown copied");
                        }}
                      >
                        Copy
                      </Button>
                      <Badge tone={selected.format === "latex" ? "info" : "accent"}>
                        {selected.format}
                      </Badge>
                    </div>
                  }
                />

                {selected.sections.length > 0 && (
                  <div className="mb-4 rounded-xl border border-ink-700 bg-ink-850 p-3">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-ink-400 font-medium mb-2">
                      <ListTree className="h-3 w-3" /> Contents
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {selected.sections.map((s) => (
                        <span
                          key={s.name}
                          className="inline-flex items-center gap-1 text-[11px] text-ink-300 bg-ink-900 border border-ink-700 rounded-md px-2 py-0.5"
                        >
                          <Hash className="h-3 w-3 text-ink-400" />
                          {s.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="markdown max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {markdown}
                  </ReactMarkdown>
                </div>

                {selected.rendered_path && (
                  <div className="mt-6 pt-4 border-t border-ink-700 flex items-center justify-between text-xs text-ink-400">
                    <div className="font-mono truncate">
                      {selected.rendered_path}
                    </div>
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(selected.rendered_path!);
                        toast.success("Path copied");
                      }}
                      className="text-ink-400 hover:text-ink-50 p-1 rounded hover:bg-ink-800 transition"
                      aria-label="Copy path"
                    >
                      <ClipboardCopy className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}
              </Card>
            ) : (
              <EmptyState
                icon={<FileText className="h-6 w-6" />}
                title="Select a draft"
                description="Pick one from the list to read it here."
              />
            )}
          </section>
        </div>
      )}
    </div>
  );
}
