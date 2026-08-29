import os
import re
import google.generativeai as genai
from backend.config import MODEL_NAME, configure_gemini
from backend.db import search_documents

# Ensure Gemini is configured
configure_gemini()

def fix_markdown_tables(text: str) -> str:
    """Ensures markdown tables have proper newline breaks and valid syntax."""
    if not text:
        return ""
    
    # 1. Replace double pipe || with newline + single pipe |\n|
    fixed = re.sub(r'\|\s*\|\s*', '|\n| ', text)
    
    # 2. Ensure header delimiter (|---|---|) has newlines before and after
    fixed = re.sub(r'([^\n])\s*(\|\s*:?-+:?\s*\|)', r'\1\n\2', fixed)
    
    # 3. Ensure lines with multiple table cells glued together get broken into separate rows
    fixed = re.sub(r'(\|\s*)\|\s*([^\n|]+)', r'\1\n| \2', fixed)
    
    return fixed

def fix_all_markdown_tables(text: str) -> str:
    """Ensures markdown tables have proper continuous rows, no blank lines, and converts multiline cell bullets to <br>."""
    if not text:
        return ""
        
    # 1. If a heading or text is glued to the start of a table on the same line (e.g. "2. Matrix: | Symbol |"):
    text = re.sub(r'([^\n|]+:)\s*(\|)', r'\1\n\n\2', text)
    
    # 2. Replace double pipe || with newline + single pipe
    text = re.sub(r'\|\s*\|\s*', '|\n| ', text)
    
    raw_lines = text.split('\n')
    cleaned_lines = []
    in_table = False
    
    for line in raw_lines:
        s = line.strip()
        
        # Check if line is a table row or delimiter
        if s.startswith('|') and s.endswith('|'):
            in_table = True
            cleaned_lines.append(s)
        elif in_table and s.startswith('|'):
            in_table = True
            cleaned_lines.append(s)
        elif in_table and s and not s.startswith('#') and not re.match(r'^\d+\.', s) and not s.startswith('==='):
            # Inside a table cell, convert newline/bullet to <br>
            if cleaned_lines:
                prev = cleaned_lines.pop()
                if prev.endswith('|'):
                    prev = prev[:-1].rstrip() + '<br>' + s + ' |'
                else:
                    prev = prev + '<br>' + s
                cleaned_lines.append(prev)
        else:
            if not s and in_table:
                # Discard blank line inside an active table!
                continue
            else:
                in_table = False
            cleaned_lines.append(line)
            
    return '\n'.join(cleaned_lines)

def clean_academic_response(raw_text: str, query: str = "") -> str:
    """Cleans RAG responses to ensure pure academic output without intro boilerplate or model names."""
    if not raw_text:
        return ""
        
    cleaned = raw_text.strip()
    
    # 0. Fix and heal any collapsed or split markdown tables
    cleaned = fix_all_markdown_tables(cleaned)
    
    # 1. Strip bracketed database paper IDs (e.g. [991686] or [911001])
    cleaned = re.sub(r'\[\s*(?:991|911)\d{3}\s*\]', '', cleaned)
    
    # 2. Strip external model names
    cleaned = re.sub(r'\bGemini\s*(?:Academic|2\.5|Pro|Flash)?\b', 'ResearchOS AI', cleaned, flags=re.IGNORECASE)
    
    # 3. Strip unprompted leading self-intros or conversational openers unless explicitly asked
    is_identity_query = bool(re.search(r'\b(who are you|what is your name|yours? name|who created you|tell (?:me|mi) your)\b', query, flags=re.IGNORECASE))
    if not is_identity_query:
        # Strip "I am the ResearchOS AI Assistant...", "Below is...", "Certainly!...", "Here is..."
        cleaned = re.sub(
            r'^(?:(?:I am|As) (?:the )?ResearchOS AI (?:Assistant|Intelligence Engine)[.,\s]*|(?:Sure|Certainly|Here is|Below is)[^\n]*[.,:\s]*)+(?:\n+)?', 
            '', 
            cleaned, 
            flags=re.IGNORECASE
        )
        cleaned = re.sub(
            r'^(?:Below is [^\n]*\n+|Here is [^\n]*\n+)',
            '',
            cleaned,
            flags=re.IGNORECASE
        )
        
    # 4. Clean horizontal whitespace
    cleaned = re.sub(r'[ \t]{2,}', ' ', cleaned)

    # 5. Remove asterisks (*) from Key Takeaway
    cleaned = re.sub(r'\*{1,3}\s*(💡\s*Key Takeaway:?)\s*\*{1,3}', r'\1', cleaned)
    
    return cleaned.strip()

