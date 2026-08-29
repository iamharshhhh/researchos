import streamlit as st
import pandas as pd
import json
import time
import re
from backend.database import (
    get_user_activities, 
    delete_user_activity, 
    clear_all_user_activities,
    clear_all_user_history,
    get_user_documents
)

# Authentication check
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="History | ResearchOS",
    page_icon="🕘",
    layout="wide"
)

# Custom Styling
st.markdown("""
    <style>
        .block-container {
            max-width: 1050px;
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
        /* Metric Banner */
        .hist-metric-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 14px 16px;
            text-align: center;
        }
        .hist-metric-val {
            font-size: 1.4rem;
            font-weight: 700;
            color: #60a5fa;
            line-height: 1.2;
        }
        .hist-metric-lbl {
            font-size: 0.78rem;
            color: #94a3b8;
            font-weight: 500;
            margin-top: 2px;
        }
        /* Activity Timeline Card */
        .hist-card {
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 18px 20px;
            margin-bottom: 14px;
            transition: all 0.2s ease-in-out;
        }
        .hist-card:hover {
            border-color: #475569;
            background: rgba(36, 52, 77, 0.9);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
        }
        .hist-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .hist-title {
            font-size: 1.02rem;
            font-weight: 600;
            color: #f8fafc;
            margin: 0;
        }
        .hist-badge {
            font-size: 0.75rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 20px;
            white-space: nowrap;
        }
        .hist-snippet {
            font-size: 0.86rem;
            line-height: 1.5;
            color: #94a3b8;
            background: rgba(15, 23, 42, 0.4);
            padding: 8px 12px;
            border-radius: 6px;
            margin: 6px 0 10px 0;
            border-left: 3px solid #60a5fa;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        /* Action buttons */
        div[class*="st-key-hist_btn_"] button,
        div[class*="st-key-hist_act_"] button,
        div[class*="st-key-hist_del_"] button {
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
            padding: 0 14px !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-hist_btn_"] button:hover,
        div[class*="st-key-hist_act_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #1e293b !important;
            color: #ffffff !important;
        }
        div[class*="st-key-hist_del_"] button:hover {
            border-color: #ef4444 !important;
            background-color: rgba(239, 68, 68, 0.15) !important;
            color: #f87171 !important;
        }
    </style>
""", unsafe_allow_html=True)

# 1. Header
st.markdown("<h3 class='header-title'>🕘 Research Activity & Session History</h3>", unsafe_allow_html=True)
st.markdown("<p class='header-subtitle'>Chronological audit trail and historical timeline of your platform interactions, research inquiries, syntheses, and analyses.</p>", unsafe_allow_html=True)

# ----------------- Feature Metadata Map -----------------
FEATURE_STYLE_MAP = {
    "AI Chat": {"icon": "💬", "color": "#38bdf8", "bg": "rgba(56, 189, 248, 0.12)", "border": "rgba(56, 189, 248, 0.3)", "route": "views/ai/chat.py", "btn_text": "💬 Open AI Chat"},
    "Summarizer": {"icon": "📝", "color": "#34d399", "bg": "rgba(52, 211, 153, 0.12)", "border": "rgba(52, 211, 153, 0.3)", "route": "views/ai/summarize.py", "btn_text": "📝 Open Summarizer"},
    "Compare": {"icon": "⚖️", "color": "#a78bfa", "bg": "rgba(167, 139, 250, 0.12)", "border": "rgba(167, 139, 250, 0.3)", "route": "views/ai/compare.py", "btn_text": "⚖️ Open Compare"},
    "Formula Explainer": {"icon": "📐", "color": "#f472b6", "bg": "rgba(244, 114, 182, 0.12)", "border": "rgba(244, 114, 182, 0.3)", "route": "views/tools/formula.py", "btn_text": "📐 Open Formula Explainer"},
    "Figure Explainer": {"icon": "🖼️", "color": "#fbbf24", "bg": "rgba(251, 191, 36, 0.12)", "border": "rgba(251, 191, 36, 0.3)", "route": "views/tools/figure.py", "btn_text": "🖼️ Open Figure Explainer"},
    "Quiz Generator": {"icon": "🎯", "color": "#f43f5e", "bg": "rgba(244, 63, 94, 0.12)", "border": "rgba(244, 63, 94, 0.3)", "route": "views/tools/quiz.py", "btn_text": "🎯 Open Quiz Generator"},
    "Citation Generator": {"icon": "🔖", "color": "#f97316", "bg": "rgba(249, 115, 22, 0.12)", "border": "rgba(249, 115, 22, 0.3)", "route": "views/tools/citation.py", "btn_text": "🔖 Open Citation Generator"},
    "Citation Graph": {"icon": "🕸️", "color": "#818cf8", "bg": "rgba(129, 140, 248, 0.12)", "border": "rgba(129, 140, 248, 0.3)", "route": "views/other/citation_graph.py", "btn_text": "🕸️ Open Citation Graph"},
    "Semantic Search": {"icon": "🔍", "color": "#06b6d4", "bg": "rgba(6, 182, 212, 0.12)", "border": "rgba(6, 182, 212, 0.3)", "route": "views/other/semantic_search.py", "btn_text": "🔍 Open Semantic Search"},
    "Notes": {"icon": "📓", "color": "#10b981", "bg": "rgba(16, 185, 129, 0.12)", "border": "rgba(16, 185, 129, 0.3)", "route": "views/other/notes.py", "btn_text": "📓 Open Notes"},
    "Paper Library": {"icon": "📄", "color": "#8b5cf6", "bg": "rgba(139, 92, 246, 0.12)", "border": "rgba(139, 92, 246, 0.3)", "route": "views/papers/library.py", "btn_text": "📄 Open Library"}
}

