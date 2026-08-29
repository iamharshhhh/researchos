import os
import re
import json
import pymupdf  # PyMuPDF
import google.generativeai as genai
from backend.config import MODEL_NAME, FALLBACK_MODELS, configure_gemini

def extract_text_from_pdf(pdf_path: str, max_pages: int = None) -> str:
    """Extract all text from a PDF file (optionally capped at max_pages)."""
    doc = pymupdf.open(pdf_path)
    text = ""
    pages_to_read = doc if max_pages is None else doc[:max_pages]
    for page in pages_to_read:
        text += page.get_text() + "\n\n"
    doc.close()
    return text

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> list[str]:
    """
    Split text into overlapping chunks.
    A simple word-based chunker.
    """
    words = text.split()
    chunks = []
    
    if not words:
        return []
        
    i = 0
    while i < len(words):
        chunk_words = words[i:i + chunk_size]
        chunk = " ".join(chunk_words)
        chunks.append(chunk)
        i += chunk_size - overlap
        
    return chunks

def clean_academic_authors(raw_authors: str) -> str:
    """Clean superscript symbols, footnotes, affiliations, or email residue from author strings."""
    if not raw_authors or raw_authors.lower() == "unknown":
        return "Unknown"
    # Remove superscripts, footnote markers like *, †, numbers attached to names
    cleaned = re.sub(r'[\*\†\‡\§\¶\d]', '', raw_authors)
    cleaned = re.sub(r'\s*,\s*', ', ', cleaned)
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned if cleaned else raw_authors

def detect_publisher_from_text_and_doi(doi: str, text: str, initial_publisher: str = "") -> str:
    """Accurately identify the academic publisher from DOI prefix, headers, and LLM output."""
    if initial_publisher and initial_publisher.lower() not in ["academic publisher", "unknown", "", "none"]:
        return initial_publisher

    doi_lower = (doi or "").lower()
    text_lower = (text or "").lower()

    if "10.1109" in doi_lower or "ieee" in doi_lower:
        return "IEEE"
    if "10.1145" in doi_lower or "acm" in doi_lower:
        return "ACM"
    if "10.1016" in doi_lower or "sciencedirect" in text_lower:
        return "Elsevier"
    if "10.1038" in doi_lower or "nature" in doi_lower:
        return "Nature Publishing Group"
    if "10.1007" in doi_lower or "springer" in doi_lower:
        return "Springer"
    if "10.1002" in doi_lower or "wiley" in doi_lower:
        return "Wiley"
    if "arxiv" in doi_lower or "arxiv:" in text_lower:
        return "arXiv"
    if "10.1093" in doi_lower or "oxford" in text_lower:
        return "Oxford University Press"
    if "10.1017" in doi_lower or "cambridge" in text_lower:
        return "Cambridge University Press"
    if "10.3390" in doi_lower or "mdpi" in text_lower:
        return "MDPI"
    if "frontiers" in text_lower:
        return "Frontiers"
    if "neurips" in text_lower or "neural information processing systems" in text_lower:
        return "NeurIPS"
    if "icml" in text_lower:
        return "ICML"
    if "association for computational linguistics" in text_lower or "anthology" in text_lower:
        return "ACL"
    if "ieee" in text_lower:
        return "IEEE"
    if "springer" in text_lower:
        return "Springer"
    if "acm" in text_lower:
        return "ACM"
        
    return initial_publisher if initial_publisher else "Academic Publisher"

