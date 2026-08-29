import os
import uuid
import hashlib
import random
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey, Date, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

load_dotenv()

# Database URL from environment or default to local PostgreSQL
DEFAULT_PG_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/researchos"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_PG_URL)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    email = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    papers = relationship("Paper", back_populates="user", cascade="all, delete-orphan")
    chats = relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")

class Paper(Base):
    __tablename__ = "papers"
    
    paper_id = Column(String(50), primary_key=True)  # e.g. '991590'
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    
    # Core IEEE Paper Metadata
    title = Column(Text, nullable=False)
    abstract = Column(Text, default="")
    publication_year = Column(Integer, nullable=True)
    publication_date = Column(String(100), default="")
    journal_or_conference = Column(Text, default="")
    volume = Column(String(50), default="")
    issue = Column(String(50), default="")
    pages = Column(String(100), default="")
    doi = Column(String(255), default="")
    ieee_document_id = Column(String(100), default="")
    keywords = Column(Text, default="")  # Stored tags / keywords
    domain = Column(String(100), default="Other")
    publisher = Column(String(255), default="IEEE")
    issn = Column(String(100), default="")
    isbn = Column(String(100), default="")
    paper_type = Column(String(100), default="Conference Paper")
    url = Column(Text, default="")
    pdf_path = Column(Text, default="")
    size_bytes = Column(Integer, default=0)
    language = Column(String(50), default="English")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="papers")
    authors = relationship("PaperAuthor", back_populates="paper", cascade="all, delete-orphan")
    figures = relationship("PaperFigure", back_populates="paper", cascade="all, delete-orphan")
    references = relationship("PaperReference", back_populates="paper", cascade="all, delete-orphan")

class Author(Base):
    __tablename__ = "authors"
    
    author_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    affiliation = Column(Text, default="")
    email = Column(String(255), default="")
    orcid = Column(String(100), default="")
    
    papers = relationship("PaperAuthor", back_populates="author")

class PaperAuthor(Base):
    __tablename__ = "paper_authors"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey("papers.paper_id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("authors.author_id", ondelete="CASCADE"), nullable=False)
    author_order = Column(Integer, default=1)
    
    paper = relationship("Paper", back_populates="authors")
    author = relationship("Author", back_populates="papers")

class PaperFigure(Base):
    __tablename__ = "figures"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey("papers.paper_id", ondelete="CASCADE"), nullable=False)
    figure_type = Column(String(50), default="figure")  # 'figure' or 'table'
    caption = Column(Text, default="")
    file_path = Column(Text, default="")
    page_number = Column(Integer, default=1)
    
    paper = relationship("Paper", back_populates="figures")

class PaperReference(Base):
    __tablename__ = "references"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    paper_id = Column(String(50), ForeignKey("papers.paper_id", ondelete="CASCADE"), nullable=False)
    reference_text = Column(Text, nullable=False)
    doi = Column(String(255), default="")
    
    paper = relationship("Paper", back_populates="references")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    session_id = Column(String(100), primary_key=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    title = Column(String(255), default="New Research Chat")
    paper_id = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("Chat", back_populates="session", cascade="all, delete-orphan")

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    session_id = Column(String(100), ForeignKey("chat_sessions.session_id", ondelete="CASCADE"), nullable=True)
    role = Column(String(50), nullable=False)  # 'user' or 'assistant'
    message = Column(Text, nullable=False)
    citations = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="chats")
    session = relationship("ChatSession", back_populates="messages")

class Note(Base):
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    title = Column(String(255), default="AI Synthesis Note")
    content = Column(Text, nullable=False)
    notebook = Column(String(100), default="AI Chat Notes")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="notes")

class UserActivity(Base):
    __tablename__ = "user_activities"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_email = Column(String(255), ForeignKey("users.email"), nullable=False)
    feature = Column(String(100), nullable=False)
    action_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    details = Column(Text, default="")
    raw_id = Column(String(100), default="")
    created_at = Column(DateTime, default=datetime.utcnow)


# Engine & Session Factory
engine = None
SessionLocal = None

