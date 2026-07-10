import os
import sys
import json
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from day2.ingestion import load_document
from day2.chunking import chunk_recursive
from day3.embeddings import embed_text, embed_query
from day4.generator import generate_answer
from day6.hybrid_retriever import HybridRetriever
from day7.reranker import rerank
from day8.evaluator import evaluate_dataset
from day8.test_dataset import TEST_CASES

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

DOCUMENTS = [
    'day2/sample.txt',
    'day2/sample.pdf',
    'day2/sample.docx',
    'day2/sample2.txt',
]

print('Building indexes (this runs once for all evaluations)...')

dense_client = chromadb.Client()
dense_collection = dense_client.create_collection('eval_dense')
all_chunks, all_ids, all_embeddings, all_meta = [], [], [], []
for path in DOCUMENTS:
    text = load_document(path)
    chunks = chunk_recursive(text, size=400, overlap=80)
    for i, chunk in enumerate(chunks):
        all_chunks.append(chunk)
        all_ids.append(f'{os.path.basename(path)}_c{i}')
        all_embeddings.append(embed_text(chunk))
        all_meta.append({'source': os.path.basename(path)})
dense_collection.add(ids=all_ids, embeddings=all_embeddings, documents=all_chunks, metadatas=all_meta)
print(f'Dense index: {len(all_chunks)} chunks')

hybrid = HybridRetriever()
hybrid.index(DOCUMENTS, collection_name='eval_hybrid')
print('Hybrid index built.')

def retrieve_dense(question, top_k=3):
    vec = embed_query(question)
    r = dense_collection.query(query_embeddings=[vec], n_results=top_k, include=['documents', 'metadatas', 'distances'])
    return [{'text': d, 'source': m['source'], 'distance': dist} for d, m, dist in zip(r['documents'][0], r['metadatas'][0], r['distances'][0])]

def retrieve_hybrid(question, top_k=3):
    return hybrid.search(question, top_k=top_k, fetch_k=10)

def retrieve_advanced(question, top_k=3):
    candidates = hybrid.search(question, top_k=10, fetch_k=15)
    return rerank(question, candidates, top_k=top_k)

results = []
results.append(evaluate_dataset(
    chatbot_name='Week 1 — Dense Only',
    test_cases=TEST_CASES,
    retrieve_fn=retrieve_dense,
    generate_fn=generate_answer,
))
results.append(evaluate_dataset(
    chatbot_name='Week 2 — Hybrid (BM25 + Dense + RRF)',
    test_cases=TEST_CASES,
    retrieve_fn=retrieve_hybrid,
    generate_fn=generate_answer,
))
results.append(evaluate_dataset(
    chatbot_name='Week 2 — Advanced (Hybrid + Re-ranking)',
    test_cases=TEST_CASES,
    retrieve_fn=retrieve_advanced,
    generate_fn=generate_answer,
))

print('\n')
print('=' * 70)
print(' FINAL EVALUATION REPORT CARD')
print('=' * 70)
print(f'{"Chatbot Version":<38} {"Faith":>6} {"Relev":>6} {"Recall":>7} {"MEAN":>6}')
print('-' * 70)
for r in results:
    print(f'{r["chatbot"]:<38} {r["faithfulness"]:>6.4f} {r["answer_relevance"]:>6.4f} {r["context_recall"]:>7.4f} {r["mean"]:>6.4f}')
print('=' * 70)

with open('day8/evaluation_results.json', 'w') as f:
    json.dump(results, f, indent=2)
print('\nResults saved to day8/evaluation_results.json')
