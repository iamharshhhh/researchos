import streamlit as st
import time
from backend.database import (
    get_user_account_stats,
    update_user_name,
    update_user_password
)

# Authentication check
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')
user_name = st.session_state.get('user_name', 'Researcher')

# Page configuration
st.set_page_config(
    page_title="Settings | ResearchOS",
    page_icon="⚙️",
    layout="wide"
)

# Fetch user account statistics
stats = get_user_account_stats(user_email)
display_name = st.session_state.get('user_name', stats['name'])

# Get user initials for avatar
initials = "".join([part[0].upper() for part in display_name.split()[:2]]) if display_name else "R"

# Ultra-Stylish Glassmorphic Dark Styling
st.markdown("""
    <style>
        .block-container {
            max-width: 1000px;
            padding-top: 1.5rem;
            padding-bottom: 3.5rem;
            margin: 0 auto;
        }
        /* Top Hero Profile Banner */
        .profile-hero-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%);
            border: 1px solid rgba(51, 65, 85, 0.8);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            backdrop-filter: blur(12px);
        }
        .hero-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .profile-avatar-circle {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            background: linear-gradient(135deg, #6366f1 0%, #3b82f6 50%, #06b6d4 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.8rem;
            font-weight: 700;
            color: #ffffff;
            box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
            border: 2px solid rgba(255, 255, 255, 0.15);
        }
        .hero-info h2 {
            font-size: 1.45rem;
            font-weight: 700;
            color: #f8fafc;
            margin: 0 0 4px 0;
            letter-spacing: -0.01em;
        }
        .hero-info p {
            color: #94a3b8;
            font-size: 0.88rem;
            margin: 0 0 6px 0;
        }
        .hero-badges {
            display: flex;
            align-items: center;
            gap: 8px;
            flex-wrap: wrap;
        }
        .hero-badge-verified {
            background: rgba(34, 197, 94, 0.15);
            color: #4ade80;
            border: 1px solid rgba(34, 197, 94, 0.3);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.76rem;
            font-weight: 600;
        }
        .hero-badge-id {
            background: rgba(56, 189, 248, 0.12);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.25);
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.76rem;
            font-weight: 500;
        }
        /* Micro Stats Strip */
        .micro-stats-strip {
            display: flex;
            align-items: center;
            gap: 16px;
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid #334155;
            padding: 10px 18px;
            border-radius: 12px;
        }
        .micro-stat-item {
            text-align: center;
        }
        .micro-stat-num {
            font-size: 1.15rem;
            font-weight: 700;
            color: #60a5fa;
            line-height: 1.1;
        }
        .micro-stat-lbl {
            font-size: 0.72rem;
            color: #94a3b8;
            font-weight: 500;
        }
        .micro-stat-divider {
            width: 1px;
            height: 26px;
            background: #334155;
        }
        /* Stylish Section Card Headers */
        .section-header-box {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 1px solid #334155;
        }
        .section-header-icon {
            font-size: 1.3rem;
        }
        .section-header-title {
            font-size: 1.12rem;
            font-weight: 600;
            color: #f8fafc;
            margin: 0;
        }
        .section-header-subtitle {
            font-size: 0.8rem;
            color: #94a3b8;
            margin: 2px 0 0 0;
        }
        /* Custom Inputs & Labels */
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextArea"] label {
            font-size: 0.85rem !important;
            font-weight: 600 !important;
            color: #cbd5e1 !important;
            margin-bottom: 4px !important;
        }
        /* Buttons */
        div[class*="st-key-btn_save_profile"] button {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
            border: 1px solid #60a5fa !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            height: 42px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 14px rgba(59, 130, 246, 0.3) !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-btn_save_profile"] button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(59, 130, 246, 0.45) !important;
        }
        div[class*="st-key-btn_update_pass"] button {
            background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%) !important;
            border: 1px solid #818cf8 !important;
            color: #ffffff !important;
            font-weight: 600 !important;
            height: 42px !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.3) !important;
            transition: all 0.2s ease-in-out !important;
        }
        div[class*="st-key-btn_update_pass"] button:hover {
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45) !important;
        }
        /* Checklist */
        .sec-check-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.8rem;
            color: #94a3b8;
            margin-bottom: 6px;
        }
    </style>
""", unsafe_allow_html=True)

