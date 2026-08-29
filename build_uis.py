import os

uis = {}

uis["views/papers/upload.py"] = '''import streamlit as st
import time

st.set_page_config(page_title="Upload PDF | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("📤 Upload PDF")
st.markdown("Drag and drop your research papers here to add them to your knowledge base.")
st.divider()

uploaded_files = st.file_uploader("Upload Documents (PDF)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.success(f"Staged {len(uploaded_files)} file(s) for processing.")
    
    col1, col2 = st.columns(2)
    with col1:
        domain = st.selectbox("Assign Domain", ["NLP", "Computer Vision", "Machine Learning", "Biology", "Physics", "Other"])
    with col2:
        tags = st.text_input("Tags (comma separated)", placeholder="e.g. transformer, attention, state-of-the-art")
        
    if st.button("Process & Extract Metadata", type="primary", width="stretch"):
        with st.spinner("Extracting text and running OCR..."):
            time.sleep(2)
        st.success("Documents successfully processed and added to the library!")
'''

uis["views/papers/details.py"] = '''import streamlit as st

st.set_page_config(page_title="Paper Details | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("📄 Paper Details")
st.divider()

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("## Attention Is All You Need")
    st.markdown("**Authors:** Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin")
    st.markdown("**Year:** 2017 | **Domain:** NLP")
    
    st.markdown("### Abstract")
    st.info("The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely...")
    
    st.button("📖 Read Full PDF", type="primary")

with col2:
    with st.container(border=True):
        st.subheader("Metadata")
        st.markdown("**Citations:** ~102,450")
        st.markdown("**Tags:** `transformer` `self-attention` `seq2seq`")
        st.markdown("**Date Added:** Oct 12, 2025")
        
        st.divider()
        st.button("💬 Chat with this Paper", width="stretch")
        st.button("📝 Summarize", width="stretch")
        st.button("🔖 Generate Citation", width="stretch")
'''

uis["views/ai/compare.py"] = '''import streamlit as st

st.set_page_config(page_title="Compare Papers | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("⚖️ Compare Papers")
st.markdown("Place two papers side-by-side to compare their methodologies and results directly.")
st.divider()

col_sel1, col_sel2 = st.columns(2)
papers = ["Attention Is All You Need (2017)", "BERT: Pre-training (2018)", "GPT-3 (2020)"]

with col_sel1:
    paper1 = st.selectbox("Paper A", papers, index=0)
with col_sel2:
    paper2 = st.selectbox("Paper B", papers, index=1)

st.divider()

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader(paper1)
        st.markdown("**Architecture:** Encoder-Decoder Transformer")
        st.markdown("**Training Objective:** Machine Translation (Seq2Seq)")
        st.markdown("**Context:** Left-to-Right decoding")
        st.markdown("**Key Innovation:** Self-attention replacing RNNs.")

with col2:
    with st.container(border=True):
        st.subheader(paper2)
        st.markdown("**Architecture:** Encoder-Only Transformer")
        st.markdown("**Training Objective:** Masked Language Modeling (MLM)")
        st.markdown("**Context:** Deep Bidirectional")
        st.markdown("**Key Innovation:** Unsupervised pre-training for NLU.")
'''

uis["views/research/ideas.py"] = '''import streamlit as st
import time

st.set_page_config(page_title="Research Ideas | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("💡 Research Idea Generator")
st.markdown("Uses your library to brainstorm novel, unexplored research directions.")
st.divider()

domain = st.selectbox("Target Domain", ["NLP", "Computer Vision", "Multimodal", "General"])
if st.button("Brainstorm Ideas 🚀", type="primary"):
    with st.spinner("Analyzing library gaps and generating novel intersections..."):
        time.sleep(2)
        
    st.success("Generated 3 novel research ideas!")
    
    with st.container(border=True):
        st.markdown("### 1. Sparse-Attention Multimodal Transformers")
        st.markdown("**Premise:** Current multimodal models use dense attention. By applying local sparse attention to visual tokens and global attention to text tokens, computational efficiency could improve by 40%.")
        st.button("Save to Notes", key="i1")
        
    with st.container(border=True):
        st.markdown("### 2. Retrieval-Augmented Pre-training for Code")
        st.markdown("**Premise:** Instead of RAG at inference, inject retrieved AST (Abstract Syntax Tree) chunks directly into the MLM pre-training objective.")
        st.button("Save to Notes", key="i2")
'''

