"""
tag_courses_prod.py
Comprehensive subject tagger for production DB.
- Specific keyword rules for every subject in the FIELDS hierarchy
- Rollup: when a specific subject is matched, parent subjects are also tagged
- Additive only — never removes existing tags
"""
from __future__ import annotations
import os, re, psycopg2

from mutation_guard import require_explicit_apply


DATABASE_URL = require_explicit_apply("Run the legacy production subject tagger.")
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

# ---------------------------------------------------------------------------
# RULES — keyword rules for every subject.
# Each entry: (slug, [keywords])
# A course can match multiple rules. Keywords are matched case-insensitively
# against (title + description). More specific subjects are listed first.
# ---------------------------------------------------------------------------
RULES: list[tuple[str, list[str]]] = [

    # ════════════════════════════════════════════════════════════════════════
    # MATHEMATICS
    # ════════════════════════════════════════════════════════════════════════

    # ── Calculus & Foundations ───────────────────────────────────────────
    ("trigonometry",             ["trigonometry", "trig ", "sine cosine", "circular functions"]),
    ("precalculus",              ["precalculus", "pre-calculus", "pre calculus",
                                   "college algebra and trigonometry"]),
    ("calculus",                 ["calculus", "differentiation", "integration",
                                   "multivariable calculus", "vector calculus",
                                   "single variable calculus", "multivariate calculus",
                                   "integral calculus", "differential calculus",
                                   "calculus i", "calculus ii", "calculus iii",
                                   "calculus 1", "calculus 2", "calculus 3"]),
    ("linear-algebra",           ["linear algebra", "vectors and matrices", "vector space",
                                   "eigenvalue", "eigenvector", "matrix algebra",
                                   "matrix analysis", "matrix theory", "linear maps",
                                   "linear transformation", "matrices and vectors"]),
    ("differential-equations",   ["differential equation", "ode ", " ode,", "pde ",
                                   "partial differential", "ordinary differential",
                                   "dynamical system", "differential equations"]),
    ("proof-writing",            ["proof", "mathematical reasoning", "introduction to proofs",
                                   "mathematical writing", "logic and proof",
                                   "proofs and", "writing proofs"]),
    ("applied-mathematics",      ["applied mathematics", "applied math",
                                   "mathematical methods", "mathematical physics",
                                   "mathematical modeling", "mathematical modelling"]),
    ("algebra",                  ["algebra", "algebraic"]),

    # ── Analysis ────────────────────────────────────────────────────────
    ("measure-theory",           ["measure theory", "lebesgue", "measure and integration",
                                   "lebesgue integral", "measure space"]),
    ("harmonic-analysis",        ["harmonic analysis", "fourier analysis", "fourier series",
                                   "fourier transform", "wavelet"]),
    ("functional-analysis",      ["functional analysis", "hilbert space", "banach space",
                                   "operator theory", "spectral theory"]),
    ("complex-analysis",         ["complex analysis", "complex variables", "complex methods",
                                   "complex function", "contour integration",
                                   "analytic function", "complex plane"]),
    ("real-analysis",            ["real analysis", "analysis i", "analysis ii", "analysis iii",
                                   "introduction to analysis", "advanced calculus",
                                   "mathematical analysis", "metric space",
                                   "real variables", "sequences and series"]),
    ("analysis",                 ["analysis"]),

    # ── Algebra & Number Theory ──────────────────────────────────────────
    ("galois-theory",            ["galois theory", "galois group", "field extension",
                                   "galois correspondence"]),
    ("homological-algebra",      ["homological algebra", "derived category", "ext functor",
                                   "chain complex", "derived functor"]),
    ("commutative-algebra",      ["commutative algebra", "commutative ring",
                                   "noetherian ring", "algebraic k-theory"]),
    ("representation-theory",    ["representation theory", "group representation",
                                   "character theory", "lie representation"]),
    ("ring-theory",              ["ring theory", "ring and module", "module theory",
                                   "ring homomorphism"]),
    ("category-theory",          ["category theory", "functor", "natural transformation",
                                   "topos", "categorical"]),
    ("group-theory",             ["group theory", "symmetry groups", "lie group", "lie algebra",
                                   "finite groups", "group actions", "group homomorphism"]),
    ("abstract-algebra",         ["abstract algebra", "modern algebra", "algebraic structures",
                                   "groups rings fields", "rings and fields",
                                   "groups and rings"]),
    ("algebraic-number-theory",  ["algebraic number theory", "algebraic number field",
                                   "class field theory", "number field"]),
    ("number-theory",            ["number theory", "analytic number theory",
                                   "prime number", "modular arithmetic",
                                   "diophantine", "integer sequence", "cryptographic number"]),

    # ── Geometry & Topology ──────────────────────────────────────────────
    ("symplectic-geometry",      ["symplectic geometry", "symplectic manifold",
                                   "symplectic topology", "hamiltonian systems"]),
    ("riemannian-geometry",      ["riemannian geometry", "riemannian manifold",
                                   "riemannian", "geodesic", "curvature of"]),
    ("algebraic-topology",       ["algebraic topology", "homology", "cohomology",
                                   "homotopy", "fundamental group", "homotopy theory"]),
    ("algebraic-geometry",       ["algebraic geometry", "algebraic curve",
                                   "algebraic variety", "scheme theory"]),
    ("differential-geometry",    ["differential geometry", "differentiable manifold",
                                   "manifold", "tensor calculus", "connections on",
                                   "riemannian"]),
    ("topology",                 ["topology", "topological space", "point-set topology",
                                   "general topology", "metric topology", "topological"]),
    ("geometry",                 ["geometry", "geometric"]),

    # ── Discrete & Combinatorics ─────────────────────────────────────────
    ("set-theory",               ["set theory", "axiomatic set theory", "zermelo",
                                   "ordinal", "cardinal number"]),
    ("logic",                    ["mathematical logic", "logic and computation",
                                   "propositional logic", "predicate logic",
                                   "model theory", "proof theory", "formal logic"]),
    ("graph-theory",             ["graph theory", "graph algorithms", "network theory",
                                   "graph coloring", "planar graph", "graph and network"]),
    ("combinatorics",            ["combinatorics", "combinatorial", "counting",
                                   "enumerative", "bijection", "permutation",
                                   "combination", "inclusion-exclusion"]),
    ("discrete-mathematics",     ["discrete mathematics", "discrete math",
                                   "discrete structures", "discrete computation"]),

    # ── Probability & Statistics ─────────────────────────────────────────
    ("stochastic-calculus",      ["stochastic calculus", "ito calculus",
                                   "stochastic integral", "stochastic differential equation"]),
    ("bayesian-statistics",      ["bayesian", "bayesian inference", "bayesian statistics",
                                   "bayesian network", "prior distribution",
                                   "bayesian analysis", "bayesian methods"]),
    ("mathematical-statistics",  ["mathematical statistics", "theoretical statistics",
                                   "statistical theory"]),
    ("stochastic-processes",     ["stochastic process", "markov chain", "markov process",
                                   "random process", "queueing", "brownian motion",
                                   "stochastic"]),
    ("probability",              ["probability", "probabilistic", "random variable",
                                   "probability theory", "probability and statistics"]),
    ("statistics",               ["statistics", "statistical inference", "statistical learning",
                                   "regression analysis", "hypothesis testing",
                                   "data analysis", "biostatistics", "statistical methods",
                                   "econometrics", "statistical modeling"]),

    # ── Applied & Numerical ──────────────────────────────────────────────
    ("convex-optimization",      ["convex optimization", "convex analysis",
                                   "convex programming"]),
    ("mathematical-optimization",["mathematical optimization", "mathematical programming",
                                   "nonlinear optimization", "integer programming",
                                   "combinatorial optimization"]),
    ("operations-research",      ["operations research", "linear programming",
                                   "network flow", "integer programming", "scheduling"]),
    ("numerical-analysis",       ["numerical analysis", "numerical linear algebra",
                                   "numerical computation", "computational mathematics",
                                   "finite element", "finite difference", "finite volume"]),
    ("numerical-methods",        ["numerical methods", "scientific computing",
                                   "computational methods", "numerical solution"]),
    ("optimization",             ["optimization", "optimisation"]),

    # ── Mathematics catch-all (last) ─────────────────────────────────────
    ("mathematics",              ["mathematics", " math ", " maths ", "mathematical"]),

    # ════════════════════════════════════════════════════════════════════════
    # PHYSICS
    # ════════════════════════════════════════════════════════════════════════

    # ── Quantum ──────────────────────────────────────────────────────────
    ("quantum-field-theory",     ["quantum field theory", "qft", "quantum electrodynamics",
                                   "quantum chromodynamics", "gauge theory"]),
    ("quantum-optics",           ["quantum optics", "cavity quantum", "photon statistics"]),
    ("quantum-information",      ["quantum information", "quantum error correction",
                                   "quantum entanglement", "quantum cryptography"]),
    ("quantum-computing",        ["quantum computing", "quantum computer",
                                   "quantum algorithm", "quantum circuit"]),
    ("particle-physics",         ["particle physics", "high energy physics", "subatomic",
                                   "elementary particle", "standard model", "collider",
                                   "quark", "lepton", "boson"]),
    ("nuclear-physics",          ["nuclear physics", "nuclear reaction", "radioactivity",
                                   "radioactive decay", "nuclear structure", "fission",
                                   "fusion"]),
    ("quantum-mechanics",        ["quantum mechanics", "quantum physics", "quantum theory",
                                   "wave function", "schrodinger", "heisenberg",
                                   "quantum"]),

    # ── Relativity & Cosmology ───────────────────────────────────────────
    ("string-theory",            ["string theory", "superstring", "m-theory", "branes"]),
    ("cosmology",                ["cosmology", "cosmological", "dark matter", "dark energy",
                                   "big bang", "cosmic microwave", "large scale structure"]),
    ("astrophysics",             ["astrophysics", "stellar", "galaxy", "galaxies",
                                   "interstellar", "black hole", "neutron star",
                                   "pulsar", "quasar"]),
    ("astronomy",                ["astronomy", "telescope", "celestial mechanics",
                                   "solar system", "planets", "exoplanet",
                                   "observational astronomy"]),
    ("general-relativity",       ["general relativity", "general theory of relativity",
                                   "curved spacetime", "einstein field equation"]),
    ("special-relativity",       ["special relativity", "special theory of relativity",
                                   "lorentz transformation", "time dilation"]),
    ("relativity",               ["relativity", "spacetime"]),
    ("theoretical-physics",      ["theoretical physics", "mathematical physics",
                                   "physics theory"]),

    # ── Statistical & Condensed Matter ──────────────────────────────────
    ("materials-science",        ["materials science", "material science", "materials engineering",
                                   "crystal structure", "polymers", "nanomaterials"]),
    ("solid-state-physics",      ["solid state physics", "solid-state physics",
                                   "semiconductor", "band structure", "condensed"]),
    ("condensed-matter",         ["condensed matter", "superconductivity", "magnetism",
                                   "phase transition", "many-body"]),
    ("statistical-mechanics",    ["statistical mechanics", "statistical physics",
                                   "thermodynamics and statistics", "partition function",
                                   "ensemble theory"]),

    # ── Classical Physics ────────────────────────────────────────────────
    ("optics",                   ["optics", "laser", "photonics", "optical physics",
                                   "light and matter", "electromagnetic waves",
                                   "wave optics", "geometrical optics"]),
    ("waves",                    ["waves", "oscillations", "vibrations and waves",
                                   "wave physics", "acoustics"]),
    ("continuum-mechanics",      ["continuum mechanics", "elasticity", "solid mechanics"]),
    ("fluid-dynamics",           ["fluid dynamics", "computational fluid", "turbulence",
                                   "aerodynamics", "fluid flow"]),
    ("fluid-mechanics",          ["fluid mechanics", "hydraulics", "hydrostatics"]),
    ("thermodynamics",           ["thermodynamics", "heat transfer", "thermal physics",
                                   "heat and mass transfer", "thermal "]),
    ("electrodynamics",          ["electrodynamics", "electromagnetic field", "maxwell equations",
                                   "electromagnetic theory"]),
    ("electromagnetism",         ["electromagnetism", "electricity and magnetism",
                                   "electric and magnetic", "electromagnetic"]),
    ("classical-mechanics",      ["classical mechanics", "newtonian mechanics",
                                   "analytical mechanics", "lagrangian mechanics",
                                   "hamiltonian mechanics"]),
    ("mechanics",                ["mechanics", "statics", "dynamics", "kinematics"]),
    ("physics",                  ["physics"]),

    # ════════════════════════════════════════════════════════════════════════
    # COMPUTER SCIENCE
    # ════════════════════════════════════════════════════════════════════════

    # ── AI & Machine Learning ────────────────────────────────────────────
    ("ai-safety",                ["ai safety", "ai alignment", "alignment"]),
    ("ai-ethics",                ["ai ethics", "ethics of ai", "algorithmic fairness",
                                   "responsible ai", "fairness in ml"]),
    ("meta-learning",            ["meta learning", "meta-learning", "few-shot learning",
                                   "transfer learning", "learning to learn"]),
    ("ai-agents",                ["ai agents", "intelligent agents", "autonomous agents",
                                   "multi-agent systems"]),
    ("generative-models",        ["generative model", "generative adversarial",
                                   "variational autoencoder", "diffusion model",
                                   "gans", "vae "]),
    ("large-language-models",    ["large language model", "llm", "gpt", "bert", "chatgpt",
                                   "language model"]),
    ("reinforcement-learning",   ["reinforcement learning", " rl ", "reward function",
                                   "markov decision process", "q-learning", "policy gradient"]),
    ("natural-language-processing", ["natural language processing", "nlp", "text mining",
                                     "computational linguistics", "speech recognition",
                                     "sentiment analysis", "information extraction"]),
    ("computer-vision",          ["computer vision", "image processing",
                                   "object detection", "image recognition",
                                   "image segmentation", "visual"]),
    ("deep-learning",            ["deep learning", "neural network", "convolutional neural",
                                   "recurrent neural", "lstm", "transformer model",
                                   "backpropagation"]),
    ("machine-learning",         ["machine learning", "statistical learning",
                                   "supervised learning", "unsupervised learning",
                                   "classification", "clustering"]),
    ("artificial-intelligence",  ["artificial intelligence", " ai ", "intelligent system",
                                   "knowledge representation", "expert system",
                                   "automated reasoning", "search algorithm"]),

    # ── Algorithms & Theory ──────────────────────────────────────────────
    ("information-theory",       ["information theory", "entropy", "channel capacity",
                                   "coding theory", "error correction"]),
    ("computational-complexity", ["computational complexity", "complexity theory",
                                   "np-complete", "np-hard", "complexity class",
                                   "p vs np"]),
    ("theory-of-computing",      ["theory of computation", "automata", "formal language",
                                   "turing machine", "computability", "formal languages"]),
    ("data-structures",          ["data structures", "data organization",
                                   "heap", "tree structure", "hash table"]),
    ("algorithms",               ["algorithms", "algorithm design", "algorithm analysis",
                                   "sorting", "searching algorithms", "dynamic programming",
                                   "greedy algorithm"]),

    # ── Systems & Architecture ───────────────────────────────────────────
    ("high-performance-computing",["high performance computing", "hpc", "supercomputing",
                                   "parallel programming", "mpi ", "cuda "]),
    ("parallel-computing",       ["parallel computing", "concurrent programming",
                                   "parallel algorithms", "multithreading", "gpu computing"]),
    ("embedded-systems",         ["embedded systems", "microcontroller", "real-time systems",
                                   "firmware", "iot", "embedded programming"]),
    ("computer-networks",        ["computer networks", "network protocols", "tcp/ip",
                                   "network architecture", "internet protocols"]),
    ("networking",               ["networking", "computer network", "internet",
                                   "socket programming"]),
    ("distributed-systems",      ["distributed systems", "distributed computing",
                                   "cloud computing", "distributed algorithms"]),
    ("systems-programming",      ["systems programming", "systems software",
                                   "low-level programming", "assembly language"]),
    ("operating-systems",        ["operating systems", "os kernel", "linux kernel",
                                   "process scheduling", "memory management",
                                   "file systems"]),
    ("computer-architecture",    ["computer architecture", "computer organization",
                                   "processor design", "digital logic", "vlsi",
                                   "microprocessor", "instruction set", "cpu"]),
    ("computer-systems",         ["computer systems", "systems and architecture"]),

    # ── Software & Development ───────────────────────────────────────────
    ("compilers",                ["compiler", "compilers", "lexical analysis", "parsing",
                                   "code generation", "interpreter"]),
    ("human-computer-interaction",["human computer interaction", "hci", "user interface",
                                   "usability", "user experience", "interaction design"]),
    ("computer-graphics",        ["computer graphics", "3d graphics", "rendering",
                                   "opengl", "ray tracing", "animation"]),
    ("game-development",         ["game development", "game design", "game engine",
                                   "unity", "unreal engine"]),
    ("mobile-development",       ["mobile development", "android", "ios development",
                                   "swift", "react native", "flutter"]),
    ("sql",                      ["sql", "structured query language", "database query"]),
    ("databases",                ["database", "relational database", "dbms",
                                   "data management", "nosql", "database design"]),
    ("web-development",          ["web development", "web design", "html", "css",
                                   "javascript", "react", "frontend", "backend",
                                   "full stack", "web application", "rest api",
                                   "node.js", "django", "flask"]),
    ("programming-languages",    ["programming languages", "language design",
                                   "type theory", "functional programming",
                                   "lambda calculus"]),
    ("software-engineering",     ["software engineering", "software design",
                                   "software architecture", "design patterns",
                                   "agile", "version control"]),
    ("programming",              ["programming", "coding", "python", "java ",
                                   "c++", "introduction to computer",
                                   "learn to code"]),

    # ── Security & Privacy ───────────────────────────────────────────────
    ("formal-verification",      ["formal verification", "model checking",
                                   "program verification", "formal methods"]),
    ("privacy",                  ["privacy", "data privacy", "differential privacy"]),
    ("digital-forensics",        ["digital forensics", "cyber forensics",
                                   "incident response", "malware analysis"]),
    ("systems-security",         ["systems security", "secure systems",
                                   "trusted computing", "security architecture"]),
    ("cryptography",             ["cryptography", "encryption", "cipher",
                                   "public key", "hash function", "blockchain"]),
    ("computer-security",        ["computer security", "information security",
                                   "network security", "web security"]),
    ("cybersecurity",            ["cybersecurity", "cyber security", "security engineering",
                                   "penetration testing", "vulnerability"]),

    # ── Data Science ─────────────────────────────────────────────────────
    ("data-management",          ["data management", "data governance", "data quality"]),
    ("data-mining",              ["data mining", "knowledge discovery", "association rules"]),
    ("data-engineering",         ["data engineering", "data pipeline", "etl", "apache spark",
                                   "data warehouse"]),
    ("big-data",                 ["big data", "hadoop", "spark", "distributed data"]),
    ("data-visualization",       ["data visualization", "visualisation", "tableau",
                                   "matplotlib", "d3.js", "information visualization"]),
    ("data-analysis",            ["data analysis", "data analytics", "exploratory data"]),
    ("data-science",             ["data science", "data scientist"]),

    # ── CS catch-all ─────────────────────────────────────────────────────
    ("computer-science",         ["computer science", "computing", "informatics",
                                   "computation ", "eecs ", "software systems"]),

    # ════════════════════════════════════════════════════════════════════════
    # ENGINEERING
    # ════════════════════════════════════════════════════════════════════════
    ("signal-processing",        ["signal processing", "digital signal processing", "dsp",
                                   "filter design", "communications systems",
                                   "signal and systems", "signals and systems"]),
    ("control-systems",          ["control systems", "control theory", "feedback control",
                                   "optimal control", "pid control", "automatic control"]),
    ("power-systems",            ["power systems", "power electronics", "electric power",
                                   "power grid"]),
    ("vlsi",                     ["vlsi", "chip design", "integrated circuit design",
                                   "cmos"]),
    ("digital-electronics",      ["digital electronics", "digital circuit", "vhdl",
                                   "fpga", "logic design"]),
    ("electronics",              ["electronics", "analog circuit", "transistor",
                                   "electronic circuits"]),
    ("circuits",                 ["circuit", "circuit analysis", "circuit theory"]),
    ("electrical-engineering",   ["electrical engineering", "power engineering",
                                   "semiconductor"]),
    ("heat-transfer",            ["heat transfer", "conduction", "convection",
                                   "radiation heat"]),
    ("vibrations",               ["vibrations", "structural vibration",
                                   "mechanical vibration"]),
    ("manufacturing",            ["manufacturing", "machining", "production engineering"]),
    ("mechatronics",             ["mechatronics", "electromechanical"]),
    ("robotics",                 ["robotics", "robot", "autonomous systems",
                                   "robotic manipulation", "robot programming"]),
    ("mechanical-engineering",   ["mechanical engineering"]),
    ("structural-analysis",      ["structural analysis", "finite element analysis",
                                   "structural mechanics"]),
    ("structural-engineering",   ["structural engineering", "building structures"]),
    ("geotechnical-engineering", ["geotechnical", "soil mechanics", "foundation engineering"]),
    ("transportation-engineering",["transportation engineering", "traffic engineering"]),
    ("urban-planning",           ["urban planning", "city planning", "land use"]),
    ("civil-engineering",        ["civil engineering"]),
    ("nanotechnology",           ["nanotechnology", "nanoscience", "nanostructure"]),
    ("bioengineering",           ["bioengineering", "biomedical engineering",
                                   "biological engineering", "biomechanics",
                                   "biomaterials"]),
    ("chemical-engineering",     ["chemical engineering", "reaction engineering",
                                   "process engineering", "mass transfer",
                                   "transport phenomena"]),
    ("ocean-engineering",        ["ocean engineering", "marine engineering", "offshore"]),
    ("environmental-engineering",["environmental engineering", "water treatment",
                                   "waste management", "environmental systems"]),
    ("nuclear-engineering",      ["nuclear engineering", "reactor physics",
                                   "nuclear reactor", "radiation"]),
    ("aerospace-engineering",    ["aerospace engineering", "aeronautics", "aircraft design",
                                   "flight dynamics", "spacecraft"]),
    ("engineering",              ["engineering"]),

    # ════════════════════════════════════════════════════════════════════════
    # NATURAL SCIENCES
    # ════════════════════════════════════════════════════════════════════════
    ("computational-neuroscience",["computational neuroscience", "neural computation",
                                   "theoretical neuroscience"]),
    ("computational-biology",    ["computational biology", "bioinformatics",
                                   "systems biology", "genomic algorithms"]),
    ("plant-biology",            ["plant biology", "botany", "plant physiology",
                                   "plant science"]),
    ("animal-science",           ["animal science", "zoology", "animal biology",
                                   "veterinary"]),
    ("origins-of-life",          ["origins of life", "abiogenesis", "astrobiology"]),
    ("bioinformatics",           ["bioinformatics", "sequence alignment", "genome assembly",
                                   "computational genomics"]),
    ("genomics",                 ["genomics", "genome", "sequencing", "transcriptomics",
                                   "proteomics"]),
    ("physiology",               ["physiology", "physiological", "organ systems"]),
    ("pharmacology",             ["pharmacology", "drug mechanism", "pharmaceutical"]),
    ("immunology",               ["immunology", "immune system", "immunotherapy",
                                   "antibody"]),
    ("microbiology",             ["microbiology", "microbial", "bacteriology", "virology",
                                   "bacteria", "virus"]),
    ("evolutionary-biology",     ["evolutionary biology", "evolution", "natural selection",
                                   "phylogenetics", "darwinian"]),
    ("ecology",                  ["ecology", "ecosystem", "biodiversity", "conservation",
                                   "population biology"]),
    ("cell-biology",             ["cell biology", "cell signaling", "cell division",
                                   "cytology", "cellular"]),
    ("neuroscience",             ["neuroscience", "neurobiology", "brain", "nervous system",
                                   "neural circuits", "cognitive neuroscience"]),
    ("molecular-biology",        ["molecular biology", "molecular genetics", "dna replication",
                                   "gene expression", "protein synthesis", "rna"]),
    ("genetics",                 ["genetics", "genomics", "heredity", "gene ", "genetic ",
                                   "mendelian"]),
    ("biochemistry",             ["biochemistry", "metabolic pathway", "enzyme kinetics",
                                   "biomolecule", "protein structure"]),
    ("biology",                  ["biology", "biological"]),

    ("sustainability",           ["sustainability", "sustainable development",
                                   "renewable energy", "clean energy"]),
    ("environmental-science",    ["environmental science", "environmental studies"]),
    ("atmospheric-science",      ["atmospheric science", "meteorology", "weather",
                                   "climate modeling"]),
    ("climate-science",          ["climate", "climate change", "global warming",
                                   "greenhouse gas"]),
    ("geology",                  ["geology", "geological", "mineralogy", "petrology",
                                   "geomorphology"]),
    ("earth-science",            ["earth science", "geophysics", "oceanography",
                                   "seismology", "earth systems"]),

    ("biostatistics",            ["biostatistics", "epidemiology", "clinical statistics"]),
    ("mental-health",            ["mental health", "psychiatry", "depression", "anxiety"]),
    ("forensic-science",         ["forensic science", "forensic biology", "crime scene"]),
    ("global-health",            ["global health", "international health"]),
    ("nutrition",                ["nutrition", "nutritional science", "dietetics"]),
    ("epidemiology",             ["epidemiology", "disease surveillance",
                                   "infectious disease"]),
    ("public-health",            ["public health", "population health", "health policy"]),
    ("anatomy",                  ["anatomy", "anatomical", "human body", "dissection"]),
    ("medicine",                 ["medicine", "clinical", "pharmacology", "pathology",
                                   "medical", "diagnosis"]),

    ("inorganic-chemistry",      ["inorganic chemistry", "coordination chemistry",
                                   "transition metal complex"]),
    ("physical-chemistry",       ["physical chemistry", "chemical thermodynamics",
                                   "chemical kinetics", "spectroscopy",
                                   "quantum chemistry"]),
    ("organic-chemistry",        ["organic chemistry", "organic synthesis",
                                   "reaction mechanism", "organic reactions",
                                   "stereochemistry"]),
    ("general-chemistry",        ["general chemistry", "introductory chemistry",
                                   "chemistry i", "chemistry 1"]),
    ("chemistry",                ["chemistry", "chemical"]),

    # ════════════════════════════════════════════════════════════════════════
    # SOCIAL SCIENCES
    # ════════════════════════════════════════════════════════════════════════
    ("econometrics",             ["econometrics", "time series analysis",
                                   "panel data", "instrumental variables"]),
    ("game-theory",              ["game theory", "nash equilibrium", "mechanism design",
                                   "auction theory", "strategic interaction"]),
    ("behavioral-economics",     ["behavioral economics", "behavioral finance",
                                   "nudge", "prospect theory"]),
    ("international-economics",  ["international economics", "international trade",
                                   "trade theory", "comparative advantage"]),
    ("political-economy",        ["political economy", "public choice", "political economics"]),
    ("economic-history",         ["economic history", "history of economics"]),
    ("macroeconomics",           ["macroeconomics", "macro economics", "gdp", "inflation",
                                   "monetary policy", "fiscal policy", "economic growth"]),
    ("microeconomics",           ["microeconomics", "micro economics", "consumer theory",
                                   "producer theory", "market structure", "price theory"]),
    ("finance",                  ["finance", "financial economics", "investment",
                                   "portfolio theory", "asset pricing", "derivatives",
                                   "banking", "accounting", "financial markets"]),
    ("economics",                ["economics", "economic"]),

    ("environmental-law",        ["environmental law", "climate law", "environmental regulation"]),
    ("civil-rights",             ["civil rights", "civil liberties"]),
    ("human-rights",             ["human rights", "international human rights"]),
    ("criminal-justice",         ["criminal justice", "criminology", "criminal law"]),
    ("legal-studies",            ["legal studies", "law and society"]),
    ("comparative-politics",     ["comparative politics", "comparative government"]),
    ("global-politics",          ["global politics", "world politics",
                                   "international security"]),
    ("constitutional-law",       ["constitutional law", "constitution"]),
    ("public-policy",            ["public policy", "policy analysis", "policy making"]),
    ("international-relations",  ["international relations", "international affairs",
                                   "foreign policy", "diplomacy"]),
    ("political-science",        ["political science", "politics", "government",
                                   "democracy", "political theory"]),
    ("law",                      ["law ", "legal", "jurisprudence", "legislation"]),

    ("cognitive-psychology",     ["cognitive psychology", "cognitive science",
                                   "perception", "memory", "attention"]),
    ("developmental-psychology", ["developmental psychology", "child development",
                                   "lifespan development"]),
    ("social-psychology",        ["social psychology", "group dynamics",
                                   "persuasion", "attitude"]),
    ("behavioral-science",       ["behavioral science", "behavior analysis"]),
    ("psychology",               ["psychology", "cognitive", "behavioral", "neuroscience",
                                   "mental", "psychological"]),

    ("demographics",             ["demographics", "demography", "population studies"]),
    ("social-theory",            ["social theory", "sociological theory"]),
    ("anthropology",             ["anthropology", "ethnography", "cultural anthropology",
                                   "archaeology"]),
    ("social-sciences",          ["social sciences"]),
    ("sociology",                ["sociology", "social science", "society", "culture",
                                   "social structure"]),

    # ════════════════════════════════════════════════════════════════════════
    # HUMANITIES
    # ════════════════════════════════════════════════════════════════════════
    ("media-history",            ["media history", "history of media", "press history"]),
    ("western-civilization",     ["western civilization", "western culture"]),
    ("art-history",              ["art history", "history of art"]),
    ("medieval-history",         ["medieval history", "middle ages", "medieval"]),
    ("european-history",         ["european history", "history of europe"]),
    ("world-history",            ["world history", "global history", "civilization"]),
    ("ancient-history",          ["ancient history", "ancient world", "classical antiquity",
                                   "ancient rome", "ancient greece", "ancient egypt",
                                   "mesopotamia"]),
    ("american-history",         ["american history", "united states history",
                                   "us history", "colonial america"]),
    ("history",                  ["history", "historical"]),

    ("political-philosophy",     ["political philosophy", "social contract",
                                   "justice theory"]),
    ("ancient-philosophy",       ["ancient philosophy", "greek philosophy", "plato",
                                   "aristotle", "stoicism"]),
    ("philosophy-of-mind",       ["philosophy of mind", "consciousness", "qualia",
                                   "mind-body problem"]),
    ("ethics",                   ["ethics", "moral philosophy", "bioethics",
                                   "professional ethics"]),
    ("philosophy",               ["philosophy", "epistemology", "metaphysics",
                                   "ontology", "logic and"]),

    ("literary-theory",          ["literary theory", "critical theory", "narratology"]),
    ("poetry",                   ["poetry", "verse", "poetic"]),
    ("linguistics",              ["linguistics", "phonology", "syntax", "semantics",
                                   "language acquisition", "morphology"]),
    ("literature",               ["literature", "literary", "novel", "fiction",
                                   "creative writing", "composition"]),
    ("language",                 ["language"]),

    ("animation",                ["animation", "animated film"]),
    ("photography",              ["photography", "photographic"]),
    ("theater",                  ["theater", "theatre", "drama", "acting",
                                   "theatrical"]),
    ("film-studies",             ["film studies", "film theory", "cinema", "cinematography"]),
    ("music-theory",             ["music theory", "harmony", "counterpoint",
                                   "ear training", "sight reading"]),
    ("arts",                     ["arts", "visual art", "drawing", "painting", "sculpture"]),
    ("music",                    ["music", "musicology", "composition"]),
    ("architecture",             ["architecture", "architectural", "urban design",
                                   "building design", "construction"]),
    ("design",                   ["design", "graphic design", "product design"]),

    # ════════════════════════════════════════════════════════════════════════
    # BUSINESS & MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════
    ("human-resources",          ["human resources", "hr management", "talent management",
                                   "organizational development"]),
    ("logistics",                ["logistics", "supply chain", "procurement"]),
    ("project-management",       ["project management", "agile", "scrum", "project planning"]),
    ("leadership",               ["leadership", "executive", "management skills"]),
    ("marketing",                ["marketing", "consumer behavior", "brand management",
                                   "digital marketing", "advertising"]),
    ("management",               ["management", "organizational behavior", "strategy",
                                   "operations management"]),
    ("entrepreneurship",         ["entrepreneurship", "startup", "venture capital",
                                   "new ventures", "innovation", "business plan"]),
    ("business",                 ["business", "mba ", "commerce"]),

    ("research-methods",         ["research methods", "research methodology",
                                   "scientific method", "qualitative research",
                                   "quantitative research"]),
    ("technology-and-society",   ["technology and society", "social implications of technology",
                                   "technology policy", "digital society"]),
    ("energy",                   ["energy", "energy systems", "energy policy",
                                   "renewable energy"]),
    ("innovation",               ["innovation", "technology transfer"]),
    ("cryptocurrency",           ["cryptocurrency", "bitcoin", "ethereum", "defi"]),
    ("blockchain",               ["blockchain", "distributed ledger", "smart contract"]),
    ("technology",               ["technology"]),
]

