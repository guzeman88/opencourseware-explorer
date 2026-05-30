"""
tag_courses.py
Auto-tags every course in the DB with one or more subjects based on
keyword rules matched against the course title (case-insensitive).
Existing tags are preserved; only new ones are inserted.
"""

import os
import psycopg2
import re

CONN_STR = os.environ.get("DATABASE_URL", "postgresql://ocw:ocwpassword@127.0.0.1:5432/opencourseware")
# Set RESET_TAGS=1 to wipe all course_subjects before retagging (clean slate).
RESET_FIRST = os.environ.get("RESET_TAGS", "0") == "1"

# Rules: list of (subject_slug, [keywords_that_match_in_title])
# Order matters only for readability. A course can match multiple subjects.
# MIT department number → list of subject slugs (used as fallback when keyword match fails)
MIT_DEPT_MAP: dict[str, list[str]] = {
    "1":   ["engineering", "ecology"],                          # Civil & Environmental
    "2":   ["engineering", "mechanics"],                        # Mechanical Engineering
    "3":   ["engineering", "chemistry"],                        # Materials Science
    "4":   ["engineering"],                                     # Architecture
    "5":   ["chemistry"],                                       # Chemistry
    "6":   ["computer-science", "electrical-engineering"],      # EECS
    "7":   ["biology"],                                         # Biology
    "8":   ["physics"],                                         # Physics
    "9":   ["biology", "psychology"],                           # Brain & Cognitive Sciences
    "10":  ["engineering", "chemistry"],                        # Chemical Engineering
    "11":  ["political-science", "sociology"],                  # Urban Studies & Planning
    "12":  ["physics", "ecology"],                              # Earth, Atmospheric, Planetary
    "14":  ["economics"],                                       # Economics
    "15":  ["economics", "finance"],                            # Sloan School of Management
    "16":  ["engineering", "mechanics"],                        # Aeronautics & Astronautics
    "17":  ["political-science"],                               # Political Science
    "18":  ["mathematics"],                                     # Mathematics
    "20":  ["biology", "engineering"],                          # Biological Engineering
    "21a": ["sociology"],                                       # Anthropology
    "21g": ["literature"],                                      # Global Languages
    "21h": ["history"],                                         # History
    "21l": ["literature"],                                      # Literature
    "21m": ["literature"],                                      # Music & Theater Arts
    "21w": ["literature"],                                      # Writing
    "22":  ["engineering", "physics"],                          # Nuclear Engineering
    "24":  ["philosophy"],                                      # Linguistics & Philosophy
    "wgs": ["sociology"],                                       # Women's & Gender Studies
    "res": ["engineering"],                                     # Resources (default)
    "sts": ["sociology"],                                       # Science, Technology & Society
    "sp":  ["engineering"],                                     # Special programs
    "esd": ["engineering", "economics"],                        # Engineering Systems
    "hsst": ["life-sciences"],                                  # Health Sciences & Technology
    "hst": ["life-sciences"],
    "mas": ["computer-science"],                                # Media Arts & Sciences
    "ids": ["statistics"],                                      # Institute for Data, Systems
    "cms": ["literature"],                                      # Comparative Media Studies
    "ccs": ["sociology"],
    "ec":  ["engineering"],
    "es":  ["engineering"],
}

