Embedding: A numeric representation of text that preserves semantic similarity.
Vector Store: A database that stores embeddings for efficient similarity search.
Chunking: Splitting large documents into smaller pieces for retrieval.
Context Window: The token limit the LLM can attend to when generating.
Hallucination: When a model invents facts not supported by context.

10. You cannot paste entire large documents because of token limits and irrelevance; chunking lets retrieval supply only relevant pieces.
11. If retrieval returns wrong chunks the model will produce incorrect or hallucinated answers because it was grounded in irrelevant context.
