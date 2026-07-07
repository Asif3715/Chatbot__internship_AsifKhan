# Day 5 — Conversation Memory & Week 1 Wrap-Up

## Observation Questions

### Exact rewritten question for Turn 2

"What formats does NexusChat support?"

The system correctly resolved 'it' to 'NexusChat' by using the conversation history from Turn 1.

### What would happen without query rewriting on Turn 2?

If we skipped query rewriting and searched for "What formats does it support?" directly, the embedding would not reliably find NexusChat-related chunks. The word 'it' carries no semantic signal — the vector would be close to generic "formats" content rather than NexusChat-specific content. Retrieval quality would drop significantly, and the answer might be incorrect or cite irrelevant documents.

### Why rewrite for retrieval but pass the original question to generate_with_memory()?

The rewritten question is optimized for vector search — it contains concrete nouns that match the document embeddings. But Gemini (the generation model) benefits from seeing the original question alongside the conversation history, because it can use the conversational context to produce a natural, coherent answer. The original question ("What formats does it support?") reads naturally to the LLM when preceded by the chat history, while the rewritten version ("What formats does NexusChat support?") would make the conversation feel stilted and robotic.
