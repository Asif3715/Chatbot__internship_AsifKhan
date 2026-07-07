import os
import sys
import numpy as np
from rank_bm25 import BM25Okapi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from day2.ingestion import load_document
from day2.chunking import chunk_recursive


class BM25Retriever:

    def __init__(self):
        self.bm25 = None
        self.chunks = []
        self.sources = []

    def _tokenise(self, text):
        return text.lower().split()

    def index(self, chunks, sources):
        self.chunks = chunks
        self.sources = sources
        tokenised = [self._tokenise(chunk) for chunk in chunks]
        self.bm25 = BM25Okapi(tokenised)
        print(f'BM25 index built over {len(chunks)} chunks.')

    def search(self, query, top_k=3):
        if self.bm25 is None:
            raise RuntimeError('Call index() before search()')
        query_tokens = self._tokenise(query)
        scores = self.bm25.get_scores(query_tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]
        results = []
        for idx in top_indices:
            results.append({
                'text': self.chunks[idx],
                'source': self.sources[idx],
                'score': float(scores[idx]),
                'rank_idx': int(idx),
            })
        return results


def build_bm25_index(doc_paths):
    all_chunks = []
    all_sources = []
    for path in doc_paths:
        text = load_document(path)
        chunks = chunk_recursive(text, size=400, overlap=80)
        for chunk in chunks:
            all_chunks.append(chunk)
            all_sources.append(os.path.basename(path))
    retriever = BM25Retriever()
    retriever.index(all_chunks, all_sources)
    return retriever


if __name__ == '__main__':
    import chromadb
    import google.generativeai as genai
    from dotenv import load_dotenv
    from day3.embeddings import embed_text, embed_query

    load_dotenv()
    genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

    doc_paths = [
        'day2/sample.txt',
        'day2/sample.pdf',
        'day2/sample.docx',
        'day2/sample2.txt',
    ]

    bm25 = build_bm25_index(doc_paths)

    client = chromadb.Client()
    collection = client.create_collection('day6_dense')
    all_chunks, all_sources, all_ids, all_embeddings = [], [], [], []
    for path in doc_paths:
        text = load_document(path)
        chunks = chunk_recursive(text, size=400, overlap=80)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_sources.append(os.path.basename(path))
            all_ids.append(f'{os.path.basename(path)}_c{i}')
            all_embeddings.append(embed_text(chunk))
    collection.add(
        ids=all_ids, embeddings=all_embeddings,
        documents=all_chunks,
        metadatas=[{'source': s} for s in all_sources],
    )

    def dense_search(query, top_k=3):
        vec = embed_query(query)
        r = collection.query(
            query_embeddings=[vec], n_results=top_k,
            include=['documents', 'metadatas', 'distances'],
        )
        return [
            {'text': d, 'source': m['source'], 'distance': dist}
            for d, m, dist in zip(r['documents'][0], r['metadatas'][0], r['distances'][0])
        ]

    test_queries = [
        'What is NexusChat?',
        'Professional plan 200 USD',
        'confidential data AI services policy',
    ]

    for query in test_queries:
        print(f'\n{"="*65}')
        print(f'QUERY: {query}')
        print(f'{"="*65}')
        bm25_results = bm25.search(query, top_k=3)
        dense_results = dense_search(query, top_k=3)
        print('\n[BM25 top result]')
        print(f' Source: {bm25_results[0]["source"]}')
        print(f' Score: {bm25_results[0]["score"]:.4f}')
        preview = bm25_results[0]['text'][:150]
        print(f' Text: {preview}...')
        print('\n[Dense top result]')
        print(f' Source: {dense_results[0]["source"]}')
        print(f' Distance: {dense_results[0]["distance"]:.4f}')
        preview = dense_results[0]['text'][:150]
        print(f' Text: {preview}...')
