import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from google import genai
import asyncio
from src.progress_state import current_progress
from src.schemas import (
    ClauseAnalysisRequest,
    ClauseAnalysisResponse,
    FullContractAnalysisResponse,
    ContractSummaryMetrics
)

from src.services.ai_service import analyze_clause_with_rag, analyze_full_contract, rag_service
from src.services.contract_parser import extract_text_from_bytes, split_contract_into_clauses

load_dotenv(override=True)

app = FastAPI(
    title="Tenant Shield API 🛡️",
    description="RAG-based Legal Advisory API for Israeli Rental Contracts",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    chroma_path = os.getenv("CHROMA_DB_PATH", "chroma_db")
    if not os.path.exists(chroma_path) or not os.listdir(chroma_path):
        print("ChromaDB not detected. Running initial ingestion...")
        from scripts.ingest_laws import run_ingestion
        run_ingestion()
        print("Ingestion complete.")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("src.api:app", host="0.0.0.0", port=port)

@app.get("/api/progress")
async def get_progress():
    return current_progress

def get_gemini_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is missing in .env file")
    return genai.Client(api_key=api_key)

@app.get("/api/health", tags=["System"])
async def health_check():
    """Returns server status and the total number of indexed statutory clauses in ChromaDB."""
    doc_count = rag_service.collection.count()
    return {
        "status": "healthy",
        "indexed_law_clauses": doc_count
    }

@app.post("/api/analyze-clause", response_model=ClauseAnalysisResponse, tags=["Analysis"])
async def analyze_single_clause(request: ClauseAnalysisRequest):
    """Analyzes a single lease clause against Israeli rental legislation using local RAG."""
    client = get_gemini_client()
    try:
        result = await analyze_clause_with_rag(client, request.clause_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Upstream AI service error: {str(e)}")

@app.post("/api/analyze-contract", response_model=FullContractAnalysisResponse, tags=["Analysis"])
async def analyze_contract_file(file: UploadFile = File(...)):
    """Extracts, segments, and analyzes all clauses from an uploaded contract file (PDF, DOCX, TXT)."""
    if not file.filename or not file.filename.lower().endswith((".pdf", ".docx", ".txt")):
        raise HTTPException(status_code=400, detail="Unsupported file extension. Allowed: .pdf, .docx, .txt")

    try:
        file_bytes = await file.read()
        raw_text = extract_text_from_bytes(file_bytes, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse document: {str(e)}")

    clauses = split_contract_into_clauses(raw_text)
    if not clauses:
        raise HTTPException(status_code=422, detail="No valid contract clauses could be extracted from the file.")

    client = get_gemini_client()
    try:
        results = await analyze_full_contract(client, clauses)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Contract analysis failed: {str(e)}")

    red_count = sum(1 for r in results if r["analysis"].get("risk") == "red")
    yellow_count = sum(1 for r in results if r["analysis"].get("risk") == "yellow")
    green_count = sum(1 for r in results if r["analysis"].get("risk") == "green")

    metrics = ContractSummaryMetrics(
        total_clauses=len(results),
        red_count=red_count,
        yellow_count=yellow_count,
        green_count=green_count
    )

    return FullContractAnalysisResponse(
        filename=file.filename,
        metrics=metrics,
        results=results
    )
