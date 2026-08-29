import streamlit as st
import time
import re
import google.generativeai as genai
from backend.database import get_user_documents, save_user_note, log_user_activity
from backend.config import MODEL_NAME
from backend.db import search_documents
from backend.rag_pipeline import clean_academic_response

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="Formula Explainer | ResearchOS",
    page_icon="📐",
    layout="wide"
)

# Ultra-Modern Dark Glassmorphic Styling
st.markdown("""
    <style>
        .block-container {
            max-width: 900px;
            padding-top: 1.5rem;
            padding-bottom: 3.5rem;
            margin: 0 auto;
        }
        .header-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #f8fafc;
            margin: 0;
        }
        .header-subtitle {
            color: #94a3b8;
            font-size: 0.9rem;
            margin-top: 3px;
            margin-bottom: 16px;
        }
        .empty-hero {
            text-align: center;
            padding: 32px 10px 18px 10px;
        }
        .empty-hero h2 {
            font-size: 1.8rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }
        .empty-hero p {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-bottom: 22px;
        }
        /* Formula Live Card */
        .latex-display-card {
            background-color: #0f172a;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px 24px;
            margin: 14px 0 20px 0;
            text-align: center;
        }
        /* Scoped Breakdown Output Container */
        .gemini-formula-view {
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 24px 26px !important;
            border-radius: 14px !important;
            margin-top: 18px;
            margin-bottom: 20px;
            font-size: 0.95rem;
            line-height: 1.7;
            color: #f1f5f9;
        }
        .gemini-formula-view p {
            line-height: 1.7 !important;
            margin-bottom: 0.85rem !important;
            color: #f1f5f9 !important;
        }
        .gemini-formula-view ul, 
        .gemini-formula-view ol {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            padding-left: 1.4rem !important;
        }
        .gemini-formula-view li {
            margin-bottom: 0.5rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        .gemini-formula-view li strong, 
        .gemini-formula-view p strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        .gemini-formula-view h1,
        .gemini-formula-view h2,
        .gemini-formula-view h3,
        .gemini-formula-view h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        .gemini-formula-view h3 {
            font-size: 1.15rem !important;
            color: #93c5fd !important;
        }
        .gemini-formula-view table,
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #334155 !important;
            font-size: 0.9rem !important;
        }
        .gemini-formula-view th,
        th {
            background-color: #0f172a !important;
            color: #60a5fa !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            border: 1px solid #334155 !important;
            text-align: left !important;
        }
        .gemini-formula-view td,
        td {
            padding: 9px 14px !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        .gemini-formula-view tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.4) !important;
        }
        .gemini-formula-view blockquote {
            border-left: 3px solid #60a5fa !important;
            background: rgba(59, 130, 246, 0.08) !important;
            padding: 10px 16px !important;
            border-radius: 0 8px 8px 0 !important;
            margin: 12px 0 !important;
            color: #cbd5e1 !important;
        }
        /* Action Row Buttons */
        div[class*="st-key-form_btn_"] button {
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            border-radius: 8px !important;
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #cbd5e1 !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 16px !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-form_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        div[class*="st-key-form_btn_"] button p,
        div[class*="st-key-form_btn_"] button div {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 1 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            text-align: center !important;
            font-size: 0.85rem !important;
            font-weight: 500 !important;
            color: inherit !important;
        }
    </style>
""", unsafe_allow_html=True)

# Fetch user library
library = get_user_documents(user_email)
st.session_state['library_metadata'] = library

import streamlit.components.v1 as components

