"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchSubjects } from "@/lib/api";
import Link from "next/link";
import type { Subject } from "@/types";

// ── Hierarchy definition ───────────────────────────────────────────────────────
// Each slug maps to exactly one place in the tree. Subjects not listed here
// fall into "Other" at the bottom.
type SubfieldDef = { name: string; slugs: string[] };
type FieldDef    = { name: string; accent: string; subfields: SubfieldDef[] };

const FIELDS: FieldDef[] = [
  {
    name: "Mathematics",
    accent: "text-blue-400",
    subfields: [
      {
        name: "Foundations",
        slugs: [
          "mathematics", "calculus", "linear-algebra", "algebra",
          "differential-equations", "precalculus", "trigonometry",
          "proof-writing", "applied-mathematics", "integration",
        ],
      },
      {
        name: "Analysis",
        slugs: [
          "real-analysis", "complex-analysis", "functional-analysis",
          "harmonic-analysis", "analysis", "measure-theory",
        ],
      },
      {
        name: "Algebra & Number Theory",
        slugs: [
          "number-theory", "abstract-algebra", "group-theory", "ring-theory",
          "galois-theory", "commutative-algebra", "homological-algebra",
          "representation-theory", "category-theory", "algebraic-number-theory",
        ],
      },
      {
        name: "Geometry & Topology",
        slugs: [
          "geometry", "topology", "differential-geometry", "algebraic-geometry",
          "algebraic-topology", "riemannian-geometry", "symplectic-geometry",
        ],
      },
      {
        name: "Discrete & Combinatorics",
        slugs: [
          "discrete-mathematics", "combinatorics", "graph-theory",
          "set-theory", "logic",
        ],
      },
      {
        name: "Probability & Statistics",
        slugs: [
          "probability", "statistics", "stochastic-processes",
          "bayesian-statistics", "mathematical-statistics", "stochastic-calculus",
          "bayesian-methods", "probabilistic-models", "regression",
          "time-series", "causal-inference", "statistical-computing",
        ],
      },
      {
        name: "Applied & Numerical",
        slugs: [
          "optimization", "numerical-methods", "numerical-analysis",
          "operations-research", "mathematical-optimization", "convex-optimization",
          "linear-programming", "simulation", "scientific-computing",
        ],
      },
    ],
  },
  {
    name: "Physics",
    accent: "text-purple-400",
    subfields: [
      {
        name: "Classical Physics",
        slugs: [
          "physics", "mechanics", "classical-mechanics", "electromagnetism",
          "electrodynamics", "optics", "thermodynamics", "fluid-mechanics",
          "fluid-dynamics", "continuum-mechanics", "waves",
        ],
      },
      {
        name: "Statistical & Condensed Matter",
        slugs: [
          "statistical-mechanics", "solid-state-physics", "condensed-matter",
          "materials-science",
        ],
      },
      {
        name: "Quantum Physics",
        slugs: [
          "quantum-physics", "quantum-mechanics", "quantum-field-theory",
          "quantum-computing", "quantum-information", "quantum-optics",
          "particle-physics", "nuclear-physics",
        ],
      },
      {
        name: "Relativity & Cosmology",
        slugs: [
          "relativity", "general-relativity", "special-relativity",
          "theoretical-physics", "string-theory", "astrophysics",
          "cosmology", "astronomy", "planetary-science", "planets",
        ],
      },
    ],
  },
  {
    name: "Computer Science",
    accent: "text-emerald-400",
    subfields: [
      {
        name: "AI & Machine Learning",
        slugs: [
          "machine-learning", "artificial-intelligence", "deep-learning",
          "computer-vision", "natural-language-processing", "reinforcement-learning",
          "large-language-models", "neural-networks", "generative-models",
          "ai-ethics", "ai-safety", "ai-agents", "meta-learning",
          "unsupervised-learning", "graph-neural-networks",
          "image-processing", "3d-reconstruction", "rendering",
        ],
      },
      {
        name: "Algorithms & Theory",
        slugs: [
          "algorithms", "data-structures", "theory-of-computing",
          "computational-complexity", "information-theory", "coding-theory",
        ],
      },
      {
        name: "Systems & Architecture",
        slugs: [
          "computer-science", "computer-systems", "operating-systems",
          "computer-architecture", "distributed-systems", "networking",
          "computer-networks", "embedded-systems", "systems-programming",
          "parallel-computing", "high-performance-computing",
          "systems", "computing", "hardware", "microprocessors", "internet",
          "internet-of-things", "cloud-computing", "devops", "linux",
          "autonomous-systems", "cyber-physical-systems",
          "decentralized-systems", "information-technology",
          "information-science", "computer-science-and-engineering",
        ],
      },
      {
        name: "Software & Development",
        slugs: [
          "programming", "software-engineering", "programming-languages",
          "web-development", "databases", "sql", "mobile-development",
          "game-development", "computer-graphics", "human-computer-interaction",
          "compilers", "c", "c-programming", "r", "r-programming", "python",
          "javascript", "java", "go-programming", "html", "css", "react",
          "node-js", "typescript", "swift", "lua", "haskell",
          "assembly-language", "object-oriented-programming",
          "functional-programming", "ios-development", "ui-design",
          "game-design", "systems-design",
        ],
      },
      {
        name: "Security & Privacy",
        slugs: [
          "cybersecurity", "cryptography", "computer-security",
          "digital-forensics", "systems-security", "formal-verification", "privacy",
          "zero-knowledge-proofs", "smart-contracts", "solidity",
        ],
      },
      {
        name: "Data Science",
        slugs: [
          "data-science", "data-analysis", "data-visualization", "big-data",
          "data-engineering", "data-mining", "data-management",
        ],
      },
    ],
  },
  {
    name: "Engineering",
    accent: "text-orange-400",
    subfields: [
      {
        name: "Electrical & Computer",
        slugs: [
          "electrical-engineering", "signal-processing", "control-systems",
          "electronics", "circuits", "digital-systems", "power-systems",
          "vlsi", "dsp", "digital-electronics", "control-theory",
          "communications", "digital-design",
        ],
      },
      {
        name: "Mechanical",
        slugs: [
          "mechanical-engineering", "engineering", "robotics",
          "mechatronics", "manufacturing", "vibrations", "heat-transfer",
          "engineering-design", "metallurgy",
        ],
      },
      {
        name: "Civil & Structural",
        slugs: [
          "civil-engineering", "structural-engineering", "geotechnical-engineering",
          "transportation-engineering", "water-resources", "structural-analysis",
          "urban-planning", "transportation",
        ],
      },
      {
        name: "Chemical & Bio",
        slugs: [
          "chemical-engineering", "bioengineering", "biological-engineering",
          "nanotechnology", "biotechnology",
        ],
      },
      {
        name: "Aerospace, Nuclear & Environmental",
        slugs: [
          "aerospace-engineering", "nuclear-engineering",
          "environmental-engineering", "ocean-engineering",
        ],
      },
    ],
  },
  {
    name: "Natural Sciences",
    accent: "text-teal-400",
    subfields: [
      {
        name: "Biology & Life Sciences",
        slugs: [
          "biology", "genetics", "molecular-biology", "cell-biology",
          "neuroscience", "ecology", "evolution", "life-sciences",
          "genomics", "bioinformatics", "microbiology", "immunology",
          "physiology", "botany", "computational-biology",
          "computational-neuroscience", "biochemistry", "animal-science",
          "plant-biology", "origins-of-life", "agriculture", "food-science",
        ],
      },
      {
        name: "Chemistry",
        slugs: [
          "chemistry", "organic-chemistry", "physical-chemistry",
          "inorganic-chemistry", "general-chemistry",
        ],
      },
      {
        name: "Earth & Environment",
        slugs: [
          "earth-science", "geology", "climate-science",
          "atmospheric-science", "environmental-science", "geography",
          "environmental-economics", "sustainability",
        ],
      },
      {
        name: "General Science",
        slugs: ["science", "science-communication"],
      },
      {
        name: "Medicine & Health",
        slugs: [
          "medicine", "anatomy", "epidemiology", "public-health", "health",
          "nutrition", "global-health", "clinical-trials", "pharmacology",
          "biostatistics", "forensic-science", "mental-health",
          "reproductive-health", "child-health", "maternal-health",
          "infectious-disease", "human-body", "sports-science", "gerontology",
          "health-informatics", "biomedical-informatics", "environmental-health",
        ],
      },
    ],
  },
  {
    name: "Social Sciences",
    accent: "text-rose-400",
    subfields: [
      {
        name: "Economics & Finance",
        slugs: [
          "economics", "microeconomics", "macroeconomics", "finance",
          "game-theory", "econometrics", "behavioral-economics", "accounting",
          "international-economics", "international-trade", "economic-history",
          "political-economy", "decision-theory",
        ],
      },
      {
        name: "Political Science & Law",
        slugs: [
          "political-science", "international-relations", "public-policy", "law",
          "constitutional-law", "comparative-politics", "global-politics",
          "legal-studies", "criminal-justice", "human-rights", "civil-rights",
          "environmental-law", "policy", "health-policy", "science-policy",
          "environmental-policy", "environmental-justice", "criminology",
        ],
      },
      {
        name: "Psychology & Cognitive Science",
        slugs: [
          "psychology", "cognitive-science", "social-psychology",
          "developmental-psychology", "behavioral-science", "cognitive-psychology",
          "behavior", "brain", "consciousness", "child-development",
        ],
      },
      {
        name: "Sociology & Anthropology",
        slugs: [
          "sociology", "social-science", "social-sciences", "anthropology",
          "social-theory", "demographics", "gender-studies",
          "african-american-studies", "american-studies",
        ],
      },
      {
        name: "Education & Communication",
        slugs: [
          "education", "education-technology", "communication", "journalism",
          "information-literacy",
        ],
      },
    ],
  },
  {
    name: "Humanities",
    accent: "text-amber-400",
    subfields: [
      {
        name: "History",
        slugs: [
          "history", "american-history", "ancient-history", "world-history",
          "european-history", "medieval-history",
          "western-civilization", "media-history",
        ],
      },
      {
        name: "Philosophy, Ethics & Religion",
        slugs: [
          "philosophy", "ethics", "philosophy-of-mind",
          "ancient-philosophy", "political-philosophy", "religion",
          "religious-studies", "islam", "mythology",
        ],
      },
      {
        name: "Language & Literature",
        slugs: [
          "literature", "linguistics", "english", "writing", "language",
          "poetry", "literary-theory", "arabic", "chinese", "french",
          "german", "japanese", "spanish",
        ],
      },
      {
        name: "Arts & Media",
        slugs: [
          "music", "arts", "architecture", "design", "music-theory",
          "film-studies", "theater", "photography", "animation", "art-history",
        ],
      },
      {
        name: "General Humanities",
        slugs: ["humanities"],
      },
    ],
  },
  {
    name: "Business & Management",
    accent: "text-cyan-400",
    subfields: [
      {
        name: "Business",
        slugs: [
          "business", "entrepreneurship", "management", "marketing",
          "leadership", "project-management", "logistics",
          "human-resources",
        ],
      },
      {
        name: "Technology & Society",
        slugs: [
          "technology", "blockchain", "cryptocurrency", "innovation",
          "energy", "technology-and-society", "research-methods",
        ],
      },
    ],
  },
];

