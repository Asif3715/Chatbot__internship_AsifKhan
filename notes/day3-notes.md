# Day 3 — Embeddings & Vector Store

## Observation Questions (Task 1)

**What is the dimension count of the Gemini embedding vector? What does each number represent?**
3072 dimensions (the available model `gemini-embedding-2` produces 3072-D vectors; the task sheet's `text-embedding-004` would produce 768). Each number represents the magnitude of the text's meaning along one latent semantic axis learned by the model during training.

**Look at your cosine similarity scores. Did any result surprise you? Which two texts are more similar than you expected?**
"The cat sat on the mat" vs "A feline rested on a rug" scored ~0.87 despite zero word overlap — surprising that the model captures synonymy so well.

**Why do we use task_type='RETRIEVAL_QUERY' for the user's question instead of 'RETRIEVAL_DOCUMENT'?**
Gemini optimizes embeddings differently for queries vs documents. Using the correct task type improves retrieval accuracy by aligning the vector space for matching.

**If two chunks have a cosine similarity of 0.95, what does that tell you about their content?**
They are nearly identical in meaning — likely paraphrases of the same information.

## Experiments (Task 2)

**A — top_k=5 with off-topic query:** Off-topic results still return chunks with low relevance. Retrieving more results increases noise — you need a distance threshold to filter.

**B — Paraphrased query "Tell me about NexusChat":** System correctly finds the NexusChat chunk even though the exact phrase wasn't in any document.

**C — Distance threshold guess:** ~0.5-0.6 seems like a reasonable cutoff. On-topic queries score ~0.2-0.4, off-topic scores >0.7.

## Reflection Questions (Task 2)

**What happens when you query outside document scope?** Distance scores jump (>0.7), returned chunks are semantically unrelated — demonstrates the importance of having good documents covering the domain.

**Why use the same model for indexing and querying?** Different models produce incompatible vector spaces. Embedding with one model and querying with another would give meaningless similarity scores.

**How to make ChromaDB persist?** Use `chromadb.PersistentClient(path='./chroma_db')` instead of `chromadb.Client()` — data saves to disk.

**What's the only missing piece?** The generation step — feeding retrieved chunks + question to Gemini for a grounded answer (Day 4).

## Pipeline Diagram (Task 3)

```
RAW FILE (.txt / .pdf / .docx)
|
v
[Day 2 Task 1] load_document() --> raw text string
|
v
[Day 2 Task 2] chunk_recursive() --> list of chunk strings
|
v
[Day 3 Task 1] embed_text() --> list of 768-dim vectors
|
v
[Day 3 Task 2] collection.add() --> stored in ChromaDB
|
(Index phase complete)
|
USER QUESTION --> embed_query() --> query vector
|
v
collection.query() --> top-K most similar chunks
|
v
[Day 4] Feed chunks + question to Gemini --> Final Answer
```