# ---------------------------------------------------------------------------
# ROLLUPS — when a specific subject is tagged, also ensure parent subjects
# are tagged. This means a "Graph Theory" course gets both graph-theory AND
# discrete-mathematics AND mathematics.
# ---------------------------------------------------------------------------
ROLLUPS: dict[str, list[str]] = {
    # Mathematics
    "trigonometry":              ["mathematics"],
    "precalculus":               ["mathematics"],
    "calculus":                  ["mathematics"],
    "linear-algebra":            ["mathematics"],
    "differential-equations":    ["mathematics"],
    "proof-writing":             ["mathematics"],
    "applied-mathematics":       ["mathematics"],
    "algebra":                   ["mathematics"],
    "measure-theory":            ["mathematics", "real-analysis"],
    "harmonic-analysis":         ["mathematics", "analysis"],
    "functional-analysis":       ["mathematics", "analysis"],
    "complex-analysis":          ["mathematics", "analysis"],
    "real-analysis":             ["mathematics", "analysis"],
    "analysis":                  ["mathematics"],
    "galois-theory":             ["mathematics", "abstract-algebra", "algebra"],
    "homological-algebra":       ["mathematics", "abstract-algebra", "algebra"],
    "commutative-algebra":       ["mathematics", "abstract-algebra", "algebra"],
    "representation-theory":     ["mathematics", "abstract-algebra", "algebra"],
    "ring-theory":               ["mathematics", "abstract-algebra", "algebra"],
    "category-theory":           ["mathematics"],
    "group-theory":              ["mathematics", "abstract-algebra", "algebra"],
    "abstract-algebra":          ["mathematics", "algebra"],
    "algebraic-number-theory":   ["mathematics", "number-theory", "abstract-algebra", "algebra"],
    "number-theory":             ["mathematics"],
    "symplectic-geometry":       ["mathematics", "differential-geometry", "geometry"],
    "riemannian-geometry":       ["mathematics", "differential-geometry", "geometry"],
    "algebraic-topology":        ["mathematics", "topology", "algebraic-geometry", "geometry"],
    "algebraic-geometry":        ["mathematics", "geometry", "algebra"],
    "differential-geometry":     ["mathematics", "geometry"],
    "topology":                  ["mathematics"],
    "geometry":                  ["mathematics"],
    "set-theory":                ["mathematics", "discrete-mathematics"],
    "logic":                     ["mathematics", "discrete-mathematics"],
    "graph-theory":              ["mathematics", "discrete-mathematics", "combinatorics"],
    "combinatorics":             ["mathematics", "discrete-mathematics"],
    "discrete-mathematics":      ["mathematics"],
    "stochastic-calculus":       ["mathematics", "probability", "calculus"],
    "bayesian-statistics":       ["mathematics", "statistics", "probability"],
    "mathematical-statistics":   ["mathematics", "statistics"],
    "stochastic-processes":      ["mathematics", "probability"],
    "probability":               ["mathematics"],
    "statistics":                ["mathematics"],
    "convex-optimization":       ["mathematics", "optimization", "mathematical-optimization"],
    "mathematical-optimization": ["mathematics", "optimization"],
    "operations-research":       ["mathematics", "optimization"],
    "numerical-analysis":        ["mathematics", "numerical-methods", "applied-mathematics"],
    "numerical-methods":         ["mathematics", "applied-mathematics"],
    "optimization":              ["mathematics"],
    # Physics
    "quantum-field-theory":      ["physics", "quantum-mechanics", "quantum-physics",
                                   "particle-physics"],
    "quantum-optics":            ["physics", "quantum-mechanics", "quantum-physics", "optics"],
    "quantum-information":       ["physics", "quantum-mechanics", "quantum-physics"],
    "quantum-computing":         ["physics", "quantum-mechanics", "quantum-physics",
                                   "computer-science"],
    "particle-physics":          ["physics", "nuclear-physics"],
    "nuclear-physics":           ["physics"],
    "quantum-mechanics":         ["physics", "quantum-physics"],
    "string-theory":             ["physics", "theoretical-physics", "quantum-field-theory"],
    "cosmology":                 ["physics", "astrophysics"],
    "astrophysics":              ["physics", "astronomy"],
    "astronomy":                 ["physics"],
    "general-relativity":        ["physics", "relativity", "theoretical-physics"],
    "special-relativity":        ["physics", "relativity", "theoretical-physics"],
    "relativity":                ["physics"],
    "theoretical-physics":       ["physics"],
    "materials-science":         ["physics", "condensed-matter"],
    "solid-state-physics":       ["physics", "condensed-matter"],
    "condensed-matter":          ["physics"],
    "statistical-mechanics":     ["physics", "thermodynamics"],
    "optics":                    ["physics"],
    "waves":                     ["physics", "mechanics"],
    "continuum-mechanics":       ["physics", "mechanics"],
    "fluid-dynamics":            ["physics", "mechanics", "fluid-mechanics"],
    "fluid-mechanics":           ["physics", "mechanics"],
    "thermodynamics":            ["physics"],
    "electrodynamics":           ["physics", "electromagnetism"],
    "electromagnetism":          ["physics"],
    "classical-mechanics":       ["physics", "mechanics"],
    "mechanics":                 ["physics"],
    # Computer Science
    "ai-safety":                 ["artificial-intelligence", "computer-science"],
    "ai-ethics":                 ["artificial-intelligence", "computer-science"],
    "meta-learning":             ["machine-learning", "artificial-intelligence",
                                   "computer-science"],
    "ai-agents":                 ["artificial-intelligence", "computer-science"],
    "generative-models":         ["deep-learning", "machine-learning", "artificial-intelligence",
                                   "computer-science"],
    "large-language-models":     ["natural-language-processing", "deep-learning",
                                   "machine-learning", "artificial-intelligence",
                                   "computer-science"],
    "reinforcement-learning":    ["machine-learning", "artificial-intelligence",
                                   "computer-science"],
    "natural-language-processing":["machine-learning", "artificial-intelligence",
                                    "computer-science"],
    "computer-vision":           ["machine-learning", "artificial-intelligence",
                                   "computer-science"],
    "deep-learning":             ["machine-learning", "artificial-intelligence",
                                   "computer-science"],
    "machine-learning":          ["artificial-intelligence", "computer-science"],
    "artificial-intelligence":   ["computer-science"],
    "information-theory":        ["mathematics", "computer-science"],
    "computational-complexity":  ["algorithms", "theory-of-computing", "computer-science"],
    "theory-of-computing":       ["algorithms", "computer-science"],
    "data-structures":           ["algorithms", "computer-science"],
    "algorithms":                ["computer-science"],
    "high-performance-computing":["parallel-computing", "computer-systems", "computer-science"],
    "parallel-computing":        ["computer-systems", "computer-science"],
    "embedded-systems":          ["computer-architecture", "computer-systems", "computer-science"],
    "computer-networks":         ["networking", "computer-systems", "computer-science"],
    "networking":                ["computer-science"],
    "distributed-systems":       ["computer-systems", "computer-science"],
    "systems-programming":       ["computer-systems", "programming", "computer-science"],
    "operating-systems":         ["computer-systems", "computer-science"],
    "computer-architecture":     ["computer-systems", "computer-science"],
    "computer-systems":          ["computer-science"],
    "compilers":                 ["programming-languages", "computer-science"],
    "human-computer-interaction":["computer-science"],
    "computer-graphics":         ["computer-science"],
    "game-development":          ["programming", "computer-science"],
    "mobile-development":        ["programming", "computer-science"],
    "sql":                       ["databases", "computer-science"],
    "databases":                 ["computer-science"],
    "web-development":           ["programming", "computer-science"],
    "programming-languages":     ["computer-science"],
    "software-engineering":      ["programming", "computer-science"],
    "programming":               ["computer-science"],
    "formal-verification":       ["cybersecurity", "computer-science"],
    "privacy":                   ["cybersecurity", "computer-science"],
    "digital-forensics":         ["cybersecurity", "computer-science"],
    "systems-security":          ["cybersecurity", "computer-science"],
    "cryptography":              ["cybersecurity", "mathematics", "computer-science"],
    "computer-security":         ["cybersecurity", "computer-science"],
    "data-management":           ["data-science", "databases", "computer-science"],
    "data-mining":               ["data-science", "machine-learning", "computer-science"],
    "data-engineering":          ["data-science", "computer-science"],
    "big-data":                  ["data-science", "computer-science"],
    "data-visualization":        ["data-science", "computer-science"],
    "data-analysis":             ["data-science", "statistics"],
    "data-science":              ["computer-science", "statistics"],
    # Engineering rollups
    "signal-processing":         ["electrical-engineering", "engineering"],
    "control-systems":           ["electrical-engineering", "engineering"],
    "vlsi":                      ["electrical-engineering", "engineering"],
    "digital-electronics":       ["electrical-engineering", "engineering"],
    "electronics":               ["electrical-engineering", "engineering"],
    "circuits":                  ["electrical-engineering", "engineering"],
    "electrical-engineering":    ["engineering"],
    "vibrations":                ["mechanical-engineering", "engineering"],
    "manufacturing":             ["mechanical-engineering", "engineering"],
    "mechatronics":              ["mechanical-engineering", "engineering"],
    "robotics":                  ["mechanical-engineering", "engineering"],
    "mechanical-engineering":    ["engineering"],
    "structural-analysis":       ["structural-engineering", "civil-engineering", "engineering"],
    "structural-engineering":    ["civil-engineering", "engineering"],
    "geotechnical-engineering":  ["civil-engineering", "engineering"],
    "transportation-engineering":["civil-engineering", "engineering"],
    "civil-engineering":         ["engineering"],
    "nanotechnology":            ["engineering"],
    "bioengineering":            ["engineering", "biology"],
    "chemical-engineering":      ["engineering", "chemistry"],
    "ocean-engineering":         ["engineering"],
    "environmental-engineering": ["engineering", "environmental-science"],
    "nuclear-engineering":       ["engineering", "nuclear-physics"],
    "aerospace-engineering":     ["engineering"],
    # Natural Sciences rollups
    "computational-neuroscience":["neuroscience", "biology", "computer-science"],
    "computational-biology":     ["biology", "computer-science", "bioinformatics"],
    "bioinformatics":            ["biology", "computer-science"],
    "genomics":                  ["genetics", "biology"],
    "physiology":                ["biology"],
    "immunology":                ["biology"],
    "microbiology":              ["biology"],
    "evolutionary-biology":      ["biology"],
    "ecology":                   ["biology"],
    "cell-biology":              ["biology"],
    "neuroscience":              ["biology"],
    "molecular-biology":         ["biology", "genetics"],
    "genetics":                  ["biology"],
    "biochemistry":              ["biology", "chemistry"],
    "biostatistics":             ["statistics", "biology"],
    "sustainability":            ["environmental-science"],
    "atmospheric-science":       ["earth-science"],
    "climate-science":           ["earth-science"],
    "geology":                   ["earth-science"],
    "epidemiology":              ["public-health", "medicine"],
    "inorganic-chemistry":       ["chemistry"],
    "physical-chemistry":        ["chemistry"],
    "organic-chemistry":         ["chemistry"],
    "general-chemistry":         ["chemistry"],
    # Social Sciences rollups
    "econometrics":              ["economics", "statistics"],
    "game-theory":               ["economics", "mathematics"],
    "behavioral-economics":      ["economics"],
    "international-economics":   ["economics"],
    "political-economy":         ["economics", "political-science"],
    "economic-history":          ["economics", "history"],
    "macroeconomics":            ["economics"],
    "microeconomics":            ["economics"],
    "finance":                   ["economics"],
    "constitutional-law":        ["law"],
    "criminal-justice":          ["law"],
    "environmental-law":         ["law", "environmental-science"],
    "comparative-politics":      ["political-science"],
    "global-politics":           ["political-science", "international-relations"],
    "cognitive-psychology":      ["psychology"],
    "developmental-psychology":  ["psychology"],
    "social-psychology":         ["psychology", "sociology"],
    "behavioral-science":        ["psychology"],
    "anthropology":              ["sociology"],
    "social-sciences":           ["sociology"],
    # Humanities rollups
    "art-history":               ["history", "arts"],
    "medieval-history":          ["history"],
    "european-history":          ["history"],
    "world-history":             ["history"],
    "ancient-history":           ["history"],
    "american-history":          ["history"],
    "political-philosophy":      ["philosophy", "political-science"],
    "ancient-philosophy":        ["philosophy"],
    "philosophy-of-mind":        ["philosophy", "psychology"],
    "ethics":                    ["philosophy"],
    "literary-theory":           ["literature"],
    "poetry":                    ["literature"],
    "linguistics":               ["literature", "language"],
    "music-theory":              ["music"],
    "film-studies":              ["arts"],
    "theater":                   ["arts"],
    "animation":                 ["arts", "computer-graphics"],
    # Business rollups
    "human-resources":           ["management", "business"],
    "logistics":                 ["management", "business"],
    "project-management":        ["management", "business"],
    "leadership":                ["management", "business"],
    "marketing":                 ["business"],
    "management":                ["business"],
    "entrepreneurship":          ["business"],
    "cryptocurrency":            ["blockchain", "finance"],
    "blockchain":                ["technology", "computer-science"],
}

