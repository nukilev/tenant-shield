# Tenant Shield

An intelligent legal RAG application for analyzing and reviewing residential lease agreements against Israeli rental housing laws. Currently under active development.

---

## About the Project

Tenant Shield is a full-stack system designed to help tenants in Israel thoroughly understand their lease agreements, identify problematic, unfair, or illegal clauses that contradict rental laws, and receive actionable legal recommendations in real time.

The system combines a local vector-based RAG (Retrieval-Augmented Generation) architecture with advanced natural language processing capabilities using Google's Gemini models, enabling automated analysis of full contracts or targeted reviews of individual clauses.

---

## Key Features

- **Automated Full Contract Analysis:** Upload lease files (PDF, DOCX, TXT) with smart batching and asynchronous parallel processing.
- **Single Clause Review:** Input a specific contract clause and receive immediate analysis against the legal database.
- **Legal RAG Grounding:** Retrieval of relevant legal clauses from a local vector database (ChromaDB) containing Israeli rental legislation.
- **Risk Classification System:** Automatic categorization of clauses by risk level (Red: illegal/high risk, Yellow: ambiguous/requires clarification, Green: compliant).
- **Real-Time Progress Tracking:** A dynamic progress bar updated directly from the backend during batch contract analysis.
- **RAG Context Inspection:** Expandable view to inspect the exact original legal text retrieved from the database for each clause.

---

## Architecture & Tech Stack

### Backend:
- **Python / FastAPI:** High-performance asynchronous API server for handling requests, file processing, and RAG pipelines.
- **Google GenAI SDK (`gemini-3.8-flash`):** Structured legal insights and analysis utilizing JSON Schemas (Pydantic).
- **ChromaDB:** Local vector database for indexing and retrieving relevant legal sections.
- **Asyncio:** Parallel processing of clause batches for improved response times.

### Frontend:
- **React (Vite):** Modern, clean, and responsive user interface.
- **Tailwind CSS:** Component styling and layout design.
- **Lucide React:** Vector icons.

---

## Local Development Setup

### Prerequisites:
- Python 3.10+
- Node.js & npm
- Active Google Gemini API Key

### 1. Clone the Repository & Setup Backend
Navigate to the backend directory and install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a .env file in the root directory of the backend and add your Gemini API key:
```bash
GEMINI_API_KEY=your_api_key_here
```

### 3. Run Legal Corpus Ingestion (Local RAG Setup)
Before starting the server for the first time, you must parse and ingest the local legal markdown files into ChromaDB:
```bash
python scripts/ingest_laws.py
```

### 4. Start the Backend Server
```bash
uvicorn src.api:app --reload
```

### 5. Start the Frontend Application
In a separate terminal, navigate to the frontend directory and start the Vite development server:
```bash
npm install
npm run dev
```

---

## Development Status & Roadmap
The project is currently in Alpha / Active Development. Upcoming milestones include:

- Enhancing the clause splitting mechanism for cleaner boundary parsing.

- Expanding the vector legal database with additional housing-related legislation.

- Adding export functionality to download the full report.

## License
Developed for personal and educational use. All rights reserved.