RULES = [
    # ── Computer Science & Programming ─────────────────────────────────────
    ("computer-science",         ["computer science", "cs 6", "cs 7", "cs 8", "cs 9",
                                   "cs 1", "cs 2", "cs 3", "cs 4", "cs 5",
                                   "eecs", "computing", "informatics", "software engineering",
                                   "software design", "computation", "computer systems",
                                   "computer organization", "computer architecture",
                                   "operating system", "compiler", "programming language",
                                   "introduction to computer", "intro to computer"]),
    ("algorithms",               ["algorithm", "data structure", "discrete math",
                                   "combinatorics", "graph theory", "complexity",
                                   "theory of computation", "computational complexity",
                                   "computational geometry"]),
    ("data-structures",          ["data structure", "data organization", "trees and graphs",
                                   "linked list", "hash table"]),
    ("operating-systems",        ["operating system", "os kernel", "linux kernel",
                                   "unix system", "process scheduling", "memory management"]),
    ("computer-architecture",    ["computer architecture", "computer organization",
                                   "digital system", "digital logic", "microprocessor",
                                   "cpu design", "hardware design", "instruction set"]),
    ("computer-systems",         ["computer systems", "systems programming", "low-level programming",
                                   "system software", "computer system design"]),
    ("distributed-systems",      ["distributed systems", "distributed computing",
                                   "microservices", "consensus algorithm", "fault tolerance",
                                   "distributed database", "cloud computing"]),
    ("computer-networks",        ["computer network", "network protocol", "tcp/ip",
                                   "wireless network", "network security", "lan ",
                                   "wan ", "socket programming"]),
    ("embedded-systems",         ["embedded system", "microcontroller", "real-time system",
                                   "arduino", "raspberry pi", "rtos", "embedded programming",
                                   "arm processor"]),
    ("systems-programming",      ["systems programming", "c programming", "unix programming",
                                   "system calls", "kernel programming"]),
    ("parallel-computing",       ["parallel computing", "parallel programming",
                                   "openmp", "mpi ", "cuda ", "gpu programming",
                                   "multicore", "multithreading"]),
    ("high-performance-computing", ["high performance computing", "hpc ", "supercomputing",
                                   "scientific computing", "numerical computing"]),
    ("programming-languages",    ["programming language", "language design", "type theory",
                                   "compiler design", "interpreter", "functional programming",
                                   "object-oriented", "language implementation"]),
    ("compilers",                ["compiler", "compiler design", "parsing", "lexical analysis",
                                   "code generation", "syntax analysis", "language processing"]),
    ("computer-graphics",        ["computer graphics", "rendering", "3d graphics",
                                   "opengl", "webgl", "shading", "ray tracing",
                                   "graphics programming", "visualization"]),
    ("human-computer-interaction", ["human computer interaction", "hci ", "user interface",
                                   "user experience", "ux design", "usability",
                                   "interaction design", "interface design"]),
    ("databases",                ["database", "sql", "relational", "data management",
                                   "data engineering", "nosql", "query language"]),
    ("networking",               ["computer network", "internet", "network protocol",
                                   "tcp/ip", "networking"]),
    ("cybersecurity",            ["security", "cybersecurity", "cryptography",
                                   "information security", "network security"]),
    ("computer-security",        ["computer security", "application security", "software security",
                                   "vulnerability", "penetration testing", "secure coding",
                                   "malware", "reverse engineering"]),
    ("digital-forensics",        ["digital forensics", "forensic computing", "incident response",
                                   "evidence analysis", "forensic investigation"]),
    ("systems-security",         ["systems security", "security engineering", "security design",
                                   "trusted computing", "access control"]),
    ("formal-verification",      ["formal verification", "model checking", "theorem proving",
                                   "program verification", "coq theorem", "isabelle",
                                   "agda ", "proof assistant", "formal methods",
                                   "program correctness"]),
    ("privacy",                  ["privacy", "data privacy", "differential privacy",
                                   "anonymization", "privacy preserving"]),
    ("web-development",          ["web development", "web design", "html", "css", "javascript",
                                   "node.js", "react", "frontend", "backend", "full stack",
                                   "web application", "rest api"]),
    ("mobile-development",       ["mobile", "android", "ios", "swift", "react native",
                                   "flutter", "app development"]),
    ("game-development",         ["game development", "game design", "game engine",
                                   "unity", "unreal"]),
    ("programming",              ["programming", "coding", "software", "python",
                                   "java ", "c++", "c programming", "lua", "r programming",
                                   "matlab", "introduction to computer"]),
    ("python",                   ["python"]),
    ("java",                     ["java "]),
    ("javascript",               ["javascript", "node.js", "typescript"]),
    ("c-programming",            ["c programming", " c ", "c++", "systems programming"]),
    ("c",                        [" c language", "c programming"]),
    ("swift",                    ["swift ", "ios development"]),
    ("sql",                      ["sql", "database query", "relational database"]),

    # ── Data Science ─────────────────────────────────────────────────────────
    ("data-science",             ["data science", "data scientist", "data analytics",
                                   "machine learning pipeline", "data analysis"]),
    ("data-analysis",            ["data analysis", "exploratory data", "statistical analysis",
                                   "data exploration", "analyzing data"]),
    ("data-visualization",       ["data visualization", "information visualization",
                                   "data viz", "tableau", "d3.js", "matplotlib",
                                   "seaborn", "visualizing data", "charts and graphs"]),
    ("big-data",                 ["big data", "hadoop", "spark", "mapreduce",
                                   "data warehouse", "data lake", "large scale data"]),
    ("data-engineering",         ["data engineering", "data pipeline", "etl ",
                                   "data infrastructure", "apache kafka",
                                   "data streaming", "data integration"]),
    ("data-mining",              ["data mining", "knowledge discovery", "pattern mining",
                                   "association rules", "clustering algorithms"]),

    # ── Theory of Computing ───────────────────────────────────────────────────
    ("theory-of-computing",      ["theory of computation", "automata theory", "turing machine",
                                   "formal languages", "computability theory",
                                   "theory of algorithms", "computational models"]),
    ("computational-complexity", ["computational complexity", "complexity theory",
                                   "np-complete", "np-hard", "p vs np",
                                   "time complexity", "space complexity"]),
    ("information-theory",       ["information theory", "entropy", "channel capacity",
                                   "data compression", "coding theory", "shannon"]),

    # ── AI / ML ─────────────────────────────────────────────────────────────
    ("machine-learning",         ["machine learning", "ml ", "supervised learning",
                                   "unsupervised learning", "classification", "regression",
                                   "neural network", "deep learning", "data science"]),
    ("deep-learning",            ["deep learning", "neural network", "cnn", "lstm",
                                   "transformer", "generative model", "diffusion"]),
    ("neural-networks",          ["neural network", "backpropagation", "multilayer perceptron",
                                   "feedforward network", "activation function"]),
    ("large-language-models",    ["large language model", "llm ", "gpt ", "chatgpt",
                                   "language model", "bert ", "foundation model",
                                   "prompt engineering"]),
    ("generative-models",        ["generative model", "generative ai", "gan ", "vae ",
                                   "diffusion model", "image generation", "stable diffusion"]),
    ("ai-ethics",                ["ai ethics", "ethics of ai", "responsible ai",
                                   "algorithmic fairness", "bias in ai", "ai safety",
                                   "ethical ai"]),
    ("ai-safety",                ["ai safety", "ai alignment", "value alignment",
                                   "existential risk", "safe ai", "corrigibility"]),
    ("ai-agents",                ["ai agents", "autonomous agents", "agentic ai",
                                   "multi-agent", "intelligent agents", "agent planning"]),
    ("artificial-intelligence",  ["artificial intelligence", "ai ", " ai,", "intelligent system",
                                   "knowledge representation", "expert system",
                                   "automated planning", "search algorithm"]),
    ("natural-language-processing", ["natural language", "nlp", "text mining",
                                     "sentiment analysis", "language model",
                                     "computational linguistics"]),
    ("computer-vision",          ["computer vision", "image processing", "object detection",
                                   "image recognition", "visual", "pattern recognition"]),
    ("reinforcement-learning",   ["reinforcement learning", "rl ", "reward", "markov decision"]),
    ("robotics",                 ["robot", "autonomous", "control system",
                                   "mechatronic", "manipulation"]),
    ("graph-neural-networks",    ["graph neural", "gnn", "graph learning"]),
    ("meta-learning",            ["meta learning", "meta-learning", "few-shot", "transfer learning"]),

    # ── Mathematics ─────────────────────────────────────────────────────────
    ("mathematics",              ["mathematics", "math ", "mathematical", "algebra",
                                   "geometry", "topology", "number theory",
                                   "combinatorics", "real analysis", "complex analysis",
                                   "abstract algebra", "linear algebra", "discrete math",
                                   "differential geometry", "algebraic"]),
    ("algebra",                  ["algebra", "pre-algebra", "college algebra",
                                   "elementary algebra", "intermediate algebra"]),
    ("linear-algebra",           ["linear algebra", "matrix", "vector space", "eigenvalue"]),
    ("calculus",                 ["calculus", "differentiation", "integration", "multivariable",
                                   "single variable", "differential calculus"]),
    ("differential-equations",   ["differential equation", "ode", "pde",
                                   "partial differential", "ordinary differential",
                                   "dynamical system"]),
    ("proof-writing",            ["proof writing", "mathematical proof", "proof techniques",
                                   "introduction to proofs", "writing proofs",
                                   "logic and proofs", "mathematical reasoning"]),
    ("analysis",                 ["mathematical analysis", "real analysis", "complex analysis",
                                   "functional analysis", "advanced calculus"]),
    ("real-analysis",            ["real analysis", "advanced calculus", "metric space",
                                   "measure theory", "riemann integral", "lebesgue"]),
    ("complex-analysis",         ["complex analysis", "complex variables", "analytic functions",
                                   "contour integration", "cauchy", "complex function",
                                   "holomorphic"]),
    ("functional-analysis",      ["functional analysis", "hilbert space", "banach space",
                                   "operator theory"]),
    ("harmonic-analysis",        ["harmonic analysis", "fourier analysis", "wavelet",
                                   "fourier series", "spectral theory",
                                   "harmonic functions"]),
    ("measure-theory",           ["measure theory", "lebesgue measure", "integration theory",
                                   "measurable function", "lebesgue integral",
                                   "sigma algebra", "measurable set"]),
    ("number-theory",            ["number theory", "prime numbers", "modular arithmetic",
                                   "number fields", "diophantine"]),
    ("abstract-algebra",         ["abstract algebra", "algebraic structure",
                                   "groups rings fields", "group theory", "ring theory"]),
    ("group-theory",             ["group theory", "group actions", "symmetry group",
                                   "finite groups", "permutation group", "lie group"]),
    ("ring-theory",              ["ring theory", "commutative ring", "polynomial ring",
                                   "module theory", "ring algebra"]),
    ("galois-theory",            ["galois theory", "galois group", "field extension",
                                   "solvability by radicals", "splitting field"]),
    ("commutative-algebra",      ["commutative algebra", "commutative ring",
                                   "ideal theory", "localization algebra", "noetherian"]),
    ("homological-algebra",      ["homological algebra", "derived category",
                                   "exact sequence", "chain complex", "ext ", "tor "]),
    ("representation-theory",    ["representation theory", "lie algebra", "lie group",
                                   "character theory", "group representation",
                                   "module representation"]),
    ("category-theory",          ["category theory", " functor ", "natural transformation",
                                   "topos theory", "categorical logic", "adjoint functor"]),
    ("algebraic-number-theory",  ["algebraic number theory", "class field theory",
                                   "elliptic curve", "diophantine equations",
                                   "number fields"]),
    ("geometry",                 ["geometry", "euclidean geometry", "analytic geometry",
                                   "projective geometry", "coordinate geometry"]),
    ("topology",                 ["topology", "topological space", "metric space",
                                   "manifold", "topological", "point-set topology",
                                   "general topology", "topological invariants"]),
    ("differential-geometry",    ["differential geometry", "riemannian", "geodesic",
                                   "curvature", "tensor analysis", "differential forms",
                                   "smooth manifold"]),
    ("algebraic-geometry",       ["algebraic geometry", "varieties", "schemes",
                                   "algebraic curves", "elliptic curve", "sheaves"]),
    ("algebraic-topology",       ["algebraic topology", "homology", "cohomology",
                                   "homotopy theory", "fundamental group",
                                   "simplicial complex", "fiber bundle"]),
    ("riemannian-geometry",      ["riemannian geometry", "riemannian manifold",
                                   "riemannian metric", "geodesic", "riemannian"]),
    ("symplectic-geometry",      ["symplectic geometry", "symplectic manifold",
                                   "hamiltonian mechanics", "contact geometry",
                                   "poisson bracket"]),
    ("probability",              ["probability", "stochastic", "random process",
                                   "bayesian", "markov chain", "monte carlo"]),
    ("statistics",               ["statistics", "statistical", "regression",
                                   "inference", "hypothesis", "data analysis",
                                   "econometrics", "biostatistics"]),
    ("stochastic-processes",     ["stochastic process", "random walk", "brownian motion",
                                   "poisson process", "markov chain", "martingale",
                                   "stochastic differential equation"]),
    ("bayesian-statistics",      ["bayesian statistics", "bayesian inference",
                                   "bayesian network", "bayesian analysis",
                                   "prior distribution", "posterior distribution",
                                   "markov chain monte carlo", "mcmc"]),
    ("mathematical-statistics",  ["mathematical statistics", "statistical theory",
                                   "estimation theory", "statistical inference",
                                   "parametric statistics", "nonparametric statistics"]),
    ("stochastic-calculus",      ["stochastic calculus", "ito calculus", "ito lemma",
                                   "stochastic differential", "brownian motion"]),
    ("discrete-mathematics",     ["discrete math", "combinatorics", "graph theory",
                                   "logic ", "boolean algebra", "set theory"]),
    ("combinatorics",            ["combinatorics", "counting methods", "enumerative combinatorics",
                                   "generating functions", "permutations and combinations"]),
    ("graph-theory",             ["graph theory", "graph algorithms", "network flow",
                                   "graph coloring", "spanning tree"]),
    ("set-theory",               ["set theory", "axiomatic set theory", "zermelo",
                                   "cantor", "ordinals", "cardinals"]),
    ("logic",                    ["logic", "mathematical logic", "propositional logic",
                                   "predicate logic", "first-order logic",
                                   "symbolic logic", "boolean logic"]),
    ("optimization",             ["optimization", "convex optimization", "linear programming",
                                   "nonlinear optimization", "gradient descent",
                                   "mathematical programming"]),
    ("numerical-methods",        ["numerical methods", "numerical analysis",
                                   "computational mathematics", "finite element",
                                   "numerical linear algebra", "scientific computing"]),
    ("numerical-analysis",       ["numerical analysis", "approximation theory",
                                   "error analysis", "interpolation", "numerical integration",
                                   "finite difference method"]),
    ("operations-research",      ["operations research", "mathematical optimization",
                                   "linear programming", "integer programming",
                                   "queueing theory", "network optimization"]),
    ("mathematical-optimization", ["mathematical optimization", "optimization theory",
                                   "variational methods", "optimal control",
                                   "convex analysis", "duality theory"]),
    ("convex-optimization",      ["convex optimization", "convex analysis",
                                   "semidefinite programming", "convex programming",
                                   "interior point method"]),
    ("applied-mathematics",      ["applied mathematics", "applied math",
                                   "mathematical methods", "mathematical modeling",
                                   "math for engineers", "engineering mathematics"]),

    # ── Physics ─────────────────────────────────────────────────────────────
    ("physics",                  ["physics", "mechanics", "electromagnetism",
                                   "thermodynamics", "quantum", "relativity",
                                   "optics", "waves", "classical mechanics"]),
    ("mechanics",                ["mechanics", "classical mechanics", "statics",
                                   "rigid body dynamics", "continuum mechanics"]),
    ("classical-mechanics",      ["classical mechanics", "newtonian mechanics",
                                   "lagrangian", "hamiltonian mechanics",
                                   "analytical mechanics"]),
    ("electromagnetism",         ["electromagnetism", "electromagnetic", "maxwell",
                                   "electric field", "magnetic field", "electrostatics"]),
    ("electrodynamics",          ["electrodynamics", "classical electrodynamics",
                                   "maxwell equations", "jackson electrodynamics",
                                   "electromagnetic waves"]),
    ("optics",                   ["optics", "optical physics", "photonics",
                                   "laser physics", "geometrical optics", "wave optics",
                                   "light and matter", "diffraction", "interference"]),
    ("thermodynamics",           ["thermodynamics", "heat transfer", "statistical mechanics",
                                   "thermal"]),
    ("fluid-mechanics",          ["fluid mechanics", "fluid dynamics", "aerodynamics",
                                   "hydraulics", "fluid flow"]),
    ("fluid-dynamics",           ["fluid dynamics", "fluid mechanics", "aerodynamics",
                                   "hydrodynamics", "turbulence"]),
    ("continuum-mechanics",      ["continuum mechanics", "solid mechanics",
                                   "deformation", "elasticity theory", "stress analysis"]),
    ("waves",                    ["wave equation", "wave propagation", "wave optics",
                                   "electromagnetic waves", "wave mechanics",
                                   "seismic waves", "acoustic wave", "acoustics",
                                   "wave phenomena", "oscillations and waves",
                                   "vibrations and waves", "physics of waves",
                                   "waves and optics"]),
    ("statistical-mechanics",    ["statistical mechanics", "thermodynamics",
                                   "boltzmann", "partition function", "entropy",
                                   "phase transition"]),
    ("solid-state-physics",      ["solid state physics", "solid-state physics",
                                   "condensed matter", "band theory", "crystal structure",
                                   "semiconductor physics"]),
    ("condensed-matter",         ["condensed matter", "condensed-matter", "many-body",
                                   "superconductivity", "band structure", "materials physics",
                                   "phase transition"]),
    ("materials-science",        ["materials science", "material science",
                                   "metallurgy", "polymers", "crystallography"]),
    ("quantum-mechanics",        ["quantum", "quantum mechanics", "quantum field",
                                   "quantum information", "quantum computing"]),
    ("quantum-physics",          ["quantum physics", "quantum theory", "quantum world",
                                   "quantum phenomena", "wave-particle duality"]),
    ("quantum-field-theory",     ["quantum field theory", "qft", "feynman diagrams",
                                   "gauge theory", "renormalization", "standard model"]),
    ("quantum-computing",        ["quantum computing", "quantum algorithm", "quantum gate",
                                   "qubit", "quantum computer", "quantum circuit"]),
    ("quantum-information",      ["quantum information", "quantum entanglement",
                                   "quantum cryptography", "qubit", "quantum error correction",
                                   "quantum communication"]),
    ("quantum-optics",           ["quantum optics", "cavity qed", "laser quantum",
                                   "photon statistics", "coherent states",
                                   "quantum light-matter"]),
    ("particle-physics",         ["particle physics", "high energy physics",
                                   "standard model", "elementary particles",
                                   "collider", "feynman"]),
    ("nuclear-physics",          ["nuclear physics", "nuclear reaction", "radioactivity",
                                   "fission", "fusion physics"]),
    ("relativity",               ["relativity", "theory of relativity", "einstein",
                                   "spacetime", "lorentz"]),
    ("general-relativity",       ["general relativity", "general theory of relativity",
                                   "einstein equations", "curved spacetime", "spacetime",
                                   "schwarzschild", "black holes"]),
    ("special-relativity",       ["special relativity", "lorentz transformation",
                                   "special theory of relativity", "minkowski spacetime",
                                   "time dilation", "length contraction"]),
    ("theoretical-physics",      ["theoretical physics", "string theory", "gauge theory",
                                   "quantum field theory", "field theory",
                                   "mathematical physics"]),
    ("string-theory",            ["string theory", "superstring", "m-theory",
                                   " branes ", "string landscape", "string compactification"]),
    ("astrophysics",             ["astrophysics", "cosmology", "stellar", "galaxy"]),
    ("cosmology",                ["cosmology", "cosmological", "dark matter", "dark energy",
                                   "big bang"]),
    ("astronomy",                ["astronomy", "telescope", "celestial", "solar system",
                                   "planet"]),
    ("planetary-science",        ["planetary science", "solar system", "exoplanet",
                                   "planet formation", "astrobiology"]),
    ("signal-processing",        ["signal processing", "fourier", "filter design",
                                   "dsp", "communications", "control system"]),
    ("control-systems",          ["control system", "feedback", "pid", "optimal control",
                                   "control engineering", "process control"]),
    ("control-theory",           ["control theory", "feedback control", "robust control",
                                   "adaptive control", "control design"]),
    ("digital-systems",          ["digital system", "digital circuit", "vhdl",
                                   "fpga", "embedded system"]),
    ("dsp",                      ["digital signal processing", "dsp ", "signal processing",
                                   "filter design", "fft ", "discrete fourier"]),
    ("circuits",                 ["circuit analysis", "circuit design", "electronic circuit",
                                   "resistor capacitor", "rc circuit", "rlc circuit",
                                   "circuit theory", "kirchhoff"]),
    ("power-systems",            ["power system", "power engineering", "electric power",
                                   "smart grid", "renewable energy", "power electronics",
                                   "power generation"]),
    ("electronics",              ["electronics", "electronic circuits",
                                   "analog circuits", "transistor"]),
    ("digital-electronics",      ["digital electronics", "digital circuit",
                                   "logic circuit", "boolean logic"]),
    ("vlsi",                     ["vlsi", "very large scale integration",
                                   "chip design", "cmos design", "asic design",
                                   "integrated circuit design", "cmos circuit"]),

    # ── Engineering ─────────────────────────────────────────────────────────
    ("engineering",              ["engineering", "manufacturing",
                                   "civil engineering", "structural engineering",
                                   "mechanical engineering", "electrical engineering",
                                   "chemical engineering", "aerospace"]),
    ("electrical-engineering",   ["electrical engineering", "circuits", "electronics",
                                   "signal processing", "power system", "semiconductor"]),
    ("mechanical-engineering",   ["mechanical engineering", "mechanics of materials",
                                   "machine design", "thermal systems",
                                   "mechanical design", "machine elements"]),
    ("mechatronics",             ["mechatronics", "mechtronic", "electromechanical",
                                   "sensors and actuators", "motion control"]),
    ("manufacturing",            ["manufacturing", "manufacturing processes",
                                   "industrial engineering", "production engineering",
                                   "machining", "cnc", "quality control"]),
    ("heat-transfer",            ["heat transfer", "thermal engineering",
                                   "conduction", "convection", "radiation heat"]),
    ("vibrations",               ["vibrations", "vibration analysis", "structural dynamics",
                                   "mechanical vibrations", "modal analysis"]),
    ("civil-engineering",        ["civil engineering", "construction engineering",
                                   "infrastructure design", "civil structures"]),
    ("structural-engineering",   ["structural engineering", "structural analysis",
                                   "structural design", "structural mechanics"]),
    ("geotechnical-engineering", ["geotechnical engineering", "soil mechanics",
                                   "foundation engineering", "geotechnics"]),
    ("transportation-engineering", ["transportation engineering", "traffic engineering",
                                    "highway design", "transportation systems"]),
    ("water-resources",          ["water resources", "hydrology", "hydraulic engineering",
                                   "water supply", "irrigation engineering"]),
    ("structural-analysis",      ["structural analysis", "finite element analysis",
                                   "stress and strain", "structural loads"]),
    ("urban-planning",           ["urban planning", "city planning", "land use",
                                   "urban design", "regional planning"]),
    ("chemical-engineering",     ["chemical engineering", "chemical process",
                                   "reaction engineering", "process design",
                                   "unit operations", "transport phenomena"]),
    ("bioengineering",           ["bioengineering", "biomedical engineering",
                                   "biological engineering", "bio-engineering"]),
    ("biological-engineering",   ["biological engineering", "bioengineering",
                                   "bio engineering", "synthetic biology engineering"]),
    ("nanotechnology",           ["nanotechnology", "nanoscience", "nanomaterials",
                                   "nanoelectronics", "nanoscale"]),
    ("nuclear-engineering",      ["nuclear engineering", "reactor design",
                                   "nuclear technology", "nuclear safety",
                                   "radiation shielding"]),
    ("aerospace-engineering",    ["aerospace engineering", "aeronautics",
                                   "flight mechanics", "spacecraft", "rocket propulsion",
                                   "orbital mechanics"]),
    ("environmental-engineering", ["environmental engineering", "pollution control",
                                   "waste treatment", "environmental remediation",
                                   "water treatment"]),
    ("ocean-engineering",        ["ocean engineering", "marine engineering",
                                   "offshore engineering", "marine technology",
                                   "offshore structures", "ocean structures"]),

    # ── Chemistry ───────────────────────────────────────────────────────────
    ("chemistry",                ["chemistry", "chemical", "organic chemistry",
                                   "inorganic", "biochemistry", "molecular",
                                   "thermochemistry"]),
    ("organic-chemistry",        ["organic chemistry", "organic synthesis",
                                   "reaction mechanism", "organic reactions"]),
    ("physical-chemistry",       ["physical chemistry", "quantum chemistry",
                                   "thermodynamics chemistry", "chemical thermodynamics",
                                   "chemical kinetics", "spectroscopy"]),
    ("inorganic-chemistry",      ["inorganic chemistry", "coordination chemistry",
                                   "transition metals", "inorganic compounds"]),
    ("general-chemistry",        ["general chemistry", "introductory chemistry",
                                   "chemistry 1", "chemistry i", "chem 101",
                                   "principles of chemistry", "fundamentals of chemistry"]),

    # ── Biology & Life Sciences ──────────────────────────────────────────────
    ("biology",                  ["biology", "biological", "cell biology",
                                   "molecular biology", "genetics", "evolution",
                                   "ecology", "neuroscience", "neurobiology",
                                   "biochemistry", "microbiology", "virology",
                                   "immunology", "physiology", "anatomy"]),
    ("genetics",                 ["genetics", "heredity", "dna", "gene expression",
                                   "mendelian", "genetic variation", "alleles"]),
    ("molecular-biology",        ["molecular biology", "dna replication",
                                   "protein synthesis", "transcription and translation",
                                   "molecular mechanisms"]),
    ("cell-biology",             ["cell biology", "cellular biology",
                                   "cell signaling", "cell division", "mitosis",
                                   "cell structure", "organelles"]),
    ("neuroscience",             ["neuroscience", "neurobiology", "brain",
                                   "neurons", "neural circuits", "synaptic"]),
    ("genomics",                 ["genomics", "genome", "next generation sequencing",
                                   "whole genome", "comparative genomics"]),
    ("bioinformatics",           ["bioinformatics", "computational biology",
                                   "sequence analysis", "genome assembly"]),
    ("microbiology",             ["microbiology", "bacteria", "bacteriology",
                                   "microbial", "microorganisms", "virology"]),
    ("immunology",               ["immunology", "immune system", "antibodies",
                                   "innate immunity", "adaptive immunity", "vaccines"]),
    ("physiology",               ["physiology", "human physiology", "organ systems",
                                   "cardiovascular physiology", "respiratory physiology"]),
    ("botany",                   ["botany", "plant science", "plant biology",
                                   "plant physiology", "plant ecology"]),
    ("biochemistry",             ["biochemistry", "biomolecules", "enzymes",
                                   "metabolic pathways", "proteins and nucleic acids"]),
    ("animal-science",           ["animal science", "zoology", "animal behavior",
                                   "veterinary", "animal biology"]),
    ("plant-biology",            ["plant biology", "botany", "plant genetics",
                                   "plant development", "plant molecular biology"]),
    ("origins-of-life",          ["origins of life", "abiogenesis", "origin of life",
                                   "prebiotic chemistry", "primordial soup",
                                   "early life", "life's origins"]),
    ("computational-biology",    ["computational biology", "bioinformatics",
                                   "genomics algorithms", "sequence alignment"]),
    ("computational-neuroscience", ["computational neuroscience", "neural computation",
                                    "neural modeling", "spiking neuron"]),
    ("life-sciences",            ["life science", "medicine", "health", "biomedical",
                                   "public health", "epidemiology", "pharmacology",
                                   "clinical"]),
    ("evolution",                ["evolution", "evolutionary", "natural selection",
                                   "darwinian", "phylogenetics"]),
    ("ecology",                  ["ecology", "environmental", "ecosystem",
                                   "sustainability", "climate", "biodiversity"]),
    ("food-science",             ["food", "nutrition", "food science", "gastronomy"]),

    # ── Earth & Environment ────────────────────────────────────────────────
    ("earth-science",            ["earth science", "geoscience", "earth systems",
                                   "geophysics", "geology", "seismology",
                                   "earth and planetary"]),
    ("geology",                  ["geology", "rocks and minerals", "stratigraphy",
                                   "petrology", "mineralogy", "geologic"]),
    ("climate-science",          ["climate science", "climate change", "global warming",
                                   "climate model", "climate system", "climate dynamics"]),
    ("atmospheric-science",      ["atmospheric science", "atmospheric chemistry",
                                   "atmospheric physics", "atmosphere and climate",
                                   "meteorology", "climatology", "weather forecasting",
                                   "atmospheric dynamics"]),
    ("environmental-science",    ["environmental science", "environmental studies",
                                   "earth and environment", "environmental systems"]),
    ("geography",                ["geography", "human geography", "physical geography",
                                   "geospatial", "gis ", "cartography"]),
    ("environmental-economics",  ["environmental economics", "ecological economics",
                                   "natural resource economics", "carbon pricing"]),
    ("sustainability",           ["sustainability", "sustainable development",
                                   "sustainable energy", "green technology",
                                   "environmental sustainability"]),

    # ── Medicine & Health ──────────────────────────────────────────────────
    ("medicine",                 ["medicine", "medical", "clinical medicine",
                                   "medical education", "pathology", "diagnosis"]),
    ("anatomy",                  ["anatomy", "human anatomy", "anatomical",
                                   "body systems", "gross anatomy"]),
    ("epidemiology",             ["epidemiology", "disease surveillance",
                                   "public health research", "epidemiological study"]),
    ("public-health",            ["public health", "community health",
                                   "population health", "health promotion",
                                   "health policy"]),
    ("health",                   ["health", "healthcare", "wellness",
                                   "health education", "health science"]),
    ("nutrition",                ["nutrition", "dietary", "food science",
                                   "nutritional science", "diet and health"]),
    ("global-health",            ["global health", "international health",
                                   "tropical medicine", "health in developing"]),
    ("clinical-trials",          ["clinical trial", "randomized controlled",
                                   "randomized controlled trial", "clinical research",
                                   "drug trial", "phase i", "phase ii", "phase iii"]),
    ("pharmacology",             ["pharmacology", "drug discovery", "pharmacokinetics",
                                   "toxicology", "drug design", "pharmaceutical"]),
    ("biostatistics",            ["biostatistics", "statistical methods in biology",
                                   "survival analysis", "clinical statistics"]),
    ("forensic-science",         ["forensic science", "forensic chemistry",
                                   "forensic biology", "criminalistics"]),
    ("mental-health",            ["mental health", "psychiatry", "depression",
                                   "anxiety disorder", "psychiatric", "mental illness"]),
    ("reproductive-health",      ["reproductive health", "reproductive biology",
                                   "fertility", "obstetrics", "maternal health"]),
    ("child-health",             ["child health", "pediatrics", "pediatric",
                                   "child medicine", "neonatal"]),
    ("maternal-health",          ["maternal health", "maternal care",
                                   "obstetrics", "prenatal", "postnatal"]),
    ("infectious-disease",       ["infectious disease", "infection", "pathogen",
                                   "antimicrobial", "epidemics", "pandemic"]),

    # ── Economics & Finance ──────────────────────────────────────────────────
    ("economics",                ["economics", "economic", "microeconomics", "macroeconomics",
                                   "market", "trade", "fiscal", "monetary"]),
    ("microeconomics",           ["microeconomics", "micro ", "consumer theory",
                                   "producer theory", "market structure"]),
    ("macroeconomics",           ["macroeconomics", "macro ", "gdp", "inflation",
                                   "monetary policy", "fiscal policy", "growth"]),
    ("finance",                  ["finance", "financial", "investment", "portfolio",
                                   "asset pricing", "derivatives", "banking", "accounting"]),
    ("game-theory",              ["game theory", "strategic", "nash equilibrium"]),
    ("econometrics",             ["econometrics", "economic modeling",
                                   "regression analysis economics", "panel data"]),
    ("behavioral-economics",     ["behavioral economics", "behavioral finance",
                                   "nudge theory", "cognitive biases economics",
                                   "decision making economics"]),
    ("accounting",               ["accounting", "financial accounting",
                                   "managerial accounting", "auditing",
                                   "bookkeeping", "balance sheet"]),
    ("international-economics",  ["international economics", "global trade",
                                   "exchange rates", "balance of payments"]),
    ("international-trade",      ["international trade", "trade theory",
                                   "comparative advantage", "tariffs", "trade policy"]),
    ("economic-history",         ["economic history", "history of economics",
                                   "historical economics"]),
    ("political-economy",        ["political economy", "political economics",
                                   "capitalism", "marxist economics"]),

    # ── Political Science & Law ───────────────────────────────────────────────
    ("political-science",        ["political science", "politics", "government",
                                   "public policy", "international relations",
                                   "democracy", "policy"]),
    ("international-relations",  ["international relations", "foreign policy",
                                   "diplomacy", "international affairs",
                                   "geopolitics", "global governance"]),
    ("public-policy",            ["public policy", "policy analysis",
                                   "policy making", "government policy"]),
    ("law",                      ["law", "legal system", "jurisprudence",
                                   "legal theory", "law and society", "legislation"]),
    ("constitutional-law",       ["constitutional law", "constitution",
                                   "constitutional rights", "bill of rights"]),
    ("comparative-politics",     ["comparative politics", "comparative government",
                                   "political systems", "comparative political"]),
    ("global-politics",          ["global politics", "world politics",
                                   "international security", "foreign policy analysis",
                                   "international order", "geopolitics"]),
    ("legal-studies",            ["legal studies", "law and society",
                                   "legal institutions", "legal practice"]),
    ("criminal-justice",         ["criminal justice", "criminology", "crime and",
                                   "criminal law", "penology", "criminal procedure"]),
    ("human-rights",             ["human rights", "international human rights",
                                   "human rights law", "civil liberties"]),
    ("civil-rights",             ["civil rights", "civil rights movement",
                                   "voting rights", "racial justice",
                                   "desegregation", "jim crow", "naacp"]),
    ("environmental-law",        ["environmental law", "environmental regulation",
                                   "climate law", "natural resources law"]),

    # ── Psychology & Cognitive Science ───────────────────────────────────────
    ("psychology",               ["psychology", "cognitive", "behavioral", "neuroscience",
                                   "perception", "learning theory", "mental"]),
    ("cognitive-science",        ["cognitive science", "cognition", "cognitive psychology",
                                   "mental processes", "thinking and reasoning"]),
    ("social-psychology",        ["social psychology", "social cognition",
                                   "attitudes and behavior", "group dynamics"]),
    ("developmental-psychology", ["developmental psychology", "child development",
                                   "developmental science", "lifespan development",
                                   "cognitive development"]),
    ("behavioral-science",       ["behavioral science", "behavioral research",
                                   "human behavior", "behavior analysis"]),
    ("cognitive-psychology",     ["cognitive psychology", "memory and cognition",
                                   "attention and perception", "cognitive processes"]),

    # ── Sociology & Anthropology ───────────────────────────────────────────────
    ("sociology",                ["sociology", "social", "society", "culture",
                                   "anthropology", "ethnography", "race ", "gender"]),
    ("social-science",           ["social science", "social research", "social studies"]),
    ("social-sciences",          ["social sciences", "behavioral and social"]),
    ("anthropology",             ["anthropology", "cultural anthropology",
                                   "physical anthropology", "social anthropology",
                                   "ethnography", "archaeological"]),
    ("social-theory",            ["social theory", "sociological theory",
                                   "critical theory", "structuralism"]),
    ("demographics",             ["demographics", "demography", "population study",
                                   "population dynamics", "census",
                                   "fertility rate", "mortality rate", "migration"]),

    # ── History ──────────────────────────────────────────────────────────────
    ("history",                  ["history", "historical", "ancient", "medieval",
                                   "modern history", "world history"]),
    ("american-history",         ["american history", "united states history",
                                   "us history", "colonial america"]),
    ("european-history",         ["european history", "europe ", "european civilization"]),
    ("ancient-history",          ["ancient history", "ancient world", "classical antiquity",
                                   "rome", "greek ", "mesopotamia"]),
    ("world-history",            ["world history", "global history", "civilization"]),
    ("medieval-history",         ["medieval history", "middle ages", "medieval europe",
                                   "byzantine", "feudalism", "crusades"]),
    ("art-history",              ["art history", "history of art", "western art",
                                   "art movements"]),
    ("western-civilization",     ["western civilization", "history of western",
                                   "european civilization"]),
    ("media-history",            ["media history", "history of media",
                                   "journalism history", "history of communication",
                                   "history of television", "history of film"]),

    # ── Philosophy & Ethics ───────────────────────────────────────────────────
    ("philosophy",               ["philosophy", "ethics", "epistemology", "logic",
                                   "ontology", "moral"]),
    ("ethics",                   ["ethics", "moral philosophy", "bioethics",
                                   "professional ethics", "justice"]),
    ("logic",                    ["logic", "mathematical logic", "propositional logic",
                                   "predicate logic", "symbolic logic",
                                   "logical reasoning", "critical thinking"]),
    ("philosophy-of-mind",       ["philosophy of mind", "consciousness",
                                   "mind-body problem", "qualia",
                                   "mental representation", "intentionality",
                                   "philosophy of consciousness"]),
    ("ancient-philosophy",       ["ancient philosophy", "greek philosophy", "plato",
                                   "aristotle", "stoicism", "epicurean",
                                   "pre-socratic", "socrates"]),
    ("political-philosophy",     ["political philosophy", "political theory",
                                   "justice and equality", "rawls", "political thought"]),

    # ── Language & Literature ─────────────────────────────────────────────────
    ("literature",               ["literature", "literary", "poetry", "novel",
                                   "fiction", "rhetoric", "phonology",
                                   "translation", "discourse"]),
    ("linguistics",              ["linguistics", "phonology", "syntax", "semantics",
                                   "morphology", "applied linguistics", "language structure"]),
    ("writing",                  ["writing", "academic writing", "creative writing",
                                   "technical writing", "essay writing", "composition"]),
    ("language",                 ["language learning", "second language",
                                   "foreign language", "language acquisition"]),
    ("poetry",                   ["poetry", "poetics", "verse", "lyric poetry",
                                   "literary poetry", "poem analysis"]),
    ("literary-theory",          ["literary theory", "literary criticism",
                                   "critical theory", "narratology",
                                   "derrida", "foucault", "new criticism",
                                   "postcolonial theory", "structuralism"]),
    ("english",                  ["english ", "english language", "english literature",
                                   "creative writing", "academic writing"]),
    ("religious-studies",        ["religion", "religious", "theology", "islam",
                                   "christianity", "buddhism", "hinduism", "spirituality",
                                   "scripture", "sacred"]),

    # ── Arts & Media ──────────────────────────────────────────────────────────
    ("music",                    ["music", "musical", "composition music",
                                   "music theory", "music history", "orchestral",
                                   "jazz", "classical music"]),
    ("music-theory",             ["music theory", "harmony", "counterpoint",
                                   "musical analysis", "voice leading"]),
    ("arts",                     ["arts", "fine arts", "visual arts",
                                   "performing arts", "studio art"]),
    ("architecture",             ["architecture", "architectural design",
                                   "building design", "urban architecture"]),
    ("design",                   ["design", "graphic design", "industrial design",
                                   "product design", "user interface design"]),
    ("film-studies",             ["film studies", "film theory", "cinema",
                                   "film history", "cinematography", "screenwriting"]),
    ("theater",                  ["theater", "theatre", "drama", "playwriting",
                                   "theatrical performance", "acting"]),
    ("photography",              ["photography", "photographic", "digital photography",
                                   "photo composition", "photojournalism"]),
    ("animation",                ["animation", "3d animation", "computer animation",
                                   "motion graphics"]),
    ("american-studies",         ["american studies", "american culture",
                                   "american society"]),
    ("african-american-studies", ["african american", "black history",
                                   "civil rights", "african diaspora"]),

    # ── Business & Management ─────────────────────────────────────────────────
    ("business",                 ["business", "business administration",
                                   "business management", "mba"]),
    ("entrepreneurship",         ["entrepreneurship", "startup", "venture capital",
                                   "new ventures", "innovation and entrepreneurship"]),
    ("management",               ["management", "organizational management",
                                   "business management", "managerial"]),
    ("marketing",                ["marketing", "digital marketing", "brand management",
                                   "market research", "consumer behavior"]),
    ("leadership",               ["leadership", "organizational leadership",
                                   "leadership development", "executive leadership"]),
    ("project-management",       ["project management", "agile", "scrum",
                                   "project planning", "risk management"]),
    ("logistics",                ["logistics", "supply chain", "operations management",
                                   "inventory management", "distribution"]),
    ("human-resources",          ["human resources", "hr management",
                                   "talent management", "workforce"]),

    # ── Technology & Society ───────────────────────────────────────────────────
    ("technology",               ["technology", "technological", "tech industry",
                                   "emerging technology"]),
    ("blockchain",               ["blockchain", "distributed ledger", "ethereum",
                                   "smart contract", "web3"]),
    ("cryptocurrency",           ["cryptocurrency", "bitcoin", "crypto",
                                   "digital currency", "defi"]),
    ("innovation",               ["innovation", "technology transfer",
                                   "disruptive technology", "design thinking"]),
    ("energy",                   ["energy", "renewable energy", "solar energy",
                                   "wind energy", "energy systems",
                                   "energy policy"]),
    ("technology-and-society",   ["technology and society", "tech and society",
                                   "social impact of technology", "digital society"]),
    ("research-methods",         ["research methods", "research methodology",
                                   "qualitative research", "quantitative research",
                                   "scientific method"]),

    # ── Additional broad catches ────────────────────────────────────────────
    ("engineering",              ["transportation", "infrastructure",
                                   "urban engineering", "construction", "aviation",
                                   "aircraft", "antenna", "radar", "satellite",
                                   "polymer", "semiconductor fabrication", "nuclear engineering",
                                   "system architecture", "system design",
                                   "product engineering"]),
    ("physics",                  ["acoustics", "acoustical", "wave mechanics",
                                   "wave propagation", "oscillation",
                                   "electromagnetic", "laser", "photonics",
                                   "spectroscopy", "geophysics"]),
    ("ecology",                  ["ocean", "atmosphere", "climate change",
                                   "environmental science", "earth science",
                                   "global warming", "water resources",
                                   "watershed", "urban ecology"]),
    ("sociology",                ["urban", "city", "cities", "community",
                                   "negotiation", "public sector",
                                   "immigration", "poverty",
                                   "inequality", "governance",
                                   "media studies", "journalism"]),
    ("economics",                ["industrial organization", "capitalism", "poverty",
                                   "development economics", "international development",
                                   "world poverty"]),
    ("mathematics",              ["quantitative", "numerical method",
                                   "simulation", "modeling", "stochastic process"]),
    ("life-sciences",            ["nuclear magnetic resonance", "nmr", "spectroscopy",
                                   "drug", "pharmaceutical", "vaccine", "immune",
                                   "pandemic", "infectious disease"]),
    ("history",                  ["columbus", "colonial", "civilization", "war ",
                                   "revolution", "empire", "dynasty"]),
    ("trigonometry",             ["trigonometry", "trigonometric", " trig "]),
    ("precalculus",              ["precalculus", "pre-calculus",
                                   "algebra and trigonometry", "functions and graphs"]),
    ("data-management",          ["database management", "data management",
                                   "information management", "data governance"]),
]


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def build_title_lower(title: str, description: str | None) -> str:
    return (title + " " + (description or "")).lower()


