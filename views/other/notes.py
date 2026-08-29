import streamlit as st
import time
import math
import re
import google.generativeai as genai
from backend.database import get_user_notes, save_user_note, update_user_note, delete_user_note, log_user_activity
from backend.config import MODEL_NAME
from backend.rag_pipeline import clean_academic_response, call_gemini_with_fallback

# Authentication check
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="Notes | ResearchOS",
    page_icon="📝",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
        .block-container {
            max-width: 1120px;
            padding-top: 1.5rem;
            padding-bottom: 3.5rem;
            margin: 0 auto;
        }
        .header-title {
            font-size: 1.65rem;
            font-weight: 700;
            color: #f8fafc;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .header-subtitle {
            color: #94a3b8;
            font-size: 0.9rem;
            margin-top: 4px;
            margin-bottom: 18px;
        }
        /* Top Action Button */
        div[class*="st-key-nt_btn_create"] button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3) !important;
            height: 40px !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-nt_btn_create"] button:hover {
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
            transform: translateY(-1px) !important;
        }
        /* Note List Cards */
        .note-card-box {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 8px;
            transition: all 0.2s ease-in-out;
        }
        .note-card-box:hover {
            border-color: #60a5fa;
            background: rgba(36, 52, 77, 0.9);
            transform: translateX(2px);
        }
        .note-card-box-active {
            border-color: #3b82f6 !important;
            background: rgba(59, 130, 246, 0.15) !important;
            box-shadow: inset 3px 0 0 #3b82f6;
        }
        /* Scoped Rendered Reader */
        .note-reader-canvas {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 26px 30px !important;
            min-height: 480px;
            color: #f1f5f9;
            font-size: 0.95rem;
            line-height: 1.75;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        }
        .note-reader-canvas h1, .note-reader-canvas h2, .note-reader-canvas h3, .note-reader-canvas h4 {
            color: #f8fafc !important;
            font-weight: 700 !important;
            margin-top: 1.3rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        .note-reader-canvas h1 { font-size: 1.45rem !important; }
        .note-reader-canvas h2 { font-size: 1.25rem !important; color: #93c5fd !important; }
        .note-reader-canvas h3 { font-size: 1.1rem !important; color: #bae6fd !important; }
        .note-reader-canvas p {
            line-height: 1.75 !important;
            margin-bottom: 0.9rem !important;
            color: #f1f5f9 !important;
        }
        .note-reader-canvas ul, .note-reader-canvas ol {
            padding-left: 1.4rem !important;
            margin-bottom: 1rem !important;
        }
        .note-reader-canvas li {
            margin-bottom: 0.45rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        .note-reader-canvas li strong, .note-reader-canvas p strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        .note-reader-canvas blockquote {
            border-left: 4px solid #3b82f6 !important;
            background: rgba(15, 23, 42, 0.5) !important;
            padding: 10px 16px !important;
            border-radius: 0 8px 8px 0 !important;
            margin: 14px 0 !important;
            color: #cbd5e1 !important;
            font-style: italic !important;
        }
        .note-reader-canvas table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #334155 !important;
        }
        .note-reader-canvas th {
            background-color: #0f172a !important;
            color: #60a5fa !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            border: 1px solid #334155 !important;
        }
        .note-reader-canvas td {
            padding: 9px 14px !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        .note-reader-canvas tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.4) !important;
        }
        /* Action Row Buttons */
        div[class*="st-key-nt_btn_"] button {
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            border-radius: 8px !important;
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #cbd5e1 !important;
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            padding: 0 14px !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-nt_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        div[class*="st-key-nt_btn_ai_polish"] button {
            background: linear-gradient(135deg, rgba(129, 140, 248, 0.15) 0%, rgba(99, 102, 241, 0.2) 100%) !important;
            border-color: rgba(129, 140, 248, 0.4) !important;
            color: #c7d2fe !important;
        }
        div[class*="st-key-nt_btn_ai_polish"] button:hover {
            border-color: #818cf8 !important;
            color: #ffffff !important;
            box-shadow: 0 4px 14px rgba(129, 140, 248, 0.25) !important;
        }
    </style>
""", unsafe_allow_html=True)

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
    col_back_nt, col_title_nt = st.columns([1.5, 4.5])
    with col_back_nt:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_notes", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_nt:
        st.markdown("<h3 class='header-title'>📝 Research Notes & Knowledge Vault</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 class='header-title'>📝 Research Notes & Knowledge Vault</h3>", unsafe_allow_html=True)

st.markdown("<p class='header-subtitle'>Unified knowledge vault for synthesized literature notes, mathematical breakdowns, quiz reviews, figure analyses, and reflections across all tabs.</p>", unsafe_allow_html=True)

# Helper: AI Polish Note
def polish_note_with_ai(title: str, content: str) -> str:
    """Uses Gemini to structure, clarify, and format personal research notes into publication-grade markdown."""
    prompt = f"""You are an elite academic editor and principal research scientist.
Refine and enhance the following research note while strictly preserving all factual equations, citations, and takeaways.

Note Title: {title}
Original Content:
{content}

Instructions:
- Improve clarity, conciseness, and academic rigor.
- Format with clean Markdown headers, bullet points, and LaTeX equations ($...$ or $$...$$).
- Correct any typographical or mathematical formatting inconsistencies.
- Return ONLY the improved note content without any conversational commentary."""

    raw = call_gemini_with_fallback(prompt)
    return clean_academic_response(raw)

# All Recognized Notebook Categories across the OS
NOTEBOOK_COLOR_MAP = {
    "AI Chat Notes": {"color": "#38bdf8", "bg": "rgba(56, 189, 248, 0.12)", "border": "rgba(56, 189, 248, 0.3)"},
    "Paper Summaries": {"color": "#34d399", "bg": "rgba(52, 211, 153, 0.12)", "border": "rgba(52, 211, 153, 0.3)"},
    "Mathematical Formulations": {"color": "#a78bfa", "bg": "rgba(167, 139, 250, 0.12)", "border": "rgba(167, 139, 250, 0.3)"},
    "Figure Analyses": {"color": "#fbbf24", "bg": "rgba(251, 191, 36, 0.12)", "border": "rgba(251, 191, 36, 0.3)"},
    "Paper Quizzes": {"color": "#f43f5e", "bg": "rgba(244, 63, 94, 0.12)", "border": "rgba(244, 63, 94, 0.3)"},
    "Paper Citations": {"color": "#f97316", "bg": "rgba(249, 115, 22, 0.12)", "border": "rgba(249, 115, 22, 0.3)"},
    "Research Lineage": {"color": "#818cf8", "bg": "rgba(129, 140, 248, 0.12)", "border": "rgba(129, 140, 248, 0.3)"},
    "Search Syntheses": {"color": "#2dd4bf", "bg": "rgba(45, 212, 191, 0.12)", "border": "rgba(45, 212, 191, 0.3)"},
    "Personal Ideas & Reflections": {"color": "#ec4899", "bg": "rgba(236, 72, 153, 0.12)", "border": "rgba(236, 72, 153, 0.3)"},
    "General": {"color": "#94a3b8", "bg": "rgba(148, 163, 184, 0.12)", "border": "rgba(148, 163, 184, 0.3)"}
}

NOTEBOOK_LIST = list(NOTEBOOK_COLOR_MAP.keys())[:-1]  # Exclude General fallback from selector
NOTEBOOK_CATEGORIES = ["🌟 All Notebooks"] + [f"🏷️ {k}" for k in NOTEBOOK_LIST]

# Fetch user notes
all_notes = get_user_notes(user_email)

# ----------------- Two Column Main Layout -----------------
col_sidebar, col_main = st.columns([3.3, 6.7], gap="large")

with col_sidebar:
    # Action Bar: Create Note
    if st.button("➕ New Note", type="primary", use_container_width=True, key="nt_btn_create"):
        st.session_state['active_note_id'] = "new"
        st.session_state['note_mode'] = "edit"
        st.rerun()

    st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
    
    # Filter by Notebook Category
    selected_category = st.selectbox(
        "Filter by Notebook",
        NOTEBOOK_CATEGORIES,
        index=0,
        key="nt_notebook_filter"
    )
    
    # Search Notes by Keyword
    search_keyword = st.text_input(
        "Search Notes",
        placeholder="Filter by title or keyword...",
        label_visibility="collapsed",
        key="nt_search_box"
    )
    
    # Filter notes
    filtered_notes = all_notes
    if selected_category != "🌟 All Notebooks":
        target_nb = selected_category.replace("🏷️ ", "").strip()
        filtered_notes = [n for n in filtered_notes if n.get('notebook') == target_nb]
        
    if search_keyword.strip():
        kw = search_keyword.strip().lower()
        filtered_notes = [
            n for n in filtered_notes 
            if kw in n.get('title', '').lower() or kw in n.get('content', '').lower()
        ]
        
    st.markdown(f"<p style='font-size:0.78rem; color:#94a3b8; margin:4px 0 8px 0;'>Showing <b>{len(filtered_notes)}</b> note(s)</p>", unsafe_allow_html=True)
    
    # Render Note List Items
    if not filtered_notes:
        st.info("No notes found in this view. Use the **'💾 Save to Notes'** button in any tab or click **'➕ New Note'** above!")
    else:
        current_active = st.session_state.get('active_note_id', filtered_notes[0]['id'])
        
        for n in filtered_notes:
            is_active = (current_active == n['id'])
            nb_name = n.get('notebook', 'General')
            style_info = NOTEBOOK_COLOR_MAP.get(nb_name, NOTEBOOK_COLOR_MAP["General"])
            date_str = n.get('created_at', '')[:10]
            
            # Button item
            btn_title = f"📄 {n['title']}"
            if len(btn_title) > 34:
                btn_title = btn_title[:32] + ".."
                
            col_nb_btn, col_del_btn = st.columns([4.3, 0.7])
            with col_nb_btn:
                btn_type = "primary" if is_active else "secondary"
                if st.button(f"{btn_title}\n\n{nb_name} • {date_str}", key=f"note_item_{n['id']}", use_container_width=True, type=btn_type):
                    st.session_state['active_note_id'] = n['id']
                    st.session_state['note_mode'] = "read"
                    st.rerun()
            with col_del_btn:
                if st.button("🗑️", key=f"del_quick_{n['id']}", help="Delete note"):
                    delete_user_note(n['id'], user_email)
                    st.toast("🗑️ Note deleted!", icon="ℹ️")
                    st.session_state['active_note_id'] = None
                    st.rerun()

with col_main:
    active_id = st.session_state.get('active_note_id')
    if not active_id and all_notes:
        active_id = all_notes[0]['id']
        st.session_state['active_note_id'] = active_id
        
    current_mode = st.session_state.get('note_mode', 'read')
    
    # Case 1: Create New Note
    if active_id == "new" or not all_notes:
        st.markdown("<p style='font-size:1.15rem; font-weight:700; color:#f8fafc; margin:0 0 10px 0;'>✍️ Compose New Research Note</p>", unsafe_allow_html=True)
        
        c_title = st.text_input("Note Title", value="", placeholder="Enter descriptive note title...", key="nt_new_title")
        
        col_c_nb, col_c_sp = st.columns([2.0, 2.0])
        with col_c_nb:
            c_notebook = st.selectbox("Assign to Notebook", NOTEBOOK_LIST, index=len(NOTEBOOK_LIST)-1, key="nt_new_nb")
            
        c_content = st.text_area("Note Content (Markdown & LaTeX supported)", height=400, placeholder="Type your findings, insights, equations, and literature review notes...", key="nt_new_content")
        
        col_ns1, col_ns2 = st.columns([1.5, 4.5])
        with col_ns1:
            if st.button("💾 Save Note", type="primary", use_container_width=True, key="nt_btn_save_new"):
                if c_title.strip() and c_content.strip():
                    saved = save_user_note(user_email, c_title.strip(), c_content.strip(), c_notebook)
                    if saved:
                        log_user_activity(user_email, "Notes", "Saved Note", f"Created Note: '{c_title.strip()}'", f"Notebook: {c_notebook}", "")
                        st.toast("✅ Note saved successfully!", icon="📝")
                        st.session_state['active_note_id'] = None
                        st.session_state['note_mode'] = "read"
                        st.rerun()
                else:
                    st.warning("Please provide both a Title and Content.")
                    
    # Case 2: View / Edit Existing Note
    else:
        active_note = next((n for n in all_notes if n['id'] == active_id), None)
        if not active_note:
            active_note = all_notes[0]
            
        nb_name = active_note.get('notebook', 'General')
        style_info = NOTEBOOK_COLOR_MAP.get(nb_name, NOTEBOOK_COLOR_MAP["General"])
        
        # Word count & Reading time
        words_count = len(re.findall(r'\w+', active_note.get('content', '')))
        read_time_min = max(1, math.ceil(words_count / 200))
        
        # Top Toolbar
        col_nb_info, col_mode_toggle = st.columns([2.8, 1.4])
        with col_nb_info:
            st.markdown(f"""
                <div style="display:flex; align-items:center; gap:8px; margin-bottom:4px;">
                    <span style="font-size:0.75rem; font-weight:600; padding:3px 10px; border-radius:20px; color:{style_info['color']}; background:{style_info['bg']}; border:1px solid {style_info['border']};">
                        {nb_name}
                    </span>
                    <span style="font-size:0.8rem; color:#94a3b8;">Saved: {active_note.get('created_at', '')[:16]}</span>
                    <span style="font-size:0.8rem; color:#64748b;">•</span>
                    <span style="font-size:0.8rem; color:#94a3b8;">⏱️ {read_time_min} min read ({words_count} words)</span>
                </div>
            """, unsafe_allow_html=True)
            
        with col_mode_toggle:
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                if st.button("📖 Read", key="nt_mode_r", use_container_width=True, type="primary" if current_mode == "read" else "secondary"):
                    st.session_state['note_mode'] = "read"
                    st.rerun()
            with t_col2:
                if st.button("✏️ Edit", key="nt_mode_e", use_container_width=True, type="primary" if current_mode == "edit" else "secondary"):
                    st.session_state['note_mode'] = "edit"
                    st.rerun()

        # MODE: READ (Rendered Markdown)
        if current_mode == "read":
            st.markdown(f"<h3 style='color:#f8fafc; margin-top:4px; margin-bottom:12px; font-size:1.35rem; font-weight:700;'>{active_note['title']}</h3>", unsafe_allow_html=True)
            
            st.markdown(f"""
<div class="note-reader-canvas">

{active_note['content']}

</div>
""", unsafe_allow_html=True)
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            
            # Action Toolbar
            act_c1, act_c2, act_c3, act_c4 = st.columns([1.6, 1.5, 1.5, 1.4])
            
            with act_c1:
                if st.button("✨ Polish with AI", key="nt_btn_ai_polish", use_container_width=True, help="Refine clarity, format equations, and enhance structure with Gemini"):
                    with st.spinner("Refining and structuring note with AI..."):
                        polished = polish_note_with_ai(active_note['title'], active_note['content'])
                        update_user_note(active_note['id'], user_email, active_note['title'], polished, active_note['notebook'])
                        st.toast("✨ Note polished and updated!", icon="🪄")
                        st.rerun()
                        
            with act_c2:
                st.download_button(
                    label="⬇️ Export (.md)",
                    data=f"# {active_note['title']}\n\n**Notebook:** {active_note['notebook']} | **Date:** {active_note['created_at']}\n\n---\n\n{active_note['content']}",
                    file_name=f"{active_note['title'][:25].replace(' ', '_')}.md",
                    mime="text/markdown",
                    use_container_width=True,
                    key="nt_btn_export_md"
                )
                
            with act_c3:
                if st.button("✏️ Edit Note", key="nt_btn_edit_switch", use_container_width=True):
                    st.session_state['note_mode'] = "edit"
                    st.rerun()
                    
            with act_c4:
                if st.button("🗑️ Delete", key="nt_btn_del_main", use_container_width=True):
                    delete_user_note(active_note['id'], user_email)
                    st.toast("🗑️ Note deleted.", icon="ℹ️")
                    st.session_state['active_note_id'] = None
                    st.rerun()

        # MODE: EDIT
        else:
            st.markdown("<p style='font-size:1.1rem; font-weight:700; color:#f8fafc; margin:4px 0 8px 0;'>✏️ Edit Research Note</p>", unsafe_allow_html=True)
            
            edit_title = st.text_input("Title", value=active_note['title'], key="nt_edit_title")
            
            cur_nb = active_note.get('notebook', NOTEBOOK_LIST[0])
            nb_idx = NOTEBOOK_LIST.index(cur_nb) if cur_nb in NOTEBOOK_LIST else 0
            edit_nb = st.selectbox("Notebook Category", NOTEBOOK_LIST, index=nb_idx, key="nt_edit_nb")
            
            edit_content = st.text_area("Content", value=active_note['content'], height=420, key="nt_edit_content")
            
            save_c1, save_c2, save_sp = st.columns([1.5, 1.5, 3.0])
            with save_c1:
                if st.button("💾 Save Changes", type="primary", use_container_width=True, key="nt_btn_save_edits"):
                    if edit_title.strip() and edit_content.strip():
                        update_user_note(active_note['id'], user_email, edit_title.strip(), edit_content.strip(), edit_nb)
                        st.toast("✅ Note changes saved!", icon="📝")
                        st.session_state['note_mode'] = "read"
                        st.rerun()
                    else:
                        st.warning("Title and content cannot be empty.")
            with save_c2:
                if st.button("Cancel", key="nt_btn_cancel_edit", use_container_width=True):
                    st.session_state['note_mode'] = "read"
                    st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopNotesEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopNotesEnd, ms));
        </script>
    """, height=0)

