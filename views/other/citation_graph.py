import streamlit as st
import networkx as nx
import plotly.graph_objects as go
import numpy as np
import time
import os
import re
import pymupdf
import google.generativeai as genai
from backend.database import get_user_documents, save_user_note, log_user_activity
from backend.config import MODEL_NAME
from backend.rag_pipeline import clean_academic_response

# Authentication check
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="Citation Graph | ResearchOS",
    page_icon="🕸️",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
        .block-container {
            max-width: 1100px;
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
        /* Metrics Banner */
        .metric-card {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 14px 16px;
            text-align: center;
        }
        .metric-val {
            font-size: 1.35rem;
            font-weight: 700;
            color: #60a5fa;
            line-height: 1.2;
        }
        .metric-lbl {
            font-size: 0.78rem;
            color: #94a3b8;
            font-weight: 500;
            margin-top: 2px;
        }
        /* Scoped Synthesis Container */
        .gemini-graph-view {
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 22px 24px !important;
            border-radius: 12px !important;
            margin-top: 16px;
            margin-bottom: 20px;
            font-size: 0.95rem;
            line-height: 1.7;
            color: #f1f5f9;
        }
        .gemini-graph-view p {
            line-height: 1.7 !important;
            margin-bottom: 0.85rem !important;
            color: #f1f5f9 !important;
        }
        .gemini-graph-view ul, 
        .gemini-graph-view ol {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            padding-left: 1.4rem !important;
        }
        .gemini-graph-view li {
            margin-bottom: 0.5rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        .gemini-graph-view li strong, 
        .gemini-graph-view p strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        .gemini-graph-view h1,
        .gemini-graph-view h2,
        .gemini-graph-view h3,
        .gemini-graph-view h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        .gemini-graph-view h3 {
            font-size: 1.15rem !important;
            color: #93c5fd !important;
        }
        .gemini-graph-view table,
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #334155 !important;
            font-size: 0.9rem !important;
        }
        .gemini-graph-view th,
        th {
            background-color: #0f172a !important;
            color: #60a5fa !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            border: 1px solid #334155 !important;
            text-align: left !important;
        }
        .gemini-graph-view td,
        td {
            padding: 9px 14px !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        .gemini-graph-view tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.4) !important;
        }
        /* Action Row Buttons */
        div[class*="st-key-cg_btn_"] button {
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
        div[class*="st-key-cg_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
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
    col_back_cg, col_title_cg = st.columns([1.5, 4.5])
    with col_back_cg:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_cg", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_cg:
        st.markdown("<h3 class='header-title'>🕸️ Citation & Knowledge Network Graph</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 class='header-title'>🕸️ Citation & Knowledge Network Graph</h3>", unsafe_allow_html=True)

st.markdown("<p class='header-subtitle'>Explore citation pathways, semantic similarity clusters, co-authorship networks, and intellectual lineage across your research library.</p>", unsafe_allow_html=True)

if not library:
    st.info("📚 No papers found in your library. Please upload papers to generate your interactive citation network graph.")
    if st.button("📤 Upload Papers", type="primary"):
        st.switch_page("views/papers/library.py")
    st.stop()

# Helper: Extract references from PDF (cached)
@st.cache_data(show_spinner=False, max_entries=32)
def extract_references_from_pdf(pdf_path: str, max_refs: int = 8) -> list[str]:
    """Extracts top cited reference titles from a paper's PDF."""
    if not pdf_path or not os.path.exists(pdf_path):
        return []
    citations = []
    try:
        doc = pymupdf.open(pdf_path)
        full_text = ""
        # Check last 3 pages where references usually appear
        start_page = max(0, len(doc) - 4)
        for p_idx in range(start_page, len(doc)):
            full_text += doc[p_idx].get_text() + "\n"
            
        ref_match = re.search(r'(?:REFERENCES|BIBLIOGRAPHY)\s*[\r\n]+(.*?)(?:\Z)', full_text, re.DOTALL | re.IGNORECASE)
        if ref_match:
            ref_block = ref_match.group(1)
            raw_citations = re.findall(r'\[\d+\]\s*(.*?)(?=\[\d+\]|\Z)', ref_block, re.DOTALL)
            for c in raw_citations[:max_refs]:
                clean_c = re.sub(r'\s+', ' ', c.strip())
                if len(clean_c) > 15:
                    citations.append(clean_c[:70] + ("..." if len(clean_c) > 70 else ""))
    except Exception:
        pass
    return citations

# Helper: AI Research Lineage Synthesis
def synthesize_lineage_pipeline(papers_list: list[dict], graph_mode: str) -> str:
    """Generates AI synthesis of research lineage and paradigm bridges across the graph."""
    papers_summary = "\n".join([
        f"- Title: {p['title']} | Domain: {p.get('domain', 'General')} | Year: {p.get('publication_year', 'N/A')} | Authors: {p.get('authors', 'Unknown')}"
        for p in papers_list
    ])
    
    prompt = f"""You are an elite academic historian of science, research director, and principal AI scientist.
Analyze the following connected research papers from a researcher's library and provide an insightful synthesis of their intellectual lineage, conceptual bridges, and research frontiers.

Library Papers:
{papers_summary}

Active Network Focus: {graph_mode}

REQUIRED OUTPUT STRUCTURE:

1. **🏛️ Foundational Intellectual Lineage**:
   - 2-3 paragraphs analyzing the core technical heritage, shared mathematical foundations, and evolutionary timeline connecting these works.

2. **🌉 Conceptual & Methodological Bridges**:
   - Identify key architectural, algorithmic, or domain synergies connecting different clusters in this library.

3. **📊 Cross-Paper Comparative Taxonomy**:
   Provide a clean Markdown table comparing the papers on core methodological axes:
| Paper Title | Core Architecture / Paradigm | Primary Benchmark / Dataset | Key Innovation |
| :--- | :--- | :--- | :--- |
| Paper 1 | Method 1 | Dataset 1 | Innovation 1 |
| Paper 2 | Method 2 | Dataset 2 | Innovation 2 |

4. **🔭 Unexplored Frontiers & Critical Knowledge Gaps**:
   - Point out 2-3 high-impact open research questions or unexplored intersections between these papers.

5. **🎯 Strategic Next-Read Recommendations**:
   - Suggest 2 foundational or emerging seminal papers the researcher should read next to complete this research graph.

Formatting Guidelines:
- Elite, authoritative academic prose.
- Never include self-introductions ("I am..."). Start directly with 🏛️ Foundational Intellectual Lineage."""

    model = genai.GenerativeModel(MODEL_NAME)
    res = model.generate_content(prompt)
    raw = res.text if res else ""
    return clean_academic_response(raw)

# ----------------- Controls Row -----------------
col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.6, 1.2, 1.2])

