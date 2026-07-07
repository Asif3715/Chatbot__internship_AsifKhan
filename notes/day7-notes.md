# Day 7 — Re-Ranking & Query Decomposition

## Task 1: Cross-Encoder Re-Ranking Observations

**Rerank scores:**
- Weather chunk (unrelated.txt): not in top 3 after re-ranking (scored lowest)
- Best NexusChat description chunk: rerank_score = 7.5527
- Format support chunk: rerank_score = 2.9445
- Unrelated chunk (weather): not in top 3

**Position change:**
- Before re-ranking: the best NexusChat chunk ("NexusChat is an enterprise RAG chatbot...") was at position 4
- After re-ranking: it moved to position 1

**Why cross-encoder on CPU is advantageous:**
No API call means zero latency from network requests, no API costs, no rate limits, and no dependency on external service availability. For a production system re-ranking thousands of queries per hour, running the model locally on CPU keeps per-query cost near zero and response times predictable. The trade-off is model size (22MB) and initial load time, but the inference itself is fast for small candidate sets (10 chunks).

## Task 3: Benchmark — All Three Chatbot Versions

**Test Question:** "What file formats does NexusChat support, what are the pricing plans, and which plan would you recommend for a 50-person team?"

| Metric | Week 1 (Dense) | Week 2 (Hybrid) | Week 2 (Advanced) |
|---|---|---|---|
| Mentions file formats? | Yes | Yes | Yes |
| Mentions pricing? | Yes | Yes | Yes |
| Gives a recommendation? | No | No | Yes |
| Answer completeness (1–5) | 3 | 3 | 5 |

Week 2 Advanced was the only version that gave a complete answer covering all three parts including the recommendation for a 50-person team (Professional plan). Dense and hybrid both returned information about formats and pricing but didn't connect them into a recommendation.

## Reflection Questions

**Cost trade-off of re-ranking + decomposition:**
Re-ranking adds a local CPU inference per query (free, ~50ms for 10 candidates). Decomposition adds 2+ Gemini API calls per complex question (~$0.002 per call). Together they add ~$0.01 and ~500ms per complex question. Skip decomposition when the question is clearly simple (under 8 words, no conjunctions). Skip re-ranking when retrieval quality is already high and latency is the priority.

**Catching a bad decomposition:**
Add a validation step: check that sub-questions contain key nouns from the original question. If a sub-question drops the main subject, reject the decomposition and fall back to the original question. Also add a max-attempts retry with a simpler prompt if Gemini returns fewer than 2 sub-questions for an obviously complex question.

**One sentence per technique describing the problem it solves:**

- **Chunking**: Splits long documents into searchable pieces so retrieval can find relevant passages instead of entire files.
- **Embedding**: Converts text into numerical vectors so semantic similarity between questions and chunks can be computed.
- **Vector search**: Finds chunks whose meaning is closest to the query by comparing embedding vectors.
- **BM25**: Finds chunks containing exact query keywords, compensating for vector search's weakness on specific terms and IDs.
- **Hybrid search**: Combines BM25 and vector search results so every query gets both keyword precision and semantic understanding.
- **RRF (Reciprocal Rank Fusion)**: Merges two ranked result lists with incompatible score scales into one combined ranking based on position agreement.
- **Re-ranking**: Uses a cross-encoder to re-score retrieved candidates by reading each chunk alongside the question, fixing retrieval order so the best chunk is always first.
- **Query decomposition**: Breaks multi-part questions into atomic sub-questions so each piece of information is retrieved independently instead of being lost in one combined embedding.
- **Conversation memory**: Rewrites follow-up questions into standalone form and passes chat history into generation so the chatbot understands references like "it" and "that."
- **Grounded generation**: Instructs the LLM to answer only from retrieved context and cite sources, preventing hallucination on topics not covered by the documents.
