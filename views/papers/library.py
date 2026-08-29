import streamlit as st
import pandas as pd

import os
import tempfile
from backend.document_processor import process_pdf_for_rag, extract_paper_metadata, extract_ieee_metadata
from backend.db import add_documents_to_db
from backend.database import (
    get_user_documents,
    save_document_metadata,
    delete_document_metadata,
    generate_unique_paper_id,
    update_paper_metadata,
    log_user_activity
)

# Check authentication
if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.warning("Please log in from the Dashboard first.")
    st.stop()

user_email = st.session_state.get('user_email', 'guest@example.com')

# Always sync library metadata from PostgreSQL database
st.session_state['library_metadata'] = get_user_documents(user_email)

# Page configuration
st.set_page_config(
    page_title="Paper Library | ResearchOS",
    page_icon="📚",
    layout="wide"
)

# Custom styling for the page
st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .upload-box {
            border: 2px dashed #475569;
            border-radius: 10px;
            padding: 30px;
            text-align: center;
            background-color: #1e293b;
        }
    </style>
""", unsafe_allow_html=True)

st.title("📚 Paper Library")
st.markdown("Manage your research papers, upload new documents, and explore your knowledge base.")

st.divider()

from collections import Counter

# Top Section: Quick Actions and Dynamic Stats
upload_col, stats_col = st.columns([1.3, 1.7])

with upload_col:
    st.subheader("Upload Papers")
    
    # Use a dynamic key to reset the uploader
    if 'lib_uploader_key' not in st.session_state:
        st.session_state['lib_uploader_key'] = 0
        
    uploaded_files = st.file_uploader("Upload PDF documents", type="pdf", accept_multiple_files=True, key=f"uploader_{st.session_state['lib_uploader_key']}")
    
    if uploaded_files:
        st.success(f"Staged {len(uploaded_files)} file(s).")
        
        # Optional Paper Title Override
        custom_titles = {}
        if len(uploaded_files) == 1:
            custom_title = st.text_input("📝 Title Override (Optional)", placeholder="Leave blank to automatically extract exact title from paper", key="lib_title_0")
            custom_titles[uploaded_files[0].name] = custom_title.strip()
        else:
            with st.expander("📝 Optional Title Overrides", expanded=False):
                for idx, uf in enumerate(uploaded_files):
                    ct = st.text_input(f"Title for {uf.name}", placeholder="Leave blank for auto-extraction", key=f"lib_title_{idx}")
                    custom_titles[uf.name] = ct.strip()
        
        col1, col2 = st.columns(2)
        with col1:
            domain_options = ["🤖 Auto-Detect from Paper (Recommended)", "Natural Language Processing (NLP)", "Computer Vision", "Machine Learning", "Medical Informatics", "Robotics", "Cybersecurity", "IoT", "Biology", "Physics", "Other"]
            domain_choice = st.selectbox("Research Domain", domain_options, index=0, key="lib_domain")
        with col2:
            tags = st.text_input("Tags / Keywords (leave blank for Auto-Extract)", placeholder="e.g. attention, vision, RAG", key="lib_tags")
            
        if st.button("Process & Extract Paper Metadata", type="primary", width="stretch"):
            from backend.config import PAPERS_DIR
            success_count = 0
            errors = []
            
            with st.spinner("Extracting Paper Metadata & Indexing literature..."):
                for uploaded_file in uploaded_files:
                    title_override = custom_titles.get(uploaded_file.name, "").strip()
                    
                    # 1. Generate unique random ID starting with 991
                    doc_id = generate_unique_paper_id(user_email)
                    
                    # 2. Save PDF permanently to storage
                    dest_pdf_path = os.path.join(PAPERS_DIR, f"{doc_id}_{uploaded_file.name}")
                    with open(dest_pdf_path, "wb") as f:
                        f.write(uploaded_file.getvalue())
                    
                    try:
                        # 3. Automatically extract metadata & domain from PDF
                        paper_meta = extract_paper_metadata(dest_pdf_path, fallback_title=title_override)
                        
                        # Use custom title if user explicitly entered one, otherwise use exact extracted title
                        final_title = title_override if title_override else paper_meta.get("title", uploaded_file.name.replace(".pdf", "").replace("_", " "))
                        
                        # Use auto-detected domain if set to auto-detect
                        if domain_choice.startswith("🤖 Auto-Detect"):
                            final_domain = paper_meta.get("domain", "Computer Science")
                        else:
                            final_domain = domain_choice
                            
                        # Use auto-extracted keywords if user left blank
                        final_tags = tags.strip() if tags.strip() else paper_meta.get("keywords", "")
                        
                        # 4. Chunk and embed into ChromaDB
                        docs = process_pdf_for_rag(dest_pdf_path, doc_id, final_title)
                        for doc in docs:
                            doc["metadata"]["domain"] = final_domain
                            doc["metadata"]["tags"] = final_tags
                            doc["metadata"]["title"] = final_title
                        add_documents_to_db(docs)
                        
                        # 5. Save comprehensive metadata into PostgreSQL
                        authors_list = [a.strip() for a in paper_meta.get("authors", "").split(",") if a.strip()]
                        saved = save_document_metadata(
                            doc_id=doc_id,
                            user_email=user_email,
                            title=final_title,
                            domain=final_domain,
                            tags=final_tags,
                            size_bytes=uploaded_file.size,
                            abstract=paper_meta.get("abstract", ""),
                            publication_year=paper_meta.get("publication_year"),
                            journal_or_conference=paper_meta.get("journal_or_conference", ""),
                            doi=paper_meta.get("doi", ""),
                            authors_list=authors_list,
                            pdf_path=dest_pdf_path,
                            publisher=paper_meta.get("publisher", "Academic Publisher")
                        )
                        if saved:
                            success_count += 1
                            log_user_activity(user_email, "Paper Library", "Paper Upload", f"Uploaded: '{final_title}'", f"Domain: {final_domain} • Authors: {paper_meta.get('authors', 'Unknown')}", doc_id)
                        else:
                            errors.append(f"{uploaded_file.name}: Database save failed.")
                        
                    except Exception as e:
                        errors.append(f"{uploaded_file.name}: {str(e)}")
                
                if success_count > 0:
                    st.session_state['lib_uploader_key'] += 1
                    if 'lib_domain' in st.session_state: del st.session_state['lib_domain']
                    if 'lib_tags' in st.session_state: del st.session_state['lib_tags']
                    st.session_state['library_metadata'] = get_user_documents(user_email)
                    st.success(f"Successfully processed and indexed {success_count} paper(s)!")
                    import time
                    time.sleep(1)
                    st.rerun()
                    
                if errors:
                    for err in errors:
                        st.error(f"Error: {err}")

with stats_col:
    st.subheader("Library Stats")
    
    # Calculate dynamic stats
    library = st.session_state.get('library_metadata', [])
    total_docs = len(library)
    
    # 1. Exact total size in MB
    total_bytes = sum(p.get("size_bytes", 0) for p in library)
    total_size_mb = total_bytes / (1024 * 1024)
    
    # 2. Research Domains & Top Domain
    domains = [p.get("domain") for p in library if p.get("domain") and p.get("domain") not in ["Other", ""]]
    unique_domains = len(set(domains))
    if domains:
        top_domain = Counter(domains).most_common(1)[0][0]
        # Shorten domain display if too long
        short_top_domain = top_domain.replace("Natural Language Processing (NLP)", "NLP").replace("Natural Language Processing", "NLP")
        domains_display = f"{unique_domains} <span style='font-size:0.95rem; color:#94a3b8; font-weight:normal;'>(Top: {short_top_domain})</span>"
    else:
        domains_display = f"{unique_domains} <span style='font-size:0.95rem; color:#64748b; font-weight:normal;'>Fields</span>"
        
    # 3. Top Publishers / Venues Breakdown
    publishers = [p.get("publisher") for p in library if p.get("publisher") and p.get("publisher") not in ["Academic Publisher", "None", "", None]]
    if not publishers:
        # Fallback to journal_or_conference if publisher not set
        publishers = [p.get("journal_or_conference") for p in library if p.get("journal_or_conference") and p.get("journal_or_conference") not in ["Conference / Journal", "Academic Publication", "", None]]
        
    if publishers:
        pub_counts = Counter(publishers)
        total_p = len(publishers)
        top_pubs = pub_counts.most_common(3)
        pub_display = ", ".join([f"<b>{name}</b> ({int(round(count/total_p*100))}%)" for name, count in top_pubs])
    else:
        pub_display = "<span style='color:#64748b; font-size:0.9rem;'>No publishers yet</span>"
    
    st.markdown(f"""
        <div style="background-color: #1e293b; padding: 18px; border-radius: 12px; border: 1px solid #334155;">
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px;">
                <div style="background-color: #0f172a; padding: 14px 16px; border-radius: 8px; border: 1px solid #334155;">
                    <p style="margin:0; color:#94a3b8; font-size:0.85rem; font-weight:500;">📄 Total Papers</p>
                    <h3 style="margin:6px 0 0 0; color:#f8fafc; font-size:1.35rem;">{total_docs} <span style="font-size:0.85rem; color:#64748b; font-weight:normal;">Papers</span></h3>
                </div>
                <div style="background-color: #0f172a; padding: 14px 16px; border-radius: 8px; border: 1px solid #334155;">
                    <p style="margin:0; color:#94a3b8; font-size:0.85rem; font-weight:500;">💾 Storage Used</p>
                    <h3 style="margin:6px 0 0 0; color:#f8fafc; font-size:1.35rem;">{total_size_mb:.2f} <span style="font-size:0.8rem; color:#64748b; font-weight:normal;">MB / 10 GB</span></h3>
                </div>
                <div style="background-color: #0f172a; padding: 14px 16px; border-radius: 8px; border: 1px solid #334155;">
                    <p style="margin:0; color:#94a3b8; font-size:0.85rem; font-weight:500;">🧠 Research Domains</p>
                    <h3 style="margin:6px 0 0 0; color:#f8fafc; font-size:1.15rem;">{domains_display}</h3>
                </div>
                <div style="background-color: #0f172a; padding: 14px 16px; border-radius: 8px; border: 1px solid #334155;">
                    <p style="margin:0; color:#94a3b8; font-size:0.85rem; font-weight:500;">🏛️ Top Publishers / Venues</p>
                    <div style="margin:6px 0 0 0; color:#f8fafc; font-size:0.92rem; line-height: 1.35;">{pub_display}</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br><br>", unsafe_allow_html=True)

