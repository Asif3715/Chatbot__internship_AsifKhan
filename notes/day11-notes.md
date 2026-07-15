# Day 11 Notes — Web Chat Interface

## Reflection Questions

### 1. Plain HTML/CSS/JS vs Framework

Two things that would be easier with React:

- **State management**: With React, managing `sessionId`, message history, and UI state (typing indicator, upload status) would be handled through hooks like `useState` and `useReducer` instead of manually tracking variables and updating the DOM. React's reactivity system eliminates the need for manual `appendChild` and `textContent` updates.
- **Component reusability**: The message bubble, source tag, and typing indicator could each be separate components with their own props and logic. Adding new features (like a delete button or emoji reactions) would mean creating a new component rather than modifying a monolithic `appendMessage` function.

One thing that was simpler without a framework:

- **Zero setup and instant iteration**: No `npm install`, no build step, no webpack config. I saved the HTML file and refreshed the browser. The entire UI lives in one file that anyone can open directly. With React, I would need `create-react-app` or Vite, a `node_modules` folder, and a dev server running.

### 2. Session ID on Page Refresh

If the user refreshes the page, `sessionId` is reset to `null` and all message history disappears from the UI. The backend still has the old session stored in SQLite, but the browser has no way to retrieve it.

To fix this using `localStorage`:

```javascript
// On receiving a new session ID from the API:
localStorage.setItem('nexuschat_session', sessionId);

// On page load, restore it:
sessionId = localStorage.getItem('nexuschat_session');
```

For a more complete solution, you could also store the full message history in `localStorage` and re-render it on load, so the conversation survives a refresh.

### 3. Supporting File Uploads (PDF/DOCX)

**UI changes:**

- Replace the textarea with an `<input type='file' accept='.pdf,.docx,.txt'>` element.
- Use the `FileReader` API or `FormData` to send the file as `multipart/form-data` instead of JSON.
- Show a progress indicator during upload since files can be large.

**API changes:**

- Change the `/ingest` endpoint to accept `UploadFile` (FastAPI's built-in file upload handler) instead of a JSON body.
- Add file parsing: use `PyPDF2` or `pdfplumber` for PDFs, `python-docx` for DOCX files, to extract raw text before chunking.
- Handle file size limits and validate file types on the server side.

### 4. Reducing Latency (8-second response)

Three places to look:

1. **RAG pipeline — Reranker**: The `rerank` function calls the Gemini API to score each chunk. With 10 chunks, that is 10 API calls. Batching them into a single prompt or using a local sentence-transformer model for reranking would cut this significantly.
2. **Embedding generation**: `embed_query` makes an API call to Gemini for each query. Caching embeddings for repeated queries or using a local embedding model (like `all-MiniLM-L6-v2`) would remove this network round trip.
3. **UI — Streaming**: Instead of waiting for the full answer, use Server-Sent Events (SSE) to stream tokens as they are generated. The user sees text appearing in real time, which feels faster even if total time is the same.

### 5. Most Impactful Component on Answer Quality

The **reranker** (Day 7) has the most impact on answer quality. Retrieval (dense + BM25) cast a wide net and return 10 candidates, but many of those are loosely related. The reranker is the final filter that picks the 3 most relevant chunks. If the reranker selects poor chunks, the generator produces a poor answer no matter how good the LLM is. Conversely, a strong reranker can compensate for mediocre retrieval by elevating the right chunks to the top. It is the quality gate between "lots of data" and "the right data."

---

## Screenshot

![NexusChat UI Working](Screenshot%20from%202026-07-15%2007-59-26.png)