# ---------------------------------------------------------------------------
# Run tagging
# ---------------------------------------------------------------------------
cur.execute("SELECT slug, id FROM subjects")
slug_to_id = {r[0]: r[1] for r in cur.fetchall()}
subject_slugs = set(slug_to_id.keys())
print(f"Subjects in DB: {len(subject_slugs)}")

cur.execute("SELECT course_id, subject_id FROM course_subjects")
existing: set[tuple] = set(cur.fetchall())
print(f"Existing tags: {len(existing)}")

cur.execute("SELECT id, title, description, source_url, source_key FROM courses")
courses = cur.fetchall()
print(f"Courses to process: {len(courses)}")

MIT_DEPT_MAP: dict[str, list[str]] = {
    "1": ["civil-engineering", "environmental-science"],
    "2": ["mechanical-engineering"],
    "3": ["materials-science", "condensed-matter"],
    "4": ["architecture"],
    "5": ["chemistry"],
    "6": ["computer-science", "electrical-engineering"],
    "7": ["biology"],
    "8": ["physics"],
    "9": ["neuroscience", "psychology"],
    "10": ["chemical-engineering"],
    "11": ["political-science", "sociology"],
    "12": ["earth-science"],
    "14": ["economics"],
    "15": ["management", "economics"],
    "16": ["aerospace-engineering"],
    "17": ["political-science"],
    "18": ["mathematics"],
    "20": ["bioengineering"],
    "21a": ["anthropology"],
    "21g": ["language"],
    "21h": ["history"],
    "21l": ["literature"],
    "21m": ["music"],
    "21w": ["literature"],
    "22": ["nuclear-engineering"],
    "24": ["philosophy", "linguistics"],
    "hst": ["medicine", "biology"],
    "mas": ["computer-science"],
    "ids": ["statistics", "data-science"],
}


