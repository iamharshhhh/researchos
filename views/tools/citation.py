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
    page_title="AI Citation Generator | ResearchOS",
    page_icon="🔖",
    layout="wide"
)

# Ultra-Modern Dark Glassmorphic Styling (Matching AI Chat, Summarizer & Compare Aesthetic)
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
        /* Citation Display Card */
        .ai-citation-box {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 24px 26px !important;
            margin-top: 18px;
            margin-bottom: 18px;
            font-size: 0.96rem;
            line-height: 1.7;
            color: #f1f5f9;
        }
        .ai-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(59, 130, 246, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 9999px;
            padding: 4px 12px;
            font-size: 0.78rem;
            font-weight: 600;
            color: #60a5fa;
            margin-bottom: 12px;
        }
        /* Action Row Buttons with Perfect Centering */
        div[class*="st-key-cite_btn_"] button {
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
        div[class*="st-key-cite_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        div[class*="st-key-cite_btn_"] button p,
        div[class*="st-key-cite_btn_"] button div {
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
    col_back_cite, col_title_cite = st.columns([1.5, 4.5])
    with col_back_cite:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_cite", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_cite:
        st.markdown("<h3 class='header-title'>🔖 AI Citation Generator</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 class='header-title'>🔖 AI Citation Generator</h3>", unsafe_allow_html=True)

st.markdown("<p class='header-subtitle'>Synthesize authoritative, standard academic citations directly from paper text and context using Gemini AI.</p>", unsafe_allow_html=True)

# Citation Style Options
citation_styles = [
    "APA (7th Edition)",
    "IEEE (Computer Science & Engineering)",
    "MLA (9th Edition)",
    "Chicago (Author-Date, 17th Ed.)",
    "Harvard Style",
    "BibTeX (LaTeX / Overleaf)",
    "RIS (Zotero / Mendeley / EndNote)",
    "Nature / Science Journal Style",
    "ACM Reference Format"
]

# Tabs for Mode: Library Paper vs. Custom Text/Title/DOI
tab_library, tab_custom = st.tabs(["📚 From Library Paper", "✍️ Raw Text, Title or DOI"])

# Function to run AI citation generation
def generate_ai_citation_pipeline(title: str, doc_id: str = None, style: str = "APA (7th Edition)", custom_text: str = "", extra_instructions: str = "") -> str:
    context_str = ""
    if doc_id:
        # Pull authentic text chunks from ChromaDB for this document
        try:
            results = search_documents(
                query="title authors publication year conference journal venue volume doi publisher abstract citation",
                n_results=5,
                filter_doc_ids=[doc_id]
            )
            chunks = results.get("documents", [[]])[0] if results and "documents" in results else []
            context_str = "\n---\n".join(chunks)
        except Exception:
            context_str = ""
            
    if custom_text:
        context_str += f"\n\nAdditional Paper Content / Abstract:\n{custom_text}"

    prompt = f"""You are a world-class academic citation generator.
Your task is to analyze the provided research paper content and synthesize an authoritative, exact academic citation in the requested style.

Target Citation Style: {style}
Paper Title / Information: {title}

Extracted Paper Text & Excerpts:
{context_str if context_str else "Use authoritative academic knowledge for this published paper title."}

Specific User Instructions:
{extra_instructions if extra_instructions else "None"}

Rules:
1. Infer or extract all complete author names, publication year, conference/journal name, volume/issue/pages (if applicable), publisher, and DOI.
2. Format the output strictly according to the official rules of {style}.
3. If BibTeX is requested, output a clean, valid `@inproceedings` or `@article` entry.
4. If RIS is requested, output standard RIS tags (`TY  - `, `TI  - `, `AU  - `, `ER  - `).
5. Do NOT include any conversational commentary, introductory text (e.g. "Here is the citation:"), or explanatory notes. Output ONLY the citation."""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    raw = response.text if response else ""
    return clean_academic_response(raw)

# ----------------- TAB 1: Library Paper -----------------
with tab_library:
    st.markdown("<p style='font-size:0.88rem; color:#94a3b8; margin-bottom:8px;'>Select a paper from your library to generate an exact academic citation.</p>", unsafe_allow_html=True)
    
    if not library:
        st.info("📚 No papers found in your library. Please upload research papers first or use the 'Raw Text, Title or DOI' tab.")
    else:
        paper_map = {f"📄 {p['title']} (ID: {p['id']})": p for p in library}
        paper_options = list(paper_map.keys())

        default_cite_idx = 0
        if 'selected_paper_id' in st.session_state and st.session_state['selected_paper_id']:
            target_id = str(st.session_state['selected_paper_id'])
            for idx, (p_label, p_data) in enumerate(paper_map.items()):
                if str(p_data.get('id')) == target_id:
                    default_cite_idx = idx
                    break

        col_p, col_s = st.columns([2.2, 1.3])
        with col_p:
            selected_paper_label = st.selectbox(
                "Select Paper",
                paper_options,
                index=default_cite_idx,
                label_visibility="collapsed",
                key="ai_cite_lib_paper"
            )
        with col_s:
            selected_style = st.selectbox(
                "Citation Style",
                citation_styles,
                index=0,
                label_visibility="collapsed",
                key="ai_cite_lib_style"
            )

        selected_paper = paper_map.get(selected_paper_label, list(paper_map.values())[0] if paper_map else {})

        with st.expander("⚙️ Optional Custom Formatting Instructions", expanded=False):
            extra_instructions = st.text_input(
                "Custom Prompt / Instruction",
                placeholder="e.g. Include DOI link, abbreviate first names, or format for arXiv preprint",
                key="ai_cite_lib_extra"
            )

        if st.button("✨ Cite", type="primary", use_container_width=True, key="btn_gen_ai_lib"):
            with st.spinner(f"Analyzing '{selected_paper['title']}' & generating {selected_style} citation with Gemini..."):
                cite_text = generate_ai_citation_pipeline(
                    title=selected_paper["title"],
                    doc_id=selected_paper["id"],
                    style=selected_style,
                    extra_instructions=extra_instructions
                )
                st.session_state["current_ai_citation"] = {
                    "text": cite_text,
                    "paper_title": selected_paper["title"],
                    "style": selected_style,
                    "created_at": time.time()
                }
                log_user_activity(user_email, "Citation Generator", selected_style, f"Citation: {selected_paper['title']}", cite_text, selected_paper['id'])
                st.rerun()

# ----------------- TAB 2: Custom Text / DOI / Title -----------------
with tab_custom:
    st.markdown("<p style='font-size:0.88rem; color:#94a3b8; margin-bottom:8px;'>Generate citations for any paper outside your library by providing its title, DOI, or abstract.</p>", unsafe_allow_html=True)
    
    col_t, col_st = st.columns([2.2, 1.3])
    with col_t:
        custom_title = st.text_input("Paper Title or DOI", placeholder="e.g. Attention Is All You Need or 10.1145/3308558.3313562", key="ai_cite_cust_title")
    with col_st:
        custom_style = st.selectbox("Citation Style", citation_styles, index=0, label_visibility="collapsed", key="ai_cite_cust_style")
        
    custom_abstract = st.text_area("Paper Excerpt / Abstract (Optional)", placeholder="Paste paper abstract, authors, or text to provide extra context...", height=90, key="ai_cite_cust_abs")
    
    if st.button("✨ Cite", type="primary", use_container_width=True, key="btn_gen_ai_cust"):
        if not custom_title.strip() and not custom_abstract.strip():
            st.warning("Please enter a paper title, DOI, or text snippet.")
        else:
            with st.spinner(f"Synthesizing {custom_style} citation with Gemini..."):
                cite_text = generate_ai_citation_pipeline(
                    title=custom_title.strip() if custom_title.strip() else "Academic Paper",
                    doc_id=None,
                    style=custom_style,
                    custom_text=custom_abstract.strip()
                )
                st.session_state["current_ai_citation"] = {
                    "text": cite_text,
                    "paper_title": custom_title.strip() if custom_title.strip() else "Academic Paper",
                    "style": custom_style,
                    "created_at": time.time()
                }
                st.rerun()

# ----------------- Output Display -----------------
if "current_ai_citation" in st.session_state and st.session_state["current_ai_citation"]:
    curr = st.session_state["current_ai_citation"]
    raw_citation = curr["text"]
    style_name = curr["style"]
    
    # Determine code highlight language
    if "BibTeX" in style_name:
        code_lang = "bibtex"
    elif "RIS" in style_name:
        code_lang = "text"
    else:
        code_lang = "markdown"

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown(f"""
            <div style="display:flex; justify-content:flex-end; align-items:center; margin-bottom:8px;">
                <div style="font-size:0.82rem; color:#94a3b8;">🏷️ <b>Format:</b> <span style="color:#60a5fa;">{style_name}</span></div>
            </div>
        """, unsafe_allow_html=True)
        
        st.code(raw_citation, language=code_lang)

    # Action Row Directly Beneath Citation
    col_act1, col_act2, col_act3, col_spacer = st.columns([1.6, 1.8, 1.6, 2.5])

    with col_act1:
        if st.button("💾 Save to Notes", key="cite_btn_save", use_container_width=True, help="Save citation to your Personal Notes"):
            saved = save_user_note(
                user_email=user_email,
                title=f"Citation ({style_name[:12]}): {curr['paper_title'][:25]}",
                content=raw_citation,
                notebook="Paper Citations"
            )
            if saved:
                st.toast("✅ Citation saved to Personal Notes!", icon="📝")
            else:
                st.error("Failed to save note.")

    with col_act2:
        file_ext = "bib" if "BibTeX" in style_name else ("ris" if "RIS" in style_name else "txt")
        safe_title = re.sub(r'[^a-zA-Z0-9_]', '_', curr['paper_title'][:30].lower())
        
        st.download_button(
            label=f"⬇️ Download .{file_ext}",
            data=raw_citation,
            file_name=f"{safe_title}_citation.{file_ext}",
            mime="text/plain",
            use_container_width=True,
            key="cite_btn_download"
        )

    with col_act3:
        if st.button("🗑️ Clear", key="cite_btn_clear", use_container_width=True, help="Clear this citation"):
            st.session_state["current_ai_citation"] = None
            st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopCiteEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopCiteEnd, ms));
        </script>
    """, height=0)
