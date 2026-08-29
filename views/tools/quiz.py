import streamlit as st
import time
import json
import re
import google.generativeai as genai
from backend.database import get_user_documents, save_user_note, log_user_activity
from backend.config import MODEL_NAME
from backend.db import search_documents

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Page configuration
st.set_page_config(
    page_title="Quiz Generator | ResearchOS",
    page_icon="🎯",
    layout="wide"
)

# Ultra-Modern Dark Glassmorphic Styling (Matching AI Chat, Summarizer, Compare & Citation)
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
        /* Score Card */
        .score-banner {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95));
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 20px 24px;
            margin-bottom: 22px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 12px;
        }
        .score-number {
            font-size: 1.8rem;
            font-weight: 700;
            color: #60a5fa;
        }
        /* Question Card */
        .question-box {
            background-color: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px 22px;
            margin-bottom: 18px;
        }
        .question-title {
            font-size: 1rem;
            font-weight: 600;
            color: #f8fafc;
            margin-bottom: 14px;
            line-height: 1.5;
        }
        .explanation-box {
            background: rgba(15, 23, 42, 0.7);
            border-left: 3px solid #60a5fa;
            border-radius: 0 8px 8px 0;
            padding: 12px 16px;
            margin-top: 14px;
            font-size: 0.88rem;
            color: #cbd5e1;
            line-height: 1.6;
        }
        /* Action Row Buttons */
        div[class*="st-key-quiz_btn_"] button {
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
        div[class*="st-key-quiz_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        div[class*="st-key-quiz_btn_"] button p,
        div[class*="st-key-quiz_btn_"] button div {
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
    col_back_quiz, col_title_quiz = st.columns([1.5, 4.5])
    with col_back_quiz:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_quiz", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_quiz:
        st.markdown("<h3 class='header-title'>🎯 Interactive Paper Quiz Generator</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 class='header-title'>🎯 Interactive Paper Quiz Generator</h3>", unsafe_allow_html=True)

st.markdown("<p class='header-subtitle'>Test and validate your technical comprehension of research papers through rigorous, AI-generated multiple-choice questions.</p>", unsafe_allow_html=True)

if not library:
    st.info("📚 No papers found in your library. Please upload research papers first to generate interactive quizzes.")
    if st.button("📤 Go to Upload Papers", type="primary"):
        st.switch_page("views/papers/library.py")
    st.stop()

# Paper Mapping
paper_map = {f"📄 {p['title']} (ID: {p['id']})": p for p in library}
paper_options = list(paper_map.keys())

default_quiz_idx = 0
if 'selected_paper_id' in st.session_state and st.session_state['selected_paper_id']:
    target_id = str(st.session_state['selected_paper_id'])
    for idx, (p_label, p_data) in enumerate(paper_map.items()):
        if str(p_data.get('id')) == target_id:
            default_quiz_idx = idx
            break

# 2. Controls Toolbar
col_p, col_d, col_n = st.columns([2.0, 1.2, 0.8])

difficulty_options = [
    "Easy (Core Concepts & Intuition)",
    "Medium (Methodology & Architecture)",
    "Hard (Mathematical Rigor & Complex Details)"
]

with col_p:
    selected_paper_label = st.selectbox(
        "Select Paper",
        paper_options,
        index=default_quiz_idx,
        label_visibility="collapsed",
        key="quiz_paper_select"
    )

selected_paper = paper_map.get(selected_paper_label, list(paper_map.values())[0] if paper_map else {})

with col_d:
    selected_difficulty = st.selectbox(
        "Difficulty",
        difficulty_options,
        index=1,
        label_visibility="collapsed",
        key="quiz_difficulty_select"
    )

with col_n:
    num_questions = st.selectbox(
        "Number of Questions",
        [3, 5, 10],
        index=1,
        label_visibility="collapsed",
        key="quiz_num_select"
    )

with st.expander("⚙️ Optional Custom Topic Focus", expanded=False):
    focus_topic = st.text_input(
        "Focus on Specific Section / Mechanism (Optional)",
        placeholder="e.g. Attention weights, Loss formulation, Benchmark metrics, Ablation studies",
        key="quiz_focus_topic"
    )

# 3. AI Quiz Generator Pipeline
def generate_ai_quiz(paper_title: str, doc_id: str, difficulty: str, count: int, topic: str = "") -> list:
    """Retrieves document chunks and prompts Gemini to generate structured MCQs in JSON."""
    try:
        query_str = f"{topic} methodology architecture equations results discussion" if topic else "introduction methodology architecture equations empirical results"
        results = search_documents(query=query_str, n_results=6, filter_doc_ids=[doc_id])
        chunks = results.get("documents", [[]])[0] if results and "documents" in results else []
        context_str = "\n\n---\n\n".join(chunks)
    except Exception:
        context_str = f"Paper Title: {paper_title}"

    prompt = f"""You are an elite academic professor and machine learning researcher creating an examination for graduate students.
Analyze the following research paper excerpts and generate {count} high-quality, technically rigorous Multiple-Choice Questions (MCQs).

Paper Title: {paper_title}
Difficulty Level: {difficulty}
{"Specific Topic Focus: " + topic if topic else ""}

Context from Paper:
{context_str}

REQUIREMENTS:
1. Each question must test genuine scientific or technical understanding of the paper (no superficial trivia).
2. Provide exactly 4 options per question (index 0, 1, 2, 3).
3. The options must be realistic and challenging; exactly one option is unambiguously correct according to the paper.
4. Include an 'explanation' citing the exact concept or mechanism from the paper.
5. Format the output strictly as a valid JSON array of objects without markdown formatting around it.

JSON SCHEMA:
[
  {{
    "id": 1,
    "question": "Clear, precise technical question text?",
    "options": [
      "Option A",
      "Option B",
      "Option C",
      "Option D"
    ],
    "correct_index": 0,
    "explanation": "Detailed explanation of why this answer is correct based on the paper's findings."
  }}
]
Output ONLY the raw JSON array:"""

    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    raw_text = response.text.strip() if response else "[]"
    
    # Clean possible markdown block wrappers
    raw_text = re.sub(r'^```(?:json)?\s*', '', raw_text, flags=re.MULTILINE)
    raw_text = re.sub(r'\s*```$', '', raw_text, flags=re.MULTILINE)
    
    try:
        quiz_data = json.loads(raw_text)
        return quiz_data if isinstance(quiz_data, list) else []
    except Exception:
        # Fallback JSON parser with regex extraction
        match = re.search(r'\[\s*\{.*\}\s*\]', raw_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return []

# Generate Button Action
btn_generate_quiz = st.button("✨ Generate AI Quiz", type="primary", use_container_width=True, key="btn_gen_quiz")

if btn_generate_quiz:
    with st.spinner(f"Reading '{selected_paper['title']}' & synthesizing {num_questions} {selected_difficulty.split()[0]} questions with Gemini..."):
        quiz_list = generate_ai_quiz(
            paper_title=selected_paper["title"],
            doc_id=selected_paper["id"],
            difficulty=selected_difficulty,
            count=num_questions,
            topic=focus_topic.strip() if focus_topic else ""
        )
        if quiz_list:
            quiz_dict = {
                "questions": quiz_list,
                "paper_title": selected_paper["title"],
                "doc_id": selected_paper["id"],
                "difficulty": selected_difficulty,
                "created_at": time.time(),
                "submitted": False,
                "user_answers": {}
            }
            st.session_state["current_quiz"] = quiz_dict
            log_user_activity(
                user_email,
                "Quiz Generator",
                selected_difficulty,
                f"Quiz: {selected_paper['title']}",
                json.dumps(quiz_dict),
                selected_paper['id']
            )
            st.rerun()
        else:
            st.error("Failed to generate quiz questions. Please try again.")

# 4. Empty State Hero (When No Quiz Yet)
if "current_quiz" not in st.session_state or not st.session_state["current_quiz"]:
    st.markdown("""
        <div class="empty-hero">
            <h2>Test Your Knowledge on Any Paper</h2>
            <p>Select a paper and difficulty level above to generate a customized multiple-choice comprehension quiz.</p>
        </div>
    """, unsafe_allow_html=True)

# 5. Interactive Quiz Presentation & Grading
if "current_quiz" in st.session_state and st.session_state["current_quiz"]:
    quiz = st.session_state["current_quiz"]
    questions = quiz["questions"]
    is_submitted = quiz.get("submitted", False)
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    # Quiz Header Info
    st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:14px; padding-bottom:8px; border-bottom:1px solid #334155;">
            <div>
                <span style="font-size:0.95rem; font-weight:600; color:#f8fafc;">📝 {quiz['paper_title']}</span>
            </div>
            <div style="font-size:0.82rem; color:#94a3b8;">
                🏷️ <b>Difficulty:</b> <span style="color:#60a5fa;">{quiz['difficulty'].split()[0]}</span> • 📊 {len(questions)} Questions
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # If submitted, show score banner
    if is_submitted:
        score = 0
        user_answers = quiz.get("user_answers", {})
        for idx, q in enumerate(questions):
            ans = user_answers.get(idx)
            if ans is not None and ans == q.get("correct_index"):
                score += 1
                
        pct = int(round((score / len(questions)) * 100)) if questions else 0
        grade_color = "#4ade80" if pct >= 70 else ("#facc15" if pct >= 50 else "#f87171")
        grade_msg = "🌟 Outstanding Mastery!" if pct >= 80 else ("👍 Solid Comprehension!" if pct >= 60 else "💡 Good Effort! Review the explanations below.")
        
        st.markdown(f"""
            <div class="score-banner">
                <div>
                    <p style="margin:0; font-size:0.85rem; color:#94a3b8; font-weight:500;">Quiz Completed</p>
                    <h3 style="margin:4px 0 0 0; color:#f8fafc; font-size:1.25rem;">{grade_msg}</h3>
                </div>
                <div style="text-align:right;">
                    <span class="score-number" style="color:{grade_color};">{score} / {len(questions)}</span>
                    <span style="font-size:0.9rem; color:#94a3b8;"> ({pct}%)</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Render Question Cards
    user_choices = {}
    for idx, q in enumerate(questions):
        with st.container(border=True):
            st.markdown(f"**Q{idx+1}: {q.get('question', 'Question')}**")
            
            opts = q.get("options", [])
            correct_idx = q.get("correct_index", 0)
            
            # Key for state
            widget_key = f"quiz_q_{idx}"
            
            if not is_submitted:
                choice = st.radio(
                    f"Select answer for Q{idx+1}:",
                    opts,
                    index=None,
                    key=widget_key,
                    label_visibility="collapsed"
                )
                if choice in opts:
                    user_choices[idx] = opts.index(choice)
            else:
                user_ans_idx = quiz.get("user_answers", {}).get(idx)
                
                # Show chosen answer vs correct answer
                for o_idx, opt_text in enumerate(opts):
                    if o_idx == correct_idx and o_idx == user_ans_idx:
                        st.markdown(f"<p style='color:#4ade80; font-weight:600; margin:4px 0;'>✅ <b>{opt_text}</b> <span style='font-size:0.8rem;'>(Your Correct Answer)</span></p>", unsafe_allow_html=True)
                    elif o_idx == correct_idx:
                        st.markdown(f"<p style='color:#4ade80; font-weight:600; margin:4px 0;'>🟢 <b>{opt_text}</b> <span style='font-size:0.8rem;'>(Correct Answer)</span></p>", unsafe_allow_html=True)
                    elif o_idx == user_ans_idx:
                        st.markdown(f"<p style='color:#f87171; font-weight:600; margin:4px 0;'>❌ <s>{opt_text}</s> <span style='font-size:0.8rem;'>(Your Answer)</span></p>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<p style='color:#94a3b8; margin:4px 0;'>⚪ {opt_text}</p>", unsafe_allow_html=True)
                
                # Explanation Box
                exp_text = q.get("explanation", "")
                if exp_text:
                    st.markdown(f"""
                        <div class="explanation-box">
                            💡 <b>Academic Explanation:</b> {exp_text}
                        </div>
                    """, unsafe_allow_html=True)

    # 6. Action Bar
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    if not is_submitted:
        if st.button("📊 Submit & Grade Quiz", type="primary", use_container_width=True, key="quiz_btn_submit"):
            if len(user_choices) < len(questions):
                st.warning(f"⚠️ You answered {len(user_choices)} of {len(questions)} questions. Please answer all questions before submitting.")
            else:
                quiz["submitted"] = True
                quiz["user_answers"] = user_choices
                st.rerun()
    else:
        c_act1, c_act2, c_act3, c_spacer = st.columns([1.8, 1.8, 1.6, 2.0])
        
        with c_act1:
            if st.button("💾 Save to Notes", key="quiz_btn_save", use_container_width=True, help="Save quiz questions, answers, and explanations to Personal Notes"):
                # Format note content
                note_lines = [f"# Quiz Results: {quiz['paper_title']}", f"**Difficulty:** {quiz['difficulty']} | **Score:** {score}/{len(questions)} ({pct}%)\n"]
                for i, q in enumerate(questions):
                    note_lines.append(f"### Q{i+1}: {q['question']}")
                    correct_text = q['options'][q['correct_index']] if q.get('options') and len(q['options']) > q['correct_index'] else "N/A"
                    note_lines.append(f"**Correct Answer:** {correct_text}")
                    note_lines.append(f"**Explanation:** {q.get('explanation', '')}\n")
                    
                saved = save_user_note(
                    user_email=user_email,
                    title=f"Quiz: {quiz['paper_title'][:30]}",
                    content="\n".join(note_lines),
                    notebook="Paper Quizzes"
                )
                if saved:
                    st.toast("✅ Quiz & Explanations saved to Personal Notes!", icon="📝")
                else:
                    st.error("Failed to save note.")
                    
        with c_act2:
            if st.button("🔄 Retake Quiz", key="quiz_btn_retake", use_container_width=True, help="Clear answers and retake this quiz"):
                quiz["submitted"] = False
                quiz["user_answers"] = {}
                st.rerun()
                
        with c_act3:
            if st.button("🗑️ Clear", key="quiz_btn_clear", use_container_width=True, help="Clear this quiz"):
                st.session_state["current_quiz"] = None
                st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopQuizEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopQuizEnd, ms));
        </script>
    """, height=0)
