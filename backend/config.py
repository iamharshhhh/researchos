import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Model Configuration
MODEL_NAME = "gemini-flash-lite-latest"
FALLBACK_MODELS = ["gemini-flash-lite-latest", "gemini-3.5-flash-lite", "gemini-3.5-flash"]
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Database & Storage Paths
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHROMA_PATH = os.path.join(DB_DIR, "chroma_db")
PAPERS_DIR = os.path.join(DB_DIR, "papers")
os.makedirs(PAPERS_DIR, exist_ok=True)

# Database URL resolution
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    try:
        import streamlit as st
        DATABASE_URL = st.secrets.get("DATABASE_URL")
    except Exception:
        pass
if not DATABASE_URL:
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/researchos"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def configure_gemini():
    """Configure the Gemini API client for Generation & RAG with key sanitization."""
    global GEMINI_API_KEY
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("GEMINI_API_KEY")
        except Exception:
            pass
    
    if not key:
        raise ValueError("GEMINI_API_KEY is not set. Please add your GEMINI_API_KEY in Streamlit Secrets.")
    
    # Strip whitespace, newlines, and quotes that might come from pasting
    cleaned_key = str(key).strip().strip('"').strip("'")
    GEMINI_API_KEY = cleaned_key
    os.environ["GEMINI_API_KEY"] = cleaned_key
    genai.configure(api_key=cleaned_key)
