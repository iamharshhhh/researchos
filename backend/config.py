import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# API Keys & DB URLs
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        import streamlit as st
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        pass

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    try:
        import streamlit as st
        DATABASE_URL = st.secrets.get("DATABASE_URL")
    except Exception:
        pass
if not DATABASE_URL:
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/researchos"

# Model Configuration
MODEL_NAME = "gemini-3.6-flash"
FALLBACK_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-flash-latest", "gemini-pro-latest"]
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Database & Storage Paths
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
CHROMA_PATH = os.path.join(DB_DIR, "chroma_db")
PAPERS_DIR = os.path.join(DB_DIR, "papers")
os.makedirs(PAPERS_DIR, exist_ok=True)

def configure_gemini():
    """Configure the Gemini API client for Generation & RAG."""
    global GEMINI_API_KEY
    if not GEMINI_API_KEY:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        if not GEMINI_API_KEY:
            try:
                import streamlit as st
                GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                pass
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment or Streamlit Secrets.")
    
    genai.configure(api_key=GEMINI_API_KEY)
