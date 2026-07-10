import os
import sys
import uuid
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import uvicorn

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from day2.chunking import chunk_recursive
from day3.embeddings import embed_text
from day4.generator import generate_answer
from day5.memory_chatbot import rewrite_query
from day6.hybrid_retriever import HybridRetriever

load_dotenv()

app = FastAPI(title='NexusChat RAG API', version='1.0.0')
retriever = HybridRetriever()
chat_sessions = {}
chunks_indexed = 0

DOC_DIR = os.path.join(ROOT, 'day2')
STARTUP_DOCUMENTS = [os.path.join(DOC_DIR, 'sample.txt'), os.path.join(DOC_DIR, 'sample.pdf'), os.path.join(DOC_DIR, 'sample.docx'), os.path.join(DOC_DIR, 'sample2.txt')]

@app.on_event('startup')
async def startup_event():
    global chunks_indexed
    print('Building RAG index on startup...')
    retriever.index(STARTUP_DOCUMENTS)
    chunks_indexed = retriever.collection.count()
    print(f'Startup complete. {chunks_indexed} chunks indexed.')

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    session_id: str

class IngestRequest(BaseModel):
    filename: str
    content: str

class IngestResponse(BaseModel):
    filename: str
    chunks_added: int
    total_chunks: int

class SessionHistoryResponse(BaseModel):
    session_id: str
    turn_count: int
    history: list

@app.get('/health')
def health():
    return {'status': 'ok', 'chunks_indexed': chunks_indexed, 'model': 'gemini-3-flash-preview', 'sessions_active': len(chat_sessions)}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    global chat_sessions
    session_id = request.session_id or str(uuid.uuid4())
    history = chat_sessions.get(session_id, [])
    try:
        standalone = rewrite_query(request.question, history)
        candidates = retriever.search(standalone, top_k=10, fetch_k=15)
        try:
            from day7.reranker import rerank
            chunks = rerank(standalone, candidates, top_k=3)
        except ImportError:
            chunks = candidates[:3]
        if not chunks:
            raise HTTPException(status_code=404, detail='No relevant documents found for this question.')
        answer = generate_answer(request.question, chunks)
        history.append({'question': request.question, 'answer': answer})
        chat_sessions[session_id] = history
        sources = [{'source': c['source'], 'preview': c['text'][:150]} for c in chunks]
        return ChatResponse(answer=answer, sources=sources, session_id=session_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Internal error: {str(e)}')

@app.post('/ingest', response_model=IngestResponse)
def ingest(request: IngestRequest):
    global chunks_indexed
    try:
        chunks = chunk_recursive(request.content, size=400, overlap=80)
        if not chunks:
            raise HTTPException(status_code=400, detail='Document produced no chunks.')
        new_ids, new_embeddings, new_texts, new_meta = [], [], [], []
        for i, chunk in enumerate(chunks):
            new_ids.append(f'{request.filename}_c{i}')
            new_embeddings.append(embed_text(chunk))
            new_texts.append(chunk)
            new_meta.append({'source': request.filename})
        retriever.collection.add(ids=new_ids, embeddings=new_embeddings, documents=new_texts, metadatas=new_meta)
        existing_chunks = retriever.bm25_retriever.chunks + new_texts
        existing_sources = retriever.bm25_retriever.sources + [request.filename] * len(chunks)
        retriever.bm25_retriever.index(existing_chunks, existing_sources)
        chunks_indexed += len(chunks)
        return IngestResponse(filename=request.filename, chunks_added=len(chunks), total_chunks=chunks_indexed)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Ingest error: {str(e)}')

@app.get('/session/{session_id}', response_model=SessionHistoryResponse)
def get_session(session_id: str):
    if session_id not in chat_sessions:
        raise HTTPException(status_code=404, detail=f'Session {session_id} not found.')
    history = chat_sessions[session_id]
    return SessionHistoryResponse(session_id=session_id, turn_count=len(history), history=history)

if __name__ == '__main__':
    uvicorn.run('rag_api:app', host='0.0.0.0', port=8000, reload=False)