with col_ctrl1:
    graph_mode = st.selectbox(
        "Network Graph Mode",
        [
            "🌐 Semantic & Domain Similarity Network",
            "📚 Paper Citation & Reference Pathways",
            "👥 Co-Authorship & Research Lab Network"
        ],
        index=0,
        key="cg_mode_select"
    )

with col_ctrl2:
    layout_choice = st.selectbox(
        "Physics Layout",
        ["Force-Directed (Spring)", "Circular", "Kamada-Kawai", "Spectral"],
        index=0,
        key="cg_layout_select"
    )

with col_ctrl3:
    all_domains = sorted(list(set([p.get('domain', 'Other') for p in library if p.get('domain')])))
    domain_filter = st.selectbox(
        "Filter by Domain",
        ["All Domains"] + all_domains,
        index=0,
        key="cg_domain_filter"
    )

# Filter library
filtered_library = library if domain_filter == "All Domains" else [p for p in library if p.get('domain') == domain_filter]
if not filtered_library:
    filtered_library = library

# ----------------- Build NetworkX Graph -----------------
G = nx.Graph()

# Add Library Paper Nodes
domain_colors = {
    "Natural Language Processing (NLP)": "#38bdf8",
    "Computer Vision": "#818cf8",
    "Machine Learning": "#34d399",
    "Medical Informatics": "#f43f5e",
    "Robotics": "#fbbf24",
    "Cybersecurity": "#a78bfa",
    "Other": "#94a3b8"
}

for p in filtered_library:
    p_domain = p.get('domain', 'Other')
    p_color = domain_colors.get(p_domain, "#60a5fa")
    G.add_node(
        str(p['id']),
        title=p['title'],
        authors=p.get('authors', 'Unknown'),
        year=p.get('publication_year', 2024),
        domain=p_domain,
        node_type="paper",
        color=p_color,
        size=26,
        doc=p
    )

# Connect Edges based on mode
if graph_mode.startswith("🌐 Semantic"):
    for i, p1 in enumerate(filtered_library):
        for j, p2 in enumerate(filtered_library):
            if i < j:
                # Domain similarity
                if p1.get('domain') and p2.get('domain') and p1.get('domain') == p2.get('domain'):
                    G.add_edge(str(p1['id']), str(p2['id']), weight=1.0, relation=f"Shared Domain ({p1.get('domain')})")
                # Title / Tag overlap
                words1 = set(re.findall(r'\w{4,}', p1.get('title', '').lower()))
                words2 = set(re.findall(r'\w{4,}', p2.get('title', '').lower()))
                common = words1.intersection(words2)
                if len(common) >= 2:
                    G.add_edge(str(p1['id']), str(p2['id']), weight=1.2, relation=f"Thematic Overlap ({', '.join(list(common)[:2])})")