def get_engine():
    global engine, SessionLocal
    if engine is None:
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base.metadata.create_all(bind=engine)
            
            # Ensure schema migrations for chat_sessions and chats.session_id
            with engine.connect() as conn:
                try:
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS chat_sessions (
                            session_id VARCHAR(100) PRIMARY KEY,
                            user_email VARCHAR(255) REFERENCES users(email),
                            title VARCHAR(255) DEFAULT 'New Research Chat',
                            paper_id VARCHAR(50),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        );
                    """))
                    conn.execute(text("""
                        DO $$ 
                        BEGIN 
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns 
                                WHERE table_name = 'chats' AND column_name = 'session_id'
                            ) THEN 
                                ALTER TABLE chats ADD COLUMN session_id VARCHAR(100);
                            END IF; 
                        END $$;
                    """))
                    conn.commit()
                except Exception as ex:
                    print(f"[Migration Info] {ex}")
        except Exception as e:
            # Fallback to local SQLite if PostgreSQL connection fails
            print(f"[Warning] PostgreSQL connection failed ({e}). Falling back to SQLite database.")
            sqlite_path = os.path.join(os.path.dirname(__file__), "researchos.db")
            engine = create_engine(f"sqlite:///{sqlite_path}")
            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            Base.metadata.create_all(bind=engine)
            with engine.connect() as conn:
                try:
                    conn.execute(text("ALTER TABLE chats ADD COLUMN session_id VARCHAR(100)"))
                    conn.commit()
                except Exception:
                    pass
    return engine

def get_db():
    get_engine()
    db = SessionLocal()
    return db

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(email: str, name: str, password: str):
    db = get_db()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return False, "Email is already registered."
        new_user = User(email=email, name=name, password_hash=hash_password(password))
        db.add(new_user)
        db.commit()
        return True, "Registration successful."
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        db.close()

def authenticate_user(email: str, password: str):
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and user.password_hash == hash_password(password):
            return True, user.name
        return False, "Invalid email or password."
    except Exception as e:
        return False, f"Database error: {str(e)}"
    finally:
        db.close()

def get_user_by_email(email: str):
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            return {"email": user.email, "name": user.name}
        return None
    except Exception as e:
        return None
    finally:
        db.close()

def generate_unique_paper_id(user_email: str) -> str:
    """
    Generates a unique random 6-digit Paper ID starting with 991 (e.g. 991001 to 991999).
    Checks existing document IDs in PostgreSQL so no collision occurs.
    When a paper is deleted, its ID is automatically freed and returned to the available pool.
    """
    db = get_db()
    try:
        existing_docs = db.query(Paper.paper_id).filter(Paper.user_email == user_email).all()
        existing_ids = {d[0] for d in existing_docs}
        
        # Available pool of 991001 to 991999
        available_pool = [f"991{i:03d}" for i in range(1, 1000) if f"991{i:03d}" not in existing_ids]
        if available_pool:
            return random.choice(available_pool)
        
        while True:
            candidate = f"991{random.randint(1000, 9999)}"
            if candidate not in existing_ids:
                return candidate
    except Exception as e:
        print(f"Error generating paper ID: {e}")
        return f"991{random.randint(100, 999)}"
    finally:
        db.close()

def save_document_metadata(
    doc_id: str,
    user_email: str,
    title: str,
    domain: str = "Other",
    tags: str = "",
    size_bytes: int = 0,
    abstract: str = "",
    publication_year: int = None,
    journal_or_conference: str = "",
    doi: str = "",
    authors_list: list = None,
    pdf_path: str = "",
    publisher: str = ""
):
    db = get_db()
    try:
        # Ensure user exists in database to satisfy foreign key constraint
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, name="ResearchOS User", password_hash="guest_hash")
            db.add(user)
            db.commit()

        paper = db.query(Paper).filter(Paper.paper_id == doc_id, Paper.user_email == user_email).first()
        if not paper:
            paper = Paper(
                paper_id=doc_id,
                user_email=user_email,
                title=title,
                domain=domain,
                keywords=tags,
                size_bytes=size_bytes,
                abstract=abstract,
                publication_year=publication_year,
                journal_or_conference=journal_or_conference,
                doi=doi,
                pdf_path=pdf_path,
                publisher=publisher or "Academic Publisher"
            )
            db.add(paper)
        else:
            paper.title = title
            paper.domain = domain
            paper.keywords = tags
            paper.size_bytes = size_bytes
            if abstract: paper.abstract = abstract
            if publication_year: paper.publication_year = publication_year
            if journal_or_conference: paper.journal_or_conference = journal_or_conference
            if doi: paper.doi = doi
            if pdf_path: paper.pdf_path = pdf_path
            if publisher: paper.publisher = publisher
        
        db.commit()
        
        # Handle Authors if provided
        if authors_list:
            for idx, author_info in enumerate(authors_list):
                name = author_info if isinstance(author_info, str) else author_info.get("name", "")
                if not name: continue
                
                author = db.query(Author).filter(Author.name == name).first()
                if not author:
                    author = Author(
                        name=name,
                        affiliation=author_info.get("affiliation", "") if isinstance(author_info, dict) else "",
                        email=author_info.get("email", "") if isinstance(author_info, dict) else "",
                        orcid=author_info.get("orcid", "") if isinstance(author_info, dict) else ""
                    )
                    db.add(author)
                    db.commit()
                
                # Check paper_author link
                link = db.query(PaperAuthor).filter(PaperAuthor.paper_id == doc_id, PaperAuthor.author_id == author.author_id).first()
                if not link:
                    pa = PaperAuthor(paper_id=doc_id, author_id=author.author_id, author_order=idx + 1)
                    db.add(pa)
            db.commit()
            
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving document: {e}")
        return False
    finally:
        db.close()

def get_user_documents(user_email: str):
    db = get_db()
    try:
        papers = db.query(Paper).filter(Paper.user_email == user_email).order_by(Paper.created_at.desc()).all()
        result = []
        for p in papers:
            # Fetch authors
            author_names = [pa.author.name for pa in p.authors] if p.authors else []
            result.append({
                "id": p.paper_id,
                "title": p.title,
                "domain": p.domain,
                "tags": p.keywords,
                "size_bytes": p.size_bytes,
                "abstract": p.abstract,
                "publication_year": p.publication_year,
                "journal_or_conference": p.journal_or_conference,
                "doi": p.doi,
                "publisher": p.publisher,
                "pdf_path": p.pdf_path or "",
                "authors": ", ".join(author_names) if author_names else "Unknown",
                "created_at": str(p.created_at)
            })
        return result
    except Exception as e:
        print(f"Error fetching documents: {e}")
        return []
    finally:
        db.close()

def delete_document_metadata(doc_id: str, user_email: str):
    db = get_db()
    try:
        paper = db.query(Paper).filter(Paper.paper_id == doc_id, Paper.user_email == user_email).first()
        if paper:
            # Remove PDF file if exists
            if paper.pdf_path and os.path.exists(paper.pdf_path):
                try:
                    os.remove(paper.pdf_path)
                except Exception:
                    pass
            db.delete(paper)
            db.commit()
            
            # Delete corresponding vector embeddings from ChromaDB
            from backend.db import delete_documents_by_doc_id
            delete_documents_by_doc_id(doc_id)
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting document: {e}")
        return False
    finally:
        db.close()

def update_paper_metadata(
    doc_id: str,
    user_email: str,
    title: str = None,
    domain: str = None,
    tags: str = None,
    abstract: str = None,
    publication_year: int = None,
    journal_or_conference: str = None,
    doi: str = None,
    authors_str: str = None,
    publisher: str = None
):
    db = get_db()
    try:
        paper = db.query(Paper).filter(Paper.paper_id == doc_id, Paper.user_email == user_email).first()
        if not paper:
            return False, "Paper not found."
        
        if title is not None: paper.title = title
        if domain is not None: paper.domain = domain
        if tags is not None: paper.keywords = tags
        if abstract is not None: paper.abstract = abstract
        if publication_year is not None: paper.publication_year = publication_year
        if journal_or_conference is not None: paper.journal_or_conference = journal_or_conference
        if doi is not None: paper.doi = doi
        if publisher is not None: paper.publisher = publisher
        
        if authors_str is not None:
            # Clear old author links for this paper and re-add
            db.query(PaperAuthor).filter(PaperAuthor.paper_id == doc_id).delete()
            authors = [a.strip() for a in authors_str.split(",") if a.strip()]
            for idx, a_name in enumerate(authors):
                author = db.query(Author).filter(Author.name == a_name).first()
                if not author:
                    author = Author(name=a_name)
                    db.add(author)
                    db.commit()
                pa = PaperAuthor(paper_id=doc_id, author_id=author.author_id, author_order=idx + 1)
                db.add(pa)
                
        db.commit()
        return True, "Paper metadata updated successfully!"
    except Exception as e:
        db.rollback()
        return False, f"Error updating paper: {str(e)}"
    finally:
        db.close()


def create_chat_session(user_email: str, paper_id: str = None, title: str = "New Research Chat") -> str:
    """Creates a new chat session thread for the user."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, name="ResearchOS User", password_hash="guest_hash")
            db.add(user)
            db.commit()

        session_id = str(uuid.uuid4())[:12]
        session = ChatSession(
            session_id=session_id,
            user_email=user_email,
            title=title,
            paper_id=paper_id
        )
        db.add(session)
        db.commit()
        return session_id
    except Exception as e:
        db.rollback()
        print(f"Error creating chat session: {e}")
        return str(uuid.uuid4())[:12]
    finally:
        db.close()