def match_subjects(combined: str, subject_slugs: set[str]) -> list[str]:
    matched = []
    for slug, keywords in RULES:
        if slug not in subject_slugs:
            continue
        for kw in keywords:
            if kw in combined:
                matched.append(slug)
                break
    return matched


def extract_mit_dept(source_url: str | None) -> str | None:
    """Extract MIT course number prefix from source_url like 14-02-... → '14'"""
    if not source_url:
        return None
    m = re.search(r"/courses/([a-z0-9]+)-", source_url)
    if not m:
        return None
    raw = m.group(1)
    # Try multi-char alpha prefix first (21h, 21g, 21a, 21l, 21m, 21w, wgs, sts, hst, mas, cms, res, esd, ec, sp, ids)
    alpha_m = re.match(r"^([0-9]+[a-z]+|[a-z]+)", raw)
    if alpha_m:
        return alpha_m.group(1)
    # Pure numeric
    num_m = re.match(r"^([0-9]+)", raw)
    if num_m:
        return num_m.group(1)
    return None


def main():
    conn = psycopg2.connect(CONN_STR)
    cur = conn.cursor()

    # Load subject slug → id
    cur.execute("SELECT slug, id FROM subjects")
    slug_to_id = {row[0]: row[1] for row in cur.fetchall()}
    subject_slugs = set(slug_to_id.keys())

    if RESET_FIRST:
        cur.execute("DELETE FROM course_subjects")
        conn.commit()
        print("Deleted all existing course_subjects (RESET mode)", flush=True)

    # Load existing tags
    cur.execute("SELECT course_id, subject_id FROM course_subjects")
    existing = set(cur.fetchall())
    print(f"Existing tags: {len(existing)}", flush=True)

    # Load all courses (with source_url for MIT dept lookup)
    cur.execute("SELECT id, title, description, source_url, source_key FROM courses")
    courses = cur.fetchall()
    print(f"Courses to tag: {len(courses)}", flush=True)

    inserted = 0
    pending: list[tuple] = []

    def flush():
        nonlocal inserted
        if not pending:
            return
        cur.executemany(
            "INSERT INTO course_subjects (course_id, subject_id) VALUES (%s, %s)"
            " ON CONFLICT DO NOTHING",
            pending,
        )
        inserted += len(pending)
        pending.clear()

    for course_id, title, description, source_url, source_key in courses:
        combined = build_title_lower(title, description)
        matched_slugs = match_subjects(combined, subject_slugs)

        course_sids: list[tuple] = []
        for slug in matched_slugs:
            if slug not in slug_to_id:
                continue
            sid = slug_to_id[slug]
            key = (course_id, sid)
            if key not in existing:
                pending.append(key)
                existing.add(key)
                course_sids.append(key)

        # MIT course-number fallback: if nothing matched, assign dept default
        if not course_sids and source_key == "mit_ocw":
            dept = extract_mit_dept(source_url)
            if dept and dept in MIT_DEPT_MAP:
                for slug in MIT_DEPT_MAP[dept]:
                    if slug not in slug_to_id:
                        continue
                    sid = slug_to_id[slug]
                    key = (course_id, sid)
                    if key not in existing:
                        pending.append(key)
                        existing.add(key)

        if len(pending) >= 500:
            flush()

    flush()
    conn.commit()
    print(f"Inserted {inserted} new tags", flush=True)

    # Report top subjects
    cur.execute("""
        SELECT s.name, COUNT(cs.course_id) cnt
        FROM subjects s
        LEFT JOIN course_subjects cs ON cs.subject_id = s.id
        GROUP BY s.name ORDER BY cnt DESC LIMIT 20
    """)
    print("\nTop subjects after tagging:")
    for name, cnt in cur.fetchall():
        print(f"  {name:35s} {cnt}")

    # Total tagged
    cur.execute("SELECT COUNT(DISTINCT course_id) FROM course_subjects")
    tagged = cur.fetchone()[0]
    print(f"\nCourses with at least 1 subject: {tagged}/{len(courses)} "
          f"= {tagged/len(courses)*100:.1f}%")

    conn.close()


if __name__ == "__main__":
    main()