# 1. Header
st.markdown("<div id='top-view-anchor'></div>", unsafe_allow_html=True)

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTop() {
                try {
                    const doc = window.parent.document;
                    const anchor = doc.getElementById('top-view-anchor');
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: 'instant', block: 'start' });
                    }
                    const mainContainers = [
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector('[data-testid="stMain"]'),
                        doc.querySelector('section.main'),
                        doc.querySelector('.main'),
                        doc.documentElement,
                        doc.body
                    ];
                    mainContainers.forEach(el => {
                        if (el) {
                            el.scrollTop = 0;
                            if (el.scrollTo) el.scrollTo({ top: 0, behavior: 'instant' });
                        }
                    });
                    window.parent.scrollTo(0, 0);
                } catch(e) {}
            }
            [0, 20, 50, 100, 200, 350, 500, 800, 1200].forEach(ms => setTimeout(forceScrollToTop, ms));
        </script>
    """, height=0)
    col_back_form, col_title_form = st.columns([1.5, 4.5])
    with col_back_form:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_form", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_form:
        st.markdown("<h3 class='header-title'>📐 Mathematical Formula Explainer</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 class='header-title'>📐 Mathematical Formula Explainer</h3>", unsafe_allow_html=True)

st.markdown("<p class='header-subtitle'>Extract and deconstruct complex equations, loss functions, neural operators, and theorems directly from research papers.</p>", unsafe_allow_html=True)

# Function to run AI Formula Explanation Pipeline
def explain_formula_pipeline(formula_latex: str, context_notes: str = "", paper_context: str = "") -> str:
    """Invokes Gemini to generate an exhaustive mathematical & architectural breakdown."""
    prompt = f"""You are an elite professor of Theoretical Computer Science, Applied Mathematics, and Machine Learning.
Perform an exhaustive, crystal-clear deconstruction of the mathematical equations from the paper.

Target Objective / Formulation:
{formula_latex}

Context / Research Domain:
{context_notes if context_notes else "General Machine Learning & Academic Literature"}

{"Paper Context Extracted from Knowledge Base:" if paper_context else ""}
{paper_context if paper_context else ""}

REQUIRED OUTPUT STRUCTURE:

1. **📐 Primary Extracted Mathematical Formulation**:
   - Provide the complete, pristine LaTeX mathematical equation on its own display line:
   $$
   \\text{{Equation...}}
   $$
   - State the official equation name (e.g. *Scaled Dot-Product Attention*, *InfoNCE Loss*, *Cross-Entropy Objective*).

2. **💡 Conceptual Intuition & High-Level Purpose**:
   - 2-3 crisp sentences explaining in plain English what this equation achieves, why standard formulations fail, and why this specific design was introduced.

3. **📊 Mathematical Term-by-Term Breakdown Matrix**:
   Provide a standard Markdown table on separate lines:
| Symbol / Term | Dimensionality / Space | Mathematical Definition & Role in Equation |
| :--- | :--- | :--- |
| Symbol 1 | Space 1 | Definition 1 |
| Symbol 2 | Space 2 | Definition 2 |
   - Format symbols in clean LaTeX ($...$).
   - (CRITICAL: Every table row MUST be on its own line. Never put the table on the same line as the heading).

4. **⚙️ Step-by-Step Computational Flow & Pipeline**:
   - Numbered chronological walkthrough of tensor operations: (e.g. Step 1: Projection, Step 2: Dot-Product Matrix Multiplication, Step 3: Scaling, Step 4: Normalization).

5. **⚠️ Numerical Stability, Edge Cases & Critical Trade-offs**:
   - Point-wise analysis of vanishing/exploding gradients, computational time/memory complexity ($\\mathcal{{O}}(\\cdot)$), and edge-case behaviors.

6. **💻 Minimal PyTorch / Python Implementation**:
   - Provide a clean, executable PyTorch code snippet (5-8 lines) showing tensor shapes and the forward operation.