def build_prompt(query: str, retrieved_sources: list[dict], research_mode: str = "⚛️ Research Agent") -> str:
    """Builds a prompt tailored to the selected specialized Research Agent in Gemini's signature academic style."""
    context_blocks = []
    for idx, src in enumerate(retrieved_sources):
        context_blocks.append(
            f"--- [Reference Document: \"{src['paper']}\"] ---\n{src['full_text']}"
        )
    
    context = "\n\n".join(context_blocks)
    
    mode_instructions = {
        "📖 Literature Review": "Specialization: Act as a Literature Review expert. Synthesize related works, thematic taxonomies, and methodology comparisons relevant to the query.",
        "🔬 Research Gaps": "Specialization: Act as a Research Gap Detector. Isolate unaddressed questions, computational bottlenecks, and limitations relevant to the query.",
        "💡 Research Ideas": "Specialization: Act as a Novel Idea Brainstormer. Propose concrete, publishable research hypotheses and extensions relevant to the query.",
        "🧪 Experiment Planner": "Specialization: Act as an Empirical Protocol Planner. Design experimental setups, baselines, datasets, and evaluation metrics relevant to the query.",
        "⚛️ Research Agent": "Specialization: Act as an elite AI Research Assistant. Provide clear, authoritative explanations with mathematical rigor and deep insights."
    }.get(research_mode, "Specialization: Provide structured academic synthesis.")
    
    prompt = f"""You are the research assistant of ResearchOS.
Active Agent Mode: {research_mode}
{mode_instructions}

Context from Knowledge Base:
{context}

User Inquiry: {query}

STYLE & FORMATTING GUIDELINES (Gemini Academic Style):
1. **Direct Intent Matching**: Answer ONLY what the user asks. If the user asks a specific question, answer that directly. If the user asks for a comprehensive breakdown, provide a thorough, structured response.
2. **Visual Hierarchy & Flow**:
   - Begin with a crisp, direct conceptual explanation or intuitive summary.
   - Organize complex points using clean subsections (e.g. `### Core Architecture`, `### Key Mechanics`).
   - Use structured bullet points with bold leading terms (e.g. `* **Attention Mechanics:** ...`).
3. **Mathematical Precision**: Format all formulas, loss functions, vectors, and variables in clean LaTeX (`$...$` for inline, `$$...$$` for display equations).
4. **Markdown Tables**: Use clean Markdown tables whenever comparing models, metrics, or datasets.
5. **Clean Tone**: Write with high clarity, precision, and intellectual depth. DO NOT use generic conversational filler or unprompted self-introductions (never start with "I am the ResearchOS AI Assistant" or "Below is...").
6. **No Database Artifacts**: DO NOT write database numbers or bracketed paper IDs (like [991XXX]).
"""
    return prompt

