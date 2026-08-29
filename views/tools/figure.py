import streamlit as st
import time
import os
import io
from PIL import Image
import pymupdf
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
    page_title="Figure Explainer | ResearchOS",
    page_icon="🖼️",
    layout="wide"
)

# Ultra-Modern Dark Glassmorphic Styling
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
        /* Scoped Figure Breakdown Container */
        .gemini-figure-view {
            background-color: #1e293b;
            border: 1px solid #334155;
            padding: 24px 26px !important;
            border-radius: 14px !important;
            margin-top: 18px;
            margin-bottom: 20px;
            font-size: 0.95rem;
            line-height: 1.7;
            color: #f1f5f9;
        }
        .gemini-figure-view p {
            line-height: 1.7 !important;
            margin-bottom: 0.85rem !important;
            color: #f1f5f9 !important;
        }
        .gemini-figure-view ul, 
        .gemini-figure-view ol {
            margin-top: 0.4rem !important;
            margin-bottom: 1rem !important;
            padding-left: 1.4rem !important;
        }
        .gemini-figure-view li {
            margin-bottom: 0.5rem !important;
            line-height: 1.65 !important;
            color: #e2e8f0 !important;
        }
        .gemini-figure-view li strong, 
        .gemini-figure-view p strong {
            color: #60a5fa !important;
            font-weight: 600 !important;
        }
        .gemini-figure-view h1,
        .gemini-figure-view h2,
        .gemini-figure-view h3,
        .gemini-figure-view h4 {
            color: #f8fafc !important;
            font-weight: 600 !important;
            margin-top: 1.25rem !important;
            margin-bottom: 0.6rem !important;
            letter-spacing: -0.01em !important;
        }
        .gemini-figure-view h3 {
            font-size: 1.15rem !important;
            color: #93c5fd !important;
        }
        .gemini-figure-view table,
        table {
            width: 100% !important;
            border-collapse: collapse !important;
            margin: 16px 0 !important;
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #334155 !important;
            font-size: 0.9rem !important;
        }
        .gemini-figure-view th,
        th {
            background-color: #0f172a !important;
            color: #60a5fa !important;
            font-weight: 600 !important;
            padding: 10px 14px !important;
            border: 1px solid #334155 !important;
            text-align: left !important;
        }
        .gemini-figure-view td,
        td {
            padding: 9px 14px !important;
            border: 1px solid #334155 !important;
            color: #e2e8f0 !important;
        }
        .gemini-figure-view tr:nth-child(even) {
            background-color: rgba(30, 41, 59, 0.4) !important;
        }
        .gemini-figure-view blockquote {
            border-left: 3px solid #60a5fa !important;
            background: rgba(59, 130, 246, 0.08) !important;
            padding: 10px 16px !important;
            border-radius: 0 8px 8px 0 !important;
            margin: 12px 0 !important;
            color: #cbd5e1 !important;
        }
        /* Action Row Buttons */
        div[class*="st-key-fig_btn_"] button {
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
        div[class*="st-key-fig_btn_"] button:hover {
            border-color: #60a5fa !important;
            background-color: #24344d !important;
            color: #ffffff !important;
        }
        div[class*="st-key-fig_btn_"] button p,
        div[class*="st-key-fig_btn_"] button div {
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
    col_back_fig, col_title_fig = st.columns([1.5, 4.5])
    with col_back_fig:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_fig", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_fig:
        st.markdown("<h3 class='header-title'>🖼️ Academic Figure & Architecture Explainer</h3>", unsafe_allow_html=True)
else:
    st.markdown("<h3 class='header-title'>🖼️ Academic Figure & Architecture Explainer</h3>", unsafe_allow_html=True)

st.markdown("<p class='header-subtitle'>Upload or extract system architectures, benchmark plots, confusion matrices, and diagrams directly from research papers for deep visual and technical breakdowns.</p>", unsafe_allow_html=True)

# Fast Cached Function to extract figures directly from stored PDF
@st.cache_data(show_spinner=False, max_entries=32)
def extract_figures_from_pdf(pdf_path: str, max_images: int = 6) -> list[dict]:
    """Extracts embedded figures and matches them with exact paper captions (e.g. Fig. 1, Figure 2) with high-speed memory caching."""
    if not pdf_path or not os.path.exists(pdf_path):
        return []
    
    extracted = []
    seen_hashes = set()
    
    try:
        import re
        doc = pymupdf.open(pdf_path)
        
        # 1. First pass: extract all captions across all pages
        all_doc_captions = []
        page_caption_map = {}
        
        for p_no in range(len(doc)):
            p_text = doc[p_no].get_text()
            # Look for Fig. X or Figure X or Table X
            caps = re.findall(r'((?:Fig(?:ure|\.)?|Table)\s*\d+[:.\s-][^\n\r]{2,90})', p_text, re.IGNORECASE)
            clean_caps = []
            for c in caps:
                c_clean = re.sub(r'\s+', ' ', c.strip())
                c_clean = c_clean.rstrip(' -:')
                clean_caps.append(c_clean)
            page_caption_map[p_no + 1] = clean_caps
            all_doc_captions.extend(clean_caps)
            
        fig_counter = 1
        
        # 2. Second pass: extract images and match with page captions
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            image_list = page.get_images(full=True)
            page_caps = page_caption_map.get(page_idx + 1, [])
            page_img_idx = 0
            
            for img_info in image_list:
                xref = img_info[0]
                base_image = doc.extract_image(xref)
                
                # Fast dimension pre-check to skip icons/lines without PIL decompression
                w = base_image.get("width", 0)
                h = base_image.get("height", 0)
                if w > 0 and h > 0 and (w < 200 or h < 180):
                    continue
                    
                image_bytes = base_image["image"]
                
                try:
                    pil_img = Image.open(io.BytesIO(image_bytes))
                    if pil_img.width >= 200 and pil_img.height >= 180:
                        img_hash = hash(image_bytes[:500])
                        if img_hash not in seen_hashes:
                            seen_hashes.add(img_hash)
                            
                            # Determine exact figure name as printed in paper
                            if page_img_idx < len(page_caps):
                                exact_title = page_caps[page_img_idx]
                            elif all_doc_captions and fig_counter <= len(all_doc_captions):
                                exact_title = all_doc_captions[fig_counter - 1]
                            else:
                                exact_title = f"Fig. {fig_counter}"
                                
                            if not re.match(r'^(?:Fig|Table)', exact_title, re.IGNORECASE):
                                exact_title = f"Fig. {fig_counter}: {exact_title}"
                                
                            exact_caption = f"{exact_title} (Page {page_idx + 1})"
                            
                            extracted.append({
                                "image": pil_img,
                                "page": page_idx + 1,
                                "exact_title": exact_title,
                                "caption": exact_caption,
                                "width": pil_img.width,
                                "height": pil_img.height
                            })
                            page_img_idx += 1
                            fig_counter += 1
                            
                            if len(extracted) >= max_images:
                                break
                except Exception:
                    continue
            if len(extracted) >= max_images:
                break
                
        # If no raster images were embedded, render key pages as scan images
        if not extracted and len(doc) > 0:
            for page_idx in range(min(len(doc), 2)):
                page = doc[page_idx]
                pix = page.get_pixmap(dpi=150)
                pil_img = Image.open(io.BytesIO(pix.tobytes("png")))
                extracted.append({
                    "image": pil_img,
                    "page": page_idx + 1,
                    "exact_title": f"Fig. {page_idx + 1}: Architecture / Pipeline Scan",
                    "caption": f"Fig. {page_idx + 1}: Architecture / Pipeline Scan (Page {page_idx + 1})",
                    "width": pil_img.width,
                    "height": pil_img.height
                })
    except Exception as e:
        print(f"Figure extraction error: {e}")
        
    return extracted

# Function to run Multimodal AI Figure Explanation
def explain_figure_pipeline(images: list[Image.Image] = None, context_info: str = "", specific_question: str = "") -> str:
    """Invokes Gemini Multimodal Vision API to dissect academic figures and charts."""
    prompt = f"""You are an elite academic peer reviewer, principal AI researcher, and data visualization specialist.
Conduct an exhaustive, high-precision technical deconstruction of the attached research paper figure/diagram.

Provided Context / Paper Details:
{context_info if context_info else "Academic Research Publication"}

{"Specific Researcher Inquiry:" if specific_question else ""}
{specific_question if specific_question else ""}

REQUIRED OUTPUT STRUCTURE:

1. **💡 Executive Visual Summary**:
   - 2-3 crisp, authoritative sentences explaining exactly what this figure represents (e.g. system pipeline, benchmark scatterplot, confusion matrix, ablation curve) and the primary takeaway.

2. **🔍 Component-by-Component Visual Deconstruction Matrix**:
   Provide a standard Markdown table on separate lines breaking down every visual block, color coding, or axis:
| Visual Component / Sub-Module | Color / Notation | Technical Function & Meaning in Pipeline |
| :--- | :--- | :--- |
| Component 1 | Blue box / Solid line | Role in architecture or evaluation |
| Component 2 | Red dashed line | Baseline comparison or loss term |
   - (CRITICAL: Every table row MUST be on its own line without blank lines between them).

3. **⚙️ End-to-End Dataflow & Tensor Trajectory**:
   - Numbered chronological walkthrough of how information, input tensors, attention weights, or sample batches propagate through the diagram from input to final output.

4. **📊 Empirical Trends, Benchmarks & Statistical Significance (if chart/plot)**:
   - Specific analysis of X/Y axes, scale (linear vs log), inflection points, convergence rates, error bars, and margin of victory over compared baselines.

5. **🔬 Methodological Innovations & Practical Implications**:
   - What architectural breakthrough or empirical insight does this figure prove? What are the key takeaways for researchers implementing this system?

Formatting Guidelines:
- Write in elite, rigorous academic prose. Format all math symbols in LaTeX ($...$).
- Never start with self-introductions ("I am..."). Start directly with 💡 Executive Visual Summary."""

    inputs = []
    if images:
        for img in images[:2]:  # Send top relevant figures to Gemini Vision
            inputs.append(img)
    inputs.append(prompt)
    
    raw = call_gemini_with_fallback(inputs)
    return clean_academic_response(raw)

# Tabs: Upload Figure Image vs Search from Library Paper
tab_upload, tab_library = st.tabs(["📤 Upload Figure / Diagram", "📚 Analyze Figure from Library Paper"])

# ----------------- TAB 1: Upload Figure Image -----------------
with tab_upload:
    st.markdown("<p style='font-size:0.88rem; color:#94a3b8; margin-bottom:8px;'>Upload a screenshot or high-resolution image of any diagram, architecture, or plot.</p>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose an image file",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed",
        key="fig_upload_file"
    )
    
    col_c1, col_c2 = st.columns([1.5, 1.5])
    with col_c1:
        paper_context_text = st.text_input(
            "Paper Title / Domain Context (Optional)",
            placeholder="e.g. Attention Is All You Need, Medical Image Segmentation, Llama 3.1",
            key="fig_upload_context"
        )
    with col_c2:
        specific_inq = st.text_input(
            "Specific Focus / Question (Optional)",
            placeholder="e.g. Explain the skip connection, what does the dotted line mean?",
            key="fig_upload_inquiry"
        )
        
    if uploaded_file is not None:
        try:
            image_preview = Image.open(uploaded_file)
            with st.container(border=True):
                st.image(image_preview, caption=f"Uploaded Figure ({uploaded_file.name})", use_container_width=True)
        except Exception as e:
            st.error(f"Error loading image: {e}")
            image_preview = None
    else:
        image_preview = None
        
    btn_explain_upload = st.button("✨ Deconstruct Figure", type="primary", use_container_width=True, key="btn_expl_up")
    
    if btn_explain_upload:
        if image_preview is None:
            st.warning("⚠️ Please upload an image file first.")
        else:
            with st.spinner("Analyzing image pixels, architecture blocks & dataflow..."):
                analysis_text = explain_figure_pipeline(
                    images=[image_preview],
                    context_info=paper_context_text.strip(),
                    specific_question=specific_inq.strip()
                )
                st.session_state["current_figure_analysis"] = {
                    "text": analysis_text,
                    "title": paper_context_text.strip() if paper_context_text.strip() else uploaded_file.name,
                    "created_at": time.time()
                }
                st.rerun()

# ----------------- TAB 2: Analyze from Library Paper -----------------
with tab_library:
    st.markdown("<p style='font-size:0.88rem; color:#94a3b8; margin-bottom:8px;'>Automatically extract diagrams and choose the exact figure you want to deconstruct.</p>", unsafe_allow_html=True)
    
    if not library:
        st.info("📚 No papers found in your library. Please upload papers first or use the 'Upload Figure / Diagram' tab.")
    else:
        paper_map = {f"📄 {p['title']} (ID: {p['id']})": p for p in library}
        default_fig_idx = 0
        if 'selected_paper_id' in st.session_state and st.session_state['selected_paper_id']:
            target_id = str(st.session_state['selected_paper_id'])
            for idx, (p_label, p_data) in enumerate(paper_map.items()):
                if str(p_data.get('id')) == target_id:
                    default_fig_idx = idx
                    break
                    
        selected_paper_label = st.selectbox(
            "Select Library Paper",
            list(paper_map.keys()),
            index=default_fig_idx,
            key="fig_lib_paper_select"
        )
        selected_paper = paper_map.get(selected_paper_label, list(paper_map.values())[0] if paper_map else {})
        pdf_file_path = selected_paper.get("pdf_path", "")
        
        # Extract figures for this paper
        extracted_figs = extract_figures_from_pdf(pdf_file_path, max_images=8)
        
        if not extracted_figs:
            st.info("ℹ️ No embedded figures detected in this paper. You can specify a topic or figure caption below to analyze the architectural text.")
            figure_choice_options = ["📄 Core Architecture & System Overview"]
            chosen_fig_obj = None
        else:
            figure_choice_options = ["✨ All Extracted Figures (Comprehensive Multi-Figure Overview)"] + [f"📌 {f['caption']}" for f in extracted_figs]
            
            selected_fig_choice = st.selectbox(
                "Choose Which Figure to Explain",
                figure_choice_options,
                index=0,
                key=f"fig_select_choice_{selected_paper['id']}"
            )
            
            # Preview Selected Figure(s)
            if selected_fig_choice.startswith("✨ All"):
                chosen_fig_obj = None
                with st.expander(f"🖼️ Preview All {len(extracted_figs)} Extracted Figures", expanded=False):
                    p_cols = st.columns(min(len(extracted_figs), 3))
                    for idx, f_item in enumerate(extracted_figs):
                        with p_cols[idx % len(p_cols)]:
                            st.image(f_item["image"], caption=f_item["caption"], use_container_width=True)
            else:
                # Find the single selected figure
                chosen_idx = figure_choice_options.index(selected_fig_choice) - 1
                chosen_fig_obj = extracted_figs[chosen_idx]
                with st.container(border=True):
                    st.image(chosen_fig_obj["image"], caption=f"Selected: {chosen_fig_obj['caption']}", use_container_width=True)

        specific_fig_query = st.text_input(
            "Specific Focus / Question for this Figure (Optional)",
            placeholder="e.g. Explain the data flow in the middle block, what is the role of the loss function here?",
            key="fig_lib_custom_q"
        )
        
        btn_extract_fig = st.button("✨ Deconstruct Selected Figure", type="primary", use_container_width=True, key="btn_expl_lib_fig")
        
        if btn_extract_fig:
            fig_label = chosen_fig_obj['exact_title'] if chosen_fig_obj else (figure_choice_options[0] if not extracted_figs else 'All Figures')
            with st.spinner(f"Analyzing '{fig_label}'..."):
                # Determine images to send
                if chosen_fig_obj:
                    target_pil_images = [chosen_fig_obj["image"]]
                    target_captions = [chosen_fig_obj["caption"]]
                    target_focus_str = f"Focus on: {chosen_fig_obj['caption']}. {specific_fig_query.strip()}"
                elif extracted_figs:
                    target_pil_images = [f["image"] for f in extracted_figs[:3]]
                    target_captions = [f["caption"] for f in extracted_figs[:3]]
                    target_focus_str = f"Conduct a comprehensive comparative analysis of all primary figures extracted from this paper. {specific_fig_query.strip()}"
                else:
                    target_pil_images = None
                    target_captions = []
                    target_focus_str = specific_fig_query.strip() if specific_fig_query.strip() else "Explain the primary system architecture and methodology."
                
                # Search ChromaDB for relevant architectural passages
                search_q = f"figure diagram architecture plot {fig_label} {specific_fig_query}"
                results = search_documents(query=search_q, n_results=6, filter_doc_ids=[selected_paper["id"]])
                chunks = results.get("documents", [[]])[0] if results and "documents" in results else []
                paper_context_str = f"Paper Title: {selected_paper['title']}\nDomain: {selected_paper.get('domain', 'Computer Science')}\n\nPassages from Paper:\n" + "\n\n---\n\n".join(chunks)
                
                # Dissect with Vision
                analysis_text = explain_figure_pipeline(
                    images=target_pil_images,
                    context_info=paper_context_str,
                    specific_question=target_focus_str
                )
                
                st.session_state["current_figure_analysis"] = {
                    "text": analysis_text,
                    "title": f"{selected_paper['title']} - {fig_label}",
                    "created_at": time.time()
                }
                log_user_activity(user_email, "Figure Explainer", "Visual Analysis", f"Figure: {selected_paper['title']}", analysis_text, selected_paper['id'])
                st.rerun()

# ----------------- Display Figure Explanation Result -----------------
if "current_figure_analysis" in st.session_state and st.session_state["current_figure_analysis"]:
    curr = st.session_state["current_figure_analysis"]
    
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    
    # Render Output inside styled container
    st.markdown(f"""
<div class="gemini-figure-view">

{curr["text"]}

</div>
""", unsafe_allow_html=True)
    
    # Action Row Directly Beneath Breakdown
    col_act1, col_act2, col_act_spacer = st.columns([1.8, 1.8, 4.0])
    
    with col_act1:
        if st.button("💾 Save to Notes", key="fig_btn_save", use_container_width=True, help="Save this figure analysis to Personal Notes"):
            saved = save_user_note(
                user_email=user_email,
                title=f"Figure Analysis: {curr['title'][:30]}",
                content=f"# Figure & Diagram Analysis: {curr['title']}\n\n{curr['text']}",
                notebook="Figure Analyses"
            )
            if saved:
                st.toast("✅ Figure Analysis saved to Personal Notes!", icon="📝")
            else:
                st.error("Failed to save note.")
                
    with col_act2:
        if st.button("🗑️ Clear Analysis", key="fig_btn_clear", use_container_width=True, help="Clear this analysis"):
            st.session_state["current_figure_analysis"] = None
            st.rerun()

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopFigEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopFigEnd, ms));
        </script>
    """, height=0)