uis["views/research/experiment.py"] = '''import streamlit as st
import time

st.set_page_config(page_title="Experiment Planner | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("🧪 Experiment Planner")
st.markdown("Turn a research idea into a concrete experimental protocol.")
st.divider()

idea = st.text_area("Describe your research idea or hypothesis:", placeholder="e.g. Using sparse attention to speed up video processing transformers...")

if st.button("Generate Experimental Design", type="primary"):
    with st.spinner("Designing protocol..."):
        time.sleep(2)
        
    with st.container(border=True):
        st.subheader("Proposed Protocol")
        st.markdown("#### 1. Baselines")
        st.markdown("- Standard Dense Vision Transformer (ViT-Base)")
        st.markdown("- Longformer applied to video frames")
        
        st.markdown("#### 2. Datasets")
        st.markdown("- Kinetics-400 (Action Recognition)")
        st.markdown("- Something-Something V2 (Temporal Reasoning)")
        
        st.markdown("#### 3. Evaluation Metrics")
        st.markdown("- Top-1 and Top-5 Accuracy")
        st.markdown("- Inference Latency (ms/video)")
        st.markdown("- Peak GPU Memory Usage (GB)")
        
        st.button("Export to PDF")
'''

uis["views/tools/citation.py"] = '''import streamlit as st

st.set_page_config(page_title="Citation Generator | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("🔖 Citation Generator")
st.divider()

paper = st.selectbox("Select Paper", ["Attention Is All You Need (2017)", "BERT: Pre-training (2018)"])
format_type = st.radio("Citation Format", ["APA", "MLA", "Chicago", "BibTeX"], horizontal=True)

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    if format_type == "APA":
        st.code("Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). Attention is all you need. Advances in neural information processing systems, 30.", language="markdown")
    elif format_type == "MLA":
        st.code("Vaswani, Ashish, et al. 'Attention is all you need.' Advances in neural information processing systems 30 (2017).", language="markdown")
    elif format_type == "BibTeX":
        st.code("""@inproceedings{vaswani2017attention,
  title={Attention is all you need},
  author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob and Jones, Llion and Gomez, Aidan N and Kaiser, {\L}ukasz and Polosukhin, Illia},
  booktitle={Advances in neural information processing systems},
  year={2017}
}""", language="bibtex")

st.button("📋 Copy to Clipboard")
'''

uis["views/tools/quiz.py"] = '''import streamlit as st
import time

st.set_page_config(page_title="Quiz Generator | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("❓ Quiz Generator")
st.markdown("Test your comprehension of a paper by taking an AI-generated quiz.")
st.divider()

col1, col2 = st.columns(2)
with col1:
    paper = st.selectbox("Select Paper", ["Attention Is All You Need (2017)"])
with col2:
    difficulty = st.selectbox("Difficulty", ["Easy (High-level)", "Medium (Concepts)", "Hard (Math & Details)"])

if st.button("Generate Quiz", type="primary"):
    with st.spinner("Generating questions..."):
        time.sleep(1.5)
        
    with st.container(border=True):
        st.markdown("**Q1: What mechanism completely replaces recurrence and convolutions in the Transformer architecture?**")
        st.radio("Select an answer:", ["LSTMs", "Self-Attention", "Residual Connections", "Word2Vec"])
        
        st.divider()
        st.markdown("**Q2: What is the purpose of Positional Encoding in the Transformer?**")
        st.radio("Select an answer:", ["To inject information about the relative or absolute position of tokens", "To normalize the outputs", "To calculate the dot-product", "To mask future tokens"], key="q2")
        
        st.button("Submit Answers")
'''