elif graph_mode.startswith("📚 Paper Citation"):
    ref_counter = 1
    for p in filtered_library:
        pdf_p = p.get('pdf_path', '')
        refs = extract_references_from_pdf(pdf_p, max_refs=4)
        for r_text in refs:
            ref_node_id = f"ref_{ref_counter}"
            G.add_node(
                ref_node_id,
                title=r_text,
                authors="Cited Reference",
                year="Historical",
                domain="Cited Foundation",
                node_type="reference",
                color="#fbbf24",
                size=16,
                doc=None
            )
            G.add_edge(str(p['id']), ref_node_id, weight=1.0, relation="Cites Reference")
            ref_counter += 1
            
    # Connect papers with shared domains
    for i, p1 in enumerate(filtered_library):
        for j, p2 in enumerate(filtered_library):
            if i < j and p1.get('domain') == p2.get('domain'):
                G.add_edge(str(p1['id']), str(p2['id']), weight=0.8, relation="Related Domain")

elif graph_mode.startswith("👥 Co-Authorship"):
    for i, p1 in enumerate(filtered_library):
        for j, p2 in enumerate(filtered_library):
            if i < j:
                a1 = set([a.strip().lower() for a in p1.get('authors', '').split(',') if a.strip()])
                a2 = set([a.strip().lower() for a in p2.get('authors', '').split(',') if a.strip()])
                shared = a1.intersection(a2)
                if shared:
                    G.add_edge(str(p1['id']), str(p2['id']), weight=2.0, relation=f"Co-Authored by {', '.join(list(shared)[:2])}")
                elif p1.get('domain') == p2.get('domain'):
                    G.add_edge(str(p1['id']), str(p2['id']), weight=0.5, relation="Same Domain")

# Ensure graph has at least minimal structure
if G.number_of_edges() == 0 and len(filtered_library) > 1:
    for i in range(len(filtered_library) - 1):
        G.add_edge(str(filtered_library[i]['id']), str(filtered_library[i+1]['id']), weight=1.0, relation="Library Association")

# Calculate Layout Positions
if layout_choice.startswith("Force"):
    pos = nx.spring_layout(G, k=0.6, iterations=60, seed=42)
elif layout_choice.startswith("Circular"):
    pos = nx.circular_layout(G)
elif layout_choice.startswith("Kamada"):
    pos = nx.kamada_kawai_layout(G)
else:
    pos = nx.spectral_layout(G)

# Compute Centrality
degree_dict = dict(G.degree())
top_node_id = max(degree_dict, key=degree_dict.get) if degree_dict else (str(filtered_library[0]['id']) if filtered_library else "N/A")
top_node_title = G.nodes[top_node_id].get('title', 'N/A') if top_node_id in G.nodes else 'N/A'

# ----------------- Metrics Banner -----------------
m_col1, m_col2, m_col3, m_col4 = st.columns(4)
with m_col1:
    st.markdown(f"<div class='metric-card'><div class='metric-val'>{G.number_of_nodes()}</div><div class='metric-lbl'>Active Nodes</div></div>", unsafe_allow_html=True)
with m_col2:
    st.markdown(f"<div class='metric-card'><div class='metric-val'>{G.number_of_edges()}</div><div class='metric-lbl'>Citation & Semantic Links</div></div>", unsafe_allow_html=True)
with m_col3:
    st.markdown(f"<div class='metric-card'><div class='metric-val'>{len(filtered_library)}</div><div class='metric-lbl'>Library Papers</div></div>", unsafe_allow_html=True)
with m_col4:
    density_pct = f"{(nx.density(G) * 100):.1f}%" if G.number_of_nodes() > 1 else "100%"
    st.markdown(f"<div class='metric-card'><div class='metric-val'>{density_pct}</div><div class='metric-lbl'>Graph Density</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ----------------- Build Plotly Interactive Graph -----------------
# 1. Edge Traces
edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,
    line=dict(width=1.5, color="rgba(148, 163, 184, 0.35)"),
    hoverinfo='none',
    mode='lines'
)

# 2. Node Traces
node_x = []
node_y = []
node_colors = []
node_sizes = []
node_hover_texts = []
node_display_labels = []

for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    
    n_info = G.nodes[node]
    n_type = n_info.get("node_type", "paper")
    n_title = n_info.get("title", "Untitled")
    n_domain = n_info.get("domain", "General")
    n_authors = n_info.get("authors", "Unknown")
    n_deg = G.degree(node)
    
    node_colors.append(n_info.get("color", "#38bdf8"))
    node_sizes.append(n_info.get("size", 24) + min(n_deg * 2, 10))
    
    # Short label for text display
    short_lbl = n_title[:20] + ("..." if len(n_title) > 20 else "")
    node_display_labels.append(short_lbl if n_type == "paper" else "")
    
    hover_str = (
        f"<b>{n_title}</b><br>"
        f"<b>Domain:</b> {n_domain}<br>"
        f"<b>Authors:</b> {n_authors}<br>"
        f"<b>Connections:</b> {n_deg} links"
    )
    node_hover_texts.append(hover_str)

