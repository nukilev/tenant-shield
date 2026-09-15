import os


HF_LOCAL_CACHE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "hf_cache"))
os.makedirs(HF_LOCAL_CACHE, exist_ok=True)
os.environ["HF_HOME"] = HF_LOCAL_CACHE

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PERSIST_DIRECTORY = "data/chroma_db"
COLLECTION_NAME = "israeli_contract_laws"


class LegalRAGService:
    def __init__(self):
        print("טוען מודל Embeddings מקומי...")
        # ציון מפורש של תיקיית השמירה
        self.embed_model = SentenceTransformer(
            "paraphrase-multilingual-MiniLM-L12-v2",
            cache_folder=HF_LOCAL_CACHE
        )

        self.chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def generate_embeddings(self, texts: list[str]) -> list[list[float]]:
        """מייצר וקטורים מקומית על המחשב ללא פנייה לאינטרנט"""
        embeddings = self.embed_model.encode(texts, show_progress_bar=False)
        return embeddings.tolist()

    def upsert_clauses(self, clauses: list[dict], law_name: str):
        """הכנסת סעיפים למאגר הווקטורי המקומי"""
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
        """חיפוש סמנטי מקומי ומהיר"""
        total_docs = self.collection.count()
        if total_docs == 0:
            return "מאגר החקיקה ריק. יש להריץ אינדוקס ראשוני."

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