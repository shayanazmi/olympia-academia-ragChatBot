"""
Seed Academic Dataset for Olympia Academia
Provides initial high-quality curated academic resources across multiple domains.
"""

import pandas as pd

SAMPLE_RESOURCES = [
    {
        "URL": "https://golem.ph.utexas.edu/category/2007/04/grothendiecks_letter_to_quille.html",
        "Final_Title": "Grothendieck's Letter to Daniel Quillen on Homotopy Theory and Derivators",
        "Scraped_Title": "Grothendieck's Letter to Quillen",
        "Resource_Type": "Research Article",
        "Enriched_Topic": "Homotopy Theory and Derivators",
        "Enriched_Category": "Mathematics > Algebraic Topology",
        "Keywords": "Grothendieck, Quillen, Derivators, Homotopy, Higher Category Theory, Simplicial Sets",
        "Scraped_Context": "In his legendary 1983 letter to Daniel Quillen, Alexander Grothendieck outlined the foundational framework for homotopical algebra, introducing derivators and expressing his vision for higher categories, weakly enriched categories, and test categories. The letter serves as an essential bridge between classical model categories and modern higher category theory.",
        "AI_Summary": "Grothendieck's letter to Daniel Quillen establishes the foundation of derivators as a replacement for triangulated categories, proposing new categorical structures for modern homotopy theory.",
        "Key_Insights": "Derivators preserve higher homotopy information lost in standard derived categories. Directly influenced Lurie's Higher Topos Theory.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://www.youtube.com/watch?v=0SPD2r0xV8k",
        "Final_Title": "Quantum Avian Navigation: Radical Pairs and Cryptochrome",
        "Scraped_Title": "How Birds Navigate Using Quantum Mechanics",
        "Resource_Type": "Video Resource",
        "Enriched_Topic": "Quantum Biology",
        "Enriched_Category": "Biology > Quantum Biophysics",
        "Keywords": "Cryptochrome, Radical Pair Mechanism, Quantum Entanglement, Avian Magnetoreception, Photoreceptors",
        "Scraped_Context": "European robins navigate across continents using magnetoreception powered by a quantum mechanical radical pair mechanism within cryptochrome proteins in their retinas. Light excitation creates spin-correlated radical pairs whose recombination depends on the inclination angle of Earth's geomagnetic field.",
        "AI_Summary": "An exploration of quantum biology showing how migratory birds perceive Earth's magnetic field through spin states of entangled radical pairs in ocular cryptochrome-4.",
        "Key_Insights": "Blue light activates Flavin Adenine Dinucleotide (FAD) to form radical pairs that maintain quantum coherence long enough to detect microtesla geomagnetic fields.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://lean-lang.org/documentation/",
        "Final_Title": "Lean 4 Interactive Theorem Prover and Programming Language",
        "Scraped_Title": "Lean Prover Official Documentation",
        "Resource_Type": "Course/Tool",
        "Enriched_Topic": "Formal Verification",
        "Enriched_Category": "Computer Science > Formal Methods",
        "Keywords": "Lean 4, Theorem Proving, Dependent Type Theory, Formal Verification, Mathlib, Calculus of Inductive Constructions",
        "Scraped_Context": "Lean 4 is a functional programming language and interactive theorem prover based on the Calculus of Inductive Constructions. Widely used in modern mathematics, notably in Terence Tao's formalization of the Polynomial Freiman-Ruzsa conjecture and the Liquid Tensor Experiment led by Peter Scholze and Dustin Clausen.",
        "AI_Summary": "Lean 4 enables mathematicians and computer scientists to formally verify mathematical theorems and write bug-free verified software using dependent types.",
        "Key_Insights": "Combines a powerful metaprogramming architecture with high-performance C++ compiler backends and Mathlib mathematical library.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://www.youtube.com/shorts/9iUPepjoPog",
        "Final_Title": "The Feynman Technique for Deep Mental Models and Accelerated Learning",
        "Scraped_Title": "The Feynman Technique Explained",
        "Resource_Type": "Video Resource",
        "Enriched_Topic": "Cognitive Science & Learning",
        "Enriched_Category": "Education > Epistemology",
        "Keywords": "Richard Feynman, Learning Technique, First Principles, Simplification, Mental Models",
        "Scraped_Context": "The Feynman Technique consists of 4 distinct steps: 1) Choose a concept, 2) Teach it to a sixth grader using plain language, 3) Identify gaps in your explanation and revisit source material, 4) Simplify through analogies and refine. It eliminates the illusion of explanatory depth.",
        "AI_Summary": "A four-stage heuristic developed by Nobel laureate Richard Feynman to ensure true intuitive mastery over complex scientific and mathematical concepts.",
        "Key_Insights": "If you cannot explain a concept without jargon, you do not truly understand the underlying mechanism.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://www.youtube.com/shorts/g5EyChOEi9o",
        "Final_Title": "Sir Michael Atiyah and the Atiyah-Singer Index Theorem",
        "Scraped_Title": "Michael Atiyah: Mathematical Visionary",
        "Resource_Type": "Video Resource",
        "Enriched_Topic": "Differential Geometry",
        "Enriched_Category": "Mathematics > Global Analysis",
        "Keywords": "Michael Atiyah, Index Theorem, K-Theory, Topological Quantum Field Theory, Dirac Operator",
        "Scraped_Context": "Sir Michael Atiyah proved the Atiyah-Singer Index Theorem in 1963, linking differential geometry, topology, and analysis. The theorem demonstrates that the analytical index of an elliptic differential operator on a compact manifold equals its topological index, forging a foundational bridge to theoretical quantum physics and string theory.",
        "AI_Summary": "An overview of Sir Michael Atiyah's landmark contributions, primarily topological K-theory and the celebrated Index Theorem connecting analysis and algebraic topology.",
        "Key_Insights": "The Index Theorem provides the mathematical bedrock for quantum anomalies and instantons in non-Abelian gauge theory.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://arxiv.org/abs/1706.03762",
        "Final_Title": "Attention Is All You Need: The Transformer Architecture",
        "Scraped_Title": "Attention Is All You Need",
        "Resource_Type": "Research Paper",
        "Enriched_Topic": "Neural Network Architectures",
        "Enriched_Category": "Computer Science > Deep Learning",
        "Keywords": "Transformer, Self-Attention, Multi-Head Attention, Sequence Modeling, NLP, Vaswani",
        "Scraped_Context": "The dominant sequence transduction models were based on complex recurrent or convolutional neural networks. The Transformer dispenses entirely with recurrence and convolutions, relying solely on multi-head scaled dot-product attention mechanisms to compute parallelized global representations of sequences.",
        "AI_Summary": "Seminal paper introducing the Transformer architecture, showing that self-attention mechanisms alone can outperform recurrent architectures while training substantially faster.",
        "Key_Insights": "Scaled dot-product attention computes $O(1)$ sequential operations across tokens, removing the sequential bottleneck of RNNs and enabling foundation models.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://arxiv.org/abs/1806.07366",
        "Final_Title": "Neural Ordinary Differential Equations",
        "Scraped_Title": "Neural Ordinary Differential Equations",
        "Resource_Type": "Research Paper",
        "Enriched_Topic": "Continuous Deep Learning",
        "Enriched_Category": "Mathematics > Dynamical Systems",
        "Keywords": "Neural ODEs, Adjoint Sensitivity, Continuous Depth, ResNet, Differential Equations",
        "Scraped_Context": "We introduce a new family of deep neural network models. Instead of specifying a discrete sequence of hidden layers, we parameterize the continuous derivative of the hidden state using a neural network. The output of the network is computed using a black-box differential equation solver with constant memory cost using the adjoint sensitivity method.",
        "AI_Summary": "Replaces discrete residual neural networks with continuous-depth dynamical systems modeled via ordinary differential equations solved with adaptive numerical solvers.",
        "Key_Insights": "Enables training continuous-time models with $O(1)$ backpropagation memory using the continuous adjoint method.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://arxiv.org/abs/2005.11401",
        "Final_Title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "Scraped_Title": "Retrieval-Augmented Generation",
        "Resource_Type": "Research Paper",
        "Enriched_Topic": "Retrieval-Augmented Generation",
        "Enriched_Category": "Computer Science > Natural Language Processing",
        "Keywords": "RAG, Dense Passage Retrieval, Lewis, Parametric Memory, Non-Parametric Memory",
        "Scraped_Context": "Large pre-trained language models store factual knowledge in parameter weights, but struggle to update memory or verify sources. We explore general-purpose fine-tuning recipes for Retrieval-Augmented Generation (RAG) combining pre-trained parametric and non-parametric memory via Dense Passage Retrieval (DPR) and sequence-to-sequence generators.",
        "AI_Summary": "The founding paper defining modern RAG, introducing joint training of parametric generator networks with non-parametric dense retrieval indices.",
        "Key_Insights": "RAG models produce more specific, factual, and verified answers with dramatically lower hallucination rates compared to pure parametric language models.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://www.quantamagazine.org/the-quantum-thermodynamics-revolution-20170502/",
        "Final_Title": "The Quantum Thermodynamics Revolution: Maxwell's Demon and Landauer's Principle",
        "Scraped_Title": "Quantum Thermodynamics and Information",
        "Resource_Type": "Research Article",
        "Enriched_Topic": "Quantum Thermodynamics",
        "Enriched_Category": "Physics > Statistical Mechanics",
        "Keywords": "Landauer Principle, Information Entropy, Maxwell Demon, Quantum Coherence, Thermalization",
        "Scraped_Context": "Physicists are extending 19th-century classical thermodynamics into microscopic quantum regimes where fluctuations, entanglement, and information erasure govern energy flow. Landauer's principle establishes that erasing one bit of information costs a fundamental minimum thermodynamic work of $k_B T \\ln 2$.",
        "AI_Summary": "An exploration of how modern physicists unite quantum information theory with statistical mechanics, solving the paradox of Maxwell's Demon through information erasure costs.",
        "Key_Insights": "Information is strictly physical; quantum coherence can act as a thermodynamic resource to extract work beyond classical limits.",
        "Link_Status": "Active"
    },
    {
        "URL": "https://ncatlab.org/nlab/show/topos",
        "Final_Title": "Topos Theory and Categorical Logic",
        "Scraped_Title": "Topos in nLab",
        "Resource_Type": "Research Article",
        "Enriched_Topic": "Category Theory",
        "Enriched_Category": "Mathematics > Category Theory",
        "Keywords": "Topos, Sheaves, Grothendieck Topos, Elementary Topos, Subobject Classifier, Intuitionistic Logic",
        "Scraped_Context": "A topos is a category that behaves like the category of sets while simultaneously representing a generalized topological space (Grothendieck topos) and a semantic universe for intuitionistic higher-order logic (elementary topos). Toposes unify geometry, algebra, and mathematical logic.",
        "AI_Summary": "Foundational introduction to topos theory, detailing how toposes generalize topological spaces via sheaves on a site and provide models for constructive logic.",
        "Key_Insights": "Every elementary topos has a subobject classifier $\\Omega$ which generalizes the classical truth values $\\{\\text{true}, \\text{false}\\}$ into intuitionistic logic.",
        "Link_Status": "Active"
    }
]

def get_seed_dataframe() -> pd.DataFrame:
    """Returns the seed academic dataset as a pandas DataFrame."""
    return pd.DataFrame(SAMPLE_RESOURCES)