uis["views/tools/formula.py"] = '''import streamlit as st

st.set_page_config(page_title="Formula Explainer | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("📐 Formula Explainer")
st.markdown("Input complex mathematical formulas from papers to get a breakdown of what each term means.")
st.divider()

formula = st.text_input("LaTeX Formula", value=r"Attention(Q, K, V) = softmax(\frac{QK^T}{\sqrt{d_k}})V")
st.latex(formula)

if st.button("Explain Formula", type="primary"):
    with st.container(border=True):
        st.markdown("### Term Breakdown")
        st.markdown("- **Q (Queries):** A matrix representing the current token you are trying to compute attention for.")
        st.markdown("- **K (Keys):** A matrix representing all other tokens in the sequence you are attending to.")
        st.markdown("- **V (Values):** The actual representations of the tokens that will be weighted and summed.")
        st.markdown("- **$d_k$:** The dimension of the queries and keys. Dividing by its square root prevents the dot products from growing too large, which would push the softmax function into regions with extremely small gradients.")
'''

uis["views/tools/figure.py"] = '''import streamlit as st

st.set_page_config(page_title="Figure Explainer | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("🖼️ Figure Explainer")
st.markdown("Upload a screenshot of a complex chart or diagram from a paper to get a detailed explanation.")
st.divider()

st.file_uploader("Upload Image (PNG/JPG)", type=["png", "jpg", "jpeg"])
st.info("Upload a figure to see the AI breakdown here.")
'''

uis["views/other/citation_graph.py"] = '''import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Citation Graph | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("🕸️ Citation Graph")
st.markdown("Visualize the relationships between papers in your library.")
st.divider()

# Dummy network graph using plotly
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=[1, 2, 3, 2],
    y=[2, 3, 2, 1],
    mode='markers+text',
    text=["Transformer", "BERT", "GPT-3", "ViT"],
    textposition="top center",
    marker=dict(size=40, color="#3b82f6")
))
# Add edges
fig.add_trace(go.Scatter(
    x=[1, 2, None, 1, 3, None, 1, 2],
    y=[2, 3, None, 2, 2, None, 2, 1],
    mode='lines',
    line=dict(width=2, color="#94a3b8")
))

fig.update_layout(showlegend=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", xaxis=dict(visible=False), yaxis=dict(visible=False))
st.plotly_chart(fig, use_container_width=True)
'''

uis["views/other/voice.py"] = '''import streamlit as st

st.set_page_config(page_title="Voice Assistant | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("🎤 Voice Assistant")
st.markdown("Talk to your research library hands-free.")
st.divider()

st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
st.button("🎙️ Click to Speak", type="primary")
st.markdown("</div>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("*Transcript will appear here...*")
'''

uis["views/other/notes.py"] = '''import streamlit as st

st.set_page_config(page_title="Notes | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("📝 Personal Notes")
st.divider()

col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Your Notebooks")
    st.selectbox("Select Notebook", ["General Ideas", "NLP Literature Review", "Math Proofs"])
    st.button("+ New Note")
    
with col2:
    st.text_area("Markdown Editor", height=400, value="# NLP Review\\n\\nTransformers are great because...")
    st.button("💾 Save Note", type="primary")
'''

uis["views/other/history.py"] = '''import streamlit as st
import pandas as pd

st.set_page_config(page_title="History | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("🕘 Action History")
st.markdown("Review your past interactions, chats, and generated reviews.")
st.divider()

history = pd.DataFrame({
    "Date": ["2026-08-12", "2026-08-11", "2026-08-10"],
    "Action Type": ["Chat", "Literature Review", "Document Upload"],
    "Details": ["Asked about Transformer attention", "Compared BERT and GPT-3", "Uploaded 'Attention is All You Need'"]
})
st.dataframe(history, hide_index=True, use_container_width=True)
'''

uis["views/other/settings.py"] = '''import streamlit as st

st.set_page_config(page_title="Settings | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

st.title("⚙️ Settings")
st.divider()

st.subheader("🤖 AI Provider")
st.selectbox("Select LLM Provider", ["OpenAI (GPT-4o)", "Anthropic (Claude 3)", "Local (Ollama)"])
st.text_input("API Key", type="password", placeholder="sk-...")

st.subheader("🗄️ Database")
st.selectbox("Vector Store", ["ChromaDB (Local)", "FAISS (Local)", "Pinecone (Cloud)"])

st.subheader("🎨 Appearance")
st.radio("Theme", ["Dark Mode", "Light Mode", "System Default"])

st.markdown("<br>", unsafe_allow_html=True)
st.button("💾 Save Settings", type="primary")
'''

for path, content in uis.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written {path}")
