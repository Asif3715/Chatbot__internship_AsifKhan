# Day 2 Notes

## Observations

- PDF raw text: may include extra newlines and spacing; some line breaks merge into spaces.
- DOCX blank paragraphs skipped to avoid creating empty chunks that waste space and add noise.
- To handle HTML pages use `beautifulsoup4` (bs4).

## Chunking Comparison (example values)

- Fixed-Size: Chunks Produced: 3, Avg Length: 300, Reads Naturally: Partially
- Sentence: Chunks Produced: 3, Avg Length: 130, Reads Naturally: Yes
- Recursive: Chunks Produced: 4, Avg Length: 220, Reads Naturally: Yes

## Experiments (notes)

- Fixed overlap=0: first and second chunk share nothing; boundary facts can be lost.
- sentences_per_chunk=1: more chunks, often too short to be useful.
- recursive size=100: chunk count goes up because target size smaller.

## Reflections

- Cutting a sentence in half hurts retrieval because semantic meaning is split.
- For "What formats does NexusChat support?" the best retriever hit is the chunk that lists formats (sentence or recursive strategies).
- Overlap exists to preserve context across boundaries; with zero overlap, facts at boundaries may be missed.

## Pipeline trace for a DOCX question

1. `load_document('sample.docx')` reads text.
2. `chunk_recursive(...)` splits into chunks.
3. Chunks are embedded and stored in the vector DB.
4. Retriever finds top chunks for a query.
5. LLM (Gemini) receives retrieved chunks and generates the answer.