# 1. Top Profile Hero Card
st.markdown(f"""
<div class="profile-hero-card">
    <div class="hero-left">
        <div class="profile-avatar-circle">{initials}</div>
        <div class="hero-info">
            <h2>{display_name}</h2>
            <p>{user_email}</p>
            <div class="hero-badges">
                <span class="hero-badge-verified">🛡️ Verified Researcher</span>
                <span class="hero-badge-id">Member since: {stats['created_at']}</span>
            </div>
        </div>
    </div>
    <div class="micro-stats-strip">
        <div class="micro-stat-item">
            <div class="micro-stat-num">{stats['paper_count']}</div>
            <div class="micro-stat-lbl">Papers</div>
        </div>
        <div class="micro-stat-divider"></div>
        <div class="micro-stat-item">
            <div class="micro-stat-num">{stats['note_count']}</div>
            <div class="micro-stat-lbl">Notes</div>
        </div>
        <div class="micro-stat-divider"></div>
        <div class="micro-stat-item">
            <div class="micro-stat-num">{stats['session_count']}</div>
            <div class="micro-stat-lbl">Threads</div>
        </div>
        <div class="micro-stat-divider"></div>
        <div class="micro-stat-item">
            <div class="micro-stat-num">{stats['activity_count']}</div>
            <div class="micro-stat-lbl">Actions</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. Side-by-Side Stylish Dual Panes
col_profile, col_security = st.columns([1.1, 1.0], gap="large")

# ----------------- Pane 1: Profile Information -----------------
with col_profile:
    with st.container(border=True):
        st.markdown("""
            <div class="section-header-box">
                <span class="section-header-icon">👤</span>
                <div>
                    <h3 class="section-header-title">Personal Profile</h3>
                    <p class="section-header-subtitle">Manage your personal and academic research identity.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        edit_name = st.text_input("Display Name", value=display_name, key="set_display_name", placeholder="Enter your full name...")
        st.text_input("Account Email (Immutable)", value=user_email, disabled=True, key="set_email_disabled", help="Your registered research email identifier.")
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            research_field = st.text_input("Primary Domain", value=st.session_state.get("user_domain", "Artificial Intelligence & ML"), key="set_user_domain", placeholder="e.g. NLP, BioMed, ML")
        with col_f2:
            affiliation = st.text_input("Academic Affiliation", value=st.session_state.get("user_affiliation", "IEEE Research Lab"), key="set_user_affil", placeholder="e.g. Stanford, MIT, IEEE")
            
        bio_text = st.text_area("Research Focus / Bio", value=st.session_state.get("user_bio", "Investigating deep representation learning, RAG pipelines, and multimodal document reasoning."), height=90, key="set_user_bio", placeholder="Brief summary of your active research projects...")
        
        st.markdown("<div style='height: 6px;'></div>", unsafe_allow_html=True)
        
        if st.button("💾 Save Profile Changes", use_container_width=True, key="btn_save_profile"):
            if edit_name.strip():
                success, msg = update_user_name(user_email, edit_name.strip())
                if success:
                    st.session_state['user_name'] = edit_name.strip()
                    st.session_state['user_domain'] = research_field.strip()
                    st.session_state['user_affiliation'] = affiliation.strip()
                    st.session_state['user_bio'] = bio_text.strip()
                    st.toast("✅ Profile details updated successfully!", icon="👤")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(msg)
            else:
                st.warning("Display name cannot be empty.")

# ----------------- Pane 2: Security & Password -----------------
with col_security:
    with st.container(border=True):
        st.markdown("""
            <div class="section-header-box">
                <span class="section-header-icon">🔒</span>
                <div>
                    <h3 class="section-header-title">Security & Password</h3>
                    <p class="section-header-subtitle">Keep your account secure with a strong password.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        curr_pass = st.text_input("Current Password", type="password", key="set_curr_pass", placeholder="Enter your current password...")
        new_pass = st.text_input("New Password", type="password", key="set_new_pass", placeholder="At least 6 characters...")
        conf_pass = st.text_input("Confirm New Password", type="password", key="set_conf_pass", placeholder="Re-enter your new password...")
        
        st.markdown("""
            <div style="background:rgba(15, 23, 42, 0.4); border:1px solid #334155; border-radius:8px; padding:10px 14px; margin:10px 0 14px 0;">
                <div class="sec-check-item">🛡️ <b>Encryption:</b> Securely hashed with SHA-256</div>
                <div class="sec-check-item">🔑 <b>Minimum length:</b> 6 characters required</div>
                <div class="sec-check-item">🌐 <b>Session status:</b> Authenticated & Active</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔑 Update Password", use_container_width=True, key="btn_update_pass"):
            if not curr_pass or not new_pass or not conf_pass:
                st.warning("Please fill in all password fields.")
            elif new_pass != conf_pass:
                st.error("New password and confirmation password do not match.")
            elif len(new_pass) < 6:
                st.error("Password must be at least 6 characters long.")
            else:
                success, msg = update_user_password(user_email, curr_pass, new_pass)
                if success:
                    st.toast("✅ Password changed successfully!", icon="🔒")
                else:
                    st.error(msg)

# 3. Bottom Clean Session Sign Out
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
col_l_sp, col_logout, col_r_sp = st.columns([2.5, 2.0, 2.5])
with col_logout:
    if st.button("🚪 Sign Out of ResearchOS", use_container_width=True, key="btn_logout_clean", help="Safely terminate your active session and return to Login"):
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = None
        st.session_state['user_name'] = None
        st.toast("👋 Signed out successfully.", icon="ℹ️")
        time.sleep(0.4)
        st.switch_page("views/dashboard.py")


