import streamlit as st
import os
import base64

st.set_page_config(page_title="Paper Details | ResearchOS", layout="wide")
if 'logged_in' not in st.session_state or not st.session_state['logged_in']: st.stop()

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
    col_back_det, col_title_det = st.columns([1.5, 4.5])
    with col_back_det:
        if st.button("⬅️ Back to History", key="hdr_back_to_hist_det", use_container_width=True):
            st.session_state['from_history'] = False
            st.switch_page("views/other/history.py")
    with col_title_det:
        st.title("📄 Paper Details")
else:
    st.title("📄 Paper Details")

st.divider()

from backend.database import get_user_documents

user_email = st.session_state.get('user_email', 'guest@example.com')
library = get_user_documents(user_email)
st.session_state['library_metadata'] = library

if not library:
    st.info("No papers found in your library. Please go to the Upload PDF page to add some!")
else:
    # Let user select which paper to view
    paper_titles = [p['title'] for p in library]
    
    # Check if a paper was pre-selected from library.py or history.py
    default_idx = 0
    if 'selected_paper_id' in st.session_state and st.session_state['selected_paper_id']:
        match_p = next((p for p in library if str(p['id']) == str(st.session_state['selected_paper_id'])), None)
        if match_p and match_p['title'] in paper_titles:
            default_idx = paper_titles.index(match_p['title'])
    elif 'selected_paper_for_details' in st.session_state and st.session_state['selected_paper_for_details'] in paper_titles:
        default_idx = paper_titles.index(st.session_state['selected_paper_for_details'])
        
    selected_title = st.selectbox("Select a paper to view details:", paper_titles, index=default_idx)
    
    # Find the selected paper metadata
    paper = next((p for p in library if p['title'] == selected_title), None)
    
    if paper:
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"## {paper.get('title', 'Untitled')}")
            st.markdown(f"**Authors:** {paper.get('authors', 'Unknown')}")
            st.markdown(f"**Domain:** `{paper.get('domain', 'Computer Science')}` | **Publisher:** `{paper.get('publisher', 'Academic Publisher')}`")
            
            st.markdown("### 📝 Abstract")
            abstract_text = paper.get('abstract')
            if abstract_text:
                st.info(abstract_text)
            else:
                st.info("The document text has been indexed into the vector database. Use 'Chat with this Paper' or 'Summarize' to query details.")
            
            # Action Buttons: View Paper & Download
            pdf_path = paper.get('pdf_path', '')
            has_pdf = bool(pdf_path and os.path.exists(pdf_path))
            
            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                show_pdf = st.checkbox("📖 View Full Paper (PDF)", value=False, key=f"view_pdf_{paper.get('id')}")
            with btn_c2:
                if has_pdf:
                    with open(pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="⬇️ Download PDF",
                            data=pdf_file,
                            file_name=f"{paper.get('title', 'paper')}.pdf",
                            mime="application/pdf",
                            width="stretch"
                        )
                else:
                    st.button("⬇️ Download PDF", disabled=True, width="stretch")
            
            if show_pdf:
                if has_pdf:
                    with open(pdf_path, "rb") as f:
                        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
                    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf" style="border: 1px solid #444; border-radius: 8px; margin-top: 15px;"></iframe>'
                    st.markdown(pdf_display, unsafe_allow_html=True)
                else:
                    st.warning("Original PDF file is not stored on local disk for this older entry. Re-uploading this paper will enable the full PDF viewer.")
        
        with col2:
            with st.container(border=True):
                st.subheader("Paper Metadata")
                st.markdown(f"**Paper ID:** `{paper.get('id', 'N/A')}`")
                st.markdown(f"**DOI:** `{paper.get('doi') or 'N/A'}`")
                st.markdown(f"**Venue:** `{paper.get('journal_or_conference') or 'Conference / Journal'}`")
                st.markdown(f"**Year:** `{paper.get('publication_year') or 'N/A'}`")
                st.markdown(f"**Keywords / Tags:** `{paper.get('tags') or 'None'}`")
                st.markdown(f"**File Size:** ~{(paper.get('size_bytes', 0) / (1024*1024)):.2f} MB")
                st.markdown(f"**Date Indexed:** {paper.get('created_at', 'Recently')}")
                
                st.divider()
                if st.button("💬 Chat with this Paper", width="stretch"):
                    st.session_state['auto_select_paper_id'] = str(paper['id'])
                    st.session_state.pop('chat_paper_scope', None)
                    st.switch_page("views/ai/chat.py")
                if st.button("📝 Summarize", width="stretch"):
                    st.session_state['selected_paper_id'] = str(paper['id'])
                    st.session_state['auto_select_paper_id'] = str(paper['id'])
                    st.session_state.pop('sum_paper_select', None)
                    st.switch_page("views/ai/summarize.py")
        
        # Edit Metadata Expander
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("✏️ Edit Paper Metadata"):
            from backend.database import update_paper_metadata
            
            edit_d_title = st.text_input("Title", value=paper.get('title', ''), key="dtl_title")
            dcol1, dcol2 = st.columns(2)
            with dcol1:
                domain_list = ["Natural Language Processing (NLP)", "Computer Vision", "Machine Learning", "Medical Informatics", "Robotics", "Cybersecurity", "IoT", "Biology", "Physics", "Other"]
                current_domain = paper.get('domain', 'Other')
                dom_idx = domain_list.index(current_domain) if current_domain in domain_list else (len(domain_list) - 1)
                edit_d_domain = st.selectbox("Domain", domain_list, index=dom_idx, key="dtl_domain")
                edit_d_year = st.number_input("Publication Year", value=paper.get('publication_year') or 2025, step=1, key="dtl_year")
                edit_d_doi = st.text_input("DOI", value=paper.get('doi', ''), key="dtl_doi")
            with dcol2:
                edit_d_tags = st.text_input("Tags / Keywords", value=paper.get('tags', ''), key="dtl_tags")
                edit_d_authors = st.text_input("Authors (comma-separated)", value=paper.get('authors', ''), key="dtl_authors")
                edit_d_venue = st.text_input("Conference / Journal", value=paper.get('journal_or_conference', ''), key="dtl_venue")
                edit_d_publisher = st.text_input("Publisher", value=paper.get('publisher', ''), key="dtl_publisher")
                
            edit_d_abstract = st.text_area("Abstract", value=paper.get('abstract', ''), height=100, key="dtl_abstract")
            
            if st.button("💾 Update Metadata", type="primary"):
                success, msg = update_paper_metadata(
                    doc_id=paper['id'],
                    user_email=user_email,
                    title=edit_d_title,
                    domain=edit_d_domain,
                    tags=edit_d_tags,
                    abstract=edit_d_abstract,
                    publication_year=int(edit_d_year) if edit_d_year else None,
                    journal_or_conference=edit_d_venue,
                    doi=edit_d_doi,
                    authors_str=edit_d_authors,
                    publisher=edit_d_publisher
                )
                if success:
                    st.success("Paper updated successfully!")
                    import time
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(msg)

if st.session_state.get('from_history'):
    components.html("""
        <script>
            function forceScrollToTopDetEnd() {
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
            [10, 50, 150, 300, 600, 1000].forEach(ms => setTimeout(forceScrollToTopDetEnd, ms));
        </script>
    """, height=0)