def generate_rag_response(
    query: str, 
    n_results: int = 4, 
    filter_doc_ids: list[str] = None,
    research_mode: str = "⚛️ Research Agent"
) -> dict:
    """
    Executes the enhanced RAG pipeline:
    1. Search vector DB for top candidate chunks (optionally scoped to filter_doc_ids).
    2. Deduplicate identical / near-identical passages.
    3. Format distinct sources with rich academic metadata.
    4. Generate clean response tailored to the active research_mode and query intent.
    """
    # 0. Handle simple conversational greetings or identity queries directly & naturally
    clean_q = re.sub(r'[^\w\s]', '', query.strip().lower())
    if clean_q in {"hi", "hello", "hey", "hola", "greetings", "good morning", "good afternoon", "good evening", "how are you"}:
        return {
            "response": "Hello! How can I assist you with your research today? You can ask specific questions about your selected paper, synthesize a literature review, detect critical research gaps, or design benchmark experiments.",
            "citations": []
        }
    if clean_q in {"who are you", "what is your name", "tell me your name", "tell mi your name", "tell mi yours name", "whats your name", "who created you"}:
        return {
            "response": "I am the ResearchOS AI Assistant, an advanced research intelligence engine designed to analyze, synthesize, and extract structured insights from academic literature.",
            "citations": []
        }

    # 1. Retrieve a wider set of candidates to allow intelligent deduplication
    candidate_k = max(n_results * 3, 12)
    search_results = search_documents(query, n_results=candidate_k, filter_doc_ids=filter_doc_ids)
    
    citations = []
    retrieved_sources = []
    seen_texts = set()
    
    if search_results and search_results.get('documents') and len(search_results['documents'][0]) > 0:
        chunks = search_results['documents'][0]
        metadata_list = search_results['metadatas'][0]
        ids = search_results['ids'][0]
        
        for idx, text in enumerate(chunks):
            if not text or not text.strip():
                continue
            
            # Simple text normalization for deduplication
            clean_snippet = re.sub(r'\s+', ' ', text.strip())
            norm_key = clean_snippet[:100].lower()
            if norm_key in seen_texts:
                continue
            seen_texts.add(norm_key)
            
            meta = metadata_list[idx] if idx < len(metadata_list) else {}
            
            source_info = {
                "index": len(retrieved_sources) + 1,
                "paper": meta.get("paper_title", "Research Paper"),
                "doc_id": meta.get("doc_id", "N/A"),
                "domain": meta.get("domain", "Computer Science"),
                "tags": meta.get("tags", ""),
                "full_text": text,
                "snippet": (text[:280] + "...") if len(text) > 280 else text
            }
            retrieved_sources.append(source_info)
            citations.append(source_info)
            
            if len(retrieved_sources) >= n_results:
                break
    
    # 2. Build Prompt with clean structured sources
    if not retrieved_sources:
        prompt = f"""You are the research intelligence engine powering ResearchOS.
Active Agent Mode: {research_mode}
Inquiry: {query}
Instructions: Jump directly into the answer without self-introductions unless explicitly asked who you are."""
    else:
        prompt = build_prompt(query, retrieved_sources, research_mode=research_mode)
    
    # 3. Generate
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    
    raw_text = response.text if response else ""
    cleaned_text = clean_academic_response(raw_text, query=query)
    
    return {
        "response": cleaned_text,
        "citations": citations
    }

def generate_paper_summary(
    paper_title: str, 
    doc_id: str, 
    summary_type: str = "Executive Summary", 
    target_length: str = "Medium (~300 words)",
    focus_topic: str = ""
) -> str:
    """
    Generates a structured, high-impact academic summary.
    Retrieves stored text passages from ChromaDB for the specified paper doc_id.
    """
    from backend.db import get_all_chunks_for_doc_id
    chunks = get_all_chunks_for_doc_id(doc_id=doc_id, limit=12)
    
    context = "\n\n---\n\n".join(chunks) if chunks else f"Paper Title: {paper_title}"
    
    format_instructions = {
        "Executive Summary": "Focus on the core research challenge, the proposed methodology, and key innovations. Structure with bullet points with bold sub-terms.",
        "Technical Deep-Dive": "Analyze the technical architecture, mathematical objective functions ($...$), algorithms, and implementation mechanics in detail.",
        "Key Empirical Results": "Highlight benchmark datasets, baseline comparisons, quantitative performance metrics, and key ablation findings.",
        "ELI5 (Intuitive Overview)": "Explain the core intuition and breakthrough using clear, relatable analogies suitable for any educated reader without mathematical jargon.",
        "Critical Gaps & Limitations": "Highlight underlying assumptions, failure modes, scalability bottlenecks, and open challenges left for future research."
    }.get(summary_type, "Provide a comprehensive, point-wise breakdown.")
    
    prompt = f"""You are the academic research synthesis engine of ResearchOS.
Generate a structured, authoritative, and stylish academic summary for the research paper: "{paper_title}".

Context from Paper:
{context}

Target Format: {summary_type}
Guidelines: {format_instructions}
Target Length: {target_length}
{"Specific Focus: " + focus_topic if focus_topic else ""}

STYLE & FORMATTING GUIDELINES (Gemini Academic Style):
1. **NO SELF-INTRODUCTIONS**: Start DIRECTLY with 💡 Key Takeaway: (1-2 crisp, punchy sentences capturing the breakthrough). DO NOT enclose "💡 Key Takeaway" in asterisks or stars (*). NEVER start with "I am..." or "Below is...".
2. **Visual Hierarchy & Flow**:
   - Begin with the 💡 Key Takeaway highlight.
   - Organize detailed findings using clear subsections (e.g. `### Core Architecture & Mechanics`, `### Key Empirical Findings`).
   - Use structured bullet points with bold blue-tinted lead-in terms (e.g. `* **Core Formulation:** ...`).
3. **Mathematical Precision**: Format all formulas, loss functions, vectors, and variables in clean LaTeX (`$...$` for inline, `$$...$$` for block equations).
4. **Fluid Prose**: Write with intellectual depth, clarity, and precision. DO NOT include bracketed database IDs (like [991XXX]).
"""
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    
    raw = response.text if response else ""
    return clean_academic_response(raw)

