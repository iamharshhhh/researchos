import streamlit as st
from backend.database import (
    authenticate_user, 
    register_user, 
    get_user_documents,
    get_user_by_email
)

# Configure base application settings
st.set_page_config(
    page_title="ResearchOS | Academic Intelligence Engine",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Auto-login persistence across browser refreshes
user_param = st.query_params.get("u")
if not st.session_state.get("logged_in") and user_param:
    user_info = get_user_by_email(user_param)
    if user_info:
        st.session_state["logged_in"] = True
        st.session_state["user_email"] = user_param
        st.session_state["user_name"] = user_info["name"]
        st.session_state["library_metadata"] = get_user_documents(user_param)

# Initialize Session Authentication State defaults
st.session_state.setdefault("logged_in", False)
st.session_state.setdefault("user_email", None)
st.session_state.setdefault("user_name", None)

# Custom branding and sidebar styling
st.markdown("""
    <style>
        .auth-brand {
            text-align: center;
            margin-bottom: 24px;
        }
        .auth-brand h1 {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 50%, #818cf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
        }
        .auth-brand p {
            color: #94a3b8;
            font-size: 0.9rem;
        }
        .sidebar-user-card {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 12px 14px;
            margin-bottom: 14px;
        }
        .sidebar-user-card p {
            margin: 0;
            font-size: 0.82rem;
            color: #94a3b8;
        }
        .sidebar-user-card h4 {
            margin: 0 0 2px 0;
            font-size: 0.95rem;
            color: #f8fafc;
        }
    </style>
""", unsafe_allow_html=True)


def login_screen():
    col_l, col_center, col_r = st.columns([1, 1.6, 1])
    with col_center:
        st.markdown("""
            <div class="auth-brand">
                <h1>🧠 ResearchOS</h1>
                <p>Autonomous AI Academic Research & Intelligence Engine</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_register = st.tabs(["🔐 Sign In", "📝 Create Account"])
        
        with tab_login:
            with st.form("login_form"):
                email = st.text_input("Email Address")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In to ResearchOS", type="primary", use_container_width=True)
                
                if submitted:
                    if not email.strip() or not password:
                        st.error("Please enter both email and password.")
                    else:
                        success, result = authenticate_user(email.strip(), password)
                        if success:
                            st.session_state["logged_in"] = True
                            st.session_state["user_email"] = email.strip()
                            st.session_state["user_name"] = result
                            st.session_state["library_metadata"] = get_user_documents(email.strip())
                            st.query_params["u"] = email.strip()
                            st.rerun()
                        else:
                            st.error(result)
                            
        with tab_register:
            with st.form("register_form"):
                reg_name = st.text_input("Full Name")
                reg_email = st.text_input("Email Address")
                reg_pass = st.text_input("Create Password", type="password")
                reg_submitted = st.form_submit_button("Register New Account", type="primary", use_container_width=True)
                
                if reg_submitted:
                    if not reg_name.strip() or not reg_email.strip() or not reg_pass:
                        st.error("Please fill in all required fields.")
                    elif len(reg_pass) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        success, msg = register_user(reg_email.strip(), reg_name.strip(), reg_pass)
                        if success:
                            st.success("Account created successfully! Please sign in.")
                        else:
                            st.error(msg)


# Routing & Navigation
if not st.session_state["logged_in"]:
    login_screen()
else:
    # Ensure current logged-in user is preserved in URL parameters
    if st.session_state.get("user_email") and st.query_params.get("u") != st.session_state.get("user_email"):
        st.query_params["u"] = st.session_state["user_email"]

    pages_dict = {
        "Overview": [
            st.Page("views/dashboard.py", title="Dashboard", icon="📊", default=True)
        ],
        "Papers": [
            st.Page("views/papers/library.py", title="Paper Library", icon="📚"),
            st.Page("views/papers/details.py", title="Paper Details", icon="📄")
        ],
        "AI Intelligence": [
            st.Page("views/ai/chat.py", title="AI Chat", icon="💬"),
            st.Page("views/ai/summarize.py", title="Summarizer", icon="📝"),
            st.Page("views/ai/compare.py", title="Compare Papers", icon="⚖️")
        ],
        "Academic Tools": [
            st.Page("views/tools/formula.py", title="Formula Explainer", icon="📐"),
            st.Page("views/tools/figure.py", title="Figure Explainer", icon="🖼️"),
            st.Page("views/tools/quiz.py", title="Quiz Generator", icon="🎯"),
            st.Page("views/tools/citation.py", title="Citation Generator", icon="🔖")
        ],
        "Knowledge & System": [
            st.Page("views/other/citation_graph.py", title="Citation Graph", icon="🕸️"),
            st.Page("views/other/semantic_search.py", title="Semantic Search", icon="🔍"),
            st.Page("views/other/notes.py", title="Notes", icon="📓"),
            st.Page("views/other/history.py", title="History", icon="🕘"),
            st.Page("views/other/settings.py", title="Settings", icon="⚙️")
        ]
    }
    
    pg = st.navigation(pages_dict)
    
    with st.sidebar:
        user_name = st.session_state.get("user_name", "Researcher")
        user_email = st.session_state.get("user_email", "user@researchos.ai")
        
        st.markdown(f"""
            <div class="sidebar-user-card">
                <h4>👤 {user_name}</h4>
                <p>{user_email}</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Sign Out", use_container_width=True, key="sidebar_logout_btn"):
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()
            
    pg.run()
