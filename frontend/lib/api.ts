export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export async function api<T = unknown>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let message = text || res.statusText;
    try {
      const parsed = JSON.parse(text);
      if (parsed?.detail) message = parsed.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(`API ${res.status}: ${message}`);
  }
  return (await res.json()) as T;
}

export type Project = {
  id: string;
  topic: string;
  created_at: string;
};

export type Paper = {
  id: string;
  source: string;
  title: string;
  abstract?: string;
  authors: string[];
  published?: string | null;
  venue?: string | null;
  url?: string | null;
  pdf_url?: string | null;
  citation_count?: number | null;
  primary_category?: string | null;
  categories?: string[];
  comment?: string | null;
  journal_ref?: string | null;
  summary?: string | null;
  key_findings?: string[];
  open_questions?: string[];
};

export type IdeaScore = {
  novelty: number;
  feasibility: number;
  impact: number;
  rationale: string;
  overall?: number;
};

export type Idea = {
  id: string;
  topic: string;
  title: string;
  hypothesis: string;
  motivation: string;
  proposed_method: string;
  expected_outcome: string;
  related_paper_ids: string[];
  keywords: string[];
  score?: IdeaScore | null;
  created_at: string;
};

export type ExperimentResult = {
  status: "pending" | "running" | "succeeded" | "failed" | "timed_out";
  stdout: string;
  stderr: string;
  returncode: number | null;
  duration_s: number;
  artifacts: string[];
  metrics: Record<string, number>;
};

export type Experiment = {
  id: string;
  idea_id: string | null;
  title: string;
  description: string;
  code: string;
  requirements: string[];
  result: ExperimentResult | null;
  created_at: string;
};

export type DraftSection = { name: string; content: string };

export type Draft = {
  id: string;
  idea_id: string | null;
  experiment_id: string | null;
  title: string;
  abstract: string;
  sections: DraftSection[];
  references: string[];
  format: "markdown" | "latex";
  rendered_path: string | null;
  created_at: string;
};