def generate_multi_paper_comparison(
    papers_list: list[dict],
    comparison_dimension: str = "Comprehensive Head-to-Head",
    focus_query: str = ""
) -> str:
    """
    Performs deep multi-paper comparative analysis.
    Retrieves stored text passages for 2 or more selected papers.
    """
    from backend.db import get_all_chunks_for_doc_id
    
    paper_contexts = []
    for idx, p in enumerate(papers_list):
        doc_id = p.get("id", "")
        title = p.get("title", "Untitled Paper")
        domain = p.get("domain", "General")
        year = p.get("year", "N/A")
        
        chunks = get_all_chunks_for_doc_id(doc_id=doc_id, limit=8)
        text_body = "\n\n".join(chunks) if chunks else "No text extracted."
        
        paper_contexts.append(
            f"=== PAPER {idx+1}: \"{title}\" (Domain: {domain}, Year: {year}) ===\n{text_body}"
        )
    
    combined_context = "\n\n" + ("="*40) + "\n\n".join(paper_contexts)
    paper_titles = [f'"{p.get("title")}"' for p in papers_list]
    
    # Specialized prompts per Comparison Dimension
    dimension_specs = {
        "Comprehensive Head-to-Head": {
            "title": "Comprehensive Head-to-Head Benchmark",
            "table_rows": "*Core Research Goal, Methodological Blueprint, Key Architectural Innovations, Primary Benchmark Results, Critical Trade-offs & Limitations*",
            "sections": """
1. **📊 Executive Comparison Matrix Table**:
   - Markdown Table comparing all papers across: *Core Research Goal, Methodological Blueprint, Key Architectural Innovations, Primary Benchmark Results, Critical Trade-offs*.

2. **🔬 End-to-End Methodological & Architectural Comparison**:
   - Structured point-wise analysis of theoretical frameworks, mechanisms, and formulations ($...$).

3. **⚖️ Relative Strengths vs Boundary Failure Modes**:
   - Contrast sample efficiency, compute requirements, and specific deployment scenarios where each model excels or degrades.

4. **💡 Cross-Paper Synergies & Novel Hybridization**:
   - Concrete research proposals combining the strengths of these papers.
"""
        },
        "Architecture & Mathematical Mechanics": {
            "title": "Mathematical Formalisms & Neural Mechanics Analysis",
            "table_rows": "*Architecture Family, Input / Feature Tokenization, Mathematical Objective / Loss Function ($...$), Core Layer / Attention Mechanism ($...$), Theoretical Time & Memory Complexity ($\mathcal{O}$)*",
            "sections": """
1. **📐 Mathematical Formulations & Objective Functions Matrix**:
   - Comprehensive Markdown Table with strict $\LaTeX$ equations comparing: *Architecture Family, Input Tokenization, Loss Function ($...$), Core Layer Equation ($...$), Asymptotic Complexity ($\mathcal{O}$)*.

2. **🧠 In-Depth Mathematical & Algorithmic Breakdown**:
   - Detailed derivation of the loss functions ($...$), backpropagation mechanics, attention weight matrices, and parameter scaling laws across each paper.

3. **⚙️ Computational Complexity & Tensor Optimization**:
   - Formal analysis of time complexity $\mathcal{O}(\cdot)$, memory allocation, and GPU compute efficiency during training and inference.

4. **🔬 Unified Theoretical Generalization**:
   - Propose a mathematical generalization or unified theorem that subsumes the mechanisms of all compared papers.
"""
        },
        "Empirical Performance & Baselines": {
            "title": "Empirical Performance, Datasets & Quantitative Benchmarks",
            "table_rows": "*Benchmark Datasets Evaluated, Baselines Compared Against, Primary Metrics (Accuracy / BLEU / F1 / Latency), Relative Improvement ($\%/\Delta$), Hardware / GPU Compute Footprint*",
            "sections": """
1. **📊 Quantitative Benchmark & Metrics Comparison Table**:
   - Detailed Markdown Table comparing: *Benchmark Datasets, Compared Baselines, Primary Numerical Results, Relative Percentage Gains ($\Delta$), Hardware & Energy Footprint*.

2. **📈 Cross-Paper Empirical Performance Analysis**:
   - Deep-dive into which paper outperforms on specific tasks, statistical significance of results, and generalization across diverse datasets.

3. **⏱️ Computational Efficiency & Resource Trade-offs**:
   - Concrete comparison of inference throughput (samples/sec), parameter efficiency, training FLOPs, and GPU memory saturation.

4. **🧪 Ablation Insights & Empirical Reproducibility**:
   - Critical takeaways from the reported ablation experiments and potential reproducibility sensitivities.
"""
        },
        "Critical Limitations & Trade-offs": {
            "title": "Critical Limitations, Assumptions & Trade-off Assessment",
            "table_rows": "*Core Implicit Assumptions, Primary Failure Modes / Edge Cases, Computational Bottlenecks & Scalability Limits, Generalization Bounds & Out-of-Distribution Sensitivity, Unresolved Scientific Questions*",
            "sections": """
1. **⚖️ Vulnerability, Limitations & Trade-off Matrix Table**:
   - Systematic Markdown Table evaluating: *Core Implicit Assumptions, Primary Failure Modes, Scalability Limits, Out-of-Distribution Vulnerability, Unresolved Scientific Questions*.

2. **🔍 Rigorous Audit of Assumptions & Methodological Omissions**:
   - Unpack what each paper assumes (e.g. infinite clean data, static environments) and what was neglected in their experimental setup.

3. **🚨 Boundary Conditions & Failure Case Scenarios**:
   - Concrete breakdown of real-world scenarios, noisy inputs, or adversarial conditions where each method collapses.

4. **🛡️ Mitigation Strategies & Open Research Vectors**:
   - High-impact suggestions on how upcoming research can resolve each paper's critical limitations.
"""
        },
        "Research Synergies & Hybridization": {
            "title": "Novel Research Synergies & Architectural Hybridization",
            "table_rows": "*Core Complementary Strength, Unaddressed Deficiency, Synergistic Intersection Point, Proposed Hybrid Technique, Anticipated Research Impact*",
            "sections": """
1. **💡 Cross-Paper Synergy & Complementary Strengths Table**:
   - Markdown Table mapping: *Core Strength, Unaddressed Deficiency, Intersection Point, Proposed Hybrid Mechanism, Expected Research Breakthrough*.

2. **🧬 Blueprints for 2-3 Novel Hybrid Architectures**:
   - Concrete, highly technical system architectures combining the complementary techniques of these papers (with pipeline diagrams described in text and mathematical objectives).

3. **🧪 Theoretical Justification & Expected Performance Gains**:
   - Mathematical argument ($...$) explaining why the combined hybrid approach solves problems neither paper could solve individually.

4. **🚀 Experimental Roadmap & Publication Strategy**:
   - Step-by-step experiment design, recommended datasets, and conference targeting strategy for the proposed hybrid paper.
"""
        }
    }
    
    spec = dimension_specs.get(comparison_dimension, dimension_specs["Comprehensive Head-to-Head"])
    
    focus_directive = ""
    if focus_query and focus_query.strip():
        focus_directive = f"""
PRIMARY MANDATE - USER CUSTOM FOCUS INQUIRY:
The user specifically requested to evaluate these papers through the lens of: "{focus_query.strip()}".
- You MUST heavily tailor the comparison table and all narrative sections around: "{focus_query.strip()}".
- Include a dedicated section: `### 🎯 Targeted Comparative Evaluation: {focus_query.strip()}` providing a point-wise cross-examination.
- Add dedicated row(s) in the comparison table specifically addressing: "{focus_query.strip()}".
"""

    prompt = f"""You are the academic comparative intelligence engine of ResearchOS.
You are conducting a specialized comparative investigation: "{spec['title']}".

Papers to Compare ({len(papers_list)}):
{", ".join(paper_titles)}

Literature Context from Knowledge Base:
{combined_context}

Selected Dimension: {comparison_dimension}
{focus_directive}

CRITICAL RULES:
1. **NO SELF-INTRODUCTIONS**: Start DIRECTLY with the Executive Comparison Matrix Table. NEVER start with "I am..." or "Below is...".
2. Required Output Structure:
{spec['sections']}

Formatting Guidelines:
- Clean bullet points with bold sub-terms. Format all equations and mathematical terms in clean LaTeX ($...$ or $$...$$).
- DO NOT insert bracketed database numbers (like [991XXX]). Write in fluent, elite academic prose.
"""
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    
    raw = response.text if response else ""
    return clean_academic_response(raw)