node_trace = go.Scatter(
    x=node_x, y=node_y,
    mode='markers+text',
    hoverinfo='text',
    text=node_display_labels,
    textposition="bottom center",
    textfont=dict(size=11, color="#cbd5e1", family="sans-serif"),
    hovertext=node_hover_texts,
    marker=dict(
        showscale=False,
        color=node_colors,
        size=node_sizes,
        line=dict(width=2, color="#0f172a")
    )
)

fig = go.Figure(
    data=[edge_trace, node_trace],
    layout=go.Layout(
        showlegend=False,
        hovermode='closest',
        margin=dict(b=10, l=10, r=10, t=10),
        plot_bgcolor="#0f172a",
        paper_bgcolor="#0f172a",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=480
    )
)

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ----------------- Node Detail Inspector -----------------
st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
paper_options = {f"📄 {p['title']} (ID: {p['id']})": p for p in filtered_library}

col_insp1, col_insp2 = st.columns([2.0, 1.2])

with col_insp1:
    selected_inspect_label = st.selectbox(
        "🔍 Inspect Node in Network",
        list(paper_options.keys()),
        index=0,
        key="cg_inspect_select"
    )
    selected_p = paper_options[selected_inspect_label]

with col_insp2:
    st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        if st.button("💬 Chat with Paper", use_container_width=True, key="cg_btn_chat"):
            st.session_state['auto_select_paper_id'] = str(selected_p['id'])
            st.switch_page("views/ai/chat.py")
    with c_btn2:
        if st.button("📝 Summarize", use_container_width=True, key="cg_btn_summ"):
            st.switch_page("views/ai/summarize.py")

with st.container(border=True):
    d_c1, d_c2, d_c3 = st.columns([2.5, 1.5, 1.0])
    with d_c1:
        st.markdown(f"**Title:** {selected_p['title']}")
        st.markdown(f"**Authors:** `{selected_p.get('authors', 'Unknown')}`")
    with d_c2:
        st.markdown(f"**Domain:** `{selected_p.get('domain', 'Other')}`")
        st.markdown(f"**Venue / Publisher:** `{selected_p.get('journal_or_conference', 'IEEE / Academic')}`")
    with d_c3:
        st.markdown(f"**Year:** `{selected_p.get('publication_year', 'N/A')}`")
        st.markdown(f"**Connections:** `{G.degree(str(selected_p['id']))} links`")

# ----------------- AI Lineage Synthesis Pipeline -----------------
st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
btn_synth_lineage = st.button("✨ Synthesize Research Lineage & Knowledge Gaps", type="primary", use_container_width=True, key="btn_cg_synth")

if btn_synth_lineage:
    with st.spinner("Analyzing graph topology, intellectual lineage & paradigm bridges..."):
        synth_res = synthesize_lineage_pipeline(filtered_library, graph_mode)
        st.session_state["current_graph_synthesis"] = {
            "text": synth_res,
            "mode": graph_mode,
            "created_at": time.time()
        }
        log_user_activity(user_email, "Citation Graph", graph_mode, f"Citation: {graph_mode}", synth_res, "")
        st.rerun()

# ----------------- Display Synthesis Result -----------------
if "current_graph_synthesis" in st.session_state and st.session_state["current_graph_synthesis"]:
    curr_synth = st.session_state["current_graph_synthesis"]
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    st.markdown(f"""
<div class="gemini-graph-view">

{curr_synth["text"]}

</div>
""", unsafe_allow_html=True)
    
    # Action Row
    col_act1, col_act2, col_act_spacer = st.columns([1.8, 1.8, 4.0])
    
    with col_act1:
        if st.button("💾 Save to Notes", key="cg_btn_save", use_container_width=True, help="Save this research lineage synthesis to Personal Notes"):
            saved = save_user_note(
                user_email=user_email,
                title=f"Citation Lineage: {curr_synth['mode'][:30]}",
                content=f"# Research Lineage & Citation Synthesis: {curr_synth['mode']}\n\n{curr_synth['text']}",
                notebook="Research Lineage"
            )
            if saved:
                st.toast("✅ Lineage synthesis saved to Personal Notes!", icon="📝")
            else:
                st.error("Failed to save note.")
                
    with col_act2:
        if st.button("🗑️ Clear Synthesis", key="cg_btn_clear", use_container_width=True, help="Clear this synthesis"):
            st.session_state["current_graph_synthesis"] = None
            st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopCgEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopCgEnd, ms));
        </script>
    """, height=0)

