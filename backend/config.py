import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env if present
load_dotenv()

# Read API Key with Streamlit Cloud secrets fallback
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    try:
        GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
    except Exception:
        GEMINI_API_KEY = None

if GEMINI_API_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY

# Read Database URL with Streamlit Cloud secrets fallback
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    try:
        DATABASE_URL = st.secrets.get("DATABASE_URL")
    except Exception:
        DATABASE_URL = None

if not DATABASE_URL:
    DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/researchos"

# Model Configuration
MODEL_NAME = "gemini-3.5-flash-lite"
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
                GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")
            except Exception:
                GEMINI_API_KEY = None
                
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set. Please add GEMINI_API_KEY in your .env or Streamlit Cloud Secrets.")
    
    genai.configure(api_key=GEMINI_API_KEY)
