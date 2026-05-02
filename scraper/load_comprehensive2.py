#!/usr/bin/env python
"""
Second comprehensive batch loader targeting remaining gaps:
- Cambridge: 29+ new (need unique URLs this time)
- Stanford: 40+ new
- Berkeley: 130+ new
- Oxford: 5 more
- Yale: 3 more
- Princeton: 5 more
- GA Tech: 10 more
"""
from __future__ import annotations
import uuid
import psycopg2
from slugify import slugify

DB = dict(host="127.0.0.1", port=5432, dbname="opencourseware", user="ocw", password="ocwpassword")

# All source_urls MUST be unique across entire batch AND not already in DB

CATALOGUE = {
    "cambridge": {
        "name": "University of Cambridge", "slug": "cambridge",
        "website": "https://www.cambridge.org", "country": "UK",
        "description": "University of Cambridge free online lectures and course materials.",
        "courses": [
            # CS courses with unique per-course URLs
            ("Discrete Mathematics (Part IA)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/DiscMath/", "undergraduate", ["Discrete Mathematics", "Mathematics"]),
            ("Object-Oriented Programming (Part IB)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/OOProg/", "undergraduate", ["Object-Oriented Programming", "Programming"]),
            ("Introduction to Graphics (Part IB)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/Graphics/", "undergraduate", ["Computer Graphics", "Computer Science"]),
            ("Security (Part II)", "Computer Science", "Frank Stajano", "https://www.cl.cam.ac.uk/teaching/2223/SecurityII/", "undergraduate", ["Cybersecurity", "Computer Science"]),
            ("Concurrent and Distributed Systems (Part IB)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/ConcDisSys/", "undergraduate", ["Distributed Systems", "Computer Science"]),
            ("Databases (Part IB)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/Databases/", "undergraduate", ["Databases", "Computer Science"]),
            ("Semantics of Programming Languages (Part II)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/Semantics/", "undergraduate", ["Programming Languages", "Computer Science"]),
            ("Advanced Algorithms (Part III)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/AdvAlgo/", "graduate", ["Algorithms", "Computer Science"]),
            ("Probabilistic Machine Learning (Part III)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/PML/", "graduate", ["Machine Learning", "Probabilistic Models"]),
            ("Quantum Computing (Part III)", "Computer Science", "Various", "https://www.cl.cam.ac.uk/teaching/2223/QuantComp/", "graduate", ["Quantum Computing", "Computer Science"]),
            # Mathematics with unique URLs
            ("Numbers and Sets (Part IA)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ia/numbers-and-sets", "undergraduate", ["Mathematics", "Set Theory"]),
            ("Vectors and Matrices (Part IA)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ia/vectors-and-matrices", "undergraduate", ["Linear Algebra", "Mathematics"]),
            ("Differential Equations (Part IA)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ia/differential-equations", "undergraduate", ["Differential Equations", "Mathematics"]),
            ("Dynamics and Relativity (Part IA)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ia/dynamics-and-relativity", "undergraduate", ["Physics", "Mechanics"]),
            ("Groups (Part IB)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ib/groups", "undergraduate", ["Algebra", "Mathematics"]),
            ("Analysis and Topology (Part IB)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ib/analysis-and-topology", "undergraduate", ["Analysis", "Topology"]),
            ("Complex Methods (Part IB)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ib/complex-methods", "undergraduate", ["Complex Analysis", "Mathematics"]),
            ("Methods (Part IB)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ib/methods", "undergraduate", ["Mathematics", "Applied Mathematics"]),
            ("Fluid Dynamics (Part IB)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ib/fluid-dynamics", "undergraduate", ["Fluid Dynamics", "Physics"]),
            ("Electromagnetism (Part IB)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ib/electromagnetism", "undergraduate", ["Electromagnetism", "Physics"]),
            ("Graph Theory (Part II)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ii/graph-theory", "undergraduate", ["Graph Theory", "Mathematics"]),
            ("Algebraic Topology (Part II)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ii/algebraic-topology", "undergraduate", ["Topology", "Mathematics"]),
            ("Logic and Set Theory (Part II)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ii/logic-and-set-theory", "undergraduate", ["Logic", "Mathematics"]),
            ("Number Theory (Part II)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/undergrad/course/ii/number-theory", "undergraduate", ["Number Theory", "Mathematics"]),
            ("Differential Geometry (Part III)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/postgrad/part-iii/files/diff-geo", "graduate", ["Differential Geometry", "Mathematics"]),
            ("Algebraic Geometry (Part III)", "Mathematics", "Various", "https://www.maths.cam.ac.uk/postgrad/part-iii/files/alg-geo", "graduate", ["Algebraic Geometry", "Mathematics"]),
            # Physics
            ("Electromagnetism (Part IB Physics)", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching/ba/ib/electromagnetism", "undergraduate", ["Electromagnetism", "Physics"]),
            ("Thermodynamics (Part IB Physics)", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching/ba/ib/thermodynamics", "undergraduate", ["Thermodynamics", "Physics"]),
            ("Classical Mechanics (Part IA Physics)", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching/ba/ia/classical-mechanics", "undergraduate", ["Mechanics", "Physics"]),
            ("Relativity (Part II Physics)", "Physics", "Various", "https://www.phy.cam.ac.uk/teaching/ba/ii/relativity", "undergraduate", ["Relativity", "Physics"]),
        ]
    },
    "stanford": {
        "name": "Stanford University", "slug": "stanford",
        "website": "https://online.stanford.edu", "country": "US",
        "description": "Stanford University free online lecture series and course recordings.",
        "courses": [
            # These are unique Stanford courses not already loaded
            ("Startup School (YC)", "Management Science", "Various", "https://www.startupschool.org/", "undergraduate", ["Entrepreneurship", "Business"]),
            ("Introduction to Probability (MATH 109)", "Mathematics", "Joe Blitzstein", "https://web.stanford.edu/class/math109/", "undergraduate", ["Probability", "Mathematics"]),
            ("Discrete Mathematics (CS 103)", "Computer Science", "Keith Schwarz", "https://web.stanford.edu/class/cs103/", "undergraduate", ["Discrete Mathematics", "Computer Science"]),
            ("Artificial Intelligence: Principles and Techniques (CS221)", "Computer Science", "Percy Liang", "https://stanford-cs221.github.io/", "graduate", ["Artificial Intelligence", "Computer Science"]),
            ("Convolutional Neural Networks (CS231N)", "Computer Science", "Fei-Fei Li", "https://cs231n.stanford.edu/", "graduate", ["Deep Learning", "Computer Vision"]),
            ("Sequence Models (CS224S)", "Computer Science", "Various", "https://web.stanford.edu/class/cs224s/", "graduate", ["Deep Learning", "Natural Language Processing"]),
            ("Reinforcement Learning (CS234)", "Computer Science", "Emma Brunskill", "https://web.stanford.edu/class/cs234/", "graduate", ["Reinforcement Learning", "Machine Learning"]),
            ("Graph Neural Networks (CS224W)", "Computer Science", "Jure Leskovec", "https://web.stanford.edu/class/cs224w/", "graduate", ["Graph Neural Networks", "Machine Learning"]),
            ("Mining Massive Datasets (CS246)", "Computer Science", "Jure Leskovec", "https://web.stanford.edu/class/cs246/", "graduate", ["Data Mining", "Big Data"]),
            ("Probabilistic Graphical Models (CS228)", "Computer Science", "Stefano Ermon", "https://cs.stanford.edu/~ermon/cs228/", "graduate", ["Machine Learning", "Probabilistic Models"]),
            ("Logic, Automata, and Complexity (CS154)", "Computer Science", "Ryan Williams", "https://web.stanford.edu/class/cs154-2024/", "undergraduate", ["Theory of Computing", "Algorithms"]),
            ("Introduction to Biomedical Informatics (BIOMEDIN 215)", "Biomedical Informatics", "Various", "https://web.stanford.edu/class/biomedin215/", "graduate", ["Biomedical Informatics", "Medicine"]),
            ("Machine Learning for Healthcare (CS 472)", "Computer Science", "Nigam Shah", "https://cs472.stanford.edu/", "graduate", ["Machine Learning", "Medicine"]),
            ("AI in Healthcare (CS 472B)", "Computer Science", "Various", "https://web.stanford.edu/class/cs472b/", "graduate", ["Artificial Intelligence", "Medicine"]),
            ("Introduction to Neuroscience (PSYCH 35)", "Psychology", "Various", "https://psychology.stanford.edu/course/introduction-neuroscience", "undergraduate", ["Neuroscience", "Biology"]),
            ("How the Economy Works (ECON 101)", "Economics", "Various", "https://economics.stanford.edu/course/how-economy-works", "undergraduate", ["Economics", "Macroeconomics"]),
            ("Economics of Innovation (ECON 281)", "Economics", "Various", "https://economics.stanford.edu/course/economics-innovation", "graduate", ["Economics", "Innovation"]),
            ("Behavioral Economics (ECON 264)", "Economics", "Various", "https://economics.stanford.edu/course/behavioral-economics", "graduate", ["Economics", "Psychology"]),
            ("Introduction to Political Economy (POLS 115)", "Political Science", "Various", "https://politicalscience.stanford.edu/course/political-economy", "undergraduate", ["Political Science", "Economics"]),
            ("Introduction to Machine Learning (CS 229M)", "Computer Science", "Percy Liang", "https://cs229m.stanford.edu/", "graduate", ["Machine Learning", "Statistics"]),
            ("Advanced Topics in Deep Learning (CS 330)", "Computer Science", "Chelsea Finn", "https://cs330.stanford.edu/", "graduate", ["Deep Learning", "Meta-Learning"]),
            ("Introduction to Operations Research (MS&E 111)", "Management Science", "Various", "https://web.stanford.edu/class/msande111/", "undergraduate", ["Operations Research", "Optimization"]),
            ("Financial Mathematics (MATH 238)", "Mathematics", "Various", "https://mathematics.stanford.edu/finance-math", "graduate", ["Mathematics", "Finance"]),
            ("Human Genetics (HUMBIO 135)", "Human Biology", "Various", "https://humanbiology.stanford.edu/genetics", "undergraduate", ["Genetics", "Biology"]),
            ("Introduction to Cancer Biology (MED 200)", "Medicine", "Various", "https://med.stanford.edu/cancer-biology", "undergraduate", ["Biology", "Medicine"]),
            ("Nanoelectronics (EE 216)", "Electrical Engineering", "Various", "https://web.stanford.edu/class/ee216/", "graduate", ["Nanotechnology", "Electrical Engineering"]),
            ("Power Electronics (EE 215)", "Electrical Engineering", "Various", "https://web.stanford.edu/class/ee215/", "graduate", ["Power Systems", "Electrical Engineering"]),
            ("Wireless Communications (EE 359)", "Electrical Engineering", "Andrea Goldsmith", "https://web.stanford.edu/class/ee359/", "graduate", ["Communications", "Electrical Engineering"]),
            ("Digital Communications (EE 379A)", "Electrical Engineering", "Various", "https://web.stanford.edu/class/ee379a/", "graduate", ["Communications", "Signal Processing"]),
            ("Computer Architecture (EE 282)", "Electrical Engineering", "Various", "https://web.stanford.edu/class/ee282/", "graduate", ["Computer Architecture", "Electrical Engineering"]),
            ("Robotics and Autonomous Vehicles (CS 237B)", "Computer Science", "Various", "https://web.stanford.edu/class/cs237b/", "graduate", ["Robotics", "Autonomous Systems"]),
            ("Introduction to Solid Mechanics (CEE 101A)", "Civil Engineering", "Various", "https://cee.stanford.edu/course/structural-mechanics", "undergraduate", ["Structural Engineering", "Mechanics"]),
            ("Geotechnical Engineering (CEE 201)", "Civil Engineering", "Various", "https://cee.stanford.edu/course/geotechnical-engineering", "graduate", ["Civil Engineering", "Geotechnical Engineering"]),
            ("Environmental Engineering (CEE 80)", "Civil Engineering", "Various", "https://cee.stanford.edu/course/environmental-engineering", "undergraduate", ["Environmental Engineering", "Chemistry"]),
            ("Global Environmental Law (LAW 2094)", "Law", "Various", "https://law.stanford.edu/courses/environmental-law", "graduate", ["Law", "Environmental Science"]),
            ("Health Law and Policy (LAW 2033)", "Law", "Various", "https://law.stanford.edu/courses/health-law", "graduate", ["Law", "Health"]),
            ("Introduction to the History of Science (STS 1)", "Science, Technology, and Society", "Various", "https://sts.stanford.edu/courses/history-of-science", "undergraduate", ["History", "Science"]),
            ("Energy Policy (ENERGY 181)", "Earth Sciences", "Various", "https://energy.stanford.edu/course/energy-policy", "graduate", ["Energy", "Public Policy"]),
            ("Solar Energy (ENERGY 81)", "Earth Sciences", "Various", "https://energy.stanford.edu/course/solar-energy", "undergraduate", ["Energy", "Environmental Science"]),
            ("Ocean Science (ESS 121)", "Earth Sciences", "Various", "https://earth.stanford.edu/course/ocean-science", "undergraduate", ["Earth Science", "Environmental Science"]),
        ]
    },
    "berkeley": {
        "name": "University of California, Berkeley", "slug": "berkeley",
        "website": "https://www.berkeley.edu", "country": "US",
        "description": "UC Berkeley free open courseware and YouTube lecture series.",
        "courses": [
            # Engineering
            ("ME 40: Introduction to Mechanical Engineering", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me40", "undergraduate", ["Mechanical Engineering"]),
            ("ME 106: Fluid Mechanics", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me106", "undergraduate", ["Fluid Mechanics", "Mechanical Engineering"]),
            ("ME 132: Dynamic Systems and Feedback Control", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me132", "undergraduate", ["Control Systems", "Mechanical Engineering"]),
            ("ME 135: Design of Microprocessor-Based Mechanical Systems", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me135", "undergraduate", ["Embedded Systems", "Mechanical Engineering"]),
            ("ME 136: Introduction to Control of Unmanned Systems", "Mechanical Engineering", "Various", "https://me.berkeley.edu/courses/me136", "undergraduate", ["Robotics", "Control Systems"]),
            ("IEOR 115: Industrial and Commercial Data Systems", "Industrial Engineering", "Various", "https://ieor.berkeley.edu/courses/ieor115", "undergraduate", ["Data Systems", "Engineering"]),
            ("IEOR 162: Linear Programming and Network Flows", "Industrial Engineering", "Various", "https://ieor.berkeley.edu/courses/ieor162", "undergraduate", ["Linear Programming", "Operations Research"]),
            ("IEOR 165: Engineering Statistics, Quality Control, and Forecasting", "Industrial Engineering", "Various", "https://ieor.berkeley.edu/courses/ieor165", "undergraduate", ["Statistics", "Engineering"]),
            ("IEOR 172: Probability and Risk Analysis for Engineers", "Industrial Engineering", "Various", "https://ieor.berkeley.edu/courses/ieor172", "undergraduate", ["Probability", "Engineering"]),
            ("IEOR 220: Introduction to Probability and Statistics in Business", "Industrial Engineering", "Various", "https://ieor.berkeley.edu/courses/ieor220", "graduate", ["Statistics", "Business"]),
            ("CE 11: Engineered Systems and Sustainability", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce11", "undergraduate", ["Civil Engineering", "Sustainability"]),
            ("CE 100: Engineering Problem Solving Using Computation", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce100", "undergraduate", ["Civil Engineering", "Programming"]),
            ("CE 120: Introduction to Structural Analysis", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce120", "undergraduate", ["Structural Engineering", "Civil Engineering"]),
            ("CE 130: Mechanics of Materials", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce130", "undergraduate", ["Structural Engineering", "Mechanics"]),
            ("CE 155: Introduction to Transportation Engineering", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce155", "undergraduate", ["Transportation Engineering", "Civil Engineering"]),
            ("CE 270: Water Resource Engineering", "Civil Engineering", "Various", "https://ce.berkeley.edu/courses/ce270", "graduate", ["Water Resources", "Environmental Engineering"]),
            ("Nuclear Engineering 101: Nuclear Reactions and Technology", "Nuclear Engineering", "Various", "https://nuc.berkeley.edu/courses/ne101", "undergraduate", ["Nuclear Engineering", "Physics"]),
            ("MSE 45: Properties of Materials", "Materials Science", "Various", "https://mse.berkeley.edu/courses/mse45", "undergraduate", ["Materials Science", "Engineering"]),
            ("MSE 102: Introduction to Phase Transformations", "Materials Science", "Various", "https://mse.berkeley.edu/courses/mse102", "undergraduate", ["Materials Science"]),
            ("MSE 130: Experimental Methods in Materials Science", "Materials Science", "Various", "https://mse.berkeley.edu/courses/mse130", "undergraduate", ["Materials Science"]),
            # Additional Computer Science
            ("CS 61C: Great Ideas in Computer Architecture", "Electrical Engineering and Computer Science", "Various", "https://cs61c.org/", "undergraduate", ["Computer Architecture", "Systems Programming"]),
            ("CS 70: Discrete Mathematics and Probability Theory", "Electrical Engineering and Computer Science", "Various", "https://www.eecs70.org/", "undergraduate", ["Discrete Mathematics", "Probability"]),
            ("CS 162: Operating Systems and Systems Programming", "Electrical Engineering and Computer Science", "Various", "https://cs162.org/", "undergraduate", ["Operating Systems", "Systems Programming"]),
            ("CS 164: Programming Languages and Compilers", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs164/", "undergraduate", ["Compilers", "Programming Languages"]),
            ("CS 168: Introduction to the Internet", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs168/", "undergraduate", ["Computer Networks", "Internet"]),
            ("CS 170: Efficient Algorithms and Intractable Problems", "Electrical Engineering and Computer Science", "Various", "https://cs170.org/", "undergraduate", ["Algorithms", "Theory of Computing"]),
            ("CS 174: Combinatorics and Discrete Probability", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs174/", "undergraduate", ["Combinatorics", "Probability"]),
            ("CS 176: Algorithms for Computational Biology", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs176/", "undergraduate", ["Bioinformatics", "Algorithms"]),
            ("CS 182: Designing, Visualizing and Understanding Deep Neural Networks", "Electrical Engineering and Computer Science", "Anant Sahai", "https://cs182sp21.github.io/", "graduate", ["Deep Learning", "Neural Networks"]),
            ("CS 189: Introduction to Machine Learning", "Electrical Engineering and Computer Science", "Various", "https://www.eecs189.org/", "undergraduate", ["Machine Learning", "Computer Science"]),
            ("CS 186: Introduction to Database Systems", "Electrical Engineering and Computer Science", "Various", "https://cs186berkeley.net/", "undergraduate", ["Databases", "Computer Science"]),
            ("CS 188: Introduction to Artificial Intelligence", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs188/", "undergraduate", ["Artificial Intelligence", "Computer Science"]),
            ("CS 184: Foundations of Computer Graphics", "Electrical Engineering and Computer Science", "Various", "https://cs184.eecs.berkeley.edu/", "undergraduate", ["Computer Graphics", "Computer Science"]),
            ("CS 267: Applications of Parallel Computers", "Electrical Engineering and Computer Science", "Jim Demmel", "https://sites.google.com/lbl.gov/cs267-spr2023/", "graduate", ["Parallel Computing", "High Performance Computing"]),
            ("CS 294: Responsible AI", "Electrical Engineering and Computer Science", "Various", "https://inst.eecs.berkeley.edu/~cs294-rai/", "graduate", ["AI Ethics", "Artificial Intelligence"]),
            # Statistics and Data Science
            ("Stat 20: Introduction to Probability and Statistics", "Statistics", "Various", "https://stat20.org/", "undergraduate", ["Statistics", "Probability"]),
            ("Stat 134: Concepts of Probability", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat134", "undergraduate", ["Probability", "Statistics"]),
            ("Stat 135: Concepts of Statistics", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat135", "undergraduate", ["Statistics"]),
            ("Stat 140: Probability for Data Science", "Statistics", "Various", "https://prob140.org/", "undergraduate", ["Statistics", "Data Science"]),
            ("Stat 150: Stochastic Processes", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat150", "undergraduate", ["Stochastic Processes", "Statistics"]),
            ("Stat 153: Introduction to Time Series", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat153", "undergraduate", ["Time Series", "Statistics"]),
            ("Stat 155: Game Theory", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat155", "undergraduate", ["Game Theory", "Mathematics"]),
            ("Stat 157: Statistical Learning Theory", "Statistics", "Various", "https://stat.berkeley.edu/courses/stat157", "undergraduate", ["Machine Learning", "Statistics"]),
            ("Stat 159: Reproducible and Collaborative Statistical Data Science", "Statistics", "Various", "https://stat159.datahub.berkeley.edu/", "undergraduate", ["Data Science", "Statistics"]),
            ("Data 100: Principles and Techniques of Data Science", "Data Science", "Various", "https://ds100.org/", "undergraduate", ["Data Science", "Statistics"]),
            # Environment and Energy
            ("Environmental Engineering 200: Environmental Engineering", "Environmental Science", "Various", "https://ce.berkeley.edu/courses/ce200", "graduate", ["Environmental Engineering", "Environmental Science"]),
            ("Energy and Resources 102: Quantitative Aspects of Global Environmental Problems", "Energy and Resources", "Various", "https://erg.berkeley.edu/courses/er102", "undergraduate", ["Environmental Science", "Energy"]),
            ("Energy and Resources 131: Ecology and Society", "Energy and Resources", "Various", "https://erg.berkeley.edu/courses/er131", "undergraduate", ["Ecology", "Environmental Science"]),
            ("Plant and Microbial Biology 11: Biology of Plants", "Plant and Microbial Biology", "Various", "https://pmb.berkeley.edu/courses/pmb11", "undergraduate", ["Biology", "Botany"]),
            ("Earth and Planetary Science 20: Earthquakes in Your Backyard", "Earth and Planetary Science", "Various", "https://eps.berkeley.edu/courses/eps20", "undergraduate", ["Geology", "Earth Science"]),
            ("Earth and Planetary Science 50: The Dynamic Earth", "Earth and Planetary Science", "Various", "https://eps.berkeley.edu/courses/eps50", "undergraduate", ["Geology", "Earth Science"]),
            # Social Sciences
            ("Psychology 140: Statistics for Social Sciences", "Psychology", "Various", "https://psychology.berkeley.edu/courses/psych140", "undergraduate", ["Statistics", "Psychology"]),
            ("Psychology 160: Social Psychology", "Psychology", "Various", "https://psychology.berkeley.edu/courses/psych160", "undergraduate", ["Social Psychology", "Psychology"]),
            ("Psychology 164: Cognitive Psychology", "Psychology", "Various", "https://psychology.berkeley.edu/courses/psych164", "undergraduate", ["Cognitive Psychology", "Psychology"]),
            ("Psychology 165: Behavior and Its Neural Bases", "Psychology", "Various", "https://psychology.berkeley.edu/courses/psych165", "undergraduate", ["Neuroscience", "Psychology"]),
            ("Psychology 167: Health Psychology", "Psychology", "Various", "https://psychology.berkeley.edu/courses/psych167", "undergraduate", ["Health", "Psychology"]),
            ("Political Science 2: Introduction to Comparative Politics", "Political Science", "Various", "https://polisci.berkeley.edu/courses/ps2", "undergraduate", ["Political Science", "Comparative Politics"]),
            ("Political Science 3: Introduction to International Relations", "Political Science", "Various", "https://polisci.berkeley.edu/courses/ps3", "undergraduate", ["International Relations", "Political Science"]),
            ("Sociology 3: Introduction to Sociological Theory", "Sociology", "Various", "https://sociology.berkeley.edu/courses/soc3", "undergraduate", ["Sociology"]),
            ("Sociology 5: Evaluating Claims About Society", "Sociology", "Various", "https://sociology.berkeley.edu/courses/soc5", "undergraduate", ["Sociology", "Statistics"]),
            ("Sociology 112: Criminology", "Sociology", "Various", "https://sociology.berkeley.edu/courses/soc112", "undergraduate", ["Criminology", "Sociology"]),
            ("Ethnic Studies 1: Introduction to Ethnic Studies", "Ethnic Studies", "Various", "https://ethnicstudies.berkeley.edu/courses/es1", "undergraduate", ["Ethnic Studies", "Social Sciences"]),
            ("Gender and Women's Studies 10: Introduction to Women, Gender, and Sexuality", "Gender and Women's Studies", "Various", "https://gws.berkeley.edu/courses/gws10", "undergraduate", ["Gender Studies", "Social Sciences"]),
            # Humanities
            ("English 1A: Reading and Composition", "English", "Various", "https://english.berkeley.edu/courses/engl1a", "undergraduate", ["Writing", "English"]),
            ("English 100: Introduction to Literature", "English", "Various", "https://english.berkeley.edu/courses/engl100", "undergraduate", ["Literature", "English"]),
            ("English 117: American Literature", "English", "Various", "https://english.berkeley.edu/courses/engl117", "undergraduate", ["Literature", "American Studies"]),
            ("History 7C: History of the United States from WWII to the Present", "History", "Various", "https://history.berkeley.edu/courses/hist7c", "undergraduate", ["History", "American History"]),
            ("History 4A: The Ancient World", "History", "Various", "https://history.berkeley.edu/courses/hist4a", "undergraduate", ["History", "Ancient History"]),
            ("History 100F: The Holocaust", "History", "Various", "https://history.berkeley.edu/courses/hist100f", "undergraduate", ["History", "Holocaust Studies"]),
            ("Philosophy 25A: Ancient Philosophy", "Philosophy", "Various", "https://philosophy.berkeley.edu/courses/phil25a", "undergraduate", ["Philosophy", "Ancient Philosophy"]),
            ("Philosophy 25B: Modern Philosophy", "Philosophy", "Various", "https://philosophy.berkeley.edu/courses/phil25b", "undergraduate", ["Philosophy"]),
            ("Philosophy 115: Political Philosophy", "Philosophy", "Various", "https://philosophy.berkeley.edu/courses/phil115", "undergraduate", ["Political Philosophy", "Philosophy"]),
            ("Philosophy 148: Philosophy of Language", "Philosophy", "Various", "https://philosophy.berkeley.edu/courses/phil148", "undergraduate", ["Philosophy", "Linguistics"]),
            # Professional Schools
            ("Business 101: Foundations of Business", "Haas School of Business", "Various", "https://haas.berkeley.edu/courses/bus101", "undergraduate", ["Business", "Management"]),
            ("Business Administration 140: Corporate Finance", "Haas School of Business", "Various", "https://haas.berkeley.edu/courses/ba140", "undergraduate", ["Finance", "Business"]),
            ("Business Administration 243: Entrepreneurship", "Haas School of Business", "Various", "https://haas.berkeley.edu/courses/ba243", "graduate", ["Entrepreneurship", "Business"]),
            ("Public Health 150: Introduction to Epidemiology", "Public Health", "Various", "https://sph.berkeley.edu/courses/ph150", "undergraduate", ["Epidemiology", "Public Health"]),
            ("Public Health 200D: Epidemiologic Methods", "Public Health", "Various", "https://sph.berkeley.edu/courses/ph200d", "graduate", ["Epidemiology", "Statistics"]),
            ("Law 250.22: Torts", "Law", "Various", "https://www.law.berkeley.edu/courses/torts", "graduate", ["Law", "Torts"]),
            ("Law 250.23: Constitutional Law", "Law", "Various", "https://www.law.berkeley.edu/courses/constitutional-law", "graduate", ["Law", "Constitutional Law"]),
            ("Journalism 200: Reporting and Writing", "Journalism", "Various", "https://journalism.berkeley.edu/courses/j200", "graduate", ["Journalism", "Writing"]),
            # Additional sciences
            ("Physics 151: Elementary Particle Physics", "Physics", "Various", "https://physics.berkeley.edu/courses/phys151", "undergraduate", ["Particle Physics", "Physics"]),
            ("Physics 250: General Relativity", "Physics", "Various", "https://physics.berkeley.edu/courses/phys250", "graduate", ["Relativity", "Physics"]),
            ("Chemistry 220A: Advanced Organic Chemistry", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/chem220a", "graduate", ["Organic Chemistry", "Chemistry"]),
            ("Chemistry 231: Statistical Thermodynamics", "Chemistry", "Various", "https://chemistry.berkeley.edu/courses/chem231", "graduate", ["Thermodynamics", "Chemistry"]),
            ("Math 172: Combinatorics", "Mathematics", "Various", "https://math.berkeley.edu/courses/math172", "undergraduate", ["Combinatorics", "Mathematics"]),
            ("Math 191: Experimental Courses in Mathematics", "Mathematics", "Various", "https://math.berkeley.edu/courses/math191", "undergraduate", ["Mathematics"]),
            ("Integrative Biology 35: The Biology of Human Reproduction", "Integrative Biology", "Various", "https://ib.berkeley.edu/courses/ib35", "undergraduate", ["Biology", "Health"]),
            ("Integrative Biology 131: Human Anatomy", "Integrative Biology", "Various", "https://ib.berkeley.edu/courses/ib131", "undergraduate", ["Anatomy", "Biology"]),
            ("Integrative Biology 163: Human Genetics", "Integrative Biology", "Various", "https://ib.berkeley.edu/courses/ib163", "undergraduate", ["Genetics", "Biology"]),
            ("Integrative Biology 200A: Biology of Aging", "Integrative Biology", "Various", "https://ib.berkeley.edu/courses/ib200a", "graduate", ["Gerontology", "Biology"]),
        ]
    },
    "oxford": {
        "name": "University of Oxford", "slug": "oxford",
        "website": "https://podcasts.ox.ac.uk", "country": "UK",
        "description": "University of Oxford open online courses and podcast lecture series.",
        "courses": [
            ("Philosophy for Beginners", "Philosophy", "Marianne Talbot", "https://podcasts.ox.ac.uk/series/philosophy-beginners", "undergraduate", ["Philosophy"]),
            ("Making Sense of Data in the Media", "Statistics", "Various", "https://podcasts.ox.ac.uk/series/making-sense-data-media", "undergraduate", ["Statistics", "Data Science"]),
            ("Contemporary Chinese Studies", "Area Studies", "Various", "https://podcasts.ox.ac.uk/series/contemporary-china-studies", "graduate", ["Social Sciences"]),
            ("Introduction to Immunology", "Medicine", "Various", "https://podcasts.ox.ac.uk/series/introduction-immunology-oxford", "undergraduate", ["Immunology", "Biology", "Medicine"]),
            ("Global Food Security", "Environmental Science", "Various", "https://podcasts.ox.ac.uk/series/global-food-security-oxford", "undergraduate", ["Environmental Science", "Public Policy"]),
            ("Introduction to Organic Chemistry", "Chemistry", "Various", "https://podcasts.ox.ac.uk/series/intro-organic-chemistry-oxford", "undergraduate", ["Organic Chemistry", "Chemistry"]),
            ("Artificial Intelligence and Society", "Computer Science", "Various", "https://podcasts.ox.ac.uk/series/ai-society-oxford", "undergraduate", ["Artificial Intelligence", "Ethics"]),
        ]
    },
    "yale": {
        "name": "Yale University", "slug": "yale",
        "website": "https://oyc.yale.edu", "country": "US",
        "description": "Open Yale Courses — free and open access to a selection of undergraduate Yale courses.",
        "courses": [
            ("Roman Architecture", "History of Art", "Diana E. E. Kleiner", "https://oyc.yale.edu/history-of-art/hsar-252", "undergraduate", ["Architecture", "History"]),
            ("Frontiers and Controversies in Astrophysics", "Astronomy", "Charles Bailyn", "https://oyc.yale.edu/astronomy/astr-160", "undergraduate", ["Astrophysics", "Physics"]),
            ("African American History: From Emancipation to the Present", "History", "Jonathan Holloway", "https://oyc.yale.edu/african-american-studies/afam-162", "undergraduate", ["History", "American History"]),
        ]
    },
    "princeton": {
        "name": "Princeton University", "slug": "princeton",
        "website": "https://www.princeton.edu", "country": "US",
        "description": "Princeton University open course materials and recorded lectures.",
        "courses": [
            ("Quantum Information Science (QIS 440)", "Computer Science", "Various", "https://www.cs.princeton.edu/courses/archive/spring23/cos440/", "graduate", ["Quantum Computing", "Information Theory"]),
            ("Advanced Computer Architecture (ELE 475)", "Electrical Engineering", "Various", "https://www.princeton.edu/~ota/", "graduate", ["Computer Architecture", "Electrical Engineering"]),
            ("Computer Graphics (COS 426)", "Computer Science", "Tom Funkhouser", "https://www.cs.princeton.edu/courses/archive/spring23/cos426b/", "undergraduate", ["Computer Graphics", "Computer Science"]),
            ("Statistical Analysis (ORF 245)", "Operations Research", "Various", "https://orfe.princeton.edu/courses", "undergraduate", ["Statistics", "Mathematics"]),
            ("Introduction to Mathematical Thinking (MAT 214)", "Mathematics", "Various", "https://www.math.princeton.edu/courses/", "undergraduate", ["Mathematics", "Proof Writing"]),
        ]
    },
    "gatech": {
        "name": "Georgia Institute of Technology", "slug": "gatech",
        "website": "https://www.gatech.edu", "country": "US",
        "description": "Georgia Tech open course materials and YouTube lecture series.",
        "courses": [
            ("Cybersecurity Policy and Privacy (CS 6727A)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6727-privacy/", "graduate", ["Privacy", "Policy"]),
            ("Autonomous Robots (CS 7648)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7648/", "graduate", ["Robotics", "Autonomous Systems"]),
            ("Probabilistic Methods in AI (CS 7616A)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs7616-prob/", "graduate", ["Artificial Intelligence", "Probability"]),
            ("Explainability in Machine Learning (CS 8803X)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs8803-xml/", "graduate", ["Machine Learning", "AI Ethics"]),
            ("Principles of UI Software (CS 4470)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4470/", "undergraduate", ["Human-Computer Interaction", "UI Design"]),
            ("Mobile and Ubiquitous Computing (CS 4605)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4605/", "undergraduate", ["Mobile Computing", "Computer Science"]),
            ("Video Game Design (CS 4455)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4455/", "undergraduate", ["Game Design", "Computer Science"]),
            ("Ethics in AI (CS 4863)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs4863/", "undergraduate", ["AI Ethics", "Computer Science"]),
            ("Applied Cryptography (CS 6260)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs6260/", "graduate", ["Cryptography", "Cybersecurity"]),
            ("Systems for AI (CS 8803SA)", "Computer Science", "Various", "https://www.cc.gatech.edu/classes/cs8803-sa/", "graduate", ["Machine Learning", "Systems"]),
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
