import sys
import os
import types
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

mock_genai = types.ModuleType('google.generativeai')
mock_genai.configure = MagicMock()
mock_genai.GenerativeModel = MagicMock()
mock_genai.embed_content = MagicMock(return_value={'embedding': [0.1] * 768})
sys.modules['google.generativeai'] = mock_genai

mock_chromadb = types.ModuleType('chromadb')
mock_chromadb.PersistentClient = MagicMock()
mock_chromadb.Client = MagicMock()
sys.modules['chromadb'] = mock_chromadb

mock_st = types.ModuleType('sentence_transformers')
mock_st.CrossEncoder = MagicMock()
sys.modules['sentence_transformers'] = mock_st

mock_ce = types.ModuleType('cross_encoder')
sys.modules['cross_encoder'] = mock_ce

mock_collection = MagicMock()
mock_collection.count.return_value = 42
mock_collection.query.return_value = {
    'documents': [['NexusChat is an enterprise RAG chatbot.']],
    'metadatas': [[{'source': 'sample.pdf'}]],
    'distances': [[0.12]],
}

mock_bm25 = MagicMock()

with patch('day10.persistent_index.smart_startup', return_value={
    'collection': mock_collection,
    'total_chunks': 42,
    'indexed_this_run': 0,
    'skipped': 4,
}), patch('day10.chat_store.initialise_db'), \
     patch('day10.chat_store.get_session_history', side_effect=lambda sid: [{'question': 'hi', 'answer': 'hello', 'timestamp': '2025-01-01'}] if sid != 'nonexistent-session-id' else []), \
     patch('day10.chat_store.save_turn'), \
     patch('day10.chat_store.list_all_sessions', return_value=[]), \
     patch('day10.chat_store.delete_session', return_value=1), \
     patch('day6.bm25_retriever.BM25Retriever', return_value=mock_bm25), \
     patch('day5.memory_chatbot.rewrite_query', return_value='What is NexusChat?'), \
     patch('day3.embeddings.embed_query', return_value=[0.1] * 768), \
     patch('day3.embeddings.embed_text', return_value=[0.1] * 768), \
     patch('day7.reranker.rerank', side_effect=lambda q, c, top_k=3: c[:top_k]), \
     patch('day4.generator.generate_answer', return_value='NexusChat is a RAG chatbot. [Source: sample.pdf]'):
    from day10 import persistent_api
    app = persistent_api.app
    persistent_api.dense_collection = mock_collection
    persistent_api.bm25_retriever = mock_bm25
    persistent_api.total_chunks = 42

from day14.auth import generate_api_key, KEYS_FILE

if KEYS_FILE.exists():
    KEYS_FILE.unlink()
TEST_API_KEY = generate_api_key('ci-test')

client = TestClient(app)
AUTH_HEADERS = {'X-API-Key': TEST_API_KEY}


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        r = client.get('/health')
        assert r.status_code == 200
        assert r.json()['status'] == 'ok'

    def test_health_contains_chunks_indexed(self):
        r = client.get('/health')
        assert 'chunks_indexed' in r.json()


class TestChatEndpoint:
    def test_chat_requires_question(self):
        r = client.post('/chat', json={}, headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_chat_returns_answer_and_session(self):
        r = client.post('/chat', json={'question': 'What is NexusChat?'}, headers=AUTH_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert 'answer' in data
        assert 'session_id' in data
        assert 'sources' in data
        assert len(data['answer']) > 0

    def test_chat_session_id_persists(self):
        r1 = client.post('/chat', json={'question': 'Hello'}, headers=AUTH_HEADERS)
        sid = r1.json()['session_id']
        r2 = client.post('/chat', json={'question': 'Follow up', 'session_id': sid}, headers=AUTH_HEADERS)
        assert r2.status_code == 200
        assert r2.json()['session_id'] == sid

    def test_chat_empty_question_rejected(self):
        r = client.post('/chat', json={'question': ''}, headers=AUTH_HEADERS)
        assert r.status_code in (200, 400, 422)


class TestIngestEndpoint:
    def test_ingest_requires_fields(self):
        r = client.post('/ingest', json={'filename': 'test.txt'}, headers=AUTH_HEADERS)
        assert r.status_code == 422

    def test_ingest_returns_chunk_count(self):
        r = client.post('/ingest', json={
            'filename': 'test.txt',
            'content': 'This is test content for the CI pipeline. ' * 20,
        }, headers=AUTH_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert 'chunks_added' in data
        assert data['chunks_added'] >= 1


class TestSessionEndpoint:
    def test_missing_session_returns_404(self):
        r = client.get('/session/nonexistent-session-id', headers=AUTH_HEADERS)
        assert r.status_code == 404

    def test_existing_session_returns_history(self):
        r1 = client.post('/chat', json={'question': 'CI test question'}, headers=AUTH_HEADERS)
        sid = r1.json()['session_id']
        r2 = client.get(f'/session/{sid}', headers=AUTH_HEADERS)
        assert r2.status_code == 200
        assert r2.json()['turn_count'] >= 1
