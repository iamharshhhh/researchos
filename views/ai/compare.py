import streamlit as st
import time
from backend.database import get_user_documents, save_user_note, log_user_activity
from backend.rag_pipeline import generate_multi_paper_comparison, clean_academic_response

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="Compare Papers | ResearchOS",
    page_icon="⚖️",
    layout="wide"
)

# Ultra-Modern Dark Glassmorphic Styling (Matching AI Chat & Summarizer Aesthetic)
st.markdown("""
    <style>
        .block-container {
            max-width: 900px;
            padding-top: 1.5rem;
            padding-bottom: 3.5rem;
            margin: 0 auto;
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
        /* Mode Quick-Select Cards (Matching AI Chat Suggestion Cards) */
        div[class*="st-key-cmp_card_"] button {
            min-height: 88px !important;
            height: 88px !important;
            max-height: 88px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: flex-start !important;
            text-align: left !important;
            padding: 14px 18px !important;
            border-radius: 12px !important;
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            width: 100% !important;
            box-sizing: border-box !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-cmp_card_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.15) !important;
        }
        div[class*="st-key-cmp_card_"] button p {
            font-size: 0.88rem !important;
            line-height: 1.35 !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: left !important;
            width: 100% !important;
            color: #cbd5e1 !important;
        }
        div[class*="st-key-cmp_card_"] button strong {
            color: #f8fafc !important;
            font-size: 0.94rem !important;
            display: block !important;
            margin-bottom: 3px !important;
        }
        /* Scoped Comparison Output Container */
        .gemini-compare-view {
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
        .gemini-compare-view p {
            line-height: 1.7 !important;
            margin-bottom: 0.85rem !important;
            color: #f1f5f9 !important;
        }
        .gemini-compare-view ul, 
        .gemini-compare-view ol {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            padding-left: 1.4rem !important;
        }
        .gemini-compare-view li {
            margin-bottom: 0.5rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        .gemini-compare-view li strong, 
        .gemini-compare-view p strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        .gemini-compare-view h1,
        .gemini-compare-view h2,
        .gemini-compare-view h3,
        .gemini-compare-view h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        .gemini-compare-view h3 {
            font-size: 1.15rem !important;
            color: #93c5fd !important;
        }
        .gemini-compare-view table,
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #334155 !important;
            font-size: 0.9rem !important;
        }
        .gemini-compare-view th,
        th {
            background-color: #0f172a !important;
            color: #60a5fa !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            border: 1px solid #334155 !important;
            text-align: left !important;
        }
        .gemini-compare-view td,
        td {
            padding: 9px 14px !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        .gemini-compare-view tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.4) !important;
        }
        .gemini-compare-view blockquote {
            border-left: 3px solid #60a5fa !important;
            background: rgba(59, 130, 246, 0.08) !important;
            padding: 10px 16px !important;
            border-radius: 0 8px 8px 0 !important;
            margin: 12px 0 !important;
            color: #cbd5e1 !important;
        }
        /* Action Row Buttons with Perfect Centering */
        div[class*="st-key-cmp_btn_"] button {
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            margin-top: 8px !important;
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
        div[class*="st-key-cmp_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        div[class*="st-key-cmp_btn_"] button p,
        div[class*="st-key-cmp_btn_"] button div {
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

# 1. Top Header
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
    col_back_cmp, col_title_cmp = st.columns([1.5, 4.5])
    with col_back_cmp:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_cmp", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_cmp:
        st.markdown("<h3 style='font-size:1.6rem; font-weight:700; color:#f8fafc; margin:0;'>⚖️ Cross-Paper Comparison</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 style='font-size:1.6rem; font-weight:700; color:#f8fafc; margin:0;'>⚖️ Cross-Paper Comparison</h3>", unsafe_allow_html=True)

st.markdown("<p style='color:#94a3b8; font-size:0.9rem; margin-top:3px; margin-bottom:16px;'>Conduct rigorous multi-paper benchmarking, architectural trade-off evaluations, and synergy discovery across papers.</p>", unsafe_allow_html=True)

if not library or len(library) < 2:
    st.info("📚 You need at least **2 papers** in your library to perform comparative analysis.")
    if st.button("📤 Upload More Papers", type="primary"):
        st.switch_page("views/papers/library.py")
    st.stop()

# Paper Options mapping
paper_map = {f"📄 {p['title']} (ID: {p['id']})": p for p in library}
paper_options = list(paper_map.keys())

# 2. Sleek Dual-Control Toolbar
col_papers, col_dim = st.columns([2.0, 1.3])

comparison_dimensions = [
    "Comprehensive Head-to-Head",
    "Architecture & Mathematical Mechanics",
    "Empirical Performance & Baselines",
    "Critical Limitations & Trade-offs",
    "Research Synergies & Hybridization"
]

# Check if a specific dimension was triggered by card click
requested_dim = st.session_state.get("selected_cmp_dim", "Comprehensive Head-to-Head")
dim_default_idx = comparison_dimensions.index(requested_dim) if requested_dim in comparison_dimensions else 0

with col_papers:
    selected_paper_keys = st.multiselect(
        "Select Papers to Compare",
        options=paper_options,
        default=[],
        placeholder="📄 Select 2 or more papers to compare...",
        label_visibility="collapsed",
        key="cmp_papers_select"
    )

with col_dim:
    selected_dimension = st.selectbox(
        "Comparison Dimension",
        comparison_dimensions,
        index=dim_default_idx,
        label_visibility="collapsed",
        key="cmp_dim_select"
    )

# 3. Streamlined Parameters Expander & Generate Action
with st.expander("⚙️ Custom Comparative Inquiry & Focal Questions", expanded=False):
    focus_inquiry = st.text_input(
        "Specific Comparison Focus (Optional)",
        placeholder="e.g. Attention mechanisms, GPU inference speed, training stability, or clinical evaluation metrics"
    )

can_compare = len(selected_paper_keys) >= 2
btn_compare = st.button("✨ Run Cross-Paper Comparison", type="primary", use_container_width=True, disabled=not can_compare)

if not can_compare:
    st.caption("ℹ️ Please select at least **2 research papers** from the dropdown to run comparative analysis.")

# 4. Empty State Hero with 4 Aligned Inquiry Cards (When No Comparison Yet)
if "last_comparison" not in st.session_state or not st.session_state["last_comparison"]:
    st.markdown("""
        <div class="empty-hero">
            <h2>Select a comparative inquiry to begin</h2>
            <p>Choose an instant comparative framework or customize dimensions above.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔬 **Novel Methodology & Architecture**\n\nSynthesize foundational models, mathematical mechanics & algorithmic pipelines", use_container_width=True, key="cmp_card_1"):
            st.session_state["selected_cmp_dim"] = "Architecture & Mathematical Mechanics"
            focus_inquiry = "Novel Methodology & Architecture"
            if can_compare:
                btn_compare = True
            selected_dimension = "Architecture & Mathematical Mechanics"
        if st.button("💡 **Novel Research Ideas & Synergies**\n\nBrainstorm high-impact research hypotheses, hybrid models & cross-paper trends", use_container_width=True, key="cmp_card_2"):
            st.session_state["selected_cmp_dim"] = "Research Synergies & Hybridization"
            focus_inquiry = "Novel Research Ideas & Synergies"
            if can_compare:
                btn_compare = True
            selected_dimension = "Research Synergies & Hybridization"
    with c2:
        if st.button("📊 **Empirical Results & Benchmarks**\n\nCompare quantitative performance, evaluation benchmarks, datasets & ablations", use_container_width=True, key="cmp_card_3"):
            st.session_state["selected_cmp_dim"] = "Empirical Performance & Baselines"
            focus_inquiry = "Empirical Results & Benchmark Performance"
            if can_compare:
                btn_compare = True
            selected_dimension = "Empirical Performance & Baselines"
        if st.button("⚠️ **Critical Gaps & Limitations**\n\nIdentify unresolved challenges, computational bottlenecks & failure trade-offs", use_container_width=True, key="cmp_card_4"):
            st.session_state["selected_cmp_dim"] = "Critical Limitations & Trade-offs"
            focus_inquiry = "Critical Limitations, Assumptions & Bottlenecks"
            if can_compare:
                btn_compare = True
            selected_dimension = "Critical Limitations & Trade-offs"

# 5. Generation Logic
if btn_compare and can_compare:
    selected_papers = [paper_map[k] for k in selected_paper_keys]
    
    with st.spinner(f"Synthesizing comparative matrix across {len(selected_papers)} papers..."):
        comp_result = generate_multi_paper_comparison(
            papers_list=selected_papers,
            comparison_dimension=selected_dimension,
            focus_query=focus_inquiry
        )
        st.session_state["last_comparison"] = {
            "text": comp_result,
            "papers": selected_papers,
            "dimension": selected_dimension,
            "focus": focus_inquiry.strip() if focus_inquiry else "",
            "created_at": time.time()
        }
        paper_names = " vs ".join([p['title'][:25] for p in selected_papers])
        log_user_activity(user_email, "Compare", selected_dimension, f"Compared: {paper_names}", comp_result, "")
        st.rerun()

# 6. Display Comparison Output
if "last_comparison" in st.session_state and st.session_state["last_comparison"]:
    curr = st.session_state["last_comparison"]
    
    display_comp = clean_academic_response(curr["text"])
    st.markdown(f"""
<div class="gemini-compare-view">

{display_comp}

</div>
""", unsafe_allow_html=True)
    
    # Action Row Directly Beneath Comparison
    col_act1, col_act2, col_act_spacer = st.columns([1.6, 1.8, 4.0])
    
    with col_act1:
        if st.button("💾 Save to Notes", key="cmp_btn_save", use_container_width=True, help="Save this comparison to your Personal Notes"):
            paper_titles_str = " vs ".join([p['title'][:18] for p in curr['papers']])
            saved = save_user_note(
                user_email=user_email,
                title=f"Comparison: {paper_titles_str}",
                content=curr["text"],
                notebook="Comparative Studies"
            )
            if saved:
                st.toast("✅ Comparative Study saved to Personal Notes!", icon="📝")
            else:
                st.error("Failed to save note.")
                
    with col_act2:
        if st.button("🗑️ Clear Chat", key="cmp_btn_clear", use_container_width=True, help="Clear this comparative study"):
            st.session_state["last_comparison"] = None
            st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopCmpEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopCmpEnd, ms));
        </script>
    """, height=0)

