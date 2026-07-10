# Day 10 Notes — Persistent Storage

## Task 1 — Observation Questions

### check_same_thread=False
FastAPI handles requests in multiple threads. With default `True`, SQLite would raise an error if a connection created in one thread is used in another. Setting it to False allows sharing the connection across threads.

### ? placeholders instead of f-strings
Prevents SQL injection attacks. If user input contains SQL syntax (e.g., `' OR 1=1 --`), f-strings could turn it into malicious SQL. Parameterised queries (? placeholders) always treat input as data, never as executable SQL.

### Running twice without deleting
The CREATE TABLE IF NOT EXISTS and CREATE INDEX IF NOT EXISTS mean the table/index are only created if missing. The INSERT INTO commands add duplicate rows to the existing table — so session-001 and session-002 would appear twice each.

## Task 2 — Smart Startup Results

- Run 1: 4.6s, 4 chunks indexed (first time, all documents embedded)
- Run 2: 0.0s, 0 chunks indexed, 4 skipped (all cached — no API calls)
- Run 3 (after modifying sample2.txt): only sample2.txt re-indexed

## Task 3 — Reflection Questions

### Startup speed comparison
Day 9/rag_api.py re-indexes every startup (~4.6s + Gemini API calls for every chunk). Day 10/persistent_api.py on Run 2+ completes startup in under 1 second with zero Gemini API calls. Saved ~4.5 seconds and 4 embed_text() API calls.

### Why BM25 doesn't need persistence
BM25 is a keyword-frequency algorithm that works on raw text — it's fast to rebuild (no API calls). ChromaDB's dense embeddings require expensive API calls so they benefit from persistence.

### Ingested document lost on restart
The /ingest endpoint only adds chunks to the in-memory BM25 index and persistent ChromaDB. It does not save the source file to disk. After restart, BM25 is rebuilt from the original STARTUP_DOCUMENTS only — newly ingested files are lost from BM25 (though they survive in persistent ChromaDB). Fix: save uploaded files to a `documents/` directory on disk and include them in startup.

### One remaining piece lost on restart
The BM25 index is rebuilt from scratch on every startup. While fast, any documents added via /ingest that weren't saved to disk are lost from BM25 retrieval.

### Debugging a disappeared conversation
Check the SQLite database: `sqlite3 day10/chat_history.db "SELECT * FROM chat_history WHERE session_id='<id>';"` — if the session exists in SQLite but the API returns 404, check the endpoint and database file permissions.
