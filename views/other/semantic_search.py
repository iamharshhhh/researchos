import streamlit as st
import time
import re
import google.generativeai as genai
from backend.database import get_user_documents, save_user_note, log_user_activity
from backend.config import MODEL_NAME
from backend.db import search_documents
from backend.rag_pipeline import clean_academic_response, call_gemini_with_fallback

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="Semantic Search | ResearchOS",
    page_icon="🔍",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
        .block-container {
            max-width: 950px;
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
        /* Search Card Result */
        .search-chunk-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px 22px;
            margin-bottom: 18px;
            transition: all 0.2s ease-in-out;
        }
        .search-chunk-card:hover {
            border-color: #475569;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        }
        .chunk-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }
        .chunk-title {
            font-size: 1.05rem;
            font-weight: 600;
            color: #f8fafc;
            margin: 0;
            line-height: 1.35;
        }
        .chunk-badge {
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.3);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.78rem;
            font-weight: 600;
            white-space: nowrap;
        }
        .chunk-meta {
            font-size: 0.82rem;
            color: #94a3b8;
            margin-bottom: 12px;
        }
        .chunk-text {
            font-size: 0.93rem;
            line-height: 1.68;
            color: #e2e8f0;
            background: rgba(15, 23, 42, 0.45);
            border-left: 3px solid #3b82f6;
            padding: 12px 14px;
            border-radius: 0 8px 8px 0;
            margin-bottom: 14px;
        }
        /* Scoped Synthesis Container */
        .gemini-search-synth {
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 22px 24px !important;
            border-radius: 12px !important;
            margin-top: 16px;
            margin-bottom: 22px;
            font-size: 0.95rem;
            line-height: 1.7;
            color: #f1f5f9;
        }
        .gemini-search-synth p {
            line-height: 1.7 !important;
            margin-bottom: 0.85rem !important;
            color: #f1f5f9 !important;
        }
        .gemini-search-synth ul, 
        .gemini-search-synth ol {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            padding-left: 1.4rem !important;
        }
        .gemini-search-synth li {
            margin-bottom: 0.5rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        .gemini-search-synth li strong, 
        .gemini-search-synth p strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        .gemini-search-synth h1,
        .gemini-search-synth h2,
        .gemini-search-synth h3,
        .gemini-search-synth h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        .gemini-search-synth h3 {
            font-size: 1.15rem !important;
            color: #93c5fd !important;
        }
        /* Action Row Buttons */
        div[class*="st-key-sr_btn_"] button {
            height: 34px !important;
            min-height: 34px !important;
            max-height: 34px !important;
            border-radius: 6px !important;
            background-color: #0f172a !important;
            border: 1px solid #334155 !important;
            color: #cbd5e1 !important;
            font-size: 0.8rem !important;
            font-weight: 500 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 12px !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-sr_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #1e293b !important;
            color: #ffffff !important;
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
    col_back_sem, col_title_sem = st.columns([1.5, 4.5])
    with col_back_sem:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_sem", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_sem:
        st.markdown("<h3 class='header-title'>🔍 Semantic & Neural Search Engine</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 class='header-title'>🔍 Semantic & Neural Search Engine</h3>", unsafe_allow_html=True)

st.markdown("<p class='header-subtitle'>Perform dense vector similarity searches and cross-paper passage retrieval directly across your indexed research library.</p>", unsafe_allow_html=True)

if not library:
    st.info("📚 No papers found in your library. Please upload papers to enable semantic search.")
    if st.button("📤 Upload Papers", type="primary"):
        st.switch_page("views/papers/library.py")
    st.stop()

# Helper: AI Search Answer Synthesis
def synthesize_search_answer(query_str: str, retrieved_chunks: list[dict]) -> str:
    """Invokes Gemini to synthesize a direct, cited answer using retrieved vector passages."""
    passages_text = "\n\n".join([
        f"[Passage {i+1}] (Paper: '{c['paper_title']}', Domain: {c['domain']}):\n{c['text']}"
        for i, c in enumerate(retrieved_chunks)
    ])
    
    prompt = f"""You are an elite academic research assistant.
Based EXCLUSIVELY on the retrieved text passages from the user's research library, provide a thorough, authoritative, and direct answer to the user's inquiry.

User Research Inquiry:
"{query_str}"

Retrieved Library Passages:
{passages_text}

REQUIRED OUTPUT STRUCTURE:

1. **💡 Comprehensive Direct Synthesis**:
   - Provide a 2-3 paragraph deep-dive answer addressing the query.
   - Use precise citations like [Paper: Title] whenever citing factual claims from the retrieved passages.

2. **📊 Core Methodological Takeaways**:
   - Bulleted summary of algorithms, datasets, performance gains, or equations mentioned in the passages.

3. **🔬 Cross-Paper Comparison & Synergies (if multiple papers retrieved)**:
   - Contrast how different papers address this problem or describe complementary approaches.

Formatting Guidelines:
- Elite, publication-grade academic prose.
- Format all equations and mathematical variables in LaTeX ($...$).
- Never start with self-introductions ("I am..."). Start directly with 💡 Comprehensive Direct Synthesis."""

    raw = call_gemini_with_fallback(prompt)
    return clean_academic_response(raw)

# Helper: Auto-detect Quick-Search Topics from Library with AI (Cached)
@st.cache_data(show_spinner=False, max_entries=16)
def generate_dynamic_search_topics(papers_info: tuple) -> list[str]:
    """Uses Gemini to analyze papers in the library and generate 5 specific search topic queries."""
    if not papers_info:
        return [
            "Attention Mechanisms & Transformers",
            "Medical Report Simplification",
            "Chest X-Ray Pathology Detection",
            "Retrieval-Augmented Generation",
            "Loss Functions & Performance Metrics"
        ]
    
    titles_summary = "\n".join([f"- {t} (Domain: {d})" for t, d in papers_info[:10]])
    prompt = f"""You are a research taxonomy specialist.
Analyze the following papers from a researcher's personal library:

{titles_summary}

Generate exactly 5 distinct, high-impact, specific search topic queries that the researcher would realistically search for across these papers.
Each topic should be crisp, academic, and under 5-8 words.

Output ONLY the 5 topics as a clean numbered list:
1. Topic 1
2. Topic 2
3. Topic 3
4. Topic 4
5. Topic 5"""

    try:
        text = call_gemini_with_fallback(prompt)
        topics = []
        for line in text.split("\n"):
            line = re.sub(r'^\d+[\.\)]\s*', '', line.strip())
            line = re.sub(r'[\*\"\_]', '', line).strip()
            if line and len(line) > 3:
                topics.append(line)
        if len(topics) >= 3:
            return topics[:5]
    except Exception:
        pass
    
    # Fallback from paper titles directly
    fallback = []
    for t, _ in papers_info[:5]:
        clean_t = t.split(':')[0].split('-')[0].strip()
        if clean_t:
            fallback.append(clean_t[:35])
    return fallback if fallback else ["General Deep Learning", "Model Architecture", "Empirical Evaluation"]

# ----------------- AI Auto-Detected Quick-Search Topics -----------------
st.markdown("<p style='font-size:0.8rem; color:#94a3b8; font-weight:600; margin:0 0 6px 0;'>⚡ AUTO-DETECTED TOPICS</p>", unsafe_allow_html=True)

# Cache key tuple of (title, domain)
papers_tuple = tuple((p.get('title', ''), p.get('domain', 'Other')) for p in library)
preset_tags = generate_dynamic_search_topics(papers_tuple)

t_cols = st.columns(min(len(preset_tags), 5))
for i, tag in enumerate(preset_tags[:5]):
    with t_cols[i]:
        # Clean label for button
        btn_label = tag.split('&')[0].split('for')[0].strip()
        if len(btn_label) > 28:
            btn_label = btn_label[:26] + ".."
        if st.button(btn_label, key=f"sr_tag_{i}", use_container_width=True, help=f"Search for: {tag}"):
            st.session_state['sem_search_query_input'] = tag
            st.rerun()

# ----------------- Search Toolbar -----------------
st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

search_val = st.session_state.pop('search_input_prefill', None) or st.session_state.get('sem_search_query_input', '')

col_q, col_btn = st.columns([4.0, 1.0])
with col_q:
    search_query = st.text_input(
        "Search Query",
        value=search_val,
        placeholder="Enter research concept, query, or algorithm (e.g. 'How does self-attention work?', 'Loss formulations')...",
        label_visibility="collapsed",
        key="sem_search_box"
    )
with col_btn:
    btn_search = st.button("🔍 Search", type="primary", use_container_width=True, key="btn_run_sem_search")

# ----------------- AI Auto-Detected Domain Filter -----------------
col_f1, col_f2, col_f3 = st.columns([1.5, 1.5, 1.0])

with col_f1:
    # Auto-detect domains and sub-domains from all papers in library
    raw_domains = set()
    for p in library:
        d = p.get('domain', '').strip()
        if d and d != "Other":
            raw_domains.add(d)
        if p.get('tags'):
            for tag in p['tags'].split(','):
                tag_c = tag.strip()
                if len(tag_c) > 2 and tag_c.lower() not in ["paper", "research", "pdf"]:
                    raw_domains.add(tag_c.title())
                    
    if not raw_domains:
        raw_domains = {"Natural Language Processing (NLP)", "Medical Informatics", "Machine Learning", "Computer Vision"}
        
    all_domains = sorted(list(raw_domains))
    sel_domain = st.selectbox(
        "Domain Filter",
        ["All Domains"] + all_domains,
        index=0,
        key="sem_domain_filter"
    )

with col_f2:
    paper_filter_map = {"All Library Papers": None}
    for p in library:
        paper_filter_map[f"📄 {p['title'][:40]}... (ID: {p['id']})"] = p['id']
        
    sel_paper_label = st.selectbox(
        "Target Paper Filter",
        list(paper_filter_map.keys()),
        index=0,
        key="sem_paper_filter"
    )
    target_doc_id = paper_filter_map[sel_paper_label]

with col_f3:
    top_k = st.slider("Top Chunks", min_value=3, max_value=10, value=5, step=1, key="sem_top_k")

# Execute Search
if (btn_search or search_query.strip()) and search_query.strip():
    with st.spinner("Searching ChromaDB neural vector index & ranking passages..."):
        # Apply paper filter if chosen
        filter_ids = [target_doc_id] if target_doc_id else None
        
        # Search ChromaDB
        raw_results = search_documents(
            query=search_query.strip(),
            n_results=top_k * 2 if sel_domain != "All Domains" else top_k,
            filter_doc_ids=filter_ids
        )
        
        log_user_activity(user_email, "Semantic Search", "Search Query", f"Searched: '{search_query.strip()}'", f"Domain: {sel_domain}", str(target_doc_id or 'all'))
        
        # Build structured results list
        paper_dict = {str(p['id']): p for p in library}
        processed_chunks = []
        
        if raw_results and "documents" in raw_results and len(raw_results["documents"]) > 0:
            docs = raw_results["documents"][0]
            metas = raw_results.get("metadatas", [[]])[0]
            dists = raw_results.get("distances", [[0.5] * len(docs)])[0]
            
            for doc_text, meta, dist in zip(docs, metas, dists):
                doc_id = str(meta.get("doc_id", ""))
                p_info = paper_dict.get(doc_id, {})
                
                # Apply domain filter if selected
                if sel_domain != "All Domains" and p_info.get("domain") != sel_domain:
                    continue
                    
                # Convert cosine distance to relevance percentage
                # Normalized similarity: 1 - (dist / 2) or standard cosine similarity
                rel_score = max(50, min(99, int((1.0 - (dist / 2.0)) * 100)))
                
                processed_chunks.append({
                    "text": doc_text.strip(),
                    "paper_id": doc_id,
                    "paper_title": p_info.get("title", meta.get("title", f"Paper {doc_id}")),
                    "authors": p_info.get("authors", "Unknown"),
                    "domain": p_info.get("domain", "Computer Science"),
                    "year": p_info.get("publication_year", "N/A"),
                    "page": meta.get("page", 1),
                    "score": rel_score
                })
                
                if len(processed_chunks) >= top_k:
                    break
                    
        st.session_state["sem_search_results"] = {
            "query": search_query.strip(),
            "chunks": processed_chunks,
            "created_at": time.time()
        }
        log_user_activity(user_email, "Semantic Search", "Neural Vector Search", f"Search: {search_query.strip()}", f"Retrieved {len(processed_chunks)} relevant passage chunks", None)

# ----------------- Display Search Results -----------------
if "sem_search_results" in st.session_state and st.session_state["sem_search_results"]:
    sr = st.session_state["sem_search_results"]
    chunks_list = sr.get("chunks", [])
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    if not chunks_list:
        st.info(f"No matching passages found for '{sr['query']}'. Try adjusting your search query or domain filters.")
    else:
        # Header with Match Summary & AI Synthesis Trigger
        col_res_hdr, col_res_btn = st.columns([2.2, 1.8])
        with col_res_hdr:
            st.markdown(f"<p style='font-size:0.95rem; color:#94a3b8; margin:6px 0 0 0;'>Showing <b>{len(chunks_list)}</b> highly relevant passage chunks for <i>'{sr['query']}'</i></p>", unsafe_allow_html=True)
        with col_res_btn:
            btn_synth_answer = st.button("✨ Synthesize Direct Answer with AI", type="primary", use_container_width=True, key="btn_synth_search_ans")
            
        if btn_synth_answer:
            with st.spinner("Synthesizing multi-paper direct answer using retrieved passages..."):
                synth_text = synthesize_search_answer(sr['query'], chunks_list)
                st.session_state["current_search_synthesis"] = {
                    "text": synth_text,
                    "query": sr['query'],
                    "created_at": time.time()
                }
                st.rerun()

        # Display AI Direct Answer Synthesis (if generated)
        if "current_search_synthesis" in st.session_state and st.session_state["current_search_synthesis"]:
            curr_synth = st.session_state["current_search_synthesis"]
            st.markdown(f"""
<div class="gemini-search-synth">

<p style="font-size:0.8rem; color:#38bdf8; font-weight:700; text-transform:uppercase; margin-bottom:6px;">Direct AI Synthesis for: "{curr_synth['query']}"</p>

{curr_synth["text"]}

</div>
""", unsafe_allow_html=True)
            
            col_s1, col_s2, col_s_sp = st.columns([1.8, 1.8, 4.0])
            with col_s1:
                if st.button("💾 Save to Notes", key="sr_btn_save_synth", use_container_width=True):
                    saved = save_user_note(
                        user_email=user_email,
                        title=f"Search Synthesis: {curr_synth['query'][:30]}",
                        content=f"# Search Synthesis: {curr_synth['query']}\n\n{curr_synth['text']}",
                        notebook="Search Syntheses"
                    )
                    if saved:
                        st.toast("✅ Search synthesis saved to Personal Notes!", icon="📝")
            with col_s2:
                if st.button("🗑️ Dismiss Answer", key="sr_btn_clear_synth", use_container_width=True):
                    st.session_state["current_search_synthesis"] = None
                    st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Render Passage Cards
        for idx, chunk in enumerate(chunks_list):
            score_color = "#34d399" if chunk["score"] >= 85 else "#38bdf8"
            
            st.markdown(f"""
<div class="search-chunk-card">
    <div class="chunk-header">
        <h4 class="chunk-title">📄 {chunk['paper_title']}</h4>
        <span class="chunk-badge" style="color: {score_color}; border-color: {score_color};">{chunk['score']}% Match</span>
    </div>
    <div class="chunk-meta">
        <b>Domain:</b> {chunk['domain']} • <b>Authors:</b> {chunk['authors'][:45]}... • <b>Year:</b> {chunk['year']} • <b>Page:</b> {chunk['page']}
    </div>
    <div class="chunk-text">
        "{chunk['text']}"
    </div>
</div>
""", unsafe_allow_html=True)
            
            # Action buttons for this chunk
            btn_col1, btn_col2, btn_sp = st.columns([1.6, 1.6, 4.0])
            with btn_col1:
                if st.button("💬 Chat with Paper", key=f"sr_btn_chat_{idx}", use_container_width=True):
                    st.session_state['auto_select_paper_id'] = str(chunk['paper_id'])
                    st.switch_page("views/ai/chat.py")
            with btn_col2:
                if st.button("📝 Summarize Paper", key=f"sr_btn_sum_{idx}", use_container_width=True):
                    st.switch_page("views/ai/summarize.py")
            
            st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)

    st.info("👆 Type a query in the search box above to begin searching across your papers.")

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopSemEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopSemEnd, ms));
        </script>
    """, height=0)
