import streamlit as st
import time
from backend.database import get_user_documents, save_user_note, log_user_activity
from backend.rag_pipeline import generate_paper_summary, clean_academic_response

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="Summarizer | ResearchOS",
    page_icon="📝",
    layout="wide"
)

# Ultra-Modern Dark Glassmorphic Styling (Matching AI Chat Aesthetic)
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
        div[class*="st-key-focus_box_"] button,
        div[class*="st-key-mode_card_"] button {
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
        div[class*="st-key-focus_box_"] button:hover,
        div[class*="st-key-mode_card_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.15) !important;
        }
        div[class*="st-key-focus_box_"] button p,
        div[class*="st-key-mode_card_"] button p {
            font-size: 0.88rem !important;
            line-height: 1.35 !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: left !important;
            width: 100% !important;
            color: #cbd5e1 !important;
        }
        div[class*="st-key-focus_box_"] button strong,
        div[class*="st-key-mode_card_"] button strong {
            color: #f8fafc !important;
            font-size: 0.94rem !important;
            display: block !important;
            margin-bottom: 3px !important;
        }
        /* Scoped Gemini-Style Summary Response Typography */
        .gemini-summary-view {
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
        .gemini-summary-view p {
            line-height: 1.7 !important;
            margin-bottom: 0.85rem !important;
            color: #f1f5f9 !important;
        }
        .gemini-summary-view ul, 
        .gemini-summary-view ol {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            padding-left: 1.4rem !important;
        }
        .gemini-summary-view li {
            margin-bottom: 0.5rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        .gemini-summary-view li strong, 
        .gemini-summary-view p strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        .gemini-summary-view h1,
        .gemini-summary-view h2,
        .gemini-summary-view h3,
        .gemini-summary-view h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        .gemini-summary-view h3 {
            font-size: 1.15rem !important;
            color: #93c5fd !important;
        }
        .gemini-summary-view table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #334155 !important;
            font-size: 0.9rem !important;
        }
        .gemini-summary-view th {
            background-color: #0f172a !important;
            color: #60a5fa !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            border: 1px solid #334155 !important;
            text-align: left !important;
        }
        .gemini-summary-view td {
            padding: 9px 14px !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        .gemini-summary-view tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.4) !important;
        }
        .gemini-summary-view blockquote {
            border-left: 3px solid #60a5fa !important;
            background: rgba(59, 130, 246, 0.08) !important;
            padding: 10px 16px !important;
            border-radius: 0 8px 8px 0 !important;
            margin: 12px 0 !important;
            color: #cbd5e1 !important;
        }
        /* Action Row Buttons with Perfect Centering */
        div[class*="st-key-sum_btn_"] button {
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
        div[class*="st-key-sum_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        div[class*="st-key-sum_btn_"] button p,
        div[class*="st-key-sum_btn_"] button div {
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
    col_back_sum, col_title_sum = st.columns([1.5, 4.5])
    with col_back_sum:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_sum", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_sum:
        st.markdown("<h3 style='font-size:1.6rem; font-weight:700; color:#f8fafc; margin:0;'>📝 Summarizer</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 style='font-size:1.6rem; font-weight:700; color:#f8fafc; margin:0;'>📝 Summarizer</h3>", unsafe_allow_html=True)

st.markdown("<p style='color:#94a3b8; font-size:0.9rem; margin-top:3px; margin-bottom:16px;'>Generate structured, high-impact syntheses, technical deep-dives, and key takeaways for any paper in your library.</p>", unsafe_allow_html=True)

if not library:
    st.info("📚 No papers found in your library. Please upload a research paper first to generate summaries.")
    if st.button("📤 Go to Upload Papers", type="primary"):
        st.switch_page("views/papers/library.py")
    st.stop()

# Paper Options mapping
paper_dict = {f"📄 {p['title']} (ID: {p['id']})": p for p in library}
paper_options = list(paper_dict.keys())

# Check if a specific paper was pre-selected from History or Details
default_paper_idx = 0
target_id = st.session_state.pop('auto_select_paper_id', None) or st.session_state.pop('selected_paper_id', None)
if target_id:
    for idx, (p_label, p_data) in enumerate(paper_dict.items()):
        if str(p_data.get('id')) == str(target_id):
            default_paper_idx = idx
            st.session_state["sum_paper_select"] = p_label
            break

if "sum_paper_select" in st.session_state and st.session_state["sum_paper_select"] in paper_options:
    default_paper_idx = paper_options.index(st.session_state["sum_paper_select"])

# 2. Sleek Dual-Dropdown Toolbar (Matching AI Chat)
col_paper, col_mode = st.columns([2.3, 1.2])

summary_types = [
    "Executive Summary",
    "Technical Deep-Dive",
    "Key Empirical Results",
    "ELI5 (Intuitive Overview)",
    "Critical Gaps & Limitations"
]

# Check if a specific mode was triggered by card click
requested_mode = st.session_state.get("selected_sum_mode", "Executive Summary")
mode_default_idx = summary_types.index(requested_mode) if requested_mode in summary_types else 0

with col_paper:
    selected_paper_str = st.selectbox(
        "Select Research Paper",
        paper_options,
        index=default_paper_idx,
        placeholder="📄 Select a paper to summarize...",
        label_visibility="collapsed",
        key="sum_paper_select"
    )

selected_paper = paper_dict[selected_paper_str]

with col_mode:
    summary_type = st.selectbox(
        "Summary Mode",
        summary_types,
        index=mode_default_idx,
        label_visibility="collapsed",
        key="sum_mode_select"
    )

# 3. Streamlined Parameters Expander & Generate Action
with st.expander("⚙️ Length & Custom Focus Parameters", expanded=False):
    c_len, c_foc = st.columns([1, 1])
    with c_len:
        target_length = st.select_slider(
            "Target Length",
            options=["Concise (~150 words)", "Medium (~300 words)", "Detailed (~600 words)"],
            value="Medium (~300 words)"
        )
    with c_foc:
        focus_topic = st.text_input("Custom Focus Area (Optional)", placeholder="e.g. Attention weights, GPU speedup, loss convergence")

if 'target_length' not in locals():
    target_length = "Medium (~300 words)"
if 'focus_topic' not in locals():
    focus_topic = ""

btn_generate = st.button("✨ Generate AI Summary", type="primary", use_container_width=True)

# 4. Empty State Hero with 4 Blue Custom Focus Area Cards (When No Summary Yet)
if "last_summary" not in st.session_state or not st.session_state["last_summary"]:
    st.markdown("""
        <div class="empty-hero">
            <h2>Select a custom focus area to begin</h2>
            <p>Choose an instant analysis protocol or customize parameters above.</p>
        </div>
    """, unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔬 **Novel Methodology & Architecture**\n\nFocuses synthesis on core algorithms, neural mechanics, and novel system designs.", use_container_width=True, key="focus_box_1"):
            focus_topic = "Novel Methodology & Architecture"
            summary_type = "Technical Deep-Dive"
            btn_generate = True
        if st.button("📊 **Empirical Results & Benchmarks**\n\nFocuses synthesis on datasets, baselines, quantitative ablation metrics, and experimental performance.", use_container_width=True, key="focus_box_2"):
            focus_topic = "Empirical Results & Benchmark Performance"
            summary_type = "Key Empirical Results"
            btn_generate = True
    with c2:
        if st.button("📐 **Mathematical Formulations & Loss**\n\nFocuses synthesis on loss functions, equations, derivations, and theoretical proofs.", use_container_width=True, key="focus_box_3"):
            focus_topic = "Mathematical Formulations & Loss Functions"
            summary_type = "Technical Deep-Dive"
            btn_generate = True
        if st.button("⚠️ **Critical Gaps & Limitations**\n\nFocuses synthesis on assumptions, failure cases, scalability constraints, and open questions.", use_container_width=True, key="focus_box_4"):
            focus_topic = "Critical Limitations, Assumptions & Future Work"
            summary_type = "Critical Gaps & Limitations"
            btn_generate = True

# 5. Process Generation
if btn_generate:
    with st.spinner(f"Analyzing '{selected_paper['title']}' & synthesizing {summary_type}..."):
        try:
            summary_res = generate_paper_summary(
                paper_title=selected_paper["title"],
                doc_id=selected_paper["id"],
                summary_type=summary_type,
                target_length=target_length,
                focus_topic=focus_topic
            )
            st.session_state["last_summary"] = {
                "text": summary_res,
                "paper_title": selected_paper["title"],
                "doc_id": selected_paper["id"],
                "domain": selected_paper.get("domain", "Academic Research"),
                "mode": summary_type,
                "length": target_length,
                "created_at": time.time()
            }
            log_user_activity(user_email, "Summarizer", summary_type, f"Summary: {selected_paper['title']}", summary_res, selected_paper['id'])
            st.rerun()
        except Exception as e:
            st.error(f"⚠️ Synthesis error: {e}")
            if st.button("🔄 Retry Synthesis", type="primary"):
                st.rerun()

# 6. Display Generated Summary
if "last_summary" in st.session_state and st.session_state["last_summary"]:
    curr = st.session_state["last_summary"]
    
    display_summary = clean_academic_response(curr["text"])
    st.markdown(f"""
<div class="gemini-summary-view">

{display_summary}

</div>
""", unsafe_allow_html=True)
    
    # Action Row Directly Beneath Summary
    col_act1, col_act2, col_act_spacer = st.columns([1.6, 1.8, 4.0])
    
    with col_act1:
        if st.button("💾 Save to Notes", key="sum_btn_save", use_container_width=True, help="Save this summary to your Personal Notes"):
            saved = save_user_note(
                user_email=user_email,
                title=f"Summary: {curr['paper_title'][:30]}",
                content=curr["text"],
                notebook="Paper Summaries"
            )
            if saved:
                st.toast("✅ Summary saved to Personal Notes!", icon="📝")
            else:
                st.error("Failed to save note.")
                
    with col_act2:
        if st.button("🗑️ Clear Chat", key="sum_btn_clear", use_container_width=True, help="Clear this generated summary"):
            st.session_state["last_summary"] = None
            st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopSumEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopSumEnd, ms));
        </script>
    """, height=0)