def extract_mit_dept(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"/courses/([a-z0-9]+)-", url)
    if not m:
        return None
    raw = m.group(1)
    for pat in [r"^([0-9]+[a-z]+|[a-z]+)", r"^([0-9]+)"]:
        mm = re.match(pat, raw)
        if mm:
            return mm.group(1)
    return None


to_insert: list[tuple] = []

def ensure_tag(course_id, slug: str) -> None:
    if slug not in slug_to_id:
        return
    sid = slug_to_id[slug]
    key = (course_id, sid)
    if key not in existing:
        to_insert.append(key)
        existing.add(key)

def apply_rollups(course_id, slug: str) -> None:
    for parent in ROLLUPS.get(slug, []):
        ensure_tag(course_id, parent)
        # one level of grandparent rollup
        for grandparent in ROLLUPS.get(parent, []):
            ensure_tag(course_id, grandparent)


for course_id, title, description, source_url, source_key in courses:
    combined = (title + " " + (description or "")).lower()

    matched_specific: list[str] = []
    for slug, keywords in RULES:
        if slug not in subject_slugs:
            continue
        for kw in keywords:
            if kw in combined:
                ensure_tag(course_id, slug)
                matched_specific.append(slug)
                break

    # Apply rollups for every matched subject
    for slug in matched_specific:
        apply_rollups(course_id, slug)

    # MIT dept fallback if still nothing matched
    if source_key == "mit_ocw" and not any(k[0] == course_id for k in to_insert):
        dept = extract_mit_dept(source_url)
        if dept and dept in MIT_DEPT_MAP:
            for slug in MIT_DEPT_MAP[dept]:
                ensure_tag(course_id, slug)
                apply_rollups(course_id, slug)


if to_insert:
    cur.executemany(
        "INSERT INTO course_subjects (course_id, subject_id) VALUES (%s,%s) ON CONFLICT DO NOTHING",
        to_insert,
    )
    conn.commit()

print(f"Inserted {len(to_insert)} new subject tags")

# Report
cur.execute("""
    SELECT s.slug,
           COUNT(cs.course_id) FILTER (WHERE c.is_published AND c.has_video_lectures) AS v
    FROM subjects s
    JOIN course_subjects cs ON cs.subject_id = s.id
    JOIN courses c ON c.id = cs.course_id
    GROUP BY s.slug
    HAVING COUNT(cs.course_id) FILTER (WHERE c.is_published AND c.has_video_lectures) > 0
    ORDER BY v DESC LIMIT 50
""")
print("\nTop subjects (video courses):")
for slug, cnt in cur.fetchall():
    print(f"  {cnt:5d}  {slug}")

cur.close(); conn.close()