# ----------------- Fetch Logged User Activities -----------------
user_activities = get_user_activities(user_email)

# Metric computations
total_activities = len(user_activities)
chat_queries_count = sum(1 for a in user_activities if a["feature"] == "AI Chat")
syntheses_count = sum(1 for a in user_activities if a["feature"] in ["Summarizer", "Compare", "Notes"])
tools_count = sum(1 for a in user_activities if a["feature"] in ["Formula Explainer", "Figure Explainer", "Quiz Generator", "Citation Generator", "Citation Graph", "Semantic Search"])

# ----------------- Metric Banner -----------------
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.markdown(f"<div class='hist-metric-card'><div class='hist-metric-val'>{total_activities}</div><div class='hist-metric-lbl'>Total Actions Logged</div></div>", unsafe_allow_html=True)
with m2:
    st.markdown(f"<div class='hist-metric-card'><div class='hist-metric-val'>{chat_queries_count}</div><div class='hist-metric-lbl'>AI Chat Queries</div></div>", unsafe_allow_html=True)
with m3:
    st.markdown(f"<div class='hist-metric-card'><div class='hist-metric-val'>{syntheses_count}</div><div class='hist-metric-lbl'>Syntheses & Notes</div></div>", unsafe_allow_html=True)
with m4:
    st.markdown(f"<div class='hist-metric-card'><div class='hist-metric-val'>{tools_count}</div><div class='hist-metric-lbl'>Tools & Analyses</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

# ----------------- Controls Row -----------------
col_f1, col_f2, col_act = st.columns([1.5, 3.0, 1.2])

with col_f1:
    filter_options = ["🌟 All Features"] + list(FEATURE_STYLE_MAP.keys())
    filter_feature = st.selectbox(
        "Filter Feature",
        filter_options,
        index=0,
        key="hist_filter_feature"
    )

with col_f2:
    search_term = st.text_input(
        "Search History",
        placeholder="Filter history by keyword or title...",
        key="hist_search_box"
    )

with col_act:
    st.markdown("<div style='height: 27px;'></div>", unsafe_allow_html=True)
    if st.button("🗑️ Clear All History", key="hist_btn_clear_all", use_container_width=True, help="Clear all user activity logs and history"):
        clear_all_user_activities(user_email)
        clear_all_user_history(user_email)
        if 'active_session_id' in st.session_state:
            st.session_state['active_session_id'] = None
        if 'active_note_id' in st.session_state:
            st.session_state['active_note_id'] = None
        st.toast("🗑️ All activity history cleared!", icon="ℹ️")
        st.rerun()

# Apply Filters
filtered_activities = user_activities
if filter_feature != "🌟 All Features":
    filtered_activities = [a for a in filtered_activities if a["feature"] == filter_feature]

if search_term.strip():
    kw = search_term.strip().lower()
    filtered_activities = [
        a for a in filtered_activities 
        if kw in a["title"].lower() or kw in a["details"].lower() or kw in a["feature"].lower() or kw in a["action_type"].lower()
    ]

st.markdown(f"<p style='font-size:0.8rem; color:#94a3b8; margin:6px 0 12px 0;'>Showing <b>{len(filtered_activities)}</b> activity record(s)</p>", unsafe_allow_html=True)

user_lib_docs = get_user_documents(user_email)
user_paper_title = user_lib_docs[0]["title"] if user_lib_docs else "Research Paper"
doc_title_lookup = {str(d["id"]): d["title"] for d in user_lib_docs} if user_lib_docs else {}

# ----------------- Render Timeline Cards -----------------
if not filtered_activities:
    st.info("No activity history recorded yet. Interact with any feature (AI Chat, Summarizer, Compare, Formula, Figure, Quiz, Citations, Search, Notes) to see your timeline build automatically!")
else:
    for idx, act in enumerate(filtered_activities):
        style = FEATURE_STYLE_MAP.get(act["feature"], {
            "icon": "⚡", 
            "color": "#94a3b8", 
            "bg": "rgba(148, 163, 184, 0.12)", 
            "border": "rgba(148, 163, 184, 0.3)", 
            "route": "views/dashboard.py", 
            "btn_text": "⚡ Open Feature"
        })
        
        timestamp_str = act["created_at"][:19] if act["created_at"] else "Earlier"
        
        # Clean, compact snippet preview for history card
        raw_det = str(act.get("details", "")).strip()
        if raw_det.startswith("{") and "questions" in raw_det:
            try:
                q_obj = json.loads(raw_det)
                snippet_preview = f"🎯 Generated {len(q_obj.get('questions', []))} comprehension questions ({q_obj.get('difficulty', 'Standard')})"
            except Exception:
                snippet_preview = "Comprehension quiz generated."
        else:
            clean_text = re.sub(r'[#*`$\\\(\)\[\]]', ' ', raw_det)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            if len(clean_text) > 160:
                snippet_preview = clean_text[:160].strip() + "..."
            else:
                snippet_preview = clean_text if clean_text else "Action recorded in timeline."

        raw_title = str(act.get('title', '')).strip()
        feature_name = act.get('feature', '')
        
        # Exact prefix formatting as specified (AI Chat: <Paper Title>)
        if feature_name == "AI Chat":
            if act.get("raw_id") and str(act.get("raw_id")) in doc_title_lookup:
                display_title = f"AI Chat: {doc_title_lookup[str(act.get('raw_id'))]}"
            elif raw_title.startswith("AI Chat:") and len(raw_title) > 12 and not raw_title.endswith("General Research") and not raw_title.endswith("Entire Library"):
                display_title = raw_title
            else:
                display_title = f"AI Chat: {user_paper_title}"
        elif feature_name == "Summarizer":
            display_title = raw_title if raw_title.startswith("Summary:") else f"Summary: {raw_title}"
        elif feature_name == "Formula Explainer":
            display_title = raw_title if raw_title.startswith("Formula:") else f"Formula: {raw_title}"
        elif feature_name == "Figure Explainer":
            display_title = raw_title if raw_title.startswith("Figure:") else f"Figure: {raw_title}"
        elif feature_name == "Quiz Generator":
            display_title = raw_title if raw_title.startswith("Quiz:") else f"Quiz: {raw_title}"
        elif feature_name == "Citation Generator":
            display_title = raw_title if raw_title.startswith("Citation:") else f"Citation: {raw_title}"
        elif feature_name == "Compare":
            display_title = raw_title if raw_title.startswith("Comparison:") else f"Comparison: {raw_title}"
        elif feature_name == "Citation Graph":
            if raw_title.startswith("Lineage:"):
                display_title = f"Citation: {raw_title.replace('Lineage:', '').strip()}"
            elif raw_title.startswith("Citation:"):
                display_title = raw_title
            else:
                display_title = f"Citation: {raw_title}"
        elif feature_name == "Semantic Search":
            if raw_title.startswith("Searched:"):
                display_title = f"Search: {raw_title.replace('Searched:', '').strip()}"
            elif raw_title.startswith("Search:"):
                display_title = raw_title
            else:
                display_title = f"Search: {raw_title}"
        elif feature_name == "Notes":
            display_title = raw_title if raw_title.startswith("Note:") else f"Note: {raw_title}"
        else:
            display_title = raw_title

        st.markdown(f"""
<div class="hist-card">
    <div class="hist-header">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:1.15rem;">{style['icon']}</span>
            <h4 class="hist-title">{display_title}</h4>
        </div>
        <span class="hist-badge" style="color:{style['color']}; background:{style['bg']}; border:1px solid {style['border']};">
            {act['feature']} • {act['action_type']}
        </span>
    </div>
    <div style="font-size:0.8rem; color:#94a3b8; margin-bottom:6px;">
        ⏱️ <b>Timestamp:</b> {timestamp_str}
    </div>
    <div class="hist-snippet">
        {snippet_preview}
    </div>
</div>
""", unsafe_allow_html=True)
        
        # Shortcut action buttons per event: [Open Feature (Left)] [Spacer] [Delete Button (Far Right)]
        btn_nav, btn_sp, btn_del = st.columns([2.0, 4.0, 1.2])
        with btn_nav:
            if st.button(style["btn_text"], key=f"hist_act_{idx}", use_container_width=True):
                st.session_state['from_history'] = True
                
                # 1. AI Assistant Chat
                if act["feature"] == "AI Chat" and act["raw_id"]:
                    st.session_state['active_session_id'] = str(act["raw_id"])
                    st.session_state['last_loaded_session'] = None
                    st.session_state.messages = []
                
                # 2. Personal Notes Vault
                elif act["feature"] == "Notes" and act["raw_id"]:
                    st.session_state['active_note_id'] = act["raw_id"]
                    st.session_state['note_mode'] = 'read'
                
                # 3. Academic Summarizer
                elif act["feature"] == "Summarizer":
                    if act["raw_id"]:
                        st.session_state['selected_paper_id'] = str(act["raw_id"])
                    paper_name = act["title"].replace("Summary: ", "").strip()
                    st.session_state["selected_sum_mode"] = act.get("action_type", "Executive Synthesis")
                    st.session_state["last_summary"] = {
                        "paper_title": paper_name,
                        "mode": act.get("action_type", "Executive Synthesis"),
                        "text": act.get("details", ""),
                        "timestamp": act.get("created_at") or time.time()
                    }
                
                # 4. Mathematical Formula Explainer
                elif act["feature"] == "Formula Explainer":
                    if act["raw_id"]:
                        st.session_state['selected_paper_id'] = str(act["raw_id"])
                    form_name = act["title"].replace("Formula: ", "").strip()
                    st.session_state["current_formula_breakdown"] = {
                        "domain": form_name,
                        "text": act.get("details", ""),
                        "timestamp": act.get("created_at") or time.time()
                    }
                
                # 5. Figure Explainer
                elif act["feature"] == "Figure Explainer":
                    if act["raw_id"]:
                        st.session_state['selected_paper_id'] = str(act["raw_id"])
                    fig_name = act["title"].replace("Figure: ", "").strip()
                    st.session_state["current_figure_analysis"] = {
                        "title": fig_name,
                        "text": act.get("details", ""),
                        "timestamp": act.get("created_at") or time.time()
                    }
                
                # 6. Interactive Quiz Generator
                elif act["feature"] == "Quiz Generator":
                    if act["raw_id"]:
                        st.session_state['selected_paper_id'] = str(act["raw_id"])
                    try:
                        loaded_q = json.loads(act.get("details", "{}"))
                        if isinstance(loaded_q, dict) and "questions" in loaded_q:
                            st.session_state["current_quiz"] = loaded_q
                    except Exception:
                        pass
                
                # 7. AI Citation Generator
                elif act["feature"] == "Citation Generator":
                    if act["raw_id"]:
                        st.session_state['selected_paper_id'] = str(act["raw_id"])
                    cite_name = act["title"].replace("Citation: ", "").strip()
                    st.session_state["current_ai_citation"] = {
                        "paper_title": cite_name,
                        "style": act.get("action_type", "APA 7th Edition"),
                        "text": act.get("details", ""),
                        "timestamp": act.get("created_at") or time.time()
                    }
                
                # 8. Cross-Paper Comparison
                elif act["feature"] == "Compare":
                    st.session_state["selected_cmp_dim"] = act.get("action_type", "Comprehensive Head-to-Head")
                    st.session_state["last_comparison"] = {
                        "papers": [],
                        "dimension": act.get("action_type", "Comprehensive Head-to-Head"),
                        "text": act.get("details", ""),
                        "timestamp": act.get("created_at") or time.time()
                    }
                
                # 9. Citation Graph Lineage
                elif act["feature"] == "Citation Graph":
                    st.session_state["current_graph_synthesis"] = {
                        "mode": act.get("action_type", "Intellectual Lineage Synthesis"),
                        "text": act.get("details", ""),
                        "timestamp": act.get("created_at") or time.time()
                    }
                
                # 10. Semantic Search Engine
                elif act["feature"] == "Semantic Search":
                    clean_query = act["title"].replace("Searched: ", "").replace("Searched:", "").replace("'", "").strip()
                    st.session_state['search_input_prefill'] = clean_query
                
                # 11. Paper Library & Details
                elif act["feature"] in ["Paper Library", "Paper Details"] and act["raw_id"]:
                    st.session_state['selected_paper_id'] = str(act["raw_id"])
                    st.session_state['selected_paper_for_details'] = str(act["raw_id"])
                
                st.switch_page(style["route"])
                
        with btn_del:
            if st.button("🗑️ Delete", key=f"hist_del_{idx}", use_container_width=True, help="Remove this activity record"):
                delete_user_activity(act["id"], user_email)
                st.toast("🗑️ Activity record removed!", icon="ℹ️")
                st.rerun()
                
        st.markdown("<div style='height: 4px;'></div>", unsafe_allow_html=True)
