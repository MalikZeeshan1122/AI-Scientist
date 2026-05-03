"use client";

import { useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  Calendar,
  ExternalLink,
  Filter,
  Library,
  Quote,
  Search,
  Tag,
  Users,
} from "lucide-react";
import { Badge, Card } from "@/components/Card";
import { Button } from "@/components/Button";
import { CategoryFilter } from "@/components/CategoryFilter";
import { EmptyState } from "@/components/EmptyState";
import { Input } from "@/components/Input";
import { PageHeader } from "@/components/PageHeader";
import { SkeletonList } from "@/components/Skeleton";
import { useToast } from "@/components/Toast";
import { api, type Paper } from "@/lib/api";
import { labelForCategory } from "@/lib/arxivCategories";
import { cn } from "@/lib/cn";

const SOURCE_TONE: Record<string, "accent" | "info" | "default" | "success"> = {
  arxiv: "accent",
  semantic_scholar: "info",
  openalex: "success",
  local: "default",
};

export default function PapersPage() {
  const [query, setQuery] = useState("graph neural networks");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<Paper[] | null>(null);
  const [stored, setStored] = useState<Paper[] | null>(null);
  const [filterSource, setFilterSource] = useState<string | null>(null);
  const [storedFilter, setStoredFilter] = useState("");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const toast = useToast();

  useEffect(() => {
    api<Paper[]>("/papers")
      .then(setStored)
      .catch((e) => toast.error(String(e), "Couldn't load indexed papers"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const search = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const ps = await api<Paper[]>("/search", {
        method: "POST",
        body: JSON.stringify({
          query,
          limit: 10,
          categories: selectedCategories.length ? selectedCategories : null,
        }),
      });
      setResults(ps);
      toast.success(`Found ${ps.length} papers`, "Search complete");
    } catch (e) {
      toast.error(String(e), "Search failed");
    } finally {
      setSearching(false);
    }
  };

  const sources = useMemo(() => {
    const s = new Set<string>();
    results?.forEach((p) => s.add(p.source));
    return Array.from(s);
  }, [results]);

  const filteredResults = useMemo(() => {
    if (!results) return null;
    if (!filterSource) return results;
    return results.filter((p) => p.source === filterSource);
  }, [results, filterSource]);

  const filteredStored = useMemo(() => {
    if (!stored) return null;
    const q = storedFilter.trim().toLowerCase();
    if (!q) return stored;
    return stored.filter(
      (p) =>
        p.title.toLowerCase().includes(q) ||
        p.authors.join(" ").toLowerCase().includes(q)
    );
  }, [stored, storedFilter]);

  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Library"
        title="Papers"
        description="Search across arXiv, Semantic Scholar, OpenAlex, and your local PDFs. Inspect papers already ingested by previous pipeline runs."
      />

      <Card className="overflow-hidden">
        <div
          aria-hidden
          className="pointer-events-none absolute inset-0 bg-gradient-to-br from-orange-500/[0.04] via-transparent to-amber-500/[0.03]"
        />
        <div className="relative">
          <div className="flex items-center gap-2 mb-4">
            <div className="grid place-items-center h-9 w-9 rounded-xl bg-orange-500/10 border border-orange-500/30 text-orange-500">
              <Search className="h-4 w-4" />
            </div>
            <div>
              <div className="text-sm font-semibold text-ink-50 tracking-tight">
                Multi-source search
              </div>
              <div className="text-xs text-ink-400">
                Queries arXiv, Semantic Scholar, and OpenAlex in parallel
              </div>
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-2">
            <Input
              containerClassName="flex-1"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && search()}
              placeholder="Search papers across all sources…"
              leftIcon={<Search className="h-4 w-4" />}
            />
            <Button
              onClick={search}
              disabled={!query.trim()}
              loading={searching}
              size="lg"
            >
              {searching ? "Searching…" : "Search"}
            </Button>
          </div>

          <div className="mt-4">
            <CategoryFilter
              value={selectedCategories}
              onChange={setSelectedCategories}
              label="arXiv categories"
              hint="Restrict to selected fields. Leave empty for all."
            />
          </div>

          {sources.length > 1 && (
            <div className="mt-4 flex items-center gap-2 flex-wrap">
              <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider text-ink-400 font-medium mr-1">
                <Filter className="h-3 w-3" /> Filter
              </div>
              <SourceChip
                active={filterSource === null}
                onClick={() => setFilterSource(null)}
              >
                All ({results?.length ?? 0})
              </SourceChip>
              {sources.map((src) => (
                <SourceChip
                  key={src}
                  active={filterSource === src}
                  onClick={() =>
                    setFilterSource(filterSource === src ? null : src)
                  }
                >
                  {src} ({results?.filter((p) => p.source === src).length ?? 0})
                </SourceChip>
              ))}
            </div>
          )}
        </div>
      </Card>

      {filteredResults && (
        <div>
          <SectionHeader
            icon={<Search className="h-3.5 w-3.5" />}
            title="Search results"
            count={filteredResults.length}
          />
          {filteredResults.length === 0 ? (
            <EmptyState
              icon={<Search className="h-6 w-6" />}
              title="No matches"
              description="Try a broader query or check your API keys."
            />
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              {filteredResults.map((p) => (
                <PaperCard key={p.id} p={p} />
              ))}
            </div>
          )}
        </div>
      )}

      <div>
        <div className="flex items-center justify-between gap-3 mb-3 flex-wrap">
          <SectionHeader
            icon={<Library className="h-3.5 w-3.5" />}
            title="Indexed papers"
            count={stored?.length ?? 0}
            inline
          />
          {stored && stored.length > 0 && (
            <Input
              containerClassName="w-full sm:w-72"
              value={storedFilter}
              onChange={(e) => setStoredFilter(e.target.value)}
              placeholder="Filter by title or author…"
              leftIcon={<Filter className="h-3.5 w-3.5" />}
            />
          )}
        </div>
        {!stored ? (
          <SkeletonList rows={4} />
        ) : filteredStored && filteredStored.length === 0 ? (
          <EmptyState
            icon={<BookOpen className="h-6 w-6" />}
            title={stored.length === 0 ? "No indexed papers yet" : "No matches"}
            description={
              stored.length === 0
                ? "Run the pipeline or use the search above to ingest papers."
                : "Try a different filter."
            }
          />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {filteredStored?.map((p) => <PaperCard key={p.id} p={p} />)}
          </div>
        )}
      </div>
    </div>
  );
}

