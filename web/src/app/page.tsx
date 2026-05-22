import { HeroBanner } from "@/components/hero-banner";
import { CourseRow } from "@/components/course-row";
import { UniversityGrid } from "@/components/university-grid";
import type { PaginatedList, CourseSummary } from "@/types";

// ISR: full page HTML is generated once and cached at Vercel's edge CDN.
// After the first render, every visitor gets sub-100ms TTFB from CDN.
// Background revalidation keeps data fresh without blocking users.
export const revalidate = 3600;

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

async function serverFetch(path: string): Promise<PaginatedList<CourseSummary> | undefined> {
  try {
    const res = await fetch(`${API}/api/v1${path}`, {
      next: { revalidate: 3600 },
      // Short timeout: if Railway cold-starts during ISR regen, fail fast and
      // render with skeleton data. Client will fill from Vercel CDN cache.
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return undefined;
    return res.json();
  } catch {
    return undefined;
  }
}

export default async function HomePage() {
  // Fetch above-the-fold rows server-side so they appear instantly
  const [featured, cs, ml, math, ai, algo, physics, ds] = await Promise.all([
    serverFetch("/courses/featured?page_size=18&has_video_lectures=true"),
    serverFetch("/courses?subject_slug=computer-science&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true"),
    serverFetch("/courses?subject_slug=machine-learning&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true"),
    serverFetch("/courses?subject_slug=mathematics&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true"),
    serverFetch("/courses?subject_slug=artificial-intelligence&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true"),
    serverFetch("/courses?subject_slug=algorithms&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true"),
    serverFetch("/courses?subject_slug=physics&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true"),
    serverFetch("/courses?subject_slug=data-science&page_size=18&sort_by=view_count&sort_dir=desc&has_video_lectures=true"),
  ]);

  return (
    <div className="space-y-0">
      <div className="hidden md:block">
        <HeroBanner initialData={featured} />
      </div>

      <div className="px-4 md:px-8 lg:px-12 space-y-10 pb-16 md:-mt-32 relative z-10">

        {/* ── Above the fold ─────────────────────────────────────── */}
        <div className="hidden md:block">
          <CourseRow title="Featured Courses" queryKey="featured" fetchType="featured" initialData={featured} priority />
        </div>
        <CourseRow title="Computer Science"           queryKey="cs"         fetchType="subject"   subjectSlug="computer-science"  initialData={cs}   priority />
        <CourseRow title="Machine Learning & AI"      queryKey="ml"         fetchType="subject"   subjectSlug="machine-learning"  initialData={ml}   priority />
        <CourseRow title="Artificial Intelligence"     queryKey="ai"         fetchType="subject"   subjectSlug="artificial-intelligence" initialData={ai} priority />
        <CourseRow title="Mathematics"                queryKey="math"       fetchType="subject"   subjectSlug="mathematics"       initialData={math} priority />

        {/* ── CS Deep Dives ──────────────────────────────────────── */}
        <CourseRow title="Algorithms & Data Structures"    queryKey="algo"        fetchType="subject" subjectSlug="algorithms" initialData={algo} />
        <CourseRow title="Deep Learning & Neural Networks" queryKey="dl"          fetchType="subject" subjectSlug="deep-learning" />
        <CourseRow title="Natural Language Processing"     queryKey="nlp"         fetchType="subject" subjectSlug="natural-language-processing" />
        <CourseRow title="Computer Vision"                 queryKey="cv"          fetchType="subject" subjectSlug="computer-vision" />
        <CourseRow title="Reinforcement Learning"          queryKey="rl"          fetchType="subject" subjectSlug="reinforcement-learning" />
        <CourseRow title="Large Language Models"           queryKey="llm"         fetchType="subject" subjectSlug="large-language-models" />
        <CourseRow title="Cybersecurity"                   queryKey="cyber"       fetchType="subject" subjectSlug="cybersecurity" />
        <CourseRow title="Cryptography"                    queryKey="crypto"      fetchType="subject" subjectSlug="cryptography" />
        <CourseRow title="Operating Systems"               queryKey="os"          fetchType="subject" subjectSlug="operating-systems" />
        <CourseRow title="Computer Systems"                queryKey="compsys"     fetchType="subject" subjectSlug="computer-systems" />
        <CourseRow title="Computer Architecture"           queryKey="arch"        fetchType="subject" subjectSlug="computer-architecture" />
        <CourseRow title="Databases"                       queryKey="db"          fetchType="subject" subjectSlug="databases" />
        <CourseRow title="Networking & Distributed Systems" queryKey="net"        fetchType="subject" subjectSlug="networking" />
        <CourseRow title="Software Engineering"            queryKey="swe"         fetchType="subject" subjectSlug="software-engineering" />
        <CourseRow title="Programming Languages"           queryKey="pl"          fetchType="subject" subjectSlug="programming-languages" />
        <CourseRow title="Compilers"                       queryKey="compilers"   fetchType="subject" subjectSlug="compilers" />
        <CourseRow title="Systems Programming"             queryKey="sysprog"     fetchType="subject" subjectSlug="systems-programming" />
        <CourseRow title="Computer Graphics"               queryKey="graphics"    fetchType="subject" subjectSlug="computer-graphics" />
        <CourseRow title="Human-Computer Interaction"      queryKey="hci"         fetchType="subject" subjectSlug="human-computer-interaction" />
        <CourseRow title="Quantum Computing"               queryKey="qc"          fetchType="subject" subjectSlug="quantum-computing" />
        <CourseRow title="Robotics"                        queryKey="robotics"    fetchType="subject" subjectSlug="robotics" />
        <CourseRow title="Python Programming"              queryKey="python"      fetchType="subject" subjectSlug="python" />
        <CourseRow title="Web Development"                 queryKey="web"         fetchType="query"   queryString="web development" />
        <CourseRow title="Data Science"                    queryKey="ds"          fetchType="subject" subjectSlug="data-science" initialData={ds} />

        {/* ── Math Deep Dives ────────────────────────────────────── */}
        <CourseRow title="Calculus"                    queryKey="calc"        fetchType="query"   queryString="calculus" />
        <CourseRow title="Linear Algebra"              queryKey="linalg"      fetchType="subject" subjectSlug="linear-algebra" />
        <CourseRow title="Differential Equations"      queryKey="diffeq"      fetchType="query"   queryString="differential equations" />
        <CourseRow title="Probability & Statistics"    queryKey="prob"        fetchType="subject" subjectSlug="probability" />
        <CourseRow title="Statistics"                  queryKey="stats"       fetchType="subject" subjectSlug="statistics" />
        <CourseRow title="Real Analysis"               queryKey="analysis"    fetchType="query"   queryString="real analysis" />
        <CourseRow title="Abstract & Modern Algebra"   queryKey="algebra"     fetchType="query"   queryString="abstract algebra modern algebra" />
        <CourseRow title="Number Theory"               queryKey="numtheory"   fetchType="query"   queryString="number theory" />
        <CourseRow title="Topology"                    queryKey="topology"    fetchType="query"   queryString="topology" />
        <CourseRow title="Combinatorics & Graph Theory" queryKey="combo"      fetchType="query"   queryString="combinatorics graph theory" />
        <CourseRow title="Discrete Mathematics"        queryKey="discrete"    fetchType="query"   queryString="discrete mathematics" />
        <CourseRow title="Optimization & Convex Analysis" queryKey="optim"   fetchType="query"   queryString="optimization convex" />
        <CourseRow title="Numerical Methods"           queryKey="numerical"   fetchType="query"   queryString="numerical methods" />
        <CourseRow title="Algebraic Geometry"          queryKey="alggeom"     fetchType="query"   queryString="algebraic geometry" />
        <CourseRow title="Complex Analysis"            queryKey="complexan"   fetchType="query"   queryString="complex analysis" />
        <CourseRow title="Applied Mathematics"         queryKey="appliedmath" fetchType="query"   queryString="applied mathematics" />
        <CourseRow title="Information Theory"          queryKey="infotheory"  fetchType="query"   queryString="information theory" />
        <CourseRow title="Stochastic Processes"        queryKey="stochastic"  fetchType="query"   queryString="stochastic" />
        <CourseRow title="Fourier Analysis"            queryKey="fourier"     fetchType="query"   queryString="fourier" />

        {/* ── Physics ────────────────────────────────────────────── */}
        <CourseRow title="Physics"                     queryKey="physics"     fetchType="subject" subjectSlug="physics" initialData={physics} />
        <CourseRow title="Quantum Physics"             queryKey="qm"          fetchType="subject" subjectSlug="quantum-physics" />
        <CourseRow title="Quantum Mechanics"           queryKey="qmech"       fetchType="query"   queryString="quantum mechanics" />
        <CourseRow title="Quantum Field Theory"        queryKey="qft"         fetchType="query"   queryString="quantum field theory" />
        <CourseRow title="Classical Mechanics"         queryKey="cm"          fetchType="query"   queryString="classical mechanics" />
        <CourseRow title="Special & General Relativity" queryKey="relativity" fetchType="query"   queryString="relativity" />
        <CourseRow title="Statistical Mechanics"       queryKey="statmech"    fetchType="query"   queryString="statistical mechanics" />
        <CourseRow title="Thermodynamics"              queryKey="thermo"      fetchType="query"   queryString="thermodynamics" />
        <CourseRow title="Electromagnetism"            queryKey="em"          fetchType="query"   queryString="electromagnetism electricity magnetism" />
        <CourseRow title="Astrophysics & Cosmology"    queryKey="astro"       fetchType="query"   queryString="astrophysics cosmology" />
        <CourseRow title="Particle Physics"            queryKey="particle"    fetchType="query"   queryString="particle physics" />
        <CourseRow title="Optics"                      queryKey="optics"      fetchType="query"   queryString="optics" />
        <CourseRow title="Nuclear Physics"             queryKey="nuclear"     fetchType="query"   queryString="nuclear physics" />
        <CourseRow title="Theoretical Physics"         queryKey="theophys"    fetchType="query"   queryString="theoretical physics" />
        <CourseRow title="Solid State Physics"         queryKey="solidstate"  fetchType="query"   queryString="solid state physics condensed matter" />
        <CourseRow title="Fluid Mechanics"             queryKey="fluid"       fetchType="query"   queryString="fluid mechanics" />

        {/* ── Chemistry & Biology ────────────────────────────────── */}
        <CourseRow title="Chemistry"                   queryKey="chem"        fetchType="subject" subjectSlug="chemistry" />
        <CourseRow title="Organic Chemistry"           queryKey="orgchem"     fetchType="subject" subjectSlug="organic-chemistry" />
        <CourseRow title="Biochemistry"                queryKey="biochem"     fetchType="subject" subjectSlug="biochemistry" />
        <CourseRow title="Physical Chemistry"          queryKey="pchem"       fetchType="subject" subjectSlug="physical-chemistry" />
        <CourseRow title="Biology"                     queryKey="bio"         fetchType="subject" subjectSlug="biology" />
        <CourseRow title="Molecular Biology"           queryKey="molbio"      fetchType="subject" subjectSlug="molecular-biology" />
        <CourseRow title="Cell Biology"                queryKey="cellbio"     fetchType="subject" subjectSlug="cell-biology" />
        <CourseRow title="Neuroscience"                queryKey="neuro"       fetchType="subject" subjectSlug="neuroscience" />
        <CourseRow title="Genetics"                    queryKey="genetics"    fetchType="query"   queryString="genetics" />
        <CourseRow title="Microbiology"                queryKey="micro"       fetchType="subject" subjectSlug="microbiology" />
        <CourseRow title="Computational Biology"       queryKey="compbio"     fetchType="subject" subjectSlug="computational-biology" />
        <CourseRow title="Ecology & Evolution"         queryKey="ecology"     fetchType="query"   queryString="ecology evolution" />

        {/* ── Engineering ────────────────────────────────────────── */}
        <CourseRow title="Electrical Engineering"      queryKey="ee"          fetchType="subject" subjectSlug="electrical-engineering" />
        <CourseRow title="Signal Processing"           queryKey="signal"      fetchType="subject" subjectSlug="signal-processing" />
        <CourseRow title="Control Systems"             queryKey="control"     fetchType="subject" subjectSlug="control-systems" />
        <CourseRow title="Circuits & Electronics"      queryKey="circuits"    fetchType="subject" subjectSlug="circuits" />
        <CourseRow title="Mechanical Engineering"      queryKey="me"          fetchType="subject" subjectSlug="mechanical-engineering" />
        <CourseRow title="Chemical Engineering"        queryKey="che"         fetchType="subject" subjectSlug="chemical-engineering" />
        <CourseRow title="Civil Engineering"           queryKey="ce"          fetchType="subject" subjectSlug="civil-engineering" />
        <CourseRow title="Materials Science"           queryKey="matscience"  fetchType="subject" subjectSlug="materials-science" />
        <CourseRow title="Bioengineering"              queryKey="bioe"        fetchType="subject" subjectSlug="bioengineering" />
        <CourseRow title="Aerospace Engineering"       queryKey="aero"        fetchType="subject" subjectSlug="aerospace-engineering" />

        {/* ── Economics & Social Sciences ────────────────────────── */}
        <CourseRow title="Economics"                   queryKey="econ"        fetchType="subject" subjectSlug="economics" />
        <CourseRow title="Microeconomics"              queryKey="micro-econ"  fetchType="subject" subjectSlug="microeconomics" />
        <CourseRow title="Macroeconomics"              queryKey="macro-econ"  fetchType="subject" subjectSlug="macroeconomics" />
        <CourseRow title="Finance & Accounting"        queryKey="finance"     fetchType="subject" subjectSlug="finance" />
        <CourseRow title="Entrepreneurship"            queryKey="entrepr"     fetchType="subject" subjectSlug="entrepreneurship" />
        <CourseRow title="Business & Management"       queryKey="business"    fetchType="subject" subjectSlug="business" />
        <CourseRow title="Econometrics & Data"         queryKey="econometrics" fetchType="query"  queryString="econometrics" />
        <CourseRow title="Game Theory"                 queryKey="gametheory"  fetchType="query"   queryString="game theory" />
        <CourseRow title="Political Science"           queryKey="polisci"     fetchType="subject" subjectSlug="political-science" />
        <CourseRow title="Psychology"                  queryKey="psych"       fetchType="subject" subjectSlug="psychology" />
        <CourseRow title="Sociology"                   queryKey="soc"         fetchType="subject" subjectSlug="sociology" />
        <CourseRow title="Philosophy"                  queryKey="phil"        fetchType="subject" subjectSlug="philosophy" />
        <CourseRow title="History"                     queryKey="hist"        fetchType="subject" subjectSlug="history" />
        <CourseRow title="Linguistics"                 queryKey="ling"        fetchType="subject" subjectSlug="linguistics" />
        <CourseRow title="Law"                         queryKey="law"         fetchType="subject" subjectSlug="law" />

        {/* ── Medicine & Health ──────────────────────────────────── */}
        <CourseRow title="Medicine & Health"           queryKey="medicine"    fetchType="subject" subjectSlug="medicine" />
        <CourseRow title="Public Health"               queryKey="pubhealth"   fetchType="subject" subjectSlug="public-health" />
        <CourseRow title="Anatomy & Physiology"        queryKey="anatomy"     fetchType="subject" subjectSlug="anatomy" />
        <CourseRow title="Immunology"                  queryKey="immuno"      fetchType="subject" subjectSlug="immunology" />

        {/* ── Data Science ───────────────────────────────────────── */}
        <CourseRow title="Data Science"                queryKey="ds"          fetchType="subject" subjectSlug="data-science" />
        <CourseRow title="Bayesian Methods"            queryKey="bayes"       fetchType="subject" subjectSlug="bayesian-methods" />
        <CourseRow title="Time Series Analysis"        queryKey="timeseries"  fetchType="subject" subjectSlug="time-series" />
        <CourseRow title="Causal Inference"            queryKey="causal"      fetchType="subject" subjectSlug="causal-inference" />

        {/* ── Curated collections ────────────────────────────────── */}
        <CourseRow title="Graduate Level Courses"      queryKey="grad"        fetchType="level"   level="graduate" />
        <CourseRow title="Introduction to Everything"  queryKey="intro"       fetchType="query"   queryString="introduction to" />
        <CourseRow title="Most Comprehensive (100+ Videos)" queryKey="long"   fetchType="query"   queryString="lecture" />

        {/* ── By institution ─────────────────────────────────────── */}
        <CourseRow title="MIT OpenCourseWare"          queryKey="mit"         fetchType="university" universitySlug="mit" />
        <CourseRow title="Stanford University"         queryKey="stanford"    fetchType="university" universitySlug="stanford" />
        <CourseRow title="UC Berkeley"                 queryKey="berkeley"    fetchType="university" universitySlug="berkeley" />
        <CourseRow title="Yale Open Courses"           queryKey="yale"        fetchType="university" universitySlug="yale" />
        <CourseRow title="Harvard University"          queryKey="harvard"     fetchType="university" universitySlug="harvard" />
        <CourseRow title="Khan Academy"                queryKey="khan"        fetchType="university" universitySlug="khan-academy" />
        <CourseRow title="freeCodeCamp"                queryKey="fcc"         fetchType="university" universitySlug="freecodecamp" />
        <CourseRow title="3Blue1Brown"                 queryKey="3b1b"        fetchType="university" universitySlug="3blue1brown" />
        <CourseRow title="Crash Course"                queryKey="crash"       fetchType="university" universitySlug="crash-course" />
        <CourseRow title="Carnegie Mellon University"  queryKey="cmu"         fetchType="university" universitySlug="carnegie-mellon" />
        <CourseRow title="Georgia Tech"                queryKey="gatech"      fetchType="university" universitySlug="georgia-tech" />
        <CourseRow title="Princeton University"        queryKey="princeton"   fetchType="university" universitySlug="princeton" />
        <CourseRow title="Columbia University"         queryKey="columbia"    fetchType="university" universitySlug="columbia" />
        <CourseRow title="ETH Zürich"                 queryKey="eth"         fetchType="university" universitySlug="eth-zurich" />
        <CourseRow title="TU Delft"                    queryKey="tudelft"     fetchType="university" universitySlug="tu-delft" />
        <CourseRow title="Oxford University"           queryKey="oxford"      fetchType="university" universitySlug="oxford" />
        <CourseRow title="Cambridge University"        queryKey="cambridge"   fetchType="university" universitySlug="cambridge" />

        {/* ── Educator channels ──────────────────────────────────── */}
        <CourseRow title="Professor Leonard"           queryKey="prof-leonard"  fetchType="university" universitySlug="professor-leonard" />
        <CourseRow title="Neso Academy"                queryKey="neso"          fetchType="university" universitySlug="neso-academy" />
        <CourseRow title="Steve Brunton — Data Science" queryKey="eigensteve"   fetchType="university" universitySlug="eigensteve" />
        <CourseRow title="CS50 by Harvard"             queryKey="cs50"          fetchType="university" universitySlug="cs50" />
        <CourseRow title="fast.ai — Deep Learning"     queryKey="fastai"        fetchType="university" universitySlug="fastai" />
        <CourseRow title="StatQuest"                   queryKey="statquest"     fetchType="university" universitySlug="statquest" />
        <CourseRow title="The Organic Chemistry Tutor" queryKey="octutor"       fetchType="university" universitySlug="organic-chem-tutor" />
        <CourseRow title="Michel van Biezen"           queryKey="vanbiezen"     fetchType="university" universitySlug="michel-van-biezen" />
        <CourseRow title="Dr. Trefor Bazett"           queryKey="drtefor"       fetchType="university" universitySlug="dr-trefor" />
        <CourseRow title="Reducible"                   queryKey="reducible"     fetchType="university" universitySlug="reducible" />

        {/* ── Browse by university grid ──────────────────────────── */}
        <section>
          <h2 className="text-xl font-semibold text-foreground mb-4">Browse by University</h2>
          <UniversityGrid />
        </section>
      </div>
    </div>
  );
}