// Build a set of all slugs covered by the hierarchy
const MAPPED_SLUGS = new Set(
  FIELDS.flatMap((f) => f.subfields.flatMap((sf) => sf.slugs))
);

// These are ingestion labels rather than useful subjects. Keep the source data
// intact, but do not surface them as destinations on the Subjects page.
const HIDDEN_SUBJECT_SLUGS = new Set([
  "introduction",
  "general",
  "theory",
  "development",
  "multidisciplinary",
  "humanities-and-social-sciences",
]);

// ── Component ─────────────────────────────────────────────────────────────────
export function SubjectsContent({ initialData }: { initialData?: any }) {
  const { data, isLoading } = useQuery({
    queryKey: ["subjects"],
    queryFn: () => fetchSubjects(false, false),
    initialData: initialData ?? undefined,
    // Data is baked into the static page at build time from API_UPSTREAM.
    // Never re-fetch on the client — the page loads instantly from CDN.
    // Redeploy to refresh counts.
    staleTime: Infinity,
  });

  const subjectMap = new Map<string, Subject>();
  for (const s of data?.items ?? []) {
    subjectMap.set(s.slug, s);
  }

  if (isLoading) {
    return (
      <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
        <div className="h-8 w-40 rounded bg-muted animate-pulse mb-8" />
        <div className="columns-2 md:columns-3 lg:columns-4 gap-6">
          {Array.from({ length: 24 }).map((_, i) => (
            <div key={i} className="h-6 rounded bg-muted animate-pulse mb-2 break-inside-avoid" />
          ))}
        </div>
      </div>
    );
  }

  // Derive a display name from a slug when the subject isn't in the DB yet
  function slugToName(slug: string): string {
    return slug.split("-").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  }

  type DisplaySubject = { slug: string; name: string; course_count: number };
  type RenderedSubfield = { name: string; subjects: DisplaySubject[] };
  type RenderedField    = { name: string; accent: string; subfields: RenderedSubfield[] };

  const otherSubjects = [...(data?.items ?? [])]
    .map((subject) => ({
      ...subject,
      course_count: subject.course_count ?? 0,
    }))
    .filter(
      (s) =>
        !MAPPED_SLUGS.has(s.slug) &&
        !HIDDEN_SUBJECT_SLUGS.has(s.slug) &&
        (s.course_count ?? 0) > 0
    )
    .sort((a, b) => (b.course_count ?? 0) - (a.course_count ?? 0));

  const renderedFields: RenderedField[] = FIELDS.map((field) => ({
    name: field.name,
    accent: field.accent,
    subfields: field.subfields.map((sf) => ({
      name: sf.name,
      // Keep the taxonomy available while showing only subjects with courses.
      subjects: sf.slugs.map((slug) => {
        const s = subjectMap.get(slug);
          return {
            slug,
            name: s?.name ?? slugToName(slug),
            course_count: s?.course_count ?? 0,
          };
      }).filter((subject) => subject.course_count > 0),
    })).filter((subfield) => subfield.subjects.length > 0),
  })).filter((field) => field.subfields.length > 0);

  return (
    <div className="max-w-screen-xl mx-auto px-4 md:px-8 py-8">
      <h1 className="text-2xl font-bold mb-4">Subjects</h1>

      <div className="columns-2 md:columns-3 lg:columns-4 gap-x-6">
        {renderedFields.map((field) =>
          field.subfields.map((sf, sfIdx) => (
            <div
              key={`${field.name}-${sf.name}`}
              className="break-inside-avoid mb-4"
            >
              {sfIdx === 0 && (
                <p className="mb-2 text-sm font-semibold text-foreground border-b border-border pb-1.5">
                  {field.name}
                </p>
              )}
              <p className="mb-1 px-2 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
                {sf.name}
              </p>
              {sf.subjects.map((subject) => (
                <Link
                  key={subject.slug}
                  href={`/subjects/${subject.slug}`}
                  className="flex items-center justify-between py-1 px-2 rounded
                             text-sm text-foreground/80 hover:text-primary hover:bg-primary/5
                             transition-colors group"
                >
                  <span className="truncate group-hover:text-primary transition-colors">
                    {subject.name}
                  </span>
                  <span className="ml-2 text-xs text-muted-foreground/60 tabular-nums shrink-0">
                    {subject.course_count}
                  </span>
                </Link>
              ))}
            </div>
          ))
        )}

        {otherSubjects.length > 0 && (
          <div className="break-inside-avoid mt-8">
            <p className="mb-2 text-sm font-semibold text-foreground border-b border-border pb-1.5">
              Other
            </p>
            {otherSubjects.map((subject) => (
              <Link
                key={subject.id}
                href={`/subjects/${subject.slug}`}
                className="flex items-center justify-between py-1 px-2 rounded
                           text-sm text-foreground/80 hover:text-primary hover:bg-primary/5
                           transition-colors group"
              >
                <span className="truncate group-hover:text-primary transition-colors">
                  {subject.name}
                </span>
                <span className="ml-2 text-xs text-muted-foreground/60 tabular-nums shrink-0">
                  {subject.course_count}
                </span>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