def get_user_chat_sessions(user_email: str) -> list:
    """Retrieves all chat sessions for the user sorted by last update."""
    db = get_db()
    try:
        sessions = db.query(ChatSession).filter(ChatSession.user_email == user_email).order_by(ChatSession.updated_at.desc()).all()
        return [{
            "session_id": s.session_id,
            "title": s.title,
            "paper_id": s.paper_id,
            "created_at": str(s.created_at),
            "updated_at": str(s.updated_at)
        } for s in sessions]
    except Exception as e:
        print(f"Error fetching chat sessions: {e}")
        return []
    finally:
        db.close()

def get_session_chats(session_id: str, user_email: str) -> list:
    """Retrieves all messages for a specific chat session."""
    db = get_db()
    try:
        chats = db.query(Chat).filter(Chat.session_id == session_id, Chat.user_email == user_email).order_by(Chat.created_at.asc()).all()
        return [{
            "role": c.role,
            "message": c.message,
            "citations": c.citations,
            "created_at": str(c.created_at)
        } for c in chats]
    except Exception as e:
        print(f"Error fetching session chats: {e}")
        return []
    finally:
        db.close()

def update_chat_session_title(session_id: str, user_email: str, title: str) -> bool:
    """Updates the title of a chat session."""
    db = get_db()
    try:
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_email == user_email).first()
        if session:
            session.title = title
            session.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error updating chat session title: {e}")