# Main Library View
st.subheader("Your Documents")

# Read from session state metadata
def get_library_data():
    metadata = st.session_state.get('library_metadata', [])
    if not metadata:
        return pd.DataFrame({
            "ID": [],
            "Title": [],
            "Authors": [],
            "Domain": [],
            "Year": [],
            "Publisher": [],
            "Venue": [],
            "DOI": [],
            "Tags": []
        })
        
    df = pd.DataFrame(metadata)
    df.rename(columns={
        "id": "ID",
        "title": "Title",
        "domain": "Domain",
        "tags": "Tags",
        "authors": "Authors",
        "publication_year": "Year",
        "publisher": "Publisher",
        "journal_or_conference": "Venue",
        "doi": "DOI"
    }, inplace=True)
    return df

df = get_library_data()

# Filtering and search
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_query = st.text_input("Search titles, authors, publishers, venues...", placeholder="Search library...")
with col2:
    domains = ["All"] + list(df['Domain'].unique()) if not df.empty and 'Domain' in df.columns else ["All"]
    selected_domain = st.selectbox("Filter by Domain", domains)
with col3:
    sort_by = st.selectbox("Sort by", ["Newest Added", "Year (Newest)", "Year (Oldest)", "Most Cited"])

# Apply filters
filtered_df = df.copy()
if search_query and not filtered_df.empty:
    filtered_df = filtered_df[
        filtered_df['Title'].astype(str).str.contains(search_query, case=False) | 
        filtered_df['Tags'].astype(str).str.contains(search_query, case=False) |
        filtered_df['Authors'].astype(str).str.contains(search_query, case=False) |
        filtered_df['Publisher'].astype(str).str.contains(search_query, case=False) |
        filtered_df['Venue'].astype(str).str.contains(search_query, case=False)
    ]
