import os
import sys
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from day2.ingestion import load_document
from day2.chunking import chunk_recursive
from day3.embeddings import embed_text, embed_query

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

def create_collection(name='nexuschat_day3'):
    client = chromadb.Client()
    collection = client.create_collection(name=name)
    print(f'Created collection: {name}')
    return collection

def index_documents(collection, doc_paths):
    all_ids = []
    all_embeddings = []
    all_texts = []
    all_metadata = []

    for doc_path in doc_paths:
        print(f' Indexing: {doc_path}')
        text = load_document(doc_path)
        chunks = chunk_recursive(text, size=300, overlap=50)
        for i, chunk in enumerate(chunks):
            chunk_id = f'{os.path.basename(doc_path)}_chunk_{i}'
            embedding = embed_text(chunk)
            all_ids.append(chunk_id)
            all_embeddings.append(embedding)
            all_texts.append(chunk)
            all_metadata.append({'source': os.path.basename(doc_path)})

    collection.add(
        ids=all_ids,
        embeddings=all_embeddings,
        documents=all_texts,
        metadatas=all_metadata,
    )
    print(f'Indexed {len(all_ids)} chunks total')
    return len(all_ids)

def search(collection, query, top_k=3):
    query_embedding = embed_query(query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=['documents', 'metadatas', 'distances'],
    )
    return results

def display_results(query, results):
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    distances = results['distances'][0]

    print(f'\nQuery: "{query}"')
    print('=' * 60)
    for rank, (doc, meta, dist) in enumerate(zip(docs, metas, distances), 1):
        print(f'\nResult #{rank}')
        print(f' Source: {meta["source"]}')
        print(f' Distance: {dist:.4f} (lower = more relevant)')
        print(f' Text: {doc[:200]}...' if len(doc) > 200 else f' Text: {doc}')
        print('=' * 60)

if __name__ == '__main__':
    print('\n--- Step 1: Creating ChromaDB collection ---')
    collection = create_collection()

    base_dir = os.path.join(os.path.dirname(__file__), '..')
    doc_paths = [
        os.path.join(base_dir, 'day2', 'sample.txt'),
        os.path.join(base_dir, 'day2', 'sample.pdf'),
        os.path.join(base_dir, 'day2', 'sample.docx'),
    ]

    print('\n--- Step 2: Indexing documents ---')
    total = index_documents(collection, doc_paths)
    print(f'Index complete. {total} chunks stored in ChromaDB.')

    print('\n--- Step 3: Running semantic search queries ---')
    queries = [
        'What is NexusChat?',
        'What are the rules about sharing data with AI tools?',
        'How does retrieval augmented generation work?',
        'What is the weather like in Paris?',
    ]

    for query in queries:
        results = search(collection, query, top_k=2)
        display_results(query, results)