def delete_document(doc_id: str, user_email: str) -> bool:
    """Deletes a paper from the database, disk, and ChromaDB."""
    db = get_db()
    try:
        paper = db.query(Paper).filter(Paper.paper_id == doc_id, Paper.user_email == user_email).first()
        if paper:
            if paper.file_path and os.path.exists(paper.file_path):
                try:
                    os.remove(paper.file_path)
                except Exception:
                    pass
            db.delete(paper)
            db.commit()
            
            try:
                from backend.db import delete_documents_by_doc_id
                delete_documents_by_doc_id(doc_id)
            except Exception:
                pass
                
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error deleting document {doc_id}: {e}")
        return False
    finally:
        db.close()

def delete_chat_session(session_id: str, user_email: str) -> bool:
    """Deletes a chat session and all its messages."""
    db = get_db()
    try:
        db.query(Chat).filter(Chat.session_id == session_id, Chat.user_email == user_email).delete()
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id, ChatSession.user_email == user_email).first()
        if session:
            db.delete(session)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting chat session: {e}")
        return False
    finally:
        db.close()

def delete_all_chat_sessions(user_email: str) -> bool:
    """Deletes all chat sessions and messages for the user."""
    db = get_db()
    try:
        db.query(Chat).filter(Chat.user_email == user_email).delete()
        db.query(ChatSession).filter(ChatSession.user_email == user_email).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error clearing all chat sessions: {e}")
        return False
    finally:
        db.close()