Formatting Guidelines:
- Write in elite, rigorous academic prose.
- Format all equations and mathematical variables in LaTeX ($...$ or $$...$$).
- Never start with self-introductions ("I am..."). Start directly with 📐 Primary Extracted Mathematical Formulation."""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    raw = response.text if response else ""
    return clean_academic_response(raw)

# ----------------- Main Input: Extract from Library Paper -----------------
if not library:
    st.info("📚 No papers found in your library. Please upload papers first to extract and deconstruct formulas.")
    if st.button("📤 Go to Upload Papers", type="primary"):
        st.switch_page("views/papers/library.py")
else:
    paper_map = {f"📄 {p['title']} (ID: {p['id']})": p for p in library}
    default_form_idx = 0
    if 'selected_paper_id' in st.session_state and st.session_state['selected_paper_id']:
        target_id = str(st.session_state['selected_paper_id'])
        for idx, (p_label, p_data) in enumerate(paper_map.items()):
            if str(p_data.get('id')) == target_id:
                default_form_idx = idx
                break
                
    col_lp, col_lf = st.columns([2.0, 1.5])
    
    with col_lp:
        selected_paper_label = st.selectbox(
            "Select Library Paper",
            list(paper_map.keys()),
            index=default_form_idx,
            key="form_lib_paper_select"
        )
        selected_paper = paper_map.get(selected_paper_label, list(paper_map.values())[0] if paper_map else {})
        
    with col_lf:
        target_formula_focus = st.text_input(
            "Target Equation / Objective Function (Optional)",
            placeholder="e.g. Loss function, Positional encoding, Attention mechanism",
            key="form_lib_focus"
        )
        
    btn_extract_lib = st.button("✨ Deconstruct Equation", type="primary", use_container_width=True, key="btn_expl_lib")
    
    if btn_extract_lib:
        with st.spinner(f"Retrieving mathematical equations from '{selected_paper['title']}' & deconstructing..."):
            # Search ChromaDB for math formulations in this paper
            search_q = f"equation formula loss objective {target_formula_focus}" if target_formula_focus else "mathematical equation loss function objective formulation"
            results = search_documents(query=search_q, n_results=6, filter_doc_ids=[selected_paper["id"]])
            chunks = results.get("documents", [[]])[0] if results and "documents" in results else []
            paper_context_str = "\n\n---\n\n".join(chunks)
            
            breakdown_res = explain_formula_pipeline(
                formula_latex=f"Primary mathematical formulation / {target_formula_focus if target_formula_focus else 'Core Model Objective'}",
                context_notes=f"Paper: {selected_paper['title']} (Domain: {selected_paper.get('domain', 'Machine Learning')})",
                paper_context=paper_context_str
            )
            
            st.session_state["current_formula_breakdown"] = {
                "latex": target_formula_focus if target_formula_focus else selected_paper['title'],
                "text": breakdown_res,
                "domain": f"Paper: {selected_paper['title']}",
                "created_at": time.time()
            }
            log_user_activity(user_email, "Formula Explainer", "Equation Deconstruction", f"Formula: {selected_paper['title']}", breakdown_res, selected_paper['id'])
            st.rerun()

# ----------------- Display Formula Explanation Result -----------------
if "current_formula_breakdown" in st.session_state and st.session_state["current_formula_breakdown"]:
    curr = st.session_state["current_formula_breakdown"]
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    # Render Output inside styled container
    st.markdown(f"""
<div class="gemini-formula-view">

{curr["text"]}

</div>
""", unsafe_allow_html=True)
    
    # Action Row Directly Beneath Breakdown
    col_act1, col_act2, col_act_spacer = st.columns([1.8, 1.8, 4.0])
    
    with col_act1:
        if st.button("💾 Save to Notes", key="form_btn_save", use_container_width=True, help="Save this mathematical breakdown to Personal Notes"):
            saved = save_user_note(
                user_email=user_email,
                title=f"Formula Breakdown: {curr['domain'][:30]}",
                content=f"# Mathematical Breakdown: {curr['domain']}\n\n{curr['text']}",
                notebook="Mathematical Formulations"
            )
            if saved:
                st.toast("✅ Mathematical Breakdown saved to Personal Notes!", icon="📝")
            else:
                st.error("Failed to save note.")
                
    with col_act2:
        if st.button("🗑️ Clear Breakdown", key="form_btn_clear", use_container_width=True, help="Clear this breakdown"):
            st.session_state["current_formula_breakdown"] = None
            st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopFormEnd() {
                try {
                    const doc = window.parent.document;
                    const anchor = doc.getElementById('top-view-anchor');
                    if (anchor) {
                        anchor.scrollIntoView({ behavior: 'instant', block: 'start' });
                    }
                    const mainContainers = [
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector('[data-testid="stMain"]'),
                        doc.querySelector('section.main'),
                        doc.querySelector('.main'),
                        doc.documentElement,
                        doc.body
                    ];
                    mainContainers.forEach(el => {
                        if (el) {
                            el.scrollTop = 0;
                            if (el.scrollTo) el.scrollTo({ top: 0, behavior: 'instant' });
                        }
                    });
                    window.parent.scrollTo(0, 0);
                } catch(e) {}
            }
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopFormEnd, ms));
        </script>
    """, height=0)
