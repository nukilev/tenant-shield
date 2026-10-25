import os
import chromadb
from google import genai

CHROMA_PERSIST_DIRECTORY = "data/chroma_db"
COLLECTION_NAME = "israeli_contract_laws"
EMBEDDING_MODEL_NAME = "gemini-embedding-001"


class LegalRAGService:
    def __init__(self):
        print("Initializing Legal RAG Service with Google Embeddings API...")

        # Use dedicated free key if available, otherwise fallback to main GEMINI_API_KEY
        api_key = os.getenv("GEMINI_FREE_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("Neither GEMINI_API_KEY nor GEMINI_FREE_KEY is set in environment.")

        self.ai_client = genai.Client(
            api_key=api_key,
            http_options={'api_version': 'v1'}
        )
        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings using Google's API efficiently and quickly."""
        if not texts:
            return []

        embeddings = []
        for text in texts:
            response = self.ai_client.models.embed_content(
                model=EMBEDDING_MODEL_NAME,
                contents=text,
            )
            embeddings.append(response.embeddings[0].values)
        return embeddings

    def upsert_clauses(self, clauses: list[dict], law_name: str):
        """Inserts or updates legal clauses in the local vector collection."""
        if not clauses:
            return

        texts = [c["text"] for c in clauses]
        ids = [c["id"] for c in clauses]
        metadatas = [{"law_name": law_name, "clause_title": c["title"]} for c in clauses]

        vectors = self.generate_embeddings(texts)

        self.collection.upsert(
            ids=ids,
            embeddings=vectors,
            documents=texts,
            metadatas=metadatas
        )

    def search_relevant_laws(self, query_text: str, top_k: int = 3) -> str:
        """Fast semantic retrieval against ChromaDB."""
        total_docs = self.collection.count()
        if total_docs == 0:
            return "Legal database is empty. Initial ingestion required."

        query_vector = self.generate_embeddings([query_text])[0]
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=min(top_k, total_docs)
        )

        extracted_sections = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            extracted_sections.append(
                f"### {meta['law_name']} - {meta['clause_title']}\n{doc}"
            )

        return "\n\n---\n\n".join(extracted_sections)