def clear_all_user_history(user_email: str) -> bool:
    """Clears all chat sessions, messages, and notes for the user."""
    db = get_db()
    try:
        db.query(Chat).filter(Chat.user_email == user_email).delete()
        db.query(ChatSession).filter(ChatSession.user_email == user_email).delete()
        db.query(Note).filter(Note.user_email == user_email).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error clearing all history: {e}")
        return False
    finally:
        db.close()

def save_chat_message(user_email: str, role: str, message: str, citations: str = "", session_id: str = None):
    """Saves a message linked to the active session."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            user = User(email=user_email, name="ResearchOS User", password_hash="guest_hash")
            db.add(user)
            db.commit()

        if session_id:
            session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
            if session:
                session.updated_at = datetime.utcnow()

        chat = Chat(
            user_email=user_email,
            session_id=session_id,
            role=role,
            message=message,
            citations=citations
        )
        db.add(chat)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving chat: {e}")
        return False
    finally:
        db.close()

def get_user_chats(user_email: str, session_id: str = None):
    """Retrieves chat messages for a user or session."""
    db = get_db()
    try:
        query = db.query(Chat).filter(Chat.user_email == user_email)
        if session_id:
            query = query.filter(Chat.session_id == session_id)
        chats = query.order_by(Chat.created_at.asc()).all()
        return [{
            "role": c.role,
            "message": c.message,
            "citations": c.citations,
            "created_at": str(c.created_at)
        } for c in chats]
    except Exception as e:
        print(f"Error fetching chats: {e}")
        return []
    finally:
        db.close()

def clear_user_chats(user_email: str, session_id: str = None):
    """Deletes messages for the specified user or session."""
    db = get_db()
    try:
        query = db.query(Chat).filter(Chat.user_email == user_email)
        if session_id:
            query = query.filter(Chat.session_id == session_id)
        query.delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error clearing chats: {e}")
        return False
    finally:
        db.close()

def save_user_note(user_email: str, title: str, content: str, notebook: str = "AI Chat Notes") -> bool:
    """Saves or appends a note for the user."""
    db = get_db()
    try:
        note = Note(
            user_email=user_email,
            title=title,
            content=content,
            notebook=notebook
        )
        db.add(note)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error saving note: {e}")
        return False
    finally:
        db.close()

def get_user_notes(user_email: str, notebook: str = None) -> list:
    """Retrieves all notes for the user."""
    db = get_db()
    try:
        query = db.query(Note).filter(Note.user_email == user_email)
        if notebook:
            query = query.filter(Note.notebook == notebook)
        notes = query.order_by(Note.created_at.desc()).all()
        return [{
            "id": n.id,
            "title": n.title,
            "content": n.content,
            "notebook": n.notebook,
            "created_at": str(n.created_at)
        } for n in notes]
    except Exception as e:
        print(f"Error fetching notes: {e}")
        return []
    finally:
        db.close()

def update_user_note(note_id: int, user_email: str, title: str, content: str, notebook: str) -> bool:
    """Updates an existing note for the user."""
    db = get_db()
    try:
        note = db.query(Note).filter(Note.id == note_id, Note.user_email == user_email).first()
        if note:
            note.title = title
            note.content = content
            note.notebook = notebook
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error updating note: {e}")
        return False
    finally:
        db.close()

def delete_user_note(note_id: int, user_email: str) -> bool:
    """Deletes a note for the user."""
    db = get_db()
    try:
        note = db.query(Note).filter(Note.id == note_id, Note.user_email == user_email).first()
        if note:
            db.delete(note)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"Error deleting note: {e}")
        return False
    finally:
        db.close()

def log_user_activity(user_email: str, feature: str, action_type: str, title: str, details: str = "", raw_id: str = "") -> bool:
    """Logs an explicit user action whenever a platform feature is used."""
    db = get_db()
    try:
        act = UserActivity(
            user_email=user_email,
            feature=feature,
            action_type=action_type,
            title=title,
            details=details,
            raw_id=str(raw_id)
        )
        db.add(act)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error logging user activity: {e}")
        return False
    finally:
        db.close()

def get_user_activities(user_email: str) -> list:
    """Retrieves all logged user activities sorted chronologically."""
    db = get_db()
    try:
        acts = db.query(UserActivity).filter(UserActivity.user_email == user_email).order_by(UserActivity.created_at.desc()).all()
        return [{
            "id": a.id,
            "feature": a.feature,
            "action_type": a.action_type,
            "title": a.title,
            "details": a.details,
            "raw_id": a.raw_id,
            "created_at": str(a.created_at)
        } for a in acts]
    except Exception as e:
        print(f"Error fetching user activities: {e}")
        return []
    finally:
        db.close()

def delete_user_activity(activity_id: int, user_email: str) -> bool:
    """Deletes a specific user activity entry."""
    db = get_db()
    try:
        db.query(UserActivity).filter(UserActivity.id == activity_id, UserActivity.user_email == user_email).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def clear_all_user_activities(user_email: str) -> bool:
    """Clears all logged user activity history."""
    db = get_db()
    try:
        db.query(UserActivity).filter(UserActivity.user_email == user_email).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False
    finally:
        db.close()

def update_user_name(user_email: str, new_name: str) -> tuple[bool, str]:
    """Updates user display name."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return False, "User not found."
        user.name = new_name.strip()
        db.commit()
        return True, "Profile name updated successfully."
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        db.close()

