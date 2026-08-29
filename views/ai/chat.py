import streamlit as st
import time
import json
from backend.rag_pipeline import generate_rag_response, clean_academic_response
from backend.database import (
    save_chat_message, 
    get_user_chats, 
    clear_user_chats, 
    get_user_documents, 
    save_user_note,
    create_chat_session,
    get_user_chat_sessions,
    get_session_chats,
    update_chat_session_title,
    delete_chat_session,
    delete_all_chat_sessions,
    log_user_activity
)

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')
user_name = st.session_state.get('user_name', 'Researcher')
first_name = user_name.split()[0] if user_name else "Researcher"

# Page configuration
st.set_page_config(
    page_title="AI Chat | ResearchOS",
    page_icon="💬",
    layout="wide"
)

import streamlit.components.v1 as components
import random

# Dynamic render nonce to ensure iframe mounts on every page view
chat_render_nonce = random.randint(100000, 999999)

components.html(f"""
    <div id="nonce_{chat_render_nonce}"></div>
    <script>
        (function() {{
            try {{
                var parentWin = window.parent;
                var parentDoc = parentWin.document;

                // Disable smooth scrolling globally on the parent
                if (!parentDoc.getElementById('force-no-smooth-scroll')) {{
                    var st = parentDoc.createElement('style');
                    st.id = 'force-no-smooth-scroll';
                    st.innerHTML = '* {{ scroll-behavior: auto !important; }}';
                    parentDoc.head.appendChild(st);
                }}

                function forceScrollToTopNow() {{
                    try {{
                        var selectors = [
                            '[data-testid="stAppViewContainer"]',
                            '[data-testid="stMain"]',
                            '[data-testid="stMainBlockContainer"]',
                            'section.main',
                            '.main'
                        ];
                        for (var i = 0; i < selectors.length; i++) {{
                            var el = parentDoc.querySelector(selectors[i]);
                            if (el) {{
                                el.scrollTop = 0;
                                if (el.scrollTo) el.scrollTo({{ top: 0, left: 0, behavior: 'instant' }});
                            }}
                        }}
                        if (parentDoc.documentElement) parentDoc.documentElement.scrollTop = 0;
                        if (parentDoc.body) parentDoc.body.scrollTop = 0;
                        if (parentWin.scrollTo) parentWin.scrollTo(0, 0);
                    }} catch(e) {{}}
                }}

                // Execute immediately
                forceScrollToTopNow();

                // Run continuously for 2.5 seconds to override Streamlit React chat_input auto-scroll
                var count = 0;
                var interval = setInterval(function() {{
                    forceScrollToTopNow();
                    count++;
                    if (count > 50) {{
                        clearInterval(interval);
                    }}
                }}, 50);
            }} catch(err) {{}}
        }})();
    </script>
""", height=0)

