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

from day2.ingestion import load_document
from day2.chunking import chunk_recursive
from day3.embeddings import embed_text, embed_query
from day4.generator import generate_answer
from day5.memory_chatbot import rewrite_query
from day6.bm25_retriever import BM25Retriever
from day6.hybrid_retriever import reciprocal_rank_fusion
from day7.reranker import rerank
from day10.chat_store import initialise_db, save_turn, get_session_history, list_all_sessions, delete_session
from day10.persistent_index import smart_startup

load_dotenv()

app = FastAPI(title='NexusChat Persistent API', version='2.0.0')

DAY2_DIR = os.path.join(ROOT, 'day2')
STARTUP_DOCUMENTS = [os.path.join(DAY2_DIR, 'sample.txt'), os.path.join(DAY2_DIR, 'sample.pdf'), os.path.join(DAY2_DIR, 'sample.docx'), os.path.join(DAY2_DIR, 'sample2.txt')]
dense_collection = None
bm25_retriever = None
total_chunks = 0

@app.on_event('startup')
async def startup():
    global dense_collection, bm25_retriever, total_chunks
    initialise_db()
    result = smart_startup(STARTUP_DOCUMENTS)
    dense_collection = result['collection']
    total_chunks = result['total_chunks']
    all_chunks, all_sources = [], []
    for path in STARTUP_DOCUMENTS:
        if not os.path.exists(path):
            continue
        text = load_document(path)
        chunks = chunk_recursive(text, size=400, overlap=80)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_sources.append(os.path.basename(path))
    bm25_retriever = BM25Retriever()
    bm25_retriever.index(all_chunks, all_sources)
    print(f'BM25 index built: {len(all_chunks)} chunks')

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: list
    session_id: str
    turn_number: int

class IngestRequest(BaseModel):
    filename: str
    content: str

class IngestResponse(BaseModel):
    filename: str
    chunks_added: int
    total_chunks: int

@app.get('/health')
def health():
    sessions = list_all_sessions()
    return {'status': 'ok', 'version': '2.0.0', 'chunks_indexed': total_chunks, 'total_sessions': len(sessions), 'storage': 'persistent (SQLite + ChromaDB PersistentClient)'}

@app.post('/chat', response_model=ChatResponse)
def chat(request: ChatRequest):
    session_id = request.session_id or str(uuid.uuid4())
    history = get_session_history(session_id)
    try:
        standalone = rewrite_query(request.question, history)
        query_vec = embed_query(standalone)
        raw = dense_collection.query(query_embeddings=[query_vec], n_results=10, include=['documents', 'metadatas', 'distances'])
        dense_results = [{'text': d, 'source': m['source'], 'distance': dist} for d, m, dist in zip(raw['documents'][0], raw['metadatas'][0], raw['distances'][0])]
        bm25_results = bm25_retriever.search(standalone, top_k=10)
        merged = reciprocal_rank_fusion([bm25_results, dense_results])
        chunks = rerank(standalone, merged[:10], top_k=3)
        if not chunks:
            raise HTTPException(status_code=404, detail='No relevant documents found.')
        answer = generate_answer(request.question, chunks)
        save_turn(session_id, request.question, answer)
        sources = [{'source': c['source'], 'preview': c['text'][:150]} for c in chunks]
        return ChatResponse(answer=answer, sources=sources, session_id=session_id, turn_number=len(history) + 1)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/sessions')
def sessions():
    return list_all_sessions()

@app.get('/session/{session_id}')
def get_session(session_id: str):
    history = get_session_history(session_id)
    if not history:
        raise HTTPException(status_code=404, detail='Session not found.')
    return {'session_id': session_id, 'turn_count': len(history), 'history': history}

@app.delete('/session/{session_id}')
def remove_session(session_id: str):
    deleted = delete_session(session_id)
    if deleted == 0:
        raise HTTPException(status_code=404, detail='Session not found.')
    return {'deleted_turns': deleted, 'session_id': session_id}

@app.post('/ingest', response_model=IngestResponse)
def ingest(request: IngestRequest):
    global total_chunks
    try:
        chunks = chunk_recursive(request.content, size=400, overlap=80)
        if not chunks:
            raise HTTPException(status_code=400, detail='No chunks produced.')
        ids, embeddings, texts, metas = [], [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f'{request.filename}_c{i}')
            embeddings.append(embed_text(chunk))
            texts.append(chunk)
            metas.append({'source': request.filename})
        dense_collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metas)
        total_chunks += len(chunks)
        return IngestResponse(filename=request.filename, chunks_added=len(chunks), total_chunks=total_chunks)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == '__main__':
    uvicorn.run('persistent_api:app', host='0.0.0.0', port=8000, reload=False)