if selected_domain != "All" and not filtered_df.empty and 'Domain' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['Domain'] == selected_domain]

# Sort logic
if sort_by == "Year (Newest)" and not filtered_df.empty:
    filtered_df = filtered_df.sort_values(by="ID", ascending=False)
elif sort_by == "Year (Oldest)" and not filtered_df.empty:
    filtered_df = filtered_df.sort_values(by="ID", ascending=True)

# Display Data Grid
if filtered_df.empty:
    st.info("No documents found in your library yet. Upload a PDF paper above to get started!")
    selected_row = None
else:
    event = st.dataframe(
        filtered_df,
        column_config={
            "ID": st.column_config.TextColumn("Paper ID", width=100),
            "Title": st.column_config.TextColumn("Paper Title", width=380),
            "Authors": st.column_config.TextColumn("Authors", width=280),
            "Domain": st.column_config.TextColumn("Domain", width=200),
            "Tags": st.column_config.TextColumn("Keywords / Tags", width=260)
        },
        column_order=["ID", "Title", "Authors", "Domain", "Tags"],
        hide_index=True,
        width="stretch",
        selection_mode="single-row",
        on_select="rerun"
    )
    
    selected_row = None
    if len(event.selection.rows) > 0:
        selected_row = filtered_df.iloc[event.selection.rows[0]]