# Ultra-Clean, Gemini Web Chat Aesthetic
st.markdown("""
    <style>
        .block-container {
            max-width: 960px;
            padding-top: 1.5rem;
            padding-bottom: 3.5rem;
            margin: 0 auto;
        }
        @media (max-width: 768px) {
            .block-container {
                padding: 1rem 0.6rem 3rem 0.6rem !important;
                max-width: 100% !important;
            }
            div[data-testid="stChatMessage"] {
                padding: 12px 14px !important;
                font-size: 0.88rem !important;
            }
        }
        .empty-hero {
            text-align: center;
            padding: 32px 10px 18px 10px;
        }
        .empty-hero h2 {
            font-size: 1.9rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 8px;
            letter-spacing: -0.02em;
        }
        .empty-hero p {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-bottom: 18px;
        }
        /* Chat Message Typography & Spacing (Gemini Style) */
        div[data-testid="stChatMessage"] {
            padding: 18px 20px !important;
            border-radius: 14px !important;
            margin-bottom: 14px !important;
            line-height: 1.7 !important;
            font-size: 0.95rem !important;
        }
        div[data-testid="stChatMessage"] p {
            line-height: 1.7 !important;
            margin-bottom: 0.85rem !important;
            color: #f1f5f9 !important;
        }
        div[data-testid="stChatMessage"] ul, 
        div[data-testid="stChatMessage"] ol {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            padding-left: 1.4rem !important;
        }
        div[data-testid="stChatMessage"] li {
            margin-bottom: 0.5rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        div[data-testid="stChatMessage"] li strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        div[data-testid="stChatMessage"] h1,
        div[data-testid="stChatMessage"] h2,
        div[data-testid="stChatMessage"] h3,
        div[data-testid="stChatMessage"] h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        div[data-testid="stChatMessage"] h3 {
            font-size: 1.15rem !important;
            color: #93c5fd !important;
        }
        /* Markdown Tables in Chat */
        div[data-testid="stChatMessage"] table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #334155 !important;
            font-size: 0.9rem !important;
        }
        div[data-testid="stChatMessage"] th {
            background-color: #0f172a !important;
            color: #60a5fa !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            border: 1px solid #334155 !important;
            text-align: left !important;
        }
        div[data-testid="stChatMessage"] td {
            padding: 9px 14px !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        div[data-testid="stChatMessage"] tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.4) !important;
        }
        /* Blockquote callout styling */
        div[data-testid="stChatMessage"] blockquote {
            border-left: 3px solid #60a5fa !important;
            background: rgba(59, 130, 246, 0.08) !important;
            padding: 10px 16px !important;
            border-radius: 0 8px 8px 0 !important;
            margin: 12px 0 !important;
            color: #cbd5e1 !important;
        }
        /* Suggestion card boxes (4 cards) */
        div[class*="st-key-sugg_"] button {
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
        div[class*="st-key-sugg_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.15) !important;
        }
        div[class*="st-key-sugg_"] button p {
            font-size: 0.88rem !important;
            line-height: 1.35 !important;
            margin: 0 !important;
            padding: 0 !important;
            text-align: left !important;
            width: 100% !important;
        }
        /* Top Header Baseline Alignment */
        div[data-testid="stHorizontalBlock"]:first-of-type {
            align-items: center !important;
            margin-bottom: 8px !important;
        }
        div[data-testid="stHorizontalBlock"]:first-of-type h3 {
            margin: 0 !important;
            padding: 0 !important;
            line-height: 40px !important;
        }
        /* Header action button */
        div[class*="st-key-hdr_"] button {
            height: 38px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            margin-top: 14px !important;
            padding: 0 16px !important;
            border-radius: 8px !important;
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #f1f5f9 !important;
            font-size: 0.84rem !important;
            font-weight: 500 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100% !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-hdr_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
        }
        /* Action row buttons directly beneath assistant messages */
        div[class*="st-key-save_note_"] button,
        div[class*="st-key-clear_chat_"] button {
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
        div[class*="st-key-save_note_"] button:hover,
        div[class*="st-key-clear_chat_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        /* Reset p and div margins inside chat action buttons for perfect center alignment */
        div[class*="st-key-save_note_"] button p,
        div[class*="st-key-clear_chat_"] button p,
        div[class*="st-key-save_note_"] button div,
        div[class*="st-key-clear_chat_"] button div {
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

# 1. Multi-Session Management
user_sessions = get_user_chat_sessions(user_email)
if "active_session_id" not in st.session_state or not st.session_state["active_session_id"]:
    if user_sessions:
        st.session_state["active_session_id"] = user_sessions[0]["session_id"]
    else:
        new_sid = create_chat_session(user_email, title="New Research Chat")
        st.session_state["active_session_id"] = new_sid
        user_sessions = get_user_chat_sessions(user_email)

active_session_id = st.session_state.get("active_session_id")

# Fetch and sync user library
library = get_user_documents(user_email)
st.session_state['library_metadata'] = library

import streamlit.components.v1 as components

# 2. Top Header & Multi-Session Toolbar
st.markdown("<div id='top-view-anchor'></div>", unsafe_allow_html=True)



if st.session_state.get('from_history'):
    col_hdr_back, col_hdr_title, col_hdr_new = st.columns([1.5, 3.2, 1.3])
    with col_hdr_back:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_hdr_title:
        st.markdown("<h3 style='font-size:1.6rem; font-weight:700; color:#f8fafc; margin:0;'>💬 AI Assistant</h3>", unsafe_allow_html=True)
    with col_hdr_new:
        if st.button("➕ New Chat", key="hdr_new_chat", use_container_width=True, help="Start a new research conversation"):
            new_sid = create_chat_session(user_email, title="New Research Chat")
            st.session_state["active_session_id"] = new_sid
            st.session_state["last_loaded_session"] = None
            st.session_state.messages = []
            st.rerun()
else:
    col_hdr_title, col_hdr_new = st.columns([4, 1.3])
    with col_hdr_title:
        st.markdown("<h3 style='font-size:1.6rem; font-weight:700; color:#f8fafc; margin:0;'>💬 AI Assistant</h3>", unsafe_allow_html=True)
    with col_hdr_new:
        if st.button("➕ New Chat", key="hdr_new_chat", use_container_width=True, help="Start a new research conversation"):
            new_sid = create_chat_session(user_email, title="New Research Chat")
            st.session_state["active_session_id"] = new_sid
            st.session_state["last_loaded_session"] = None
            st.session_state.messages = []
            st.rerun()

# 3. Agent Mode & Context Paper Selectors
col_mode, col_paper = st.columns([1.2, 2.8])

# 4 Specialized Research Agents + General Research Agent
RESEARCH_AGENT_MODES = [
    "⚛️ Research Agent",
    "📖 Literature Review",
    "🔬 Research Gaps",
    "💡 Research Ideas",
    "🧪 Experiment Planner"
]

with col_mode:
    current_agent_mode = st.selectbox(
        "Select Research Agent",
        RESEARCH_AGENT_MODES,
        index=RESEARCH_AGENT_MODES.index(st.session_state.get("agent_mode", "⚛️ Research Agent")) if st.session_state.get("agent_mode") in RESEARCH_AGENT_MODES else 0,
        label_visibility="collapsed",
        key="agent_mode_select"
    )
    st.session_state["agent_mode"] = current_agent_mode

# Paper selection dropdown
paper_options = []
paper_map = {}
auto_selected_doc_id = st.session_state.pop("auto_select_paper_id", None)
auto_selected_index = None

if library:
    for idx, doc in enumerate(library):
        label = f"📄 {doc['title']} (ID: {doc['id']})"
        paper_options.append(label)
        paper_map[label] = doc['id']
        if auto_selected_doc_id and str(doc.get('id')) == str(auto_selected_doc_id):
            auto_selected_index = idx

if auto_selected_index is not None and auto_selected_index < len(paper_options):
    st.session_state["chat_paper_scope"] = paper_options[auto_selected_index]

with col_paper:
    selected_paper_option = st.selectbox(
        "Scope to Paper",
        paper_options,
        index=auto_selected_index,
        placeholder="📄 Select a paper to focus context",
        label_visibility="collapsed",
        key="chat_paper_scope"
    )

# Determine document filter
filter_doc_ids = None
if selected_paper_option:
    chosen_id = paper_map.get(selected_paper_option)
    if chosen_id:
        filter_doc_ids = [chosen_id]

# Load messages for active session if not populated or if active_session_id switched
if "messages" not in st.session_state or st.session_state.get("last_loaded_session") != active_session_id:
    st.session_state.messages = []
    st.session_state["last_loaded_session"] = active_session_id
    db_chats = get_session_chats(active_session_id, user_email)
    for c in db_chats:
        citations_data = []
        if c.get("citations"):
            try:
                citations_data = json.loads(c["citations"]) if isinstance(c["citations"], str) else c["citations"]
            except Exception:
                citations_data = []
        st.session_state.messages.append({
            "role": c["role"],
            "content": c["message"],
            "citations": citations_data
        })

# 4. Scrollable Conversation Container
chat_box = st.container(height=540, border=False)

with chat_box:
    # Empty State Hero with 4 Aligned Research Agent Suggestion Cards
    clicked_prompt = None
    if len(st.session_state.messages) == 0:
        st.markdown("""
            <div class="empty-hero">
                <h2>What would you like to research today?</h2>
                <p>Select a specialized Research Agent below or ask any question about your papers.</p>
            </div>
        """, unsafe_allow_html=True)
        
        # 4 Perfectly-Aligned Suggestion Cards
        col1, col2 = st.columns(2)
        
        q_lit = "Conduct a comprehensive literature review synthesizing the core methodology, architecture, and theoretical foundations."
        q_gap = "Identify critical research gaps, unaddressed limitations, and future work opportunities."
        q_idea = "Brainstorm novel, publishable research hypotheses and hybrid methodology ideas."
        q_exp = "Design a rigorous empirical experiment protocol, benchmark baselines, and ablation study."
        
        with col1:
            if st.button("📖 **Literature Review Synthesis**\n\nSynthesize related works, thematic taxonomies & cross-paper trends", use_container_width=True, key="sugg_1"):
                st.session_state["agent_mode"] = "📖 Literature Review"
                clicked_prompt = q_lit
            if st.button("💡 **Novel Research Ideas**\n\nBrainstorm high-impact research hypotheses & hybrid methodologies", use_container_width=True, key="sugg_2"):
                st.session_state["agent_mode"] = "💡 Research Ideas"
                clicked_prompt = q_idea
        with col2:
            if st.button("🔬 **Research Gaps & Limitations**\n\nIdentify unresolved challenges, bottlenecks & future directions", use_container_width=True, key="sugg_3"):
                st.session_state["agent_mode"] = "🔬 Research Gaps"
                clicked_prompt = q_gap
            if st.button("🧪 **Experimental Design & Protocol**\n\nStructure benchmark baselines, datasets, ablations & evaluation metrics", use_container_width=True, key="sugg_4"):
                st.session_state["agent_mode"] = "🧪 Experiment Planner"
                clicked_prompt = q_exp
    else:
        # Display Conversation History starting from top
        for msg_idx, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                display_text = clean_academic_response(msg["content"]) if msg["role"] == "assistant" else msg["content"]
                st.markdown(display_text)
                            
                # Action Buttons directly beneath Assistant Messages
                if msg["role"] == "assistant":
                    col_act1, col_act2, col_act_spacer = st.columns([1.6, 1.8, 4.0])
                    with col_act1:
                        if st.button("💾 Save to Notes", key=f"save_note_{msg_idx}", use_container_width=True, help="Save this synthesis to your Personal Notes"):
                            first_line = msg["content"].strip().split("\n")[0].replace("#", "").strip()[:40]
                            note_title = f"AI Synthesis: {first_line}" if first_line else "AI Research Note"
                            saved = save_user_note(
                                user_email=user_email,
                                title=note_title,
                                content=msg["content"],
                                notebook="AI Chat Notes"
                            )
                            if saved:
                                st.toast("✅ Saved to Notes!", icon="📝")
                            else:
                                st.error("Failed to save note.")
                    with col_act2:
                        if st.button("🗑️ Clear Chat", key=f"clear_chat_{msg_idx}", use_container_width=True, help="Clear active screen and start fresh (chat is preserved in History)"):
                            new_sid = create_chat_session(user_email, title="New Research Chat")
                            st.session_state["active_session_id"] = new_sid
                            st.session_state["last_loaded_session"] = new_sid
                            st.session_state.messages = []
                            st.toast("🧹 Screen cleared! Conversation saved to History.", icon="ℹ️")
                            st.rerun()

# User Chat Input
current_mode_label = st.session_state.get("agent_mode", "⚛️ Research Agent")
user_query = st.chat_input(f"Ask {current_mode_label} about your research papers...")
active_input = clicked_prompt if clicked_prompt else user_query

if active_input:
    # Auto-update session title on first message if default
    current_session = next((s for s in user_sessions if s["session_id"] == active_session_id), None)
    if current_session and (current_session["title"] == "New Research Chat" or not current_session["title"]):
        clean_title = active_input.strip()[:35]
        update_chat_session_title(active_session_id, user_email, clean_title)

    # Append & display user message
    st.session_state.messages.append({"role": "user", "content": active_input})
    save_chat_message(user_email=user_email, role="user", message=active_input, session_id=active_session_id)

    # Determine title matching other feature format (AI Chat: <Paper Title>)
    if selected_paper_option:
        paper_scope_title = selected_paper_option.replace("📄 ", "").split(" (ID:")[0].strip()
    elif library:
        paper_scope_title = library[0]["title"]
    else:
        paper_scope_title = "Research Paper"

    chat_activity_title = f"AI Chat: {paper_scope_title}"
    log_user_activity(user_email, "AI Chat", current_mode_label, chat_activity_title, active_input, active_session_id)
    
    with st.chat_message("user"):
        st.markdown(active_input)

    # Generate Assistant Response with Active Research Agent Mode
    with st.chat_message("assistant"):
        if not selected_paper_option:
            response_text = "⚠️ **Please select a research paper first.**\n\nTo analyze methodology, answer technical questions, or synthesize insights, please select a research paper from the **'Scope to Paper'** dropdown above (or upload one to your Library)."
            citations = []
            st.markdown(response_text)
        else:
            with st.spinner(f"Synthesizing analysis via {current_mode_label}..."):
                try:
                    rag_result = generate_rag_response(
                        active_input, 
                        n_results=4, 
                        filter_doc_ids=filter_doc_ids,
                        research_mode=current_mode_label
                    )
                    response_text = rag_result["response"]
                    citations = rag_result["citations"]
                except Exception as e:
                    response_text = f"**Error generating response:** {str(e)}"
                    citations = []

            st.markdown(response_text)

    # Save Assistant Message linked to active session
    st.session_state.messages.append({
        "role": "assistant",
        "content": response_text,
        "citations": citations
    })
    save_chat_message(
        user_email=user_email,
        role="assistant",
        message=response_text,
        citations=json.dumps(citations),
        session_id=active_session_id
    )
    st.rerun()


