import chromadb
from chromadb.utils import embedding_functions
from backend.config import CHROMA_PATH, EMBEDDING_MODEL_NAME

# Initialize ChromaDB persistent client
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

_minilm_ef = None

def get_embedding_function():
    """Lazy-loads the SentenceTransformer embedding function."""
    global _minilm_ef
    if _minilm_ef is None:
        _minilm_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL_NAME
        )
    return _minilm_ef

def get_or_create_collection(collection_name: str = "research_papers"):
    """Returns the ChromaDB collection."""
    return chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=get_embedding_function()
    )

def add_documents_to_db(documents: list[dict], collection_name: str = "research_papers"):
    """
    Adds or updates processed document chunks in ChromaDB.
    documents format: [{"id": "chunk_id", "text": "content", "metadata": {...}}]
    """
    if not documents:
        return
    collection = get_or_create_collection(collection_name)
    
    ids = [doc["id"] for doc in documents]
    texts = [doc["text"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    
    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas
    )

def search_documents(
    query: str, 
    n_results: int = 5, 
    filter_doc_ids: list[str] = None, 
    collection_name: str = "research_papers"
) -> dict:
    """Searches ChromaDB for the most relevant chunks with optional doc_id filtering."""
    collection = get_or_create_collection(collection_name)
    
    where_clause = None
    if filter_doc_ids and len(filter_doc_ids) > 0:
        if len(filter_doc_ids) == 1:
            where_clause = {"doc_id": filter_doc_ids[0]}
        else:
            where_clause = {"doc_id": {"$in": filter_doc_ids}}
            
    results = collection.query(
        query_texts=[query],
        n_results=n_results,
        where=where_clause
    )
    return results

def delete_documents_by_doc_id(doc_id: str, collection_name: str = "research_papers"):
    """Deletes all chunks belonging to doc_id from ChromaDB."""
    try:
        collection = get_or_create_collection(collection_name)
        collection.delete(where={"doc_id": doc_id})
    except Exception as e:
        print(f"Error deleting ChromaDB chunks for doc_id {doc_id}: {e}")

def get_all_chunks_for_doc_id(doc_id: str, limit: int = 16, collection_name: str = "research_papers") -> list[str]:
    """Retrieves stored text chunks for a specific paper doc_id without loading embedding models."""
    try:
        collection = chroma_client.get_or_create_collection(name=collection_name)
        results = collection.get(
            where={"doc_id": doc_id},
            limit=limit
        )
        if results and results.get("documents"):
            return results["documents"]
        return []
    except Exception as e:
        print(f"Error fetching chunks for doc_id {doc_id}: {e}")
        return []

