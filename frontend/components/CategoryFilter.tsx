"use client";

import { useMemo, useState } from "react";
import { ChevronDown, ChevronUp, X } from "lucide-react";
import { cn } from "@/lib/cn";
import {
  ARXIV_CATEGORIES,
  ARXIV_CATEGORY_BY_CODE,
  type ArxivCategory,
} from "@/lib/arxivCategories";

const POPULAR = ["cs.LG", "cs.AI", "cs.CL", "cs.CV", "stat.ML"];

export function CategoryFilter({
  value,
  onChange,
  label = "Categories",
  hint,
  popular = POPULAR,
}: {
  value: string[];
  onChange: (next: string[]) => void;
  label?: string;
  hint?: string;
  popular?: string[];
}) {
  const [expanded, setExpanded] = useState(false);

  const groups = useMemo(() => {
    const byGroup = new Map<ArxivCategory["group"], ArxivCategory[]>();
    for (const cat of ARXIV_CATEGORIES) {
      const arr = byGroup.get(cat.group) ?? [];
      arr.push(cat);
      byGroup.set(cat.group, arr);
    }
    return Array.from(byGroup.entries());
  }, []);

  const toggle = (code: string) => {
    if (value.includes(code)) {
      onChange(value.filter((c) => c !== code));
    } else {
      onChange([...value, code]);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[11px] uppercase tracking-wider text-ink-400 font-medium">
            {label}
          </span>
          {value.length > 0 && (
            <button
              type="button"
              onClick={() => onChange([])}
              className="text-[11px] text-ink-400 hover:text-ink-50 inline-flex items-center gap-1"
            >
              <X className="h-3 w-3" />
              Clear ({value.length})
            </button>
          )}
        </div>
        <button
          type="button"
          onClick={() => setExpanded((e) => !e)}
          className="text-[11px] text-ink-400 hover:text-ink-50 inline-flex items-center gap-1"
        >
          {expanded ? "Less" : "More"}
          {expanded ? (
            <ChevronUp className="h-3 w-3" />
          ) : (
            <ChevronDown className="h-3 w-3" />
          )}
        </button>
      </div>

      {!expanded ? (
        <div className="flex flex-wrap gap-1.5">
          {popular.map((code) => (
            <CategoryChip
              key={code}
              code={code}
              active={value.includes(code)}
              onClick={() => toggle(code)}
            />
          ))}
          {value
            .filter((c) => !popular.includes(c))
            .map((code) => (
              <CategoryChip
                key={code}
                code={code}
                active
                onClick={() => toggle(code)}
              />
            ))}
        </div>
      ) : (
        <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
          {groups.map(([group, cats]) => (
            <div key={group}>
              <div className="text-[10px] uppercase tracking-wider text-ink-400 mb-1">
                {group}
              </div>
              <div className="flex flex-wrap gap-1.5">
                {cats.map((cat) => (
                  <CategoryChip
                    key={cat.code}
                    code={cat.code}
                    active={value.includes(cat.code)}
                    onClick={() => toggle(cat.code)}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {hint && <p className="mt-2 text-[11px] text-ink-400">{hint}</p>}
    </div>
  );
}

function CategoryChip({
  code,
  active,
  onClick,
}: {
  code: string;
  active: boolean;
  onClick: () => void;
}) {
  const meta = ARXIV_CATEGORY_BY_CODE[code];
  return (
    <button
      type="button"
      onClick={onClick}
      title={meta?.field ?? code}
      className={cn(
        "text-[11px] font-mono px-2 py-0.5 rounded border transition",
        active
          ? "bg-orange-500/15 text-orange-700 border-orange-500/40"
          : "bg-ink-850 text-ink-300 border-ink-700 hover:border-ink-600 hover:text-ink-50"
      )}
    >
      {code}
    </button>
  );
}