def update_user_password(user_email: str, current_pass: str, new_pass: str) -> tuple[bool, str]:
    """Updates user password after validating current password."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            return False, "User not found."
        if user.password_hash != hash_password(current_pass):
            return False, "Current password is incorrect."
        user.password_hash = hash_password(new_pass)
        db.commit()
        return True, "Password updated successfully."
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        db.close()

def reset_user_password(email: str, new_pass: str) -> tuple[bool, str]:
    """Resets user password for an account."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == email.strip()).first()
        if not user:
            return False, "No account found with this email address."
        user.password_hash = hash_password(new_pass)
        db.commit()
        return True, "Password reset successfully! Please sign in with your new password."
    except Exception as e:
        db.rollback()
        return False, f"Database error: {str(e)}"
    finally:
        db.close()

def get_user_account_stats(user_email: str) -> dict:
    """Returns aggregated usage statistics for user."""
    db = get_db()
    try:
        user = db.query(User).filter(User.email == user_email).first()
        paper_count = db.query(Paper).filter(Paper.user_email == user_email).count()
        note_count = db.query(Note).filter(Note.user_email == user_email).count()
        chat_count = db.query(Chat).filter(Chat.user_email == user_email).count()
        session_count = db.query(ChatSession).filter(ChatSession.user_email == user_email).count()
        activity_count = db.query(UserActivity).filter(UserActivity.user_email == user_email).count()
        
        # Calculate total paper storage bytes
        papers = db.query(Paper).filter(Paper.user_email == user_email).all()
        total_bytes = sum([p.size_bytes or 0 for p in papers])
        
        return {
            "name": user.name if user else "Researcher",
            "email": user_email,
            "created_at": str(user.created_at)[:10] if user and user.created_at else "Recently",
            "paper_count": paper_count,
            "note_count": note_count,
            "chat_count": chat_count,
            "session_count": session_count,
            "activity_count": activity_count,
            "storage_bytes": total_bytes
        }
    except Exception as e:
        print(f"Error fetching user stats: {e}")
        return {
            "name": "Researcher",
            "email": user_email,
            "created_at": "Recently",
            "paper_count": 0,
            "note_count": 0,
            "chat_count": 0,
            "session_count": 0,
            "activity_count": 0,
            "storage_bytes": 0
        }
    finally:
        db.close()

def get_user_chat_interaction_count(user_email: str) -> int:
    """Returns real-time total count of AI chat queries/interactions by the user."""
    db = get_db()
    try:
        # Count all user messages across all sessions
        count = db.query(Chat).filter(Chat.user_email == user_email, Chat.role == "user").count()
        if count == 0:
            # Fallback: Count total logged AI Chat activities
            act_count = db.query(UserActivity).filter(UserActivity.user_email == user_email, UserActivity.feature == "AI Chat").count()
            return act_count
        return count
    except Exception as e:
        print(f"Error fetching chat interaction count: {e}")
        return 0
    finally:
        db.close()

# Initialize DB on load
get_engine()