def generate_literature_review(
    papers_list: list[dict],
    review_theme: str = "Comprehensive Thematic Survey",
    depth: str = "Detailed (~800 words)",
    target_topic: str = ""
) -> str:
    """
    Generates a publication-grade literature review synthesizing multiple papers.
    Retrieves stored text passages from ChromaDB for all selected papers.
    """
    from backend.db import get_all_chunks_for_doc_id
    
    paper_contexts = []
    for idx, p in enumerate(papers_list):
        doc_id = p.get("id", "")
        title = p.get("title", "Untitled Paper")
        domain = p.get("domain", "General")
        year = p.get("year", "N/A")
        authors = p.get("authors", "")
        
        chunks = get_all_chunks_for_doc_id(doc_id=doc_id, limit=6)
        text_body = "\n\n".join(chunks) if chunks else "No text extracted."
        
        paper_contexts.append(
            f"=== PAPER [{idx+1}]: \"{title}\" (Authors: {authors}, Year: {year}, Domain: {domain}) ===\n{text_body}"
        )
    
    combined_context = "\n\n" + ("="*40) + "\n\n".join(paper_contexts)
    paper_titles = [f'"{p.get("title")}"' for p in papers_list]
    
    theme_guidance = {
        "Comprehensive Thematic Survey": "Provide an exhaustive thematic taxonomy, chronological evolution, and holistic cross-domain analysis.",
        "Methodological & Architectural Evolution": "Focus sharply on architectural transitions, mathematical formulation shifts ($...$), and algorithmic evolution.",
        "Empirical Benchmarks & Comparative Findings": "Synthesize quantitative performance metrics, benchmark datasets, evaluation setups, and ablation lessons.",
        "Critical Research Gaps & Open Challenges": "Isolate the unaddressed questions, bottleneck assumptions, and promising high-impact directions for novel research.",
        "Publication-Ready Related Work Section": "Draft a polished, academic 'Related Work' section in high-impact IEEE/ACM/ACL narrative style ready for an academic manuscript."
    }.get(review_theme, "Provide a comprehensive, thematic synthesis.")
    
    prompt = f"""You are the academic literature review engine of ResearchOS.
Generate a structured, publication-grade Literature Review synthesizing the following {len(papers_list)} research papers:
{", ".join(paper_titles)}

Target Review Theme: {review_theme}
Guidance: {theme_guidance}
Target Depth: {depth}
{"Target Planned Research Topic: " + target_topic if target_topic else ""}

Literature Context from Knowledge Base:
{combined_context}

CRITICAL RULES:
1. **NO SELF-INTRODUCTIONS**: Start DIRECTLY with the **📑 Thematic Taxonomy & Summary Table**. NEVER start with "I am..." or "Below is...".
2. Required Structure:
   * **📑 Thematic Taxonomy & Summary Table**
   * **🧬 Thematic Narrative & Paradigm Evolution**
   * **⚖️ Methodological Contrast & Formulation Shifts**
   * **💡 Synthesized Research Gaps & Strategic Future Directions**

Formatting Guidelines:
- Clean bullet points with bold sub-terms. Format all equations in LaTeX ($...$).
- DO NOT insert bracketed database numbers (like [991XXX]). Write in fluent, elite academic prose.
"""
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    
    raw = response.text if response else ""
    return clean_academic_response(raw)
