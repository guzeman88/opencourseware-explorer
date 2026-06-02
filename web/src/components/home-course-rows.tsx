"use client";

import { useEffect, useRef, useState } from "react";

import { ContinueWatchingRow } from "@/components/continue-watching-row";
import { CourseRow } from "@/components/course-row";
import { UniversityGrid } from "@/components/university-grid";
import type { CourseLevel, CourseSummary, PaginatedList } from "@/types";

type RowConfig = {
  title: string;
  queryKey: string;
  fetchType: "featured" | "university" | "subject" | "level" | "query";
  universitySlug?: string;
  subjectSlug?: string;
  level?: CourseLevel;
  queryString?: string;
};

const INITIAL_DEFERRED_ROWS = 3;
const ROW_BATCH_SIZE = 8;

const deferredRows: RowConfig[] = [
  { title: "Machine Learning & AI", queryKey: "ml", fetchType: "subject", subjectSlug: "machine-learning" },
  { title: "Artificial Intelligence", queryKey: "ai", fetchType: "subject", subjectSlug: "artificial-intelligence" },
  { title: "Mathematics", queryKey: "math", fetchType: "subject", subjectSlug: "mathematics" },
  { title: "Algorithms & Data Structures", queryKey: "algo", fetchType: "subject", subjectSlug: "algorithms" },
  { title: "Deep Learning & Neural Networks", queryKey: "dl", fetchType: "subject", subjectSlug: "deep-learning" },
  { title: "Natural Language Processing", queryKey: "nlp", fetchType: "subject", subjectSlug: "natural-language-processing" },
  { title: "Computer Vision", queryKey: "cv", fetchType: "subject", subjectSlug: "computer-vision" },
  { title: "Reinforcement Learning", queryKey: "rl", fetchType: "subject", subjectSlug: "reinforcement-learning" },
  { title: "Large Language Models", queryKey: "llm", fetchType: "subject", subjectSlug: "large-language-models" },
  { title: "Cybersecurity", queryKey: "cyber", fetchType: "subject", subjectSlug: "cybersecurity" },
  { title: "Cryptography", queryKey: "crypto", fetchType: "subject", subjectSlug: "cryptography" },
  { title: "Operating Systems", queryKey: "os", fetchType: "subject", subjectSlug: "operating-systems" },
  { title: "Computer Systems", queryKey: "compsys", fetchType: "subject", subjectSlug: "computer-systems" },
  { title: "Computer Architecture", queryKey: "arch", fetchType: "subject", subjectSlug: "computer-architecture" },
  { title: "Databases", queryKey: "db", fetchType: "subject", subjectSlug: "databases" },
  { title: "Networking & Distributed Systems", queryKey: "net", fetchType: "subject", subjectSlug: "networking" },
  { title: "Software Engineering", queryKey: "swe", fetchType: "subject", subjectSlug: "software-engineering" },
  { title: "Programming Languages", queryKey: "pl", fetchType: "subject", subjectSlug: "programming-languages" },
  { title: "Compilers", queryKey: "compilers", fetchType: "subject", subjectSlug: "compilers" },
  { title: "Systems Programming", queryKey: "sysprog", fetchType: "subject", subjectSlug: "systems-programming" },
  { title: "Computer Graphics", queryKey: "graphics", fetchType: "subject", subjectSlug: "computer-graphics" },
  { title: "Human-Computer Interaction", queryKey: "hci", fetchType: "subject", subjectSlug: "human-computer-interaction" },
  { title: "Quantum Computing", queryKey: "qc", fetchType: "subject", subjectSlug: "quantum-computing" },
  { title: "Robotics", queryKey: "robotics", fetchType: "subject", subjectSlug: "robotics" },
  { title: "Python Programming", queryKey: "python", fetchType: "subject", subjectSlug: "python" },
  { title: "Web Development", queryKey: "web", fetchType: "query", queryString: "web development" },
  { title: "Calculus", queryKey: "calc", fetchType: "query", queryString: "calculus" },
  { title: "Linear Algebra", queryKey: "linalg", fetchType: "subject", subjectSlug: "linear-algebra" },
  { title: "Differential Equations", queryKey: "diffeq", fetchType: "query", queryString: "differential equations" },
  { title: "Probability & Statistics", queryKey: "prob", fetchType: "subject", subjectSlug: "probability" },
  { title: "Statistics", queryKey: "stats", fetchType: "subject", subjectSlug: "statistics" },
  { title: "Real Analysis", queryKey: "analysis", fetchType: "query", queryString: "real analysis" },
  { title: "Abstract & Modern Algebra", queryKey: "algebra", fetchType: "query", queryString: "abstract algebra modern algebra" },
  { title: "Number Theory", queryKey: "numtheory", fetchType: "query", queryString: "number theory" },
  { title: "Topology", queryKey: "topology", fetchType: "query", queryString: "topology" },
  { title: "Combinatorics & Graph Theory", queryKey: "combo", fetchType: "query", queryString: "combinatorics graph theory" },
  { title: "Discrete Mathematics", queryKey: "discrete", fetchType: "query", queryString: "discrete mathematics" },
  { title: "Optimization & Convex Analysis", queryKey: "optim", fetchType: "query", queryString: "optimization convex" },
  { title: "Numerical Methods", queryKey: "numerical", fetchType: "query", queryString: "numerical methods" },
  { title: "Algebraic Geometry", queryKey: "alggeom", fetchType: "query", queryString: "algebraic geometry" },
  { title: "Complex Analysis", queryKey: "complexan", fetchType: "query", queryString: "complex analysis" },
  { title: "Applied Mathematics", queryKey: "appliedmath", fetchType: "query", queryString: "applied mathematics" },
  { title: "Information Theory", queryKey: "infotheory", fetchType: "query", queryString: "information theory" },
  { title: "Stochastic Processes", queryKey: "stochastic", fetchType: "query", queryString: "stochastic" },
  { title: "Fourier Analysis", queryKey: "fourier", fetchType: "query", queryString: "fourier" },
  { title: "Physics", queryKey: "physics", fetchType: "subject", subjectSlug: "physics" },
  { title: "Quantum Physics", queryKey: "qm", fetchType: "subject", subjectSlug: "quantum-physics" },
  { title: "Quantum Mechanics", queryKey: "qmech", fetchType: "query", queryString: "quantum mechanics" },
  { title: "Quantum Field Theory", queryKey: "qft", fetchType: "query", queryString: "quantum field theory" },
  { title: "Classical Mechanics", queryKey: "cm", fetchType: "query", queryString: "classical mechanics" },
  { title: "Special & General Relativity", queryKey: "relativity", fetchType: "query", queryString: "relativity" },
  { title: "Statistical Mechanics", queryKey: "statmech", fetchType: "query", queryString: "statistical mechanics" },
  { title: "Thermodynamics", queryKey: "thermo", fetchType: "query", queryString: "thermodynamics" },
  { title: "Electromagnetism", queryKey: "em", fetchType: "query", queryString: "electromagnetism electricity magnetism" },
  { title: "Astrophysics & Cosmology", queryKey: "astro", fetchType: "query", queryString: "astrophysics cosmology" },
  { title: "Particle Physics", queryKey: "particle", fetchType: "query", queryString: "particle physics" },
  { title: "Optics", queryKey: "optics", fetchType: "query", queryString: "optics" },
  { title: "Nuclear Physics", queryKey: "nuclear", fetchType: "query", queryString: "nuclear physics" },
  { title: "Theoretical Physics", queryKey: "theophys", fetchType: "query", queryString: "theoretical physics" },
  { title: "Solid State Physics", queryKey: "solidstate", fetchType: "query", queryString: "solid state physics condensed matter" },
  { title: "Fluid Mechanics", queryKey: "fluid", fetchType: "query", queryString: "fluid mechanics" },
  { title: "Chemistry", queryKey: "chem", fetchType: "subject", subjectSlug: "chemistry" },
  { title: "Organic Chemistry", queryKey: "orgchem", fetchType: "subject", subjectSlug: "organic-chemistry" },
  { title: "Biochemistry", queryKey: "biochem", fetchType: "subject", subjectSlug: "biochemistry" },
  { title: "Physical Chemistry", queryKey: "pchem", fetchType: "subject", subjectSlug: "physical-chemistry" },
  { title: "Biology", queryKey: "bio", fetchType: "subject", subjectSlug: "biology" },
  { title: "Molecular Biology", queryKey: "molbio", fetchType: "subject", subjectSlug: "molecular-biology" },
  { title: "Cell Biology", queryKey: "cellbio", fetchType: "subject", subjectSlug: "cell-biology" },
  { title: "Neuroscience", queryKey: "neuro", fetchType: "subject", subjectSlug: "neuroscience" },
  { title: "Genetics", queryKey: "genetics", fetchType: "query", queryString: "genetics" },
  { title: "Microbiology", queryKey: "micro", fetchType: "subject", subjectSlug: "microbiology" },
  { title: "Computational Biology", queryKey: "compbio", fetchType: "subject", subjectSlug: "computational-biology" },
  { title: "Ecology & Evolution", queryKey: "ecology", fetchType: "query", queryString: "ecology evolution" },
  { title: "Electrical Engineering", queryKey: "ee", fetchType: "subject", subjectSlug: "electrical-engineering" },
  { title: "Signal Processing", queryKey: "signal", fetchType: "subject", subjectSlug: "signal-processing" },
  { title: "Control Systems", queryKey: "control", fetchType: "subject", subjectSlug: "control-systems" },
  { title: "Circuits & Electronics", queryKey: "circuits", fetchType: "subject", subjectSlug: "circuits" },
  { title: "Mechanical Engineering", queryKey: "me", fetchType: "subject", subjectSlug: "mechanical-engineering" },
  { title: "Chemical Engineering", queryKey: "che", fetchType: "subject", subjectSlug: "chemical-engineering" },
  { title: "Civil Engineering", queryKey: "ce", fetchType: "subject", subjectSlug: "civil-engineering" },
  { title: "Materials Science", queryKey: "matscience", fetchType: "subject", subjectSlug: "materials-science" },
  { title: "Bioengineering", queryKey: "bioe", fetchType: "subject", subjectSlug: "bioengineering" },
  { title: "Aerospace Engineering", queryKey: "aero", fetchType: "subject", subjectSlug: "aerospace-engineering" },
  { title: "Economics", queryKey: "econ", fetchType: "subject", subjectSlug: "economics" },
  { title: "Microeconomics", queryKey: "micro-econ", fetchType: "subject", subjectSlug: "microeconomics" },
  { title: "Macroeconomics", queryKey: "macro-econ", fetchType: "subject", subjectSlug: "macroeconomics" },
  { title: "Finance & Accounting", queryKey: "finance", fetchType: "subject", subjectSlug: "finance" },
  { title: "Entrepreneurship", queryKey: "entrepr", fetchType: "subject", subjectSlug: "entrepreneurship" },
  { title: "Business & Management", queryKey: "business", fetchType: "subject", subjectSlug: "business" },
  { title: "Econometrics & Data", queryKey: "econometrics", fetchType: "query", queryString: "econometrics" },
  { title: "Game Theory", queryKey: "gametheory", fetchType: "query", queryString: "game theory" },
  { title: "Political Science", queryKey: "polisci", fetchType: "subject", subjectSlug: "political-science" },
  { title: "Psychology", queryKey: "psych", fetchType: "subject", subjectSlug: "psychology" },
  { title: "Sociology", queryKey: "soc", fetchType: "subject", subjectSlug: "sociology" },
  { title: "Philosophy", queryKey: "phil", fetchType: "subject", subjectSlug: "philosophy" },
  { title: "History", queryKey: "hist", fetchType: "subject", subjectSlug: "history" },
  { title: "Linguistics", queryKey: "ling", fetchType: "subject", subjectSlug: "linguistics" },
  { title: "Law", queryKey: "law", fetchType: "subject", subjectSlug: "law" },
  { title: "Medicine & Health", queryKey: "medicine", fetchType: "subject", subjectSlug: "medicine" },
  { title: "Public Health", queryKey: "pubhealth", fetchType: "subject", subjectSlug: "public-health" },
  { title: "Anatomy & Physiology", queryKey: "anatomy", fetchType: "subject", subjectSlug: "anatomy" },
  { title: "Immunology", queryKey: "immuno", fetchType: "subject", subjectSlug: "immunology" },
  { title: "Data Science", queryKey: "ds", fetchType: "subject", subjectSlug: "data-science" },
  { title: "Bayesian Methods", queryKey: "bayes", fetchType: "subject", subjectSlug: "bayesian-methods" },
  { title: "Time Series Analysis", queryKey: "timeseries", fetchType: "subject", subjectSlug: "time-series" },
  { title: "Causal Inference", queryKey: "causal", fetchType: "subject", subjectSlug: "causal-inference" },
  { title: "Graduate Level Courses", queryKey: "grad", fetchType: "level", level: "graduate" },
  { title: "Introduction to Everything", queryKey: "intro", fetchType: "query", queryString: "introduction to" },
  { title: "Most Comprehensive (100+ Videos)", queryKey: "long", fetchType: "query", queryString: "lecture" },
  { title: "MIT OpenCourseWare", queryKey: "mit", fetchType: "university", universitySlug: "mit" },
  { title: "Stanford University", queryKey: "stanford", fetchType: "university", universitySlug: "stanford" },
  { title: "UC Berkeley", queryKey: "berkeley", fetchType: "university", universitySlug: "berkeley" },
  { title: "Yale Open Courses", queryKey: "yale", fetchType: "university", universitySlug: "yale" },
  { title: "Harvard University", queryKey: "harvard", fetchType: "university", universitySlug: "harvard" },
  { title: "Khan Academy", queryKey: "khan", fetchType: "university", universitySlug: "khan-academy" },
  { title: "freeCodeCamp", queryKey: "fcc", fetchType: "university", universitySlug: "freecodecamp" },
  { title: "3Blue1Brown", queryKey: "3b1b", fetchType: "university", universitySlug: "3blue1brown" },
  { title: "Crash Course", queryKey: "crash", fetchType: "university", universitySlug: "crash-course" },
  { title: "Carnegie Mellon University", queryKey: "cmu", fetchType: "university", universitySlug: "carnegie-mellon" },
  { title: "Georgia Tech", queryKey: "gatech", fetchType: "university", universitySlug: "georgia-tech" },
  { title: "Princeton University", queryKey: "princeton", fetchType: "university", universitySlug: "princeton" },
  { title: "Columbia University", queryKey: "columbia", fetchType: "university", universitySlug: "columbia" },
  { title: "ETH Zurich", queryKey: "eth", fetchType: "university", universitySlug: "eth-zurich" },
  { title: "TU Delft", queryKey: "tudelft", fetchType: "university", universitySlug: "tu-delft" },
  { title: "Oxford University", queryKey: "oxford", fetchType: "university", universitySlug: "oxford" },
  { title: "Cambridge University", queryKey: "cambridge", fetchType: "university", universitySlug: "cambridge" },
  { title: "Professor Leonard", queryKey: "prof-leonard", fetchType: "university", universitySlug: "professor-leonard" },
  { title: "Neso Academy", queryKey: "neso", fetchType: "university", universitySlug: "neso-academy" },
  { title: "Steve Brunton - Data Science", queryKey: "eigensteve", fetchType: "university", universitySlug: "eigensteve" },
  { title: "CS50 by Harvard", queryKey: "cs50", fetchType: "university", universitySlug: "cs50" },
  { title: "fast.ai - Deep Learning", queryKey: "fastai", fetchType: "university", universitySlug: "fastai" },
  { title: "StatQuest", queryKey: "statquest", fetchType: "university", universitySlug: "statquest" },
  { title: "The Organic Chemistry Tutor", queryKey: "octutor", fetchType: "university", universitySlug: "organic-chem-tutor" },
  { title: "Michel van Biezen", queryKey: "vanbiezen", fetchType: "university", universitySlug: "michel-van-biezen" },
  { title: "Dr. Trefor Bazett", queryKey: "drtefor", fetchType: "university", universitySlug: "dr-trefor" },
  { title: "Reducible", queryKey: "reducible", fetchType: "university", universitySlug: "reducible" },
];

