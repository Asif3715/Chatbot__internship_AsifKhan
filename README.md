# NexusChat — RAG Chatbot (Week 1 Build)

A Retrieval-Augmented Generation chatbot built from scratch using Google Gemini and ChromaDB. Answers questions from a set of documents with cited sources and supports multi-turn conversation.

## What It Does

- Loads documents in TXT, PDF, and DOCX format
- Splits documents into searchable chunks
- Embeds chunks using Gemini's text-embedding-004 model
- Stores and searches vectors using ChromaDB
- Generates grounded, cited answers using gemini-1.5-flash
- Remembers conversation history and resolves follow-up questions

## How to Run

1. Clone this repo and create a virtual environment
2. pip install -r requirements.txt
3. Copy .env.example to .env and add your GEMINI_API_KEY
4. Run: python day5/memory_chatbot.py
5. Ask questions about the sample documents in day2/

## Project Structure

day2/ - document ingestion and chunking
day3/ - embeddings and vector store
day4/ - generation and the first complete pipeline
day5/ - conversation memory and the polished final version
notes/ - daily learning notes and reflections

## What I Learned This Week

Building a RAG system from scratch taught me how each component — ingestion, chunking, embedding, retrieval, and generation — must work together for reliable answers. The biggest insight was that retrieval quality is the hardest problem: without good chunks, even the best LLM cannot produce correct answers. Adding conversation memory showed me how seemingly simple features like follow-up questions require careful design across both retrieval and generation layers.
