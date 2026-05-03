export type ArxivCategory = {
  code: string;
  field: string;
  group: "CS" | "Stats" | "Math" | "Bio" | "Finance" | "Econ" | "Physics";
};

export const ARXIV_CATEGORIES: ArxivCategory[] = [
  { code: "cs.AI", field: "Artificial Intelligence", group: "CS" },
  { code: "cs.LG", field: "Machine Learning", group: "CS" },
  { code: "cs.CL", field: "Computation and Language (NLP)", group: "CS" },
  { code: "cs.CV", field: "Computer Vision", group: "CS" },
  { code: "cs.RO", field: "Robotics", group: "CS" },
  { code: "cs.NE", field: "Neural and Evolutionary Computing", group: "CS" },
  { code: "cs.IR", field: "Information Retrieval", group: "CS" },
  { code: "cs.CR", field: "Cryptography and Security", group: "CS" },
  { code: "cs.DC", field: "Distributed Computing", group: "CS" },
  { code: "cs.SE", field: "Software Engineering", group: "CS" },
  { code: "cs.HC", field: "Human-Computer Interaction", group: "CS" },
  { code: "stat.ML", field: "Statistics — Machine Learning", group: "Stats" },
  { code: "math.OC", field: "Math — Optimization and Control", group: "Math" },
  {
    code: "q-bio.NC",
    field: "Quantitative Biology — Neurons and Cognition",
    group: "Bio",
  },
  {
    code: "q-fin.TR",
    field: "Quantitative Finance — Trading and Microstructure",
    group: "Finance",
  },
  { code: "econ.EM", field: "Economics — Econometrics", group: "Econ" },
  { code: "physics.bio-ph", field: "Physics — Biological Physics", group: "Physics" },
  { code: "hep-ph", field: "High Energy Physics — Phenomenology", group: "Physics" },
];

export const ARXIV_CATEGORY_BY_CODE: Record<string, ArxivCategory> =
  Object.fromEntries(ARXIV_CATEGORIES.map((c) => [c.code, c]));

/** Pretty label, falling back to the raw code (e.g. for OpenAlex / S2 categories). */
export function labelForCategory(code: string): string {
  return ARXIV_CATEGORY_BY_CODE[code]?.field ?? code;
}
