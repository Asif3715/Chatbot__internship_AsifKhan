# Day 6 — Hybrid Search & Reciprocal Rank Fusion

## BM25 vs Dense Search Comparison

| Query | BM25 Top Source | Dense Top Source | Better Method? |
|---|---|---|---|
| What is NexusChat? | sample2.txt | sample.pdf | Dense — BM25 matched wrong doc (pricing) because "NexusChat" keyword appears there too |
| Professional plan 200 USD | sample2.txt | sample2.txt | Tie — both correctly find pricing doc |
| confidential data AI services policy | sample.docx | sample.docx | Tie — both correctly find policy doc |

## Observation Questions (Task 1)

**For query 2 ('Professional plan 200 USD'), which method found the pricing document first? Why?**

Both methods found sample2.txt, but BM25 gives it a higher relative confidence because the query terms "Professional plan 200 USD" are exact keywords that appear verbatim in the document. BM25's term-frequency scoring naturally boosts chunks where these specific terms appear multiple times.

**For query 1 ('What is NexusChat?'), which method performed better? Is that what you expected?**

Dense performed better — it correctly returned sample.pdf (the NexusChat overview). BM25 returned sample2.txt (the pricing doc) because the word "NexusChat" appears there too, even though that doc doesn't describe what NexusChat is. This is a clear example of BM25's weakness: it matches keywords without understanding meaning.

**What would happen to BM25 if a user typed 'What does the product do?' instead of 'What is NexusChat?' — would it still find the right chunk?**

BM25 would likely struggle because none of the query words ("product", "do") appear in the NexusChat overview chunk verbatim. The word "NexusChat" itself would match, but the surrounding terms add noise. Dense search would handle this easily since the embedding captures semantic meaning.

## Side-by-Side Benchmark (Task 3)

**Question: 'Professional plan 200 USD'**

| Metric | Week 1 (Dense Only) | Week 2 (Hybrid) |
|---|---|---|
| Top source returned | sample2.txt | sample2.txt |
| Does it find sample2.txt? | Yes | Yes |
| Answer quality (1–5) | 4 | 5 |

## Reflection Questions (Task 3)

**For the keyword-heavy query, did hybrid outperform dense-only?**

Hybrid retrieved the same top source (sample2.txt) but with higher confidence because BM25 confirmed the keyword match and RRF boosted the combined rank. The answer quality improved because the chunk was ranked more reliably.

**What would happen if you set k=1 instead of k=60?**

With k=1, top-ranked results get much more weight: 1/(1+1)=0.5 for rank 1 vs 1/(1+3)=0.25 for rank 3. This makes the fusion heavily biased toward whoever ranked a chunk first, reducing the benefit of consensus between the two methods. With k=60, the scores are more evenly distributed (1/61 vs 1/63), giving more weight to chunks that appear in both lists.

**Engineering changes for scale (100,000 chunks):**

1. Pre-compute BM25 index once and store it on disk instead of rebuilding on every run
2. Use approximate nearest neighbour (ANN) indexes for dense search instead of brute-force
3. Cache frequent query results
4. Run BM25 and dense search in parallel threads
5. Use a two-stage approach: run BM25 first (cheaper), then only run dense search if BM25 confidence is below a threshold

**When would you choose each method?**

- **Dense-only**: When the corpus is highly semantic and users ask conceptual questions (e.g., "Explain how RAG works")
- **BM25-only**: When queries are known to be keyword-heavy with specific terms, IDs, or codes (e.g., "Find SKU-7842" or "Section 4.2.1")
- **Hybrid**: In production for general-purpose Q&A where query types vary — it gets the best of both with minimal added complexity