st.markdown("<br>", unsafe_allow_html=True)

# Dialog for editing paper metadata
@st.dialog("✏️ Edit Paper Metadata")
def edit_paper_modal(paper_data):
    st.caption(f"Editing Paper ID: `{paper_data.get('id')}`")
    
    with st.form("edit_modal_form"):
        edit_title = st.text_input("Title", value=paper_data.get('title', ''))
        
        ecol1, ecol2 = st.columns(2)
        with ecol1:
            domain_list = ["Natural Language Processing (NLP)", "Computer Vision", "Machine Learning", "Medical Informatics", "Robotics", "Cybersecurity", "IoT", "Biology", "Physics", "Other"]
            current_domain = paper_data.get('domain', 'Other')
            dom_idx = domain_list.index(current_domain) if current_domain in domain_list else (len(domain_list) - 1)
            edit_domain = st.selectbox("Domain", domain_list, index=dom_idx)
            edit_year = st.number_input("Publication Year", value=paper_data.get('publication_year') or 2025, step=1)
            edit_doi = st.text_input("DOI", value=paper_data.get('doi', ''), placeholder="e.g. 10.1109/... or 10.1145/...")
        with ecol2:
            edit_tags = st.text_input("Tags / Keywords", value=paper_data.get('tags', ''))
            edit_authors = st.text_input("Authors (comma-separated)", value=paper_data.get('authors', ''), placeholder="e.g. John Doe, Alice Smith")
            edit_venue = st.text_input("Conference / Journal", value=paper_data.get('journal_or_conference', ''), placeholder="e.g. IEEE Transactions on AI")
            edit_publisher = st.text_input("Publisher", value=paper_data.get('publisher', ''), placeholder="e.g. IEEE, ACM, Springer, arXiv")
            
        edit_abstract = st.text_area("Abstract / Summary", value=paper_data.get('abstract', ''), height=120)
        
        submitted = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)
        if submitted:
            success, msg = update_paper_metadata(
                doc_id=paper_data['id'],
                user_email=user_email,
                title=edit_title,
                domain=edit_domain,
                tags=edit_tags,
                abstract=edit_abstract,
                publication_year=int(edit_year) if edit_year else None,
                journal_or_conference=edit_venue,
                doi=edit_doi,
                authors_str=edit_authors,
                publisher=edit_publisher
            )
            if success:
                st.success("Paper updated successfully!")
                import time
                time.sleep(1)
                st.rerun()
            else:
                st.error(msg)

# Action Bar
col_action1, col_action2, col_action3, col_action4, col_empty = st.columns([1.5, 1.5, 1.5, 1.5, 2.5])
is_disabled = selected_row is None

with col_action1:
    if st.button("👁️ View Details", width="stretch", disabled=is_disabled):
        st.session_state['selected_paper_for_details'] = selected_row['Title']
        st.switch_page("views/papers/details.py")

with col_action2:
    if st.button("✏️ Edit Selected", width="stretch", disabled=is_disabled):
        full_paper = next((p for p in library if str(p.get('id')) == str(selected_row['ID'])), {})
        edit_paper_modal(full_paper)

with col_action3:
    if st.button("💬 Chat with Paper", width="stretch", disabled=is_disabled):
        st.session_state['auto_select_paper_id'] = str(selected_row['ID'])
        st.switch_page("views/ai/chat.py")

with col_action4:
    if st.button("🗑️ Delete Selected", type="primary", width="stretch", disabled=is_disabled):
        doc_id_to_delete = selected_row['ID']
        user_email = st.session_state.get('user_email', 'guest@example.com')
        
        # Remove from database
        from backend.database import delete_document_metadata
        delete_document_metadata(doc_id_to_delete, user_email)
        
        # Remove from session state metadata
        st.session_state['library_metadata'] = [
            p for p in st.session_state.get('library_metadata', []) 
            if p.get('id') != doc_id_to_delete
        ]
        st.success(f"Deleted {selected_row['Title']} from your library.")
        import time
        time.sleep(1)
        st.rerun()


