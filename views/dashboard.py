import streamlit as st
import pandas as pd
import plotly.express as px

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

st.set_page_config(
    page_title="ResearchOS | Dashboard",
    page_icon="🧠",
    layout="wide"
)

# Custom CSS for some minor styling tweaks
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        h1 {
            color: #e2e8f0;
        }
        .stat-card {
            background-color: #1e293b;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #334155;
            text-align: center;
        }
        .stat-card h3 {
            margin: 0;
            color: #94a3b8;
            font-size: 1rem;
        }
        .stat-card h2 {
            margin: 10px 0 0 0;
            color: #f8fafc;
            font-size: 2.5rem;
        }
    </style>
""", unsafe_allow_html=True)


# Header
user_name = st.session_state.get('user_name', 'Researcher')
first_name = user_name.split()[0] if user_name else 'Researcher'
st.title(f"Welcome back, {first_name} 👋")
st.markdown("Here is what's happening with your research today.")

st.markdown("<br>", unsafe_allow_html=True)

from backend.database import get_user_documents, get_user_chat_interaction_count

# Fetch Dynamic Data from PostgreSQL
user_email = st.session_state.get('user_email', 'guest@example.com')
library = get_user_documents(user_email)
st.session_state['library_metadata'] = library
total_papers = len(library)

# Dynamic Real-time AI Chat Interactions from Database
chat_interactions = get_user_chat_interaction_count(user_email)

# Stat Cards
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.markdown(f"""
        <div class="stat-card">
            <h3>Total Papers</h3>
            <h2>{total_papers}</h2>
        </div>
    """, unsafe_allow_html=True)

with col_b:
    st.markdown(f"""
        <div class="stat-card">
            <h3>AI Chat Interactions</h3>
            <h2>{chat_interactions}</h2>
        </div>
    """, unsafe_allow_html=True)

with col_c:
    # Count unique domains
    domains = {p.get('domain', 'Other') for p in library}
    total_domains = len(domains)
    st.markdown(f"""
        <div class="stat-card">
            <h3>Research Domains</h3>
            <h2>{total_domains}</h2>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Main Content Grid
left_col, right_col = st.columns([2, 1])

with left_col:
    st.subheader("Research Activity (Past 7 Days)")
    
    # Dynamic 7-day activity tracking
    from datetime import datetime, timedelta
    from backend.database import get_user_activities
    
    user_acts = get_user_activities(user_email)
    now = datetime.now()
    days_list = [(now - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
    day_counts = {d: 0 for d in days_list}
    
    for act in user_acts:
        try:
            dt_str = str(act.get("created_at", ""))[:10]
            act_date = datetime.strptime(dt_str, "%Y-%m-%d")
            d_lbl = act_date.strftime("%a")
            if d_lbl in day_counts and (now - act_date).days < 7:
                day_counts[d_lbl] += 1
        except Exception:
            pass
            
    today_lbl = now.strftime("%a")
    if day_counts[today_lbl] < chat_interactions:
        day_counts[today_lbl] = max(day_counts[today_lbl], chat_interactions)
        
    chart_data = pd.DataFrame({
        "Day": list(day_counts.keys()),
        "Activity": list(day_counts.values())
    })
    
    fig = px.area(chart_data, x="Day", y="Activity", template="plotly_dark")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="#334155")
    )
    fig.update_traces(line_color="#3b82f6", fillcolor="rgba(59, 130, 246, 0.3)")
    st.plotly_chart(fig, use_container_width=True)

with right_col:
    st.subheader("Recent Papers")
    
    if not library:
        st.info("No papers uploaded yet.")
    else:
        # Get the last 3 uploaded papers
        recent_papers = library[-3:]
        recent_papers.reverse() # Show newest first
        
        for paper in recent_papers:
            with st.container():
                st.markdown(f"**{paper.get('title', 'Untitled')}**")
                st.caption(f"Domain: {paper.get('domain', 'Unknown')} • Tags: {paper.get('tags', 'None')}")
                st.divider()
    
    if st.button("🕒 View Library", width="stretch"):
        st.switch_page("views/papers/library.py")