interface HomeCourseRowsProps {
  featured?: PaginatedList<CourseSummary>;
  computerScience?: PaginatedList<CourseSummary>;
}

export function HomeCourseRows({ featured, computerScience }: HomeCourseRowsProps) {
  const sentinelRef = useRef<HTMLDivElement>(null);
  const [visibleDeferredRows, setVisibleDeferredRows] = useState(INITIAL_DEFERRED_ROWS);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    if (!("IntersectionObserver" in window)) {
      setVisibleDeferredRows(deferredRows.length);
      return;
    }

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        setVisibleDeferredRows((count) =>
          Math.min(count + ROW_BATCH_SIZE, deferredRows.length)
        );
      },
      { rootMargin: "900px" }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  const rowsToRender = deferredRows.slice(0, visibleDeferredRows);

  return (
    <>
      <ContinueWatchingRow />
      <CourseRow
        title="Featured Courses"
        queryKey="featured"
        fetchType="featured"
        initialData={featured}
        priority
      />
      <CourseRow
        title="Computer Science"
        queryKey="cs"
        fetchType="subject"
        subjectSlug="computer-science"
        initialData={computerScience}
      />

      {rowsToRender.map((row) => (
        <CourseRow key={row.queryKey} {...row} />
      ))}

      {visibleDeferredRows < deferredRows.length ? (
        <div ref={sentinelRef} aria-hidden="true" className="h-12" />
      ) : (
        <section>
          <h2 className="text-xl font-semibold text-foreground mb-4">Browse by University</h2>
          <UniversityGrid />
        </section>
      )}
    </>
  );
}
