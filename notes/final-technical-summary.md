# NexusChat — Final Technical Summary

## 1. What Was Built

NexusChat is a retrieval-augmented generation (RAG) chatbot that answers questions using the user's own documents. It ingests PDF, DOCX, and TXT files, breaks them into searchable chunks, and retrieves the most relevant passages at query time using a hybrid search pipeline combining dense vector search and BM25 keyword search. The system is served through a FastAPI backend with a browser-based chat UI, persisted in SQLite and ChromaDB, and containerised with Docker for deployment on any machine.

## 2. Architecture

| Layer | Technology |
|---|---|
| Document ingestion | PyMuPDF (PDF), python-docx (DOCX), plain text reader |
| Chunking | LangChain RecursiveCharacterTextSplitter (400 chars, 80 overlap) |
| Embeddings | Google Gemini Embedding API (gemini-embedding-2) |
| Vector store | ChromaDB PersistentClient |
| Keyword search | rank-bm25 BM25Retriever |
| Retrieval fusion | Reciprocal Rank Fusion (RRF) |
| Re-ranking | sentence-transformers CrossEncoder (ms-marco-MiniLM-L-6-v2) |
| Query rewriting | Google Gemini Flash (standalone query decomposition) |
| Answer generation | Google Gemini Flash |
| Chat persistence | SQLite |
| Backend API | FastAPI + Uvicorn |
| Chat UI | Single-file HTML/CSS/JS with fetch API |
| Containerisation | Docker + Docker Compose |
| CI/CD | GitHub Actions |

## 3. Key Technical Decisions

**Hybrid search (dense + BM25) over dense-only retrieval.** Dense embeddings excel at semantic similarity but miss exact keyword matches — a query for "DOCX format" might not retrieve a chunk that literally says "DOCX" if the embedding space maps it closer to "document type." BM25 catches these lexical matches. Reciprocal Rank Fusion combines both result lists into a single ranking, giving us the precision of semantic search and the recall of keyword search. The measurable impact was clear: hybrid retrieval consistently outperformed dense-only in the Day 8 evaluation.

**SQLite over PostgreSQL for chat history.** NexusChat is a single-user or small-team application. SQLite requires zero configuration, stores the entire database in a single file, and is perfectly adequate for thousands of chat turns. PostgreSQL would add a service dependency, require a running database container, and add operational complexity with no practical benefit at this scale. The trade-off is clear: SQLite for simplicity when scale doesn't demand otherwise.

**Single-file HTML for the chat UI over a React SPA.** The UI's job is to send questions and display answers. A React project would add npm, a build step, node_modules, and a dev server — all overhead that slows iteration when the backend is the real product. A single HTML file with vanilla JavaScript loads instantly, requires no build tools, and can be served directly by FastAPI. The trade-off is that state management and component reuse are manual, but for a chat interface with four interactive elements, that cost is negligible.

## 4. What I Would Do Next

**Streaming token output via Server-Sent Events.** The API currently waits for Gemini to generate the full answer before responding — 5 to 8 seconds of dead time. Using SSE, the FastAPI endpoint would stream tokens as they arrive from Gemini, and the chat UI would append them in real time. This cuts perceived latency from seconds to milliseconds without changing the underlying generation speed.

**PDF and DOCX file upload support.** The upload panel currently accepts raw text only. I would add a file input element accepting `.pdf` and `.docx`, parse the uploaded file server-side using PyPDF2 and python-docx, extract the text, and pass it to the existing chunking pipeline. This requires changing the `/ingest` endpoint to accept `multipart/form-data` and adding file type validation.

**Persistent session restoration across page refreshes.** Currently, refreshing the browser loses the session ID and message history. I would store the session ID in `localStorage` on the client side and load message history from the `/session/{id}` endpoint on page load, re-rendering past messages so the conversation survives a refresh.
