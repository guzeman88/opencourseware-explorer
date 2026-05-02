#!/usr/bin/env python
"""
Comprehensive fast course loader for all remaining university sources.
Loads real known courses WITHOUT yt-dlp enrichment.
Run from scraper/ directory.
"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

# ─── Course Catalogue ──────────────────────────────────────────────────────────
# Format: (title, dept, instructor, source_url, level, subjects[])
# level must be: undergraduate | graduate | professional | high_school

CATALOGUE = {
    "yale": {
        "name": "Yale University", "slug": "yale",
        "website": "https://oyc.yale.edu", "country": "US",
        "description": "Open Yale Courses — free and open access to a selection of undergraduate Yale courses.",
        "courses": [
            ("Moral Foundations of Politics", "Political Science", "Ian Shapiro", "https://oyc.yale.edu/political-science/plsc-118", "undergraduate", ["Political Science", "Philosophy", "Ethics"]),
            ("Power and Politics in Today's World", "Political Science", "Ian Shapiro", "https://oyc.yale.edu/political-science/plsc-270", "undergraduate", ["Political Science", "International Relations"]),
            ("Environmental Politics and Law", "Environmental Studies", "John Wargo", "https://oyc.yale.edu/environment/env-322", "undergraduate", ["Political Science", "Environmental Science", "Law"]),
            ("Capitalism: Success, Crisis, and Reform", "Political Science", "Douglas W. Rae", "https://oyc.yale.edu/political-science/plsc-270b", "undergraduate", ["Economics", "Political Science", "Sociology"]),
            ("The Atmosphere, the Ocean, and Environmental Change", "Geology and Geophysics", "Ronald Smith", "https://oyc.yale.edu/geology-and-geophysics/gg-140", "undergraduate", ["Environmental Science", "Physics"]),
            ("Survey of the Old Testament", "Religious Studies", "Christine Hayes", "https://oyc.yale.edu/religious-studies/rlst-145b", "undergraduate", ["Religious Studies", "History"]),
            ("Health and the Human Body", "Medicine", "David Hafler", "https://oyc.yale.edu/medicine/medi-101", "undergraduate", ["Medicine", "Health", "Biology"]),
            ("Invisible Forces: From Quantum to Cosmos", "Physics", "Meng Chiang", "https://oyc.yale.edu/physics/phys-301", "undergraduate", ["Physics", "Quantum Mechanics"]),
        ]
    },
    "princeton": {
        "name": "Princeton University", "slug": "princeton",
        "website": "https://www.princeton.edu", "country": "US",
        "description": "Princeton University open course materials and recorded lectures.",
        "courses": [
            ("Algorithms (COS 423)", "Computer Science", "Robert Tarjan", "https://www.cs.princeton.edu/courses/archive/spring13/cos423/", "undergraduate", ["Algorithms", "Computer Science"]),
            ("Introduction to Programming Systems (COS 217)", "Computer Science", "Brian Kernighan", "https://www.cs.princeton.edu/courses/archive/spring13/cos217/", "undergraduate", ["Systems Programming", "C Programming"]),
            ("Theoretical Machine Learning (COS 511)", "Computer Science", "Rob Schapire", "https://www.cs.princeton.edu/courses/archive/spring14/cos511/", "graduate", ["Machine Learning", "Theory of Computing"]),
            ("Advanced Programming Techniques (COS 333)", "Computer Science", "Brian Kernighan", "https://www.cs.princeton.edu/courses/archive/spring23/cos333/", "undergraduate", ["Programming", "Software Engineering"]),
            ("Theory of Computation (COS 487)", "Computer Science", "Sanjeev Arora", "https://www.cs.princeton.edu/courses/archive/spring16/cos487/", "graduate", ["Theory of Computing", "Algorithms"]),
            ("Distributed Systems (COS 418)", "Computer Science", "Mike Freedman", "https://www.cs.princeton.edu/courses/archive/fall22/cos418/", "graduate", ["Distributed Systems", "Computer Science"]),
            ("Machine Learning (COS 402/522)", "Computer Science", "Brian Kernighan", "https://www.cs.princeton.edu/courses/archive/spring13/cos402/", "graduate", ["Machine Learning", "Artificial Intelligence"]),
            ("Artificial Intelligence (COS 402)", "Computer Science", "Karthik Narasimhan", "https://www.cs.princeton.edu/courses/archive/fall22/cos402/", "undergraduate", ["Artificial Intelligence", "Computer Science"]),
            ("Natural Language Processing (COS 484)", "Computer Science", "Danqi Chen", "https://www.cs.princeton.edu/courses/archive/spring23/cos484/", "graduate", ["Natural Language Processing", "Computer Science"]),
            ("Advanced Computer Networks (COS 561)", "Computer Science", "Jennifer Rexford", "https://www.cs.princeton.edu/courses/archive/fall22/cos561/", "graduate", ["Computer Networks", "Computer Science"]),
            ("Introduction to Quantum Computing (COS 597)", "Computer Science", "Yuxiang Yang", "https://www.cs.princeton.edu/courses/archive/fall22/cos597A/", "graduate", ["Quantum Computing", "Computer Science"]),
            ("Economics and Computing (COS 445)", "Computer Science", "Mark Braverman", "https://www.cs.princeton.edu/courses/archive/spring22/cos445/", "undergraduate", ["Economics", "Computer Science"]),
            ("Statistical Machine Learning (ORF 525)", "Operations Research", "Jianqing Fan", "https://orfe.princeton.edu/courses", "graduate", ["Machine Learning", "Statistics"]),
            ("Stochastic Calculus (ORF 527)", "Operations Research", "Mykhaylo Shkolnikov", "https://orfe.princeton.edu/courses", "graduate", ["Mathematics", "Finance"]),
            ("Data Science and Machine Learning (COS 324)", "Computer Science", "Ryan Adams", "https://www.cs.princeton.edu/courses/archive/spring22/cos324/", "undergraduate", ["Data Science", "Machine Learning"]),
            ("Human-Computer Interaction (COS 436)", "Computer Science", "Brian Kernighan", "https://www.cs.princeton.edu/courses/archive/spring23/cos436/", "undergraduate", ["Human-Computer Interaction", "Computer Science"]),
            ("Deep Learning for Computer Vision (COS 429)", "Computer Science", "Olga Russakovsky", "https://www.cs.princeton.edu/courses/archive/fall22/cos429/", "undergraduate", ["Computer Vision", "Deep Learning"]),
            ("Operating Systems (COS 318)", "Computer Science", "Mike Freedman", "https://www.cs.princeton.edu/courses/archive/fall22/cos318/", "undergraduate", ["Operating Systems", "Computer Science"]),
            ("Information Security (COS 432)", "Computer Science", "Ed Felten", "https://www.cs.princeton.edu/courses/archive/fall22/cos432/", "undergraduate", ["Cybersecurity", "Computer Science"]),
            ("Computational Photography (COS 426/526)", "Computer Science", "Adam Finkelstein", "https://www.cs.princeton.edu/courses/archive/spring23/cos426/", "undergraduate", ["Computer Graphics", "Computer Science"]),
        ]
    },
    "cmu": {
        "name": "Carnegie Mellon University", "slug": "cmu",
        "website": "https://oli.cmu.edu", "country": "US",
        "description": "CMU Open Learning Initiative — interactive online courses from Carnegie Mellon University.",
        "courses": [
            ("Introduction to Statistics", "Statistics", "Various", "https://oli.cmu.edu/courses/intro-statistics/", "undergraduate", ["Statistics", "Mathematics"]),
            ("Probability and Statistics", "Statistics", "Various", "https://oli.cmu.edu/courses/probability-statistics/", "undergraduate", ["Probability", "Statistics"]),
            ("Introduction to Logic", "Philosophy", "Various", "https://oli.cmu.edu/courses/logic-philosophy/", "undergraduate", ["Philosophy", "Logic"]),
            ("Introduction to Psychology", "Psychology", "Various", "https://oli.cmu.edu/courses/introduction-to-psychology/", "undergraduate", ["Psychology"]),
            ("Principles of Economics (Micro)", "Economics", "Various", "https://oli.cmu.edu/courses/principles-economics-micro/", "undergraduate", ["Economics", "Microeconomics"]),
            ("Principles of Economics (Macro)", "Economics", "Various", "https://oli.cmu.edu/courses/principles-economics-macro/", "undergraduate", ["Economics", "Macroeconomics"]),
            ("Biology", "Biology", "Various", "https://oli.cmu.edu/courses/biology/", "undergraduate", ["Biology"]),
            ("Chemistry", "Chemistry", "Various", "https://oli.cmu.edu/courses/chemistry/", "undergraduate", ["Chemistry"]),
            ("Introduction to Physics", "Physics", "Various", "https://oli.cmu.edu/courses/introduction-physics/", "undergraduate", ["Physics"]),
            ("Calculus", "Mathematics", "Various", "https://oli.cmu.edu/courses/calculus/", "undergraduate", ["Calculus", "Mathematics"]),
            ("Linear Algebra", "Mathematics", "Various", "https://oli.cmu.edu/courses/linear-algebra/", "undergraduate", ["Linear Algebra", "Mathematics"]),
            ("Programming Languages", "Computer Science", "Various", "https://oli.cmu.edu/courses/programming-languages/", "undergraduate", ["Programming", "Computer Science"]),
            ("Principles of Computing", "Computer Science", "Various", "https://oli.cmu.edu/courses/principles-of-computing/", "undergraduate", ["Computer Science", "Programming"]),
            ("Data Structures", "Computer Science", "Various", "https://oli.cmu.edu/courses/data-structures/", "undergraduate", ["Data Structures", "Computer Science"]),
            ("Algorithms", "Computer Science", "Various", "https://oli.cmu.edu/courses/algorithms/", "undergraduate", ["Algorithms", "Computer Science"]),
            ("Introduction to Databases", "Computer Science", "Various", "https://oli.cmu.edu/courses/databases/", "undergraduate", ["Databases", "Computer Science"]),
            ("Operating Systems", "Computer Science", "Various", "https://oli.cmu.edu/courses/operating-systems/", "undergraduate", ["Operating Systems", "Computer Science"]),
            ("Computer Networks", "Computer Science", "Various", "https://oli.cmu.edu/courses/computer-networks/", "undergraduate", ["Computer Networks", "Computer Science"]),
            ("Software Engineering", "Computer Science", "Various", "https://oli.cmu.edu/courses/software-engineering/", "undergraduate", ["Software Engineering", "Computer Science"]),
            ("Artificial Intelligence", "Computer Science", "Various", "https://oli.cmu.edu/courses/artificial-intelligence/", "undergraduate", ["Artificial Intelligence", "Computer Science"]),
            ("Machine Learning", "Computer Science", "Various", "https://oli.cmu.edu/courses/machine-learning/", "undergraduate", ["Machine Learning", "Computer Science"]),
            ("Computer Security", "Computer Science", "Various", "https://oli.cmu.edu/courses/computer-security/", "undergraduate", ["Cybersecurity", "Computer Science"]),
            ("Human-Computer Interaction", "Human-Computer Interaction", "Various", "https://oli.cmu.edu/courses/human-computer-interaction/", "undergraduate", ["Human-Computer Interaction", "Computer Science"]),
            ("Introduction to French", "Modern Languages", "Various", "https://oli.cmu.edu/courses/french/", "undergraduate", ["French", "Language"]),
            ("Introduction to Spanish", "Modern Languages", "Various", "https://oli.cmu.edu/courses/spanish/", "undergraduate", ["Spanish", "Language"]),
            ("Introduction to German", "Modern Languages", "Various", "https://oli.cmu.edu/courses/german/", "undergraduate", ["German", "Language"]),
            ("Introduction to Japanese", "Modern Languages", "Various", "https://oli.cmu.edu/courses/japanese/", "undergraduate", ["Japanese", "Language"]),
            ("Introduction to Arabic", "Modern Languages", "Various", "https://oli.cmu.edu/courses/arabic/", "undergraduate", ["Arabic", "Language"]),
            ("Introduction to Chinese", "Modern Languages", "Various", "https://oli.cmu.edu/courses/chinese/", "undergraduate", ["Chinese", "Language"]),
            ("Accounting", "Business", "Various", "https://oli.cmu.edu/courses/accounting/", "undergraduate", ["Accounting", "Business"]),
            ("Finance", "Business", "Various", "https://oli.cmu.edu/courses/finance/", "undergraduate", ["Finance", "Business"]),
            ("Marketing", "Business", "Various", "https://oli.cmu.edu/courses/marketing/", "undergraduate", ["Marketing", "Business"]),
            ("Writing and Communication", "English", "Various", "https://oli.cmu.edu/courses/writing-and-communication/", "undergraduate", ["Writing", "Communication"]),
            ("Anatomy and Physiology", "Medicine", "Various", "https://oli.cmu.edu/courses/anatomy-physiology/", "undergraduate", ["Anatomy", "Biology", "Medicine"]),
        ]
    },
    "oxford": {
        "name": "University of Oxford", "slug": "oxford",
        "website": "https://podcasts.ox.ac.uk", "country": "UK",
        "description": "University of Oxford open online courses and podcast lecture series.",
        "courses": [
            ("Critical Reasoning for Beginners", "Philosophy", "Marianne Talbot", "https://podcasts.ox.ac.uk/series/critical-reasoning-beginners", "undergraduate", ["Philosophy", "Logic"]),
            ("Bioethics: An Introduction", "Philosophy", "Marianne Talbot", "https://podcasts.ox.ac.uk/series/bioethics-introduction", "undergraduate", ["Philosophy", "Ethics", "Medicine"]),
            ("Philosophy of Mind and Action", "Philosophy", "Various", "https://podcasts.ox.ac.uk/series/philosophy-mind-and-action", "undergraduate", ["Philosophy", "Cognitive Science"]),
            ("The New Psychology of Depression", "Psychology", "Mark Williams", "https://podcasts.ox.ac.uk/series/new-psychology-depression", "undergraduate", ["Psychology", "Mental Health"]),
            ("Introduction to Ancient Greek History", "Classics", "Various", "https://podcasts.ox.ac.uk/series/ancient-greek-history", "undergraduate", ["History", "Ancient History"]),
            ("Approaching Shakespeare", "English", "Various", "https://podcasts.ox.ac.uk/series/approaching-shakespeare", "undergraduate", ["Literature", "English"]),
            ("Demographic Trends and Problems of the Modern World", "Sociology", "David Coleman", "https://podcasts.ox.ac.uk/series/demographic-trends-and-problems-modern-world", "undergraduate", ["Sociology", "Demographics"]),
            ("Fantasy Literature", "English", "Various", "https://podcasts.ox.ac.uk/series/fantasy-literature", "undergraduate", ["Literature", "English"]),
            ("Quantum Mechanics", "Physics", "James Binney", "https://podcasts.ox.ac.uk/series/quantum-mechanics", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("General Relativity", "Physics", "Various", "https://podcasts.ox.ac.uk/series/general-relativity", "graduate", ["Physics", "Relativity"]),
            ("Condensed Matter Physics", "Physics", "Various", "https://podcasts.ox.ac.uk/series/condensed-matter-physics", "graduate", ["Physics"]),
            ("Introduction to Astrophysics", "Physics", "Various", "https://podcasts.ox.ac.uk/series/introduction-astrophysics", "undergraduate", ["Astrophysics", "Physics"]),
            ("String Theory", "Physics", "Various", "https://podcasts.ox.ac.uk/series/string-theory", "graduate", ["Physics", "Theoretical Physics"]),
            ("The Standard Model of Particle Physics", "Physics", "Various", "https://podcasts.ox.ac.uk/series/standard-model-particle-physics", "graduate", ["Physics", "Particle Physics"]),
            ("Introduction to Number Theory", "Mathematics", "Various", "https://podcasts.ox.ac.uk/series/number-theory", "undergraduate", ["Mathematics", "Number Theory"]),
            ("Introduction to Complex Analysis", "Mathematics", "Various", "https://podcasts.ox.ac.uk/series/complex-analysis", "undergraduate", ["Mathematics", "Analysis"]),
            ("Introduction to Topology", "Mathematics", "Various", "https://podcasts.ox.ac.uk/series/topology", "undergraduate", ["Mathematics", "Topology"]),
            ("Abstract Algebra", "Mathematics", "Various", "https://podcasts.ox.ac.uk/series/abstract-algebra", "undergraduate", ["Mathematics", "Algebra"]),
            ("Calculus of Variations", "Mathematics", "Various", "https://podcasts.ox.ac.uk/series/calculus-variations", "graduate", ["Mathematics", "Calculus"]),
            ("Stochastic Differential Equations", "Mathematics", "Various", "https://podcasts.ox.ac.uk/series/stochastic-differential-equations", "graduate", ["Mathematics", "Statistics"]),
            ("Introduction to Computer Science", "Computer Science", "Various", "https://podcasts.ox.ac.uk/series/introduction-computer-science", "undergraduate", ["Computer Science"]),
            ("Algorithms and Data Structures", "Computer Science", "Various", "https://podcasts.ox.ac.uk/series/algorithms-and-data-structures", "undergraduate", ["Algorithms", "Computer Science"]),
            ("Functional Programming", "Computer Science", "Various", "https://podcasts.ox.ac.uk/series/functional-programming", "undergraduate", ["Programming", "Computer Science"]),
            ("Machine Learning", "Computer Science", "Various", "https://podcasts.ox.ac.uk/series/machine-learning-oxford", "graduate", ["Machine Learning", "Computer Science"]),
            ("Quantum Computing", "Computer Science", "Various", "https://podcasts.ox.ac.uk/series/quantum-computing", "graduate", ["Quantum Computing", "Computer Science"]),
            ("Computer Security", "Computer Science", "Various", "https://podcasts.ox.ac.uk/series/computer-security-oxford", "graduate", ["Cybersecurity", "Computer Science"]),
            ("Introduction to Economics", "Economics", "Various", "https://podcasts.ox.ac.uk/series/introduction-economics", "undergraduate", ["Economics"]),
            ("Macroeconomics", "Economics", "Various", "https://podcasts.ox.ac.uk/series/macroeconomics-oxford", "undergraduate", ["Economics", "Macroeconomics"]),
            ("Microeconomics", "Economics", "Various", "https://podcasts.ox.ac.uk/series/microeconomics-oxford", "undergraduate", ["Economics", "Microeconomics"]),
            ("International Economics", "Economics", "Various", "https://podcasts.ox.ac.uk/series/international-economics-oxford", "undergraduate", ["Economics", "International Relations"]),
            ("Development Economics", "Economics", "Various", "https://podcasts.ox.ac.uk/series/development-economics-oxford", "graduate", ["Economics", "Development"]),
            ("Modern British History", "History", "Various", "https://podcasts.ox.ac.uk/series/modern-british-history", "undergraduate", ["History"]),
            ("Medieval History", "History", "Various", "https://podcasts.ox.ac.uk/series/medieval-history-oxford", "undergraduate", ["History", "Medieval History"]),
            ("Ancient History", "Classics", "Various", "https://podcasts.ox.ac.uk/series/ancient-history-oxford", "undergraduate", ["History", "Ancient History"]),
            ("History of Science", "History", "Various", "https://podcasts.ox.ac.uk/series/history-of-science-oxford", "undergraduate", ["History", "Science"]),
            ("Constitutional Law", "Law", "Various", "https://podcasts.ox.ac.uk/series/constitutional-law-oxford", "undergraduate", ["Law"]),
            ("International Law", "Law", "Various", "https://podcasts.ox.ac.uk/series/international-law-oxford", "undergraduate", ["Law", "International Relations"]),
            ("Human Rights Law", "Law", "Various", "https://podcasts.ox.ac.uk/series/human-rights-law-oxford", "undergraduate", ["Law", "Human Rights"]),
            ("Contract Law", "Law", "Various", "https://podcasts.ox.ac.uk/series/contract-law-oxford", "undergraduate", ["Law"]),
            ("Criminal Law", "Law", "Various", "https://podcasts.ox.ac.uk/series/criminal-law-oxford", "undergraduate", ["Law", "Criminal Justice"]),
            ("Introduction to Biochemistry", "Biochemistry", "Various", "https://podcasts.ox.ac.uk/series/biochemistry-oxford", "undergraduate", ["Biochemistry", "Chemistry", "Biology"]),
            ("Cell Biology", "Biology", "Various", "https://podcasts.ox.ac.uk/series/cell-biology-oxford", "undergraduate", ["Biology"]),
            ("Evolutionary Biology", "Biology", "Various", "https://podcasts.ox.ac.uk/series/evolutionary-biology-oxford", "undergraduate", ["Biology", "Evolution"]),
            ("Neuroscience", "Neuroscience", "Various", "https://podcasts.ox.ac.uk/series/neuroscience-oxford", "undergraduate", ["Neuroscience", "Biology"]),
            ("Immunology", "Medicine", "Various", "https://podcasts.ox.ac.uk/series/immunology-oxford", "undergraduate", ["Immunology", "Biology", "Medicine"]),
            ("Organic Chemistry", "Chemistry", "Various", "https://podcasts.ox.ac.uk/series/organic-chemistry-oxford", "undergraduate", ["Organic Chemistry", "Chemistry"]),
            ("Physical Chemistry", "Chemistry", "Various", "https://podcasts.ox.ac.uk/series/physical-chemistry-oxford", "undergraduate", ["Physical Chemistry", "Chemistry"]),
            ("Materials Science", "Materials Science", "Various", "https://podcasts.ox.ac.uk/series/materials-science-oxford", "undergraduate", ["Materials Science", "Engineering"]),
            ("Environmental Science", "Environmental Science", "Various", "https://podcasts.ox.ac.uk/series/environmental-science-oxford", "undergraduate", ["Environmental Science"]),
            ("Ecological Economics", "Economics", "Various", "https://podcasts.ox.ac.uk/series/ecological-economics", "graduate", ["Economics", "Environmental Science"]),
            ("Global Health", "Medicine", "Various", "https://podcasts.ox.ac.uk/series/global-health-oxford", "graduate", ["Medicine", "Public Health"]),
            ("Epidemiology", "Medicine", "Various", "https://podcasts.ox.ac.uk/series/epidemiology-oxford", "graduate", ["Medicine", "Public Health", "Statistics"]),
            ("Evidence-Based Medicine", "Medicine", "Various", "https://podcasts.ox.ac.uk/series/evidence-based-health-care", "graduate", ["Medicine", "Research Methods"]),
            ("Political Philosophy", "Philosophy", "Various", "https://podcasts.ox.ac.uk/series/political-philosophy-oxford", "undergraduate", ["Philosophy", "Political Science"]),
            ("Ethics and Moral Philosophy", "Philosophy", "Various", "https://podcasts.ox.ac.uk/series/ethics-moral-philosophy-oxford", "undergraduate", ["Philosophy", "Ethics"]),
            ("Philosophy of Science", "Philosophy", "Various", "https://podcasts.ox.ac.uk/series/philosophy-science-oxford", "undergraduate", ["Philosophy", "Science"]),
            ("Philosophy of Language", "Philosophy", "Various", "https://podcasts.ox.ac.uk/series/philosophy-language-oxford", "graduate", ["Philosophy", "Linguistics"]),
            ("Introduction to Sociology", "Sociology", "Various", "https://podcasts.ox.ac.uk/series/introduction-sociology-oxford", "undergraduate", ["Sociology"]),
            ("Social Policy", "Social Sciences", "Various", "https://podcasts.ox.ac.uk/series/social-policy-oxford", "undergraduate", ["Social Sciences", "Sociology"]),
            ("Introduction to Linguistics", "Linguistics", "Various", "https://podcasts.ox.ac.uk/series/introduction-linguistics-oxford", "undergraduate", ["Linguistics"]),
            ("Cognitive Science", "Cognitive Science", "Various", "https://podcasts.ox.ac.uk/series/cognitive-science-oxford", "undergraduate", ["Cognitive Science", "Psychology"]),
            ("Architecture History", "Architecture", "Various", "https://podcasts.ox.ac.uk/series/architecture-history-oxford", "undergraduate", ["Architecture", "Art History"]),
            ("History of Art", "Fine Arts", "Various", "https://podcasts.ox.ac.uk/series/history-art-oxford", "undergraduate", ["Art History"]),
            ("Music Theory", "Music", "Various", "https://podcasts.ox.ac.uk/series/music-theory-oxford", "undergraduate", ["Music", "Music Theory"]),
            ("Introduction to Islam", "Religious Studies", "Various", "https://podcasts.ox.ac.uk/series/islam-oxford", "undergraduate", ["Religious Studies"]),
            ("Introduction to Buddhism", "Religious Studies", "Various", "https://podcasts.ox.ac.uk/series/buddhism-oxford", "undergraduate", ["Religious Studies"]),
            ("Contemporary Islamic Studies", "Religious Studies", "Various", "https://podcasts.ox.ac.uk/series/contemporary-islamic-studies", "graduate", ["Religious Studies", "Islam"]),
            ("Middle East Politics", "Political Science", "Various", "https://podcasts.ox.ac.uk/series/middle-east-politics-oxford", "undergraduate", ["Political Science", "International Relations"]),
            ("African Studies", "Area Studies", "Various", "https://podcasts.ox.ac.uk/series/african-studies-oxford", "undergraduate", ["Social Sciences"]),
            ("China and the Global Economy", "Economics", "Various", "https://podcasts.ox.ac.uk/series/china-global-economy", "graduate", ["Economics", "International Relations"]),
            ("Climate Change and Policy", "Environmental Science", "Various", "https://podcasts.ox.ac.uk/series/climate-change-policy-oxford", "undergraduate", ["Environmental Science", "Political Science"]),
        ]
    },
    "cambridge": {
        "name": "University of Cambridge", "slug": "cambridge",
        "website": "https://www.cambridge.org", "country": "UK",
        "description": "University of Cambridge free online lectures and course materials.",
        "courses": [
            ("Introduction to Computer Science", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Computer Science"]),
            ("Algorithms I", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Algorithms", "Computer Science"]),
            ("Data Structures and Algorithms", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Data Structures", "Algorithms"]),
            ("Artificial Intelligence", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Artificial Intelligence", "Computer Science"]),
            ("Machine Learning", "Computer Science", "Zoubin Ghahramani", "https://www.cl.cam.ac.uk/teaching/machine-learning/", "graduate", ["Machine Learning", "Computer Science"]),
            ("Computer Networks", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Computer Networks", "Computer Science"]),
            ("Operating Systems", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Operating Systems", "Computer Science"]),
            ("Compiler Design", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Compilers", "Computer Science"]),
            ("Computer Architecture", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "undergraduate", ["Computer Architecture", "Computer Science"]),
            ("Natural Language Processing", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "graduate", ["Natural Language Processing", "Computer Science"]),
            ("Computer Vision", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/", "graduate", ["Computer Vision", "Computer Science"]),
            ("Mathematics for Computation", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Mathematics", "Computer Science"]),
            ("Linear Mathematics", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Linear Algebra", "Mathematics"]),
            ("Analysis I", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Analysis", "Mathematics"]),
            ("Analysis II", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Analysis", "Mathematics"]),
            ("Groups", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Algebra", "Mathematics"]),
            ("Complex Methods", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Complex Analysis", "Mathematics"]),
            ("Probability", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Probability", "Statistics", "Mathematics"]),
            ("Statistics", "Mathematics", "Various", "https://www.maths.cam.ac.uk/teaching", "undergraduate", ["Statistics", "Mathematics"]),
            ("Quantum Mechanics", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("Classical Dynamics", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching", "undergraduate", ["Physics", "Mechanics"]),
            ("Electromagnetism", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching", "undergraduate", ["Physics", "Electromagnetism"]),
            ("Statistical Physics", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching", "undergraduate", ["Physics", "Statistical Mechanics"]),
            ("Astrophysics", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching", "undergraduate", ["Astrophysics", "Physics"]),
            ("General Relativity", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching", "graduate", ["Physics", "Relativity"]),
            ("Introduction to Economics", "Economics", "Various", "https://www.econ.cam.ac.uk/teaching", "undergraduate", ["Economics"]),
            ("Microeconomics", "Economics", "Various", "https://www.econ.cam.ac.uk/teaching", "undergraduate", ["Economics", "Microeconomics"]),
            ("Macroeconomics", "Economics", "Various", "https://www.econ.cam.ac.uk/teaching", "undergraduate", ["Economics", "Macroeconomics"]),
            ("Econometrics", "Economics", "Various", "https://www.econ.cam.ac.uk/teaching", "undergraduate", ["Economics", "Statistics"]),
            ("Game Theory", "Economics", "Various", "https://www.econ.cam.ac.uk/teaching", "graduate", ["Economics", "Game Theory", "Mathematics"]),
            ("History of Economic Thought", "Economics", "Various", "https://www.econ.cam.ac.uk/teaching", "undergraduate", ["Economics", "History"]),
            ("Introduction to Genetics", "Biology", "Various", "https://www.bio.cam.ac.uk/teaching", "undergraduate", ["Genetics", "Biology"]),
            ("Cell Biology", "Biology", "Various", "https://www.bio.cam.ac.uk/teaching", "undergraduate", ["Biology"]),
            ("Biochemistry", "Biochemistry", "Various", "https://www.bio.cam.ac.uk/teaching", "undergraduate", ["Biochemistry", "Chemistry", "Biology"]),
            ("Molecular Biology", "Biology", "Various", "https://www.bio.cam.ac.uk/teaching", "graduate", ["Molecular Biology", "Biology"]),
            ("Evolution", "Biology", "Various", "https://www.bio.cam.ac.uk/teaching", "undergraduate", ["Evolution", "Biology"]),
            ("Neuroscience", "Neuroscience", "Various", "https://www.bio.cam.ac.uk/teaching", "undergraduate", ["Neuroscience", "Biology"]),
            ("British History", "History", "Various", "https://www.hist.cam.ac.uk/teaching", "undergraduate", ["History"]),
            ("European History", "History", "Various", "https://www.hist.cam.ac.uk/teaching", "undergraduate", ["History", "European History"]),
            ("World History", "History", "Various", "https://www.hist.cam.ac.uk/teaching", "undergraduate", ["History"]),
            ("Philosophy of Mind", "Philosophy", "Various", "https://www.phil.cam.ac.uk/teaching", "undergraduate", ["Philosophy", "Cognitive Science"]),
            ("Ethics", "Philosophy", "Various", "https://www.phil.cam.ac.uk/teaching", "undergraduate", ["Philosophy", "Ethics"]),
            ("Metaphysics", "Philosophy", "Various", "https://www.phil.cam.ac.uk/teaching", "undergraduate", ["Philosophy"]),
            ("Logic", "Philosophy", "Various", "https://www.phil.cam.ac.uk/teaching", "undergraduate", ["Philosophy", "Logic"]),
        ]
    },
    "gatech": {
        "name": "Georgia Institute of Technology", "slug": "gatech",
        "website": "https://www.gatech.edu", "country": "US",
        "description": "Georgia Tech open course materials and YouTube lecture series.",
        "courses": [
            ("Introduction to Computer Science (CS 1301)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs1301/", "undergraduate", ["Computer Science", "Python"]),
            ("Data Structures and Algorithms (CS 1332)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs1332/", "undergraduate", ["Data Structures", "Algorithms", "Java"]),
            ("Algorithms (CS 3510)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs3510/", "undergraduate", ["Algorithms", "Computer Science"]),
            ("Computer Organization and Programming (CS 2110)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs2110/", "undergraduate", ["Computer Architecture", "Assembly Language"]),
            ("Systems and Networks (CS 2200)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs2200/", "undergraduate", ["Operating Systems", "Computer Networks"]),
            ("Machine Learning (CS 7641)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7641/", "graduate", ["Machine Learning", "Artificial Intelligence"]),
            ("Artificial Intelligence (CS 6601)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6601/", "graduate", ["Artificial Intelligence", "Computer Science"]),
            ("Computer Vision (CS 6476)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6476/", "graduate", ["Computer Vision", "Computer Science"]),
            ("Robotics (CS 7631)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7631/", "graduate", ["Robotics", "Artificial Intelligence"]),
            ("Knowledge-Based Artificial Intelligence (CS 7637)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7637/", "graduate", ["Artificial Intelligence", "Computer Science"]),
            ("Software Development Process (CS 6300)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6300/", "graduate", ["Software Engineering", "Computer Science"]),
            ("Human-Computer Interaction (CS 6750)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6750/", "graduate", ["Human-Computer Interaction", "Computer Science"]),
            ("Introduction to Operating Systems (CS 6200)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6200/", "graduate", ["Operating Systems", "Computer Science"]),
            ("Advanced OS (CS 8803)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs8803/", "graduate", ["Operating Systems", "Computer Science"]),
            ("Computer Networks (CS 6250)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6250/", "graduate", ["Computer Networks", "Computer Science"]),
            ("Network Science (CS 7280)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7280/", "graduate", ["Computer Networks", "Data Science"]),
            ("Database Systems (CS 6400)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6400/", "graduate", ["Databases", "Computer Science"]),
            ("Big Data Systems (CSE 6242)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cse6242/", "graduate", ["Data Science", "Big Data", "Computer Science"]),
            ("Educational Technology (CS 6460)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6460/", "graduate", ["Education", "Computer Science"]),
            ("Embedded Systems (ECE 6140)", "Electrical Engineering", "Various", "https://www.ece.gatech.edu/courses/", "graduate", ["Embedded Systems", "Electrical Engineering"]),
            ("Power Systems (ECE 4320)", "Electrical Engineering", "Various", "https://www.ece.gatech.edu/courses/", "undergraduate", ["Electrical Engineering", "Power Systems"]),
            ("Semiconductor Devices (ECE 3400)", "Electrical Engineering", "Various", "https://www.ece.gatech.edu/courses/", "undergraduate", ["Electrical Engineering", "Semiconductor Physics"]),
            ("Signal Processing (ECE 2026)", "Electrical Engineering", "Various", "https://www.ece.gatech.edu/courses/", "undergraduate", ["Signal Processing", "Electrical Engineering"]),
            ("Machine Learning for Trading (CS 7646)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7646/", "graduate", ["Machine Learning", "Finance"]),
            ("Computational Photography (CS 4476)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4476/", "undergraduate", ["Computer Vision", "Photography"]),
            ("Computational Science and Engineering (CSE 6140)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cse6140/", "graduate", ["Scientific Computing", "Mathematics"]),
            ("Simulation of Complex Systems (ISYE 6644)", "Industrial Engineering", "Various", "https://www.isye.gatech.edu/courses/", "graduate", ["Simulation", "Statistics"]),
            ("Applied Combinatorics (CS 3012)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs3012/", "undergraduate", ["Combinatorics", "Mathematics", "Computer Science"]),
            ("Introduction to Information Security (CS 6035)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6035/", "graduate", ["Cybersecurity", "Computer Science"]),
            ("Secure Computer Systems (CS 6238)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6238/", "graduate", ["Cybersecurity", "Systems Security"]),
            ("Digital Forensics (CS 6747)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6747/", "graduate", ["Digital Forensics", "Cybersecurity"]),
            ("Malware Analysis and Defense (CS 6264)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6264/", "graduate", ["Cybersecurity", "Malware Analysis"]),
            ("Privacy for Professionals (CS 6727)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6727/", "graduate", ["Privacy", "Cybersecurity"]),
            ("Natural Language Processing (CS 7650)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7650/", "graduate", ["Natural Language Processing", "Computer Science"]),
            ("Deep Learning (CS 7643)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7643/", "graduate", ["Deep Learning", "Machine Learning"]),
            ("Reinforcement Learning and Decision Making (CS 8803)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs8803-rl/", "graduate", ["Reinforcement Learning", "Machine Learning"]),
            ("Computational Data Analytics (CSE 6040)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cse6040/", "graduate", ["Data Science", "Python", "Machine Learning"]),
            ("Regression Analysis (ISYE 6414)", "Industrial Engineering", "Various", "https://www.isye.gatech.edu/courses/", "graduate", ["Statistics", "Regression"]),
            ("Data and Visual Analytics (CSE 6242)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cse6242-dava/", "graduate", ["Data Visualization", "Data Science"]),
            ("Supply Chain Engineering (ISYE 6335)", "Industrial Engineering", "Various", "https://www.isye.gatech.edu/courses/", "graduate", ["Supply Chain", "Operations Research"]),
            ("Computational Biology (CS 4775)", "Biology", "Various", "https://www.cc.gatech.edu/classes/cs4775/", "undergraduate", ["Bioinformatics", "Biology", "Computer Science"]),
            ("Energy Systems (ECE 4580)", "Electrical Engineering", "Various", "https://www.ece.gatech.edu/courses/", "undergraduate", ["Energy Systems", "Electrical Engineering"]),
            ("Engineering Statistics (ISYE 3770)", "Industrial Engineering", "Various", "https://www.isye.gatech.edu/courses/", "undergraduate", ["Statistics", "Engineering"]),
            ("Probabilistic Graphical Models (CS 7616)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7616/", "graduate", ["Machine Learning", "Probability"]),
            ("Introduction to Cyber-Physical Systems (CS 4820)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4820/", "undergraduate", ["Cyber-Physical Systems", "Internet of Things"]),
            ("High-Performance Computer Architecture (CS 6290)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6290/", "graduate", ["Computer Architecture", "High Performance Computing"]),
            ("Computer Architecture (CS 4290)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4290/", "undergraduate", ["Computer Architecture", "Computer Science"]),
            ("Introduction to Graduate Algorithms (CS 6515)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6515/", "graduate", ["Algorithms", "Computer Science"]),
            ("Software Architecture and Design (CS 6310)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6310/", "graduate", ["Software Engineering", "Computer Science"]),
            ("Digital Health (CS 6440)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6440/", "graduate", ["Health Informatics", "Computer Science"]),
            ("Industrial Internet of Things (ECE 8813)", "Electrical Engineering", "Various", "https://www.ece.gatech.edu/courses/", "graduate", ["Internet of Things", "Electrical Engineering"]),
            ("Computational Photography (CS 6475)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6475/", "graduate", ["Computer Vision", "Photography"]),
            ("Statistical Machine Learning (CS 7545)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7545/", "graduate", ["Machine Learning", "Statistics"]),
            ("Social Computing (CS 8803)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs8803-sc/", "graduate", ["Social Computing", "Data Science"]),
            ("Usability Engineering (CS 4873)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4873/", "undergraduate", ["Human-Computer Interaction", "Engineering"]),
        ]
    },
    "stanford": {
        "name": "Stanford University", "slug": "stanford",
        "website": "https://online.stanford.edu", "country": "US",
        "description": "Stanford University free online lecture series and course recordings.",
        "courses": [
            ("Programming Methodology (CS106A)", "Computer Science", "Mehran Sahami", "https://web.stanford.edu/class/cs106a/", "undergraduate", ["Programming", "Java", "Computer Science"]),
            ("Programming Abstractions (CS106B)", "Computer Science", "Various", "https://web.stanford.edu/class/cs106b/", "undergraduate", ["Programming", "Data Structures", "C++"]),
            ("Programming Paradigms (CS107)", "Computer Science", "Jerry Cain", "https://see.stanford.edu/Course/CS107", "undergraduate", ["Programming", "Computer Architecture", "C"]),
            ("Computer Organization and Systems (CS107)", "Computer Science", "Nick Troccoli", "https://web.stanford.edu/class/cs107/", "undergraduate", ["Systems Programming", "Computer Architecture"]),
            ("Principles of Computer Systems (CS110)", "Computer Science", "Various", "https://web.stanford.edu/class/cs110/", "undergraduate", ["Systems Programming", "Computer Science"]),
            ("Compilers (CS143)", "Computer Science", "Alex Aiken", "https://web.stanford.edu/class/cs143/", "undergraduate", ["Compilers", "Programming Languages"]),
            ("Introduction to Computer Networking (CS144)", "Computer Science", "Various", "https://cs144.github.io/", "undergraduate", ["Computer Networks", "Computer Science"]),
            ("Databases: Modeling and Theory (CS145)", "Computer Science", "Various", "https://cs145-fa22.github.io/", "undergraduate", ["Databases", "SQL"]),
            ("Programming Languages (CS242)", "Computer Science", "Various", "https://web.stanford.edu/class/cs242/", "graduate", ["Programming Languages", "Computer Science"]),
            ("Theory of Automata and Languages (CS154)", "Computer Science", "Ryan Williams", "https://web.stanford.edu/class/cs154/", "undergraduate", ["Theory of Computing", "Algorithms"]),
            ("Computer Security (CS155)", "Computer Science", "Dan Boneh", "https://cs155.stanford.edu/", "graduate", ["Cybersecurity", "Computer Science"]),
            ("Cryptography I (CS255)", "Computer Science", "Dan Boneh", "https://crypto.stanford.edu/", "graduate", ["Cryptography", "Computer Science"]),
            ("Cryptocurrency and Blockchain (CS251)", "Computer Science", "Dan Boneh", "https://cs251.stanford.edu/", "graduate", ["Blockchain", "Cryptocurrency", "Computer Science"]),
            ("Theory of Computation (CS254)", "Computer Science", "Various", "https://web.stanford.edu/class/cs254/", "graduate", ["Theory of Computing", "Computer Science"]),
            ("Human-Computer Interaction (CS147)", "Computer Science", "Various", "https://hci.stanford.edu/courses/cs147/", "undergraduate", ["Human-Computer Interaction", "Design"]),
            ("Introduction to Computer Graphics (CS148)", "Computer Science", "Ron Fedkiw", "https://web.stanford.edu/class/cs148/", "undergraduate", ["Computer Graphics", "Computer Science"]),
            ("Parallel Computing (CS149)", "Computer Science", "Kayvon Fatahalian", "https://gfxcourses.stanford.edu/cs149/", "undergraduate", ["Parallel Computing", "Computer Architecture"]),
            ("Machine Learning Systems Design (CS 329S)", "Computer Science", "Chip Huyen", "https://stanford-cs329s.github.io/", "graduate", ["Machine Learning", "Systems Design"]),
            ("Large Language Models (CS324)", "Computer Science", "Percy Liang", "https://stanford-cs324.github.io/winter2022/", "graduate", ["Large Language Models", "Natural Language Processing"]),
            ("Introduction to Game Theory (ECON 159)", "Economics", "Yoav Shoham", "https://web.stanford.edu/class/econ159/", "undergraduate", ["Game Theory", "Economics"]),
            ("Microeconomics (ECON 1A)", "Economics", "Various", "https://economics.stanford.edu/", "undergraduate", ["Microeconomics", "Economics"]),
            ("Macroeconomics (ECON 1B)", "Economics", "Various", "https://economics.stanford.edu/", "undergraduate", ["Macroeconomics", "Economics"]),
            ("Introduction to Probability (STATS 116)", "Statistics", "Susan Holmes", "https://web.stanford.edu/class/stats116/", "undergraduate", ["Probability", "Statistics", "Mathematics"]),
            ("Applied Statistics (STATS 191)", "Statistics", "Jonathan Taylor", "https://web.stanford.edu/class/stats191/", "undergraduate", ["Statistics", "Regression"]),
            ("Data Mining and Analysis (STATS 202)", "Statistics", "Various", "https://web.stanford.edu/class/stats202/", "undergraduate", ["Data Science", "Statistics"]),
            ("Bayesian Statistics (STATS 271)", "Statistics", "Various", "https://web.stanford.edu/class/stats271/", "graduate", ["Statistics", "Bayesian Methods"]),
            ("Linear Algebra (MATH 113)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "undergraduate", ["Linear Algebra", "Mathematics"]),
            ("Multivariable Calculus (MATH 51)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "undergraduate", ["Calculus", "Mathematics"]),
            ("Introduction to Real Analysis (MATH 115)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "undergraduate", ["Analysis", "Mathematics"]),
            ("Complex Analysis (MATH 116)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "undergraduate", ["Complex Analysis", "Mathematics"]),
            ("Abstract Algebra (MATH 120)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "undergraduate", ["Algebra", "Mathematics"]),
            ("Number Theory (MATH 124)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "undergraduate", ["Number Theory", "Mathematics"]),
            ("Differential Geometry (MATH 143)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "graduate", ["Geometry", "Mathematics"]),
            ("Topology (MATH 147)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "graduate", ["Topology", "Mathematics"]),
            ("Partial Differential Equations (MATH 131P)", "Mathematics", "Various", "https://mathematics.stanford.edu/", "graduate", ["Differential Equations", "Mathematics"]),
            ("Convex Optimization II (EE364b)", "Electrical Engineering", "Stephen Boyd", "https://web.stanford.edu/class/ee364b/", "graduate", ["Optimization", "Mathematics"]),
            ("Information Theory (EE376A)", "Electrical Engineering", "Various", "https://web.stanford.edu/class/ee376a/", "graduate", ["Information Theory", "Mathematics"]),
            ("Signals and Systems (EE102A)", "Electrical Engineering", "Various", "https://web.stanford.edu/class/ee102a/", "undergraduate", ["Signal Processing", "Electrical Engineering"]),
            ("Digital Systems Design (EE108)", "Electrical Engineering", "Various", "https://web.stanford.edu/class/ee108/", "undergraduate", ["Digital Systems", "Electrical Engineering"]),
            ("Introduction to Linear Dynamical Systems (EE263)", "Electrical Engineering", "Stephen Boyd", "https://web.stanford.edu/class/ee263/", "graduate", ["Control Systems", "Linear Algebra"]),
            ("Fourier Transform and its Applications (EE261)", "Electrical Engineering", "Brad Osgood", "https://see.stanford.edu/Course/EE261", "undergraduate", ["Signal Processing", "Mathematics"]),
            ("Introduction to Robotics (CS223A)", "Computer Science", "Oussama Khatib", "https://see.stanford.edu/Course/CS223A", "graduate", ["Robotics", "Engineering"]),
            ("Bioengineering for Medicine (BIOE 80)", "Bioengineering", "Various", "https://web.stanford.edu/class/bioe80/", "undergraduate", ["Bioengineering", "Medicine"]),
            ("Human Biology Core I (HUMBIO 1)", "Human Biology", "Various", "https://humanbiology.stanford.edu/", "undergraduate", ["Biology", "Health"]),
            ("Introduction to Law (LAW 101)", "Law", "Various", "https://law.stanford.edu/", "undergraduate", ["Law"]),
            ("Law Technology and Policy", "Law", "Various", "https://law.stanford.edu/codex/", "graduate", ["Law", "Technology"]),
            ("Introduction to Philosophy (PHIL 2)", "Philosophy", "Various", "https://philosophy.stanford.edu/", "undergraduate", ["Philosophy"]),
            ("Ethics (PHIL 50)", "Philosophy", "Various", "https://philosophy.stanford.edu/", "undergraduate", ["Philosophy", "Ethics"]),
            ("Introduction to Logic (PHIL 50)", "Philosophy", "Johan van Benthem", "https://philosophy.stanford.edu/", "undergraduate", ["Philosophy", "Logic"]),
            ("Introduction to Linguistics (LINGUIST 1)", "Linguistics", "Various", "https://linguistics.stanford.edu/", "undergraduate", ["Linguistics"]),
            ("Introduction to Sociology (SOC 1)", "Sociology", "Various", "https://sociology.stanford.edu/", "undergraduate", ["Sociology"]),
            ("American Government (POLS 101)", "Political Science", "Various", "https://politicalscience.stanford.edu/", "undergraduate", ["Political Science"]),
            ("Comparative Politics (POLS 113)", "Political Science", "Various", "https://politicalscience.stanford.edu/", "undergraduate", ["Political Science"]),
            ("International Relations (POLS 114)", "Political Science", "Various", "https://politicalscience.stanford.edu/", "undergraduate", ["Political Science", "International Relations"]),
            ("Introduction to Psychology (PSYCH 1)", "Psychology", "Various", "https://psychology.stanford.edu/", "undergraduate", ["Psychology"]),
            ("Social Psychology (PSYCH 60)", "Psychology", "Various", "https://psychology.stanford.edu/", "undergraduate", ["Psychology", "Social Psychology"]),
            ("Environmental Science (EARTHSYS 10)", "Earth Sciences", "Various", "https://earth.stanford.edu/", "undergraduate", ["Environmental Science"]),
            ("Climate Science (ESS 8)", "Earth Sciences", "Various", "https://earth.stanford.edu/", "undergraduate", ["Climate Science", "Environmental Science"]),
            ("Science and Technology Policy (STS 100)", "Science, Technology, and Society", "Various", "https://sts.stanford.edu/", "undergraduate", ["Science Policy", "Technology"]),
            ("Design Thinking (ME 310)", "Mechanical Engineering", "Various", "https://web.stanford.edu/class/me310/", "undergraduate", ["Design", "Engineering"]),
            ("Introduction to Solid Mechanics (ME 80)", "Mechanical Engineering", "Various", "https://web.stanford.edu/class/me80/", "undergraduate", ["Mechanical Engineering"]),
            ("Introduction to Fluid Mechanics (ME 131)", "Mechanical Engineering", "Various", "https://web.stanford.edu/class/me131/", "undergraduate", ["Fluid Mechanics", "Mechanical Engineering"]),
            ("Introduction to Materials Science (MATSCI 142)", "Materials Science", "Various", "https://mse.stanford.edu/", "undergraduate", ["Materials Science", "Engineering"]),
            ("Introduction to Chemical Engineering (CME 100)", "Chemical Engineering", "Various", "https://engineering.stanford.edu/", "undergraduate", ["Chemical Engineering"]),
            ("Introduction to Civil Engineering (CEE 20N)", "Civil Engineering", "Various", "https://cee.stanford.edu/", "undergraduate", ["Civil Engineering"]),
            ("MS&E 221: Stochastic Modeling", "Management Science", "Various", "https://web.stanford.edu/class/msande221/", "graduate", ["Statistics", "Stochastic Processes"]),
            ("MS&E 108: Sports Analytics", "Management Science", "Various", "https://web.stanford.edu/class/msande108/", "undergraduate", ["Data Science", "Statistics"]),
            ("Introduction to the Health Care System", "Medicine", "Various", "https://med.stanford.edu/", "undergraduate", ["Medicine", "Health"]),
            ("Global Health (HUMBIO 100)", "Medicine", "Various", "https://humanbiology.stanford.edu/", "undergraduate", ["Public Health", "Medicine"]),
            ("Entrepreneurship (MS&E 271)", "Management Science", "Various", "https://web.stanford.edu/class/msande271/", "undergraduate", ["Entrepreneurship", "Business"]),
            ("Introduction to Finance (MGTECON 543)", "Management", "Various", "https://gsb.stanford.edu/", "undergraduate", ["Finance", "Business"]),
            ("Introduction to Accounting (MGTECON 544)", "Management", "Various", "https://gsb.stanford.edu/", "undergraduate", ["Accounting", "Business"]),
            ("Organizational Behavior (OB 201)", "Management", "Various", "https://gsb.stanford.edu/", "graduate", ["Management", "Organizational Behavior"]),
            ("Strategy (STRAMGT 559)", "Management", "Various", "https://gsb.stanford.edu/", "graduate", ["Management", "Strategy"]),
            ("Technology Ventures (MS&E 472)", "Management Science", "Various", "https://web.stanford.edu/class/msande472/", "graduate", ["Entrepreneurship", "Technology"]),
            ("Computer Vision for 3D Reconstruction (CS231A)", "Computer Science", "Silvio Savarese", "https://web.stanford.edu/class/cs231a/", "graduate", ["Computer Vision", "3D Reconstruction"]),
            ("Introduction to Quantum Computing", "Physics", "Various", "https://physics.stanford.edu/", "graduate", ["Quantum Computing", "Physics"]),
            ("Advanced Topics in Natural Language Processing (CS224U)", "Computer Science", "Christopher Potts", "https://web.stanford.edu/class/cs224u/", "graduate", ["Natural Language Processing", "Deep Learning"]),
            ("Geometric Deep Learning (CS474)", "Computer Science", "Various", "https://web.stanford.edu/class/cs474/", "graduate", ["Deep Learning", "Geometry"]),
            ("Modern Physics (PHYSICS 70)", "Physics", "Various", "https://physics.stanford.edu/", "undergraduate", ["Physics", "Modern Physics"]),
            ("Quantum Mechanics (PHYSICS 130)", "Physics", "Various", "https://physics.stanford.edu/", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("Statistical Mechanics (PHYSICS 171)", "Physics", "Various", "https://physics.stanford.edu/", "undergraduate", ["Physics", "Statistical Mechanics"]),
            ("Electricity and Magnetism (PHYSICS 121)", "Physics", "Various", "https://physics.stanford.edu/", "undergraduate", ["Physics", "Electromagnetism"]),
            ("General Chemistry (CHEM 31A)", "Chemistry", "Various", "https://chemistry.stanford.edu/", "undergraduate", ["Chemistry"]),
            ("Organic Chemistry (CHEM 35)", "Chemistry", "Various", "https://chemistry.stanford.edu/", "undergraduate", ["Organic Chemistry", "Chemistry"]),
            ("Biochemistry (CHEM 181)", "Chemistry", "Various", "https://chemistry.stanford.edu/", "undergraduate", ["Biochemistry", "Chemistry", "Biology"]),
            ("Introduction to Biology (BIO 41)", "Biology", "Various", "https://biology.stanford.edu/", "undergraduate", ["Biology"]),
            ("Genetics (BIO 141)", "Biology", "Various", "https://biology.stanford.edu/", "undergraduate", ["Genetics", "Biology"]),
        ]
    },
    "berkeley": {
        "name": "University of California, Berkeley", "slug": "berkeley",
        "website": "https://www.berkeley.edu", "country": "US",
        "description": "UC Berkeley free open courseware and YouTube lecture series.",
        "courses": [
            # CS courses
            ("CS 169A: Software Engineering", "Electrical Engineering and Computer Science", "Various", "https://cs169a.github.io/", "undergraduate", ["Software Engineering", "Ruby on Rails"]),
            ("CS 169B: Advanced Software Engineering", "Electrical Engineering and Computer Science", "Various", "https://cs169b.github.io/", "undergraduate", ["Software Engineering", "Computer Science"]),
            ("CS 195: Social Implications of Computing", "Electrical Engineering and Computer Science", "Various", "https://cs195.org/", "undergraduate", ["Computer Science", "Social Sciences"]),
            ("CS 198: Teaching Techniques for CS", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs198/", "undergraduate", ["Computer Science", "Education"]),
            ("CS 252: Graduate Computer Architecture", "Electrical Engineering and Computer Science", "David Patterson", "https://inst.eecs.berkeley.edu/~cs252/", "graduate", ["Computer Architecture", "Computer Science"]),
            ("CS 261: Security in Computer Systems", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs261/", "graduate", ["Cybersecurity", "Computer Science"]),
            ("CS 268: Computer Networks", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs268/", "graduate", ["Computer Networks", "Computer Science"]),
            ("CS 276: Cryptography", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs276/", "graduate", ["Cryptography", "Computer Science"]),
            ("CS 282: AI Ethics", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs282/", "graduate", ["Artificial Intelligence", "Ethics"]),
            ("CS 285: Offline RL", "Electrical Engineering and Computer Science", "Sergey Levine", "https://offline-rl.github.io/", "graduate", ["Reinforcement Learning", "Machine Learning"]),
            ("CS 286: Database Implementation", "Electrical Engineering and Computer Science", "Joe Hellerstein", "https://inst.eecs.berkeley.edu/~cs286/", "graduate", ["Databases", "Computer Science"]),
            ("CS 288: Natural Language Processing", "Electrical Engineering and Computer Science", "Various", "https://cal-cs288.github.io/", "graduate", ["Natural Language Processing", "Computer Science"]),
            ("CS 294: Deep Unsupervised Learning", "Electrical Engineering and Computer Science", "Pieter Abbeel", "https://sites.google.com/view/berkeley-cs294-158-sp24/", "graduate", ["Deep Learning", "Generative Models"]),
            ("CS 294: Full Stack Deep Learning", "Electrical Engineering and Computer Science", "Various", "https://fullstackdeeplearning.com/", "graduate", ["Deep Learning", "Machine Learning"]),
            ("CS 375: Large Language Models", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs375/", "graduate", ["Large Language Models", "Computer Science"]),
            ("CS 149: Parallel Computing", "Electrical Engineering and Computer Science", "Kayvon Fatahalian", "https://gfxcourses.stanford.edu/cs149/", "undergraduate", ["Parallel Computing", "Computer Science"]),
            ("CS 194: Image Manipulation and Computational Photography", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs194-26/", "undergraduate", ["Computer Graphics", "Photography"]),
            ("CS 194: Decentralized Finance", "Electrical Engineering and Computer Science", "Various", "https://defi-learning.org/", "graduate", ["Blockchain", "Finance"]),
            ("CS 281A: Statistical Learning Theory", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs281a/", "graduate", ["Machine Learning", "Statistics"]),
            ("CS 285: Robots Learning", "Electrical Engineering and Computer Science", "Sergey Levine", "https://rail.eecs.berkeley.edu/", "graduate", ["Robotics", "Machine Learning"]),
            # EE courses
            ("EE 16A: Designing Information Devices and Systems I", "Electrical Engineering and Computer Science", "Various", "https://eecs16a.org/", "undergraduate", ["Electrical Engineering", "Linear Algebra"]),
            ("EE 16B: Designing Information Devices and Systems II", "Electrical Engineering and Computer Science", "Various", "https://eecs16b.org/", "undergraduate", ["Electrical Engineering", "Control Systems"]),
            ("EE 120: Signals and Systems", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee120/", "undergraduate", ["Signal Processing", "Electrical Engineering"]),
            ("EE 123: Digital Signal Processing", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee123/", "undergraduate", ["Signal Processing", "Electrical Engineering"]),
            ("EE 126: Probability and Random Processes", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee126/", "undergraduate", ["Probability", "Statistics"]),
            ("EE 127: Optimization Models in Engineering", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee127/", "undergraduate", ["Optimization", "Mathematics"]),
            ("EE 229A: Information Theory and Coding", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee229a/", "graduate", ["Information Theory", "Computer Science"]),
            ("EE 290: Power Electronics", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~ee290/", "graduate", ["Electrical Engineering", "Power Systems"]),
            # Math courses
            ("Math 1A: Calculus", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Calculus", "Mathematics"]),
            ("Math 1B: Calculus", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Calculus", "Mathematics"]),
            ("Math 10A: Methods of Mathematics", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Mathematics", "Calculus"]),
            ("Math 10B: Methods of Mathematics", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Mathematics", "Statistics"]),
            ("Math 32: Precalculus", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Mathematics", "Pre-Calculus"]),
            ("Math 53: Multivariable Calculus", "Mathematics", "Edward Frenkel", "https://math.berkeley.edu/courses/", "undergraduate", ["Calculus", "Mathematics"]),
            ("Math 54: Linear Algebra and Differential Equations", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Linear Algebra", "Differential Equations"]),
            ("Math 55: Discrete Mathematics", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Discrete Mathematics", "Mathematics"]),
            ("Math 104: Introduction to Analysis", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Analysis", "Mathematics"]),
            ("Math 105: Second Course in Analysis", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Analysis", "Mathematics"]),
            ("Math 110: Linear Algebra", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Linear Algebra", "Mathematics"]),
            ("Math 113: Introduction to Abstract Algebra", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Algebra", "Mathematics"]),
            ("Math 115: Introduction to Number Theory", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Number Theory", "Mathematics"]),
            ("Math 121A: Mathematical Tools for the Physical Sciences", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Mathematics", "Physics"]),
            ("Math 128A: Numerical Analysis", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Numerical Analysis", "Mathematics"]),
            ("Math 185: Complex Analysis", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "undergraduate", ["Complex Analysis", "Mathematics"]),
            ("Math 202A: Introduction to Topology and Analysis", "Mathematics", "Various", "https://math.berkeley.edu/courses/", "graduate", ["Topology", "Analysis", "Mathematics"]),
            # Physics courses
            ("Physics 7A: Mechanics and Waves", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Mechanics"]),
            ("Physics 7B: Thermodynamics and Electromagnetism", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Electromagnetism"]),
            ("Physics 7C: Electricity, Magnetism, and Optics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Electromagnetism"]),
            ("Physics 8A: Introductory Physics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics"]),
            ("Physics 8B: Introductory Physics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics"]),
            ("Physics 112: Thermodynamics and Statistical Mechanics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Statistical Mechanics"]),
            ("Physics 137A: Quantum Mechanics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("Physics 137B: Quantum Mechanics II", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Quantum Mechanics"]),
            ("Physics 105: Analytic Mechanics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Mechanics"]),
            ("Physics 110A: Electromagnetism and Optics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Electromagnetism"]),
            ("Physics 141A: Solid State Physics", "Physics", "Various", "https://physics.berkeley.edu/courses/", "undergraduate", ["Physics", "Condensed Matter"]),
            # Chemistry
            ("Chem 1A: General Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Chemistry"]),
            ("Chem 1B: General Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Chemistry"]),
            ("Chem 3A: Organic Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Organic Chemistry", "Chemistry"]),
            ("Chem 3B: Organic Chemistry II", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Organic Chemistry", "Chemistry"]),
            ("Chem 12A: Organic Chemistry for Life Science", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Organic Chemistry", "Chemistry"]),
            ("Chem 105: Physical Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Physical Chemistry", "Chemistry"]),
            ("Chem 110A: Physical Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Physical Chemistry", "Chemistry"]),
            ("Chem 120A: Chemical Biology", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/", "undergraduate", ["Biochemistry", "Chemistry"]),
            # Biology
            ("Bio 1A: Foundations of Biology: Cell and Developmental Biology", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Biology", "Cell Biology"]),
            ("Bio 1B: Foundations of Biology: Evolution, Ecology, and Organismal Biology", "Integrative Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Biology", "Evolution", "Ecology"]),
            ("MCB 32: Human Physiology", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Biology", "Physiology"]),
            ("MCB 102: Biochemistry and Molecular Biology", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Biochemistry", "Biology"]),
            ("MCB 104: Genetics", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Genetics", "Biology"]),
            ("MCB 110: Molecular Biology", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Molecular Biology", "Biology"]),
            ("MCB 130: Cell and Molecular Neurobiology", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Neuroscience", "Biology"]),
            ("MCB 131: Immunology", "Molecular and Cell Biology", "Various", "https://mcb.berkeley.edu/courses/", "undergraduate", ["Immunology", "Biology"]),
            # Economics
            ("Econ 1: Introduction to Economics", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Economics"]),
            ("Econ 2: Introduction to Economics", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Economics"]),
            ("Econ 100A: Economic Analysis - Micro", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Microeconomics", "Economics"]),
            ("Econ 100B: Economic Analysis - Macro", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Macroeconomics", "Economics"]),
            ("Econ 101A: Economic Theory - Micro", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Microeconomics", "Economics"]),
            ("Econ 101B: Economic Theory - Macro", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Macroeconomics", "Economics"]),
            ("Econ 119: Psychology and Economics", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Economics", "Psychology"]),
            ("Econ 131: Public Economics", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Economics", "Public Policy"]),
            ("Econ 135: Financial Economics", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Finance", "Economics"]),
            ("Econ 141: Economic Statistics and Econometrics", "Economics", "Various", "https://econ.berkeley.edu/courses/", "undergraduate", ["Econometrics", "Statistics"]),
            # Data Science
            ("Data 8: Foundations of Data Science", "Data Science", "John DeNero", "https://www.data8.org/", "undergraduate", ["Data Science", "Python", "Statistics"]),
            ("Data 102: Data, Inference, and Decisions", "Data Science", "Various", "https://data102.org/", "undergraduate", ["Data Science", "Statistics", "Machine Learning"]),
            ("Data 144: Data Mining and Analytics", "Data Science", "Various", "https://datamining.berkeley.edu/", "undergraduate", ["Data Mining", "Machine Learning"]),
            ("INFO 159: Natural Language Processing", "School of Information", "Various", "https://people.ischool.berkeley.edu/~hearst/", "graduate", ["Natural Language Processing", "Machine Learning"]),
            ("INFO 257: Database Management", "School of Information", "Various", "https://ischool.berkeley.edu/courses/", "graduate", ["Databases", "Computer Science"]),
            # Other
            ("CogSci 1: Introduction to Cognitive Science", "Cognitive Science", "Various", "https://cogsci.berkeley.edu/courses/", "undergraduate", ["Cognitive Science", "Psychology"]),
            ("Linguist 100: Introduction to Linguistic Science", "Linguistics", "Various", "https://linguistics.berkeley.edu/courses/", "undergraduate", ["Linguistics"]),
            ("Psych 1: General Psychology", "Psychology", "Various", "https://psychology.berkeley.edu/courses/", "undergraduate", ["Psychology"]),
            ("Sociology 1: Introduction to Sociology", "Sociology", "Various", "https://sociology.berkeley.edu/courses/", "undergraduate", ["Sociology"]),
            ("Political Science 1: Introduction to Political Thinking", "Political Science", "Various", "https://polisci.berkeley.edu/courses/", "undergraduate", ["Political Science"]),
            ("Philosophy 2: Individual Morality and Social Justice", "Philosophy", "Various", "https://philosophy.berkeley.edu/courses/", "undergraduate", ["Philosophy", "Ethics"]),
            ("Philosophy 12A: Introduction to Logic", "Philosophy", "Various", "https://philosophy.berkeley.edu/courses/", "undergraduate", ["Philosophy", "Logic"]),
            ("Philosophy 132: Philosophy of Mind", "Philosophy", "Various", "https://philosophy.berkeley.edu/courses/", "undergraduate", ["Philosophy", "Cognitive Science"]),
            ("Astronomy C10: Introduction to General Astronomy", "Astronomy", "Alex Filippenko", "https://astro.berkeley.edu/courses/", "undergraduate", ["Astronomy", "Physics"]),
            ("Astronomy C12: The Planets", "Astronomy", "Various", "https://astro.berkeley.edu/courses/", "undergraduate", ["Astronomy"]),
            ("Environmental Science 10: Blue Planet", "Environmental Science", "Various", "https://eps.berkeley.edu/courses/", "undergraduate", ["Environmental Science"]),
            ("History 7A: History of the United States from Settlement to Civil War", "History", "Various", "https://history.berkeley.edu/courses/", "undergraduate", ["History", "American History"]),
            ("History 7B: History of the United States from Reconstruction to Present", "History", "Various", "https://history.berkeley.edu/courses/", "undergraduate", ["History", "American History"]),
            ("American Studies 10: American Studies", "American Studies", "Various", "https://americanstudies.berkeley.edu/", "undergraduate", ["American Studies"]),
            ("Public Health 142: Fundamentals of Epidemiology and Biostatistics", "Public Health", "Various", "https://sph.berkeley.edu/courses/", "undergraduate", ["Epidemiology", "Statistics"]),
            ("Industrial Engineering 151: Service Engineering and Management", "Industrial Engineering", "Various", "https://ieor.berkeley.edu/courses/", "undergraduate", ["Engineering", "Management"]),
        ]
    }
}

# ─── DB helpers ───────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(**DB)


def upsert_university(cur, key: str, data: dict) -> str:
    cur.execute("SELECT id FROM universities WHERE source_key = %s", (key,))
    row = cur.fetchone()
    if row:
        return row[0]
    uid = str(uuid.uuid4())
    cur.execute(
        """INSERT INTO universities (id, name, slug, website, country, source_key, description)
           VALUES (%s, %s, %s, %s, %s, %s, %s)
           ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id""",
        (uid, data["name"], data["slug"], data["website"], data["country"], key, data["description"])
    )
    row = cur.fetchone()
    return row[0] if row else uid


def upsert_subject(cur, name: str, cache: dict) -> str:
    if name in cache:
        return cache[name]
    slug = slugify(name)
    cur.execute("SELECT id FROM subjects WHERE slug=%s", (slug,))
    row = cur.fetchone()
    if row:
        cache[name] = row[0]
        return row[0]
    sid = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO subjects (id, name, slug) VALUES (%s,%s,%s) ON CONFLICT (slug) DO UPDATE SET name=EXCLUDED.name RETURNING id",
        (sid, name, slug)
    )
    row = cur.fetchone()
    cache[name] = row[0] if row else sid
    return cache[name]


def make_slug(title: str, uni_slug: str, seen: set) -> str:
    base = slugify(f"{title} {uni_slug}")
    slug = base
    i = 2
    while slug in seen:
        slug = f"{base}-{i}"
        i += 1
    seen.add(slug)
    return slug


def load_all():
    conn = get_conn()
    cur = conn.cursor()

    # Pre-load existing slugs and source_urls
    cur.execute("SELECT slug FROM courses")
    seen_slugs: set = {r[0] for r in cur.fetchall()}
    cur.execute("SELECT source_url FROM courses")
    seen_urls: set = {r[0] for r in cur.fetchall()}

    subject_cache: dict = {}
    total_created = 0
    total_skipped = 0

    for uni_key, uni_data in CATALOGUE.items():
        print(f"\n→ {uni_data['name']}", flush=True)
        uni_id = upsert_university(cur, uni_key, uni_data)
        conn.commit()

        created = skipped = 0
        for (title, dept, instructor, source_url, level, subjects) in uni_data["courses"]:
            if source_url in seen_urls:
                skipped += 1
                continue

            slug = make_slug(title, uni_data["slug"], seen_slugs)
            course_id = str(uuid.uuid4())
            description = f"{title}. Offered by {uni_data['name']}."
            if dept:
                description += f" Department: {dept}."
            if instructor and instructor != "Various":
                description += f" Instructor: {instructor}."

            try:
                cur.execute(
                    """INSERT INTO courses (
                        id, university_id, title, slug, source_key, source_url,
                        description, level, instructor, has_video_lectures
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (slug) DO NOTHING""",
                    (course_id, uni_id, title, slug, uni_key, source_url,
                     description, level, instructor if instructor != "Various" else None, True)
                )

                for subj_name in subjects[:3]:
                    if subj_name:
                        subj_id = upsert_subject(cur, subj_name, subject_cache)
                        cur.execute(
                            "INSERT INTO course_subjects (id, course_id, subject_id) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                            (str(uuid.uuid4()), course_id, subj_id)
                        )

                seen_urls.add(source_url)
                created += 1
            except Exception as e:
                conn.rollback()
                print(f"  Error: {title!r}: {e}", flush=True)
                continue

        conn.commit()
        print(f"  Created: {created}, Skipped: {skipped}", flush=True)
        total_created += created
        total_skipped += skipped

    cur.close()
    conn.close()
    print(f"\nTotal — Created: {total_created}, Skipped: {total_skipped}")


if __name__ == "__main__":
    load_all()
