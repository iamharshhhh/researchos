# Re-exporting database and authentication functions for compatibility
from backend.database import (
    register_user,
    authenticate_user,
    save_document_metadata,
    get_user_documents,
    delete_document_metadata,
    update_paper_metadata,
    save_chat_message,
    get_user_chats,
    generate_unique_paper_id
)

def init_db():
    pass
