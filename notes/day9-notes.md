# Day 9 Notes — FastAPI Backend

## Task 1 — Observation Questions

### /docs page
FastAPI automatically generates interactive Swagger UI docs from the Pydantic models — request schemas, response schemas, validation rules, all without writing any documentation manually.

### Missing field status code
FastAPI returns 422 Unprocessable Entity when a required field is missing. This comes from Pydantic validation built into FastAPI — no custom validation code needed.

### GET vs POST
GET is for reading data (no body, idempotent, cacheable). POST is for sending data to create/process something. /health is GET because it just reads server status. /echo and /chat are POST because they send data to the server.

## Task 2 — RAG API Design

### Endpoints
- GET /health — server status and index info
- POST /chat — ask a question with optional session_id for follow-ups
- POST /ingest — add a new document to the index at runtime
- GET /session/{id} — retrieve conversation history

## Task 3 — Reflection Questions

### 400 vs 422
400 Bad Request is raised manually for business logic errors (e.g., divide by zero, invalid operation). 422 Unprocessable Entity is raised automatically by FastAPI/Pydantic when request JSON fails schema validation (missing fields, wrong types).

### Problems with in-memory index
1. The index disappears on server restart — must rebuild from scratch every time. Solution: use ChromaDB PersistentClient to save to disk.
2. Only one server instance has the index — can't scale horizontally. Solution: use a shared database (PostgreSQL with pgvector, or a remote ChromaDB instance).

### File uploads instead of raw text
Would need to accept multipart/form-data with UploadFile, detect file type, use load_document() to extract text, then chunk and index.

### Session history on server crash
Everything in chat_sessions dict is lost. Solution: store sessions in a persistent database (SQLite or PostgreSQL).

### Next step for users
A web-based chat UI (HTML/JS frontend) so they can interact without curl or terminal.