function SectionHeader({
  icon,
  title,
  count,
  inline = false,
}: {
  icon: React.ReactNode;
  title: string;
  count: number;
  inline?: boolean;
}) {
  return (
    <div className={cn("flex items-center gap-2", !inline && "mb-3")}>
      <div className="text-orange-500">{icon}</div>
      <h2 className="text-[11px] uppercase tracking-[0.18em] text-ink-300 font-medium">
        {title}
      </h2>
      <Badge>{count}</Badge>
    </div>
  );
}

function SourceChip({
  children,
  active,
  onClick,
}: {
  children: React.ReactNode;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "text-[11px] uppercase tracking-wider font-medium px-2.5 py-1 rounded-full border transition",
        active
          ? "bg-orange-500/15 text-orange-600 border-orange-500/40"
          : "bg-ink-850 text-ink-300 border-ink-700 hover:border-ink-600 hover:text-ink-50"
      )}
    >
      {children}
    </button>
  );
}

function PaperCard({ p }: { p: Paper }) {
  const tone = SOURCE_TONE[p.source] ?? "default";
  return (
    <Card className="group overflow-hidden hover-lift hover:border-ink-600">
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="text-[15px] font-semibold text-ink-50 leading-snug tracking-tight min-w-0">
          {p.url ? (
            <a
              href={p.url}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-start gap-1 hover:text-orange-600 transition"
            >
              <span>{p.title}</span>
              <ExternalLink className="h-3 w-3 mt-1 shrink-0 opacity-0 group-hover:opacity-100 transition" />
            </a>
          ) : (
            p.title
          )}
        </div>
        <Badge tone={tone}>{p.source}</Badge>
      </div>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-ink-400 mb-3">
        {p.authors.length > 0 && (
          <span className="inline-flex items-center gap-1 min-w-0">
            <Users className="h-3 w-3 shrink-0" />
            <span className="truncate">
              {p.authors.slice(0, 4).join(", ")}
              {p.authors.length > 4 && ` +${p.authors.length - 4}`}
            </span>
          </span>
        )}
        {p.published && (
          <span className="inline-flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {p.published}
          </span>
        )}
        {p.citation_count != null && (
          <span className="inline-flex items-center gap-1">
            <Quote className="h-3 w-3" />
            {p.citation_count} cites
          </span>
        )}
        {p.journal_ref && (
          <span
            className="inline-flex items-center gap-1 truncate max-w-[18rem]"
            title={p.journal_ref}
          >
            <BookOpen className="h-3 w-3" />
            {p.journal_ref}
          </span>
        )}
      </div>
      {p.categories && p.categories.length > 0 && (
        <div className="flex flex-wrap items-center gap-1 mb-3">
          <Tag className="h-3 w-3 text-ink-400 mr-1" />
          {p.categories.slice(0, 6).map((cat) => (
            <span
              key={cat}
              title={labelForCategory(cat)}
              className={cn(
                "text-[10px] font-mono px-1.5 py-0.5 rounded border",
                cat === p.primary_category
                  ? "bg-orange-500/12 text-orange-700 border-orange-500/30"
                  : "bg-ink-850 text-ink-300 border-ink-700"
              )}
            >
              {cat}
            </span>
          ))}
          {p.categories.length > 6 && (
            <span className="text-[10px] text-ink-400">
              +{p.categories.length - 6}
            </span>
          )}
        </div>
      )}
      {p.summary ? (
        <p className="text-sm text-ink-200 leading-relaxed">{p.summary}</p>
      ) : (
        <p className="text-sm text-ink-300 leading-relaxed line-clamp-3">
          {p.abstract}
        </p>
      )}
      {p.comment && (
        <p className="mt-2 text-[11px] text-ink-400 italic">{p.comment}</p>
      )}
      {p.key_findings && p.key_findings.length > 0 && (
        <div className="mt-3 pt-3 border-t border-ink-700">
          <div className="text-[10px] uppercase tracking-wider text-ink-400 font-medium mb-1.5">
            Key findings
          </div>
          <ul className="space-y-1">
            {p.key_findings.slice(0, 3).map((f, i) => (
              <li
                key={i}
                className="text-[12.5px] text-ink-200 leading-relaxed pl-3 relative before:absolute before:left-0 before:top-2 before:h-1 before:w-1 before:rounded-full before:bg-orange-400"
              >
                {f}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
