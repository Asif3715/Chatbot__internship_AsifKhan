import os
import sys
import json
import hashlib
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from day2.ingestion import load_document
from day2.chunking import chunk_recursive
from day3.embeddings import embed_text

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

CHROMA_DIR = os.path.join(os.path.dirname(__file__), 'chroma_store')
HASH_FILE = os.path.join(os.path.dirname(__file__), 'doc_hashes.json')
COLLECTION_NAME = 'nexuschat_persistent'

def file_hash(path: str) -> str:
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def load_hashes() -> dict:
    if not os.path.exists(HASH_FILE):
        return {}
    with open(HASH_FILE, 'r') as f:
        return json.load(f)

def save_hashes(hashes: dict):
    with open(HASH_FILE, 'w') as f:
        json.dump(hashes, f, indent=2)

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    return client.get_or_create_collection(COLLECTION_NAME)

def index_document(collection, path: str):
    filename = os.path.basename(path)
    text = load_document(path)
    chunks = chunk_recursive(text, size=400, overlap=80)
    existing = collection.get(where={'source': filename})
    if existing['ids']:
        collection.delete(ids=existing['ids'])
        print(f' Removed {len(existing["ids"])} stale chunks for {filename}')
    ids, embeddings, texts, metas = [], [], [], []
    for i, chunk in enumerate(chunks):
        ids.append(f'{filename}_c{i}')
        embeddings.append(embed_text(chunk))
        texts.append(chunk)
        metas.append({'source': filename})
    collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metas)
    print(f' Indexed {len(chunks)} chunks for {filename}')
    return len(chunks)

def smart_startup(doc_paths: list) -> dict:
    collection = get_collection()
    saved_hashes = load_hashes()
    current_hashes = {}
    indexed_count = 0
    skipped_count = 0
    print('\nChecking document index...')
    for path in doc_paths:
        if not os.path.exists(path):
            print(f' WARNING: {path} not found, skipping.')
            continue
        filename = os.path.basename(path)
        current_hash = file_hash(path)
        current_hashes[filename] = current_hash
        if saved_hashes.get(filename) == current_hash:
            print(f' SKIP: {filename} unchanged')
            skipped_count += 1
        else:
            print(f' INDEX: {filename} (new or modified)')
            indexed_count += index_document(collection, path)
    save_hashes(current_hashes)
    total = collection.count()
    print(f'\nIndex ready: {total} total chunks')
    print(f' Indexed this run: {indexed_count} chunks')
    print(f' Skipped (cached): {skipped_count} documents')
    return {'collection': collection, 'total_chunks': total, 'indexed_this_run': indexed_count, 'skipped': skipped_count}

if __name__ == '__main__':
    import time
    DAY2 = os.path.join(ROOT, 'day2')
    DOCS = [os.path.join(DAY2, 'sample.txt'), os.path.join(DAY2, 'sample.pdf'), os.path.join(DAY2, 'sample.docx'), os.path.join(DAY2, 'sample2.txt')]
    print('=== RUN 1: First startup ===')
    start = time.time()
    result = smart_startup(DOCS)
    print(f'Run 1 completed in {time.time() - start:.1f}s')
    print(f'Total chunks: {result["total_chunks"]}')
    print('\n=== RUN 2: Second startup (cached) ===')
    start = time.time()
    result = smart_startup(DOCS)
    print(f'Run 2 completed in {time.time() - start:.1f}s')
    print(f'Indexed this run: {result["indexed_this_run"]} chunks')
    print(f'Skipped: {result["skipped"]} documents')