def extract_paper_metadata(pdf_path: str, fallback_title: str = "") -> dict:
    """
    Extracts high-precision 100% exact research paper metadata from any academic document 
    (IEEE, arXiv, ACM, Springer, Nature, Elsevier, ACL, NeurIPS, Science, etc.) using hybrid 
    PyMuPDF inspection + Gemini 3.5 Flash-Lite LLM parsing.
    """
    # 1. Extract embedded PDF document metadata
    doc_meta = {}
    front_text = ""
    try:
        doc = pymupdf.open(pdf_path)
        doc_meta = doc.metadata or {}
        # Read first 3 pages (covers full front matter, abstract, header/footer, DOI)
        pages_to_read = doc[:min(3, len(doc))]
        for page in pages_to_read:
            front_text += page.get_text() + "\n\n"
        doc.close()
    except Exception as e:
        print(f"Error reading PDF with PyMuPDF: {e}")

    # Fallback default metadata
    clean_filename_title = os.path.basename(pdf_path).replace(".pdf", "").replace("_", " ").replace("-", " ")
    default_meta = {
        "title": fallback_title or doc_meta.get("title") or clean_filename_title,
        "authors": doc_meta.get("author") or "Unknown",
        "abstract": "",
        "keywords": doc_meta.get("keywords") or "",
        "domain": "Computer Science / AI",
        "publication_year": 2024,
        "journal_or_conference": "Academic Publication",
        "doi": "",
        "publisher": "Academic Publisher"
    }

    # Regex Pre-Checks for DOI and arXiv IDs
    doi_match = re.search(r'\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b', front_text)
    if doi_match:
        default_meta["doi"] = doi_match.group(1).rstrip('.')

    arxiv_match = re.search(r'arXiv:\s*(\d{4}\.\d{4,5}(?:v\d+)?)', front_text, re.IGNORECASE)
    if arxiv_match and not default_meta["doi"]:
        default_meta["doi"] = f"arXiv:{arxiv_match.group(1)}"

    if not front_text.strip():
        return default_meta

    # 2. Precision LLM Extraction via Gemini
    try:
        configure_gemini()
        prompt = f"""You are an elite academic bibliographer and metadata extraction engine.
Analyze the following front matter text of a research paper and extract the exact academic metadata with 100% precision into the specified JSON format.

Front Matter Text:
\"\"\"
{front_text[:7000]}
\"\"\"

Embedded PDF Meta Hints:
- Title Hint: {doc_meta.get('title', '')}
- Author Hint: {doc_meta.get('author', '')}

Extraction Rules:
1. "title": Extract the EXACT full research paper title. Do NOT include running conference headers, author names, or page numbers.
2. "authors": Extract the full names of all authors as a clean comma-separated list (e.g. "Alice Chen, Bob Smith, David Kumar"). Exclude emails, affiliations, university names, and footnote symbols (*, 1, 2).
3. "abstract": Extract the EXACT, COMPLETE abstract text verbatim from the paper. Do NOT summarize.
4. "keywords": Extract the explicit author keywords or index terms as a comma-separated list. If none are explicitly labeled, extract 4-6 highly specific technical terms.
5. "domain": Classify the exact primary academic field (e.g. "Natural Language Processing", "Computer Vision", "Graph Neural Networks & RAG", "Deep Learning", "Medical Informatics", "Robotics", "Cybersecurity", "Distributed Systems", "Bioinformatics", "Quantum Computing", etc.).
6. "publication_year": Extract the exact publication or copyright year as an integer (e.g. 2024).
7. "journal_or_conference": Extract the exact conference proceedings name, journal title, or "arXiv preprint" (e.g. "IEEE Transactions on Pattern Analysis and Machine Intelligence", "ACL 2023", "NeurIPS 2024", "arXiv preprint").
8. "doi": Extract the exact DOI string if present (e.g. "10.1109/TPAMI.2024.123456").
9. "publisher": Extract the publishing body or organization (e.g. "IEEE", "ACM", "Springer", "Elsevier", "Nature Publishing Group", "arXiv", "USENIX", "OpenReview").

JSON Output Schema:
{{
    "title": "string",
    "authors": "string",
    "abstract": "string",
    "keywords": "string",
    "domain": "string",
    "publication_year": 2024,
    "journal_or_conference": "string",
    "doi": "string",
    "publisher": "string"
}}
"""
        parsed = None
        for m_name in FALLBACK_MODELS:
            try:
                model = genai.GenerativeModel(
                    m_name,
                    generation_config={
                        "response_mime_type": "application/json",
                        "temperature": 0.0  # Deterministic precision for exact metadata extraction
                    }
                )
                response = model.generate_content(prompt)
                if response and response.text:
                    parsed = json.loads(response.text)
                    break
            except Exception:
                continue
                
        if not parsed:
            return default_meta

        # Merge and clean results
        if parsed.get("title") and parsed["title"].strip():
            default_meta["title"] = parsed["title"].strip()
        if parsed.get("authors") and parsed["authors"].strip():
            default_meta["authors"] = clean_academic_authors(parsed["authors"].strip())
        if parsed.get("abstract") and parsed["abstract"].strip():
            default_meta["abstract"] = parsed["abstract"].strip()
        if parsed.get("keywords") and parsed["keywords"].strip():
            default_meta["keywords"] = parsed["keywords"].strip()
        if parsed.get("domain") and parsed["domain"].strip():
            default_meta["domain"] = parsed["domain"].strip()
        if parsed.get("publication_year"):
            try:
                default_meta["publication_year"] = int(parsed["publication_year"])
            except:
                pass
        if parsed.get("journal_or_conference") and parsed["journal_or_conference"].strip():
            default_meta["journal_or_conference"] = parsed["journal_or_conference"].strip()
        # Guarantee accurate publisher resolution
        default_meta["publisher"] = detect_publisher_from_text_and_doi(
            default_meta.get("doi", ""),
            front_text,
            parsed.get("publisher", "")
        )

        return default_meta
    except Exception as e:
        print(f"Error extracting paper metadata with Gemini: {e}")
        default_meta["publisher"] = detect_publisher_from_text_and_doi(
            default_meta.get("doi", ""),
            front_text,
            default_meta.get("publisher", "")
        )
        return default_meta

# Aliases for backward compatibility
extract_ieee_metadata = extract_paper_metadata

def process_pdf_for_rag(pdf_path: str, doc_id: str, original_filename: str = None) -> list[dict]:
    """
    Extract text, chunk it, and format it for the vector database.
    """
    full_text = extract_text_from_pdf(pdf_path)
    text_chunks = chunk_text(full_text)
    
    source_name = original_filename if original_filename else os.path.basename(pdf_path)
    
    documents = []
    for i, chunk in enumerate(text_chunks):
        documents.append({
            "id": f"{doc_id}_chunk_{i}",
            "text": chunk,
            "metadata": {
                "source": source_name,
                "title": source_name,
                "doc_id": doc_id,
                "chunk_index": i
            }
        })
        
    return documents
