# Day 4 -- Generation & Complete RAG Pipeline

## Observation Questions (Task 1)

**Q2's output: Did Gemini follow the "I could not find it" instruction, or did it hallucinate?**

Exact response from Gemini: "I could not find that information in the provided documents."

Gemini correctly refused to answer. The grounding instruction in the prompt worked as intended.

**Q1's SOURCES section: Does it correctly name sample.pdf? What would go wrong if you forgot the source label?**

Yes, the answer cites sample.pdf. Without source labels in the prompt, the model has no way to reference documents -- answers would be unverifiable claims with no citation trail.

**Why test generation with fake chunks before connecting ChromaDB?**

It isolates the generation logic from retrieval bugs. If a test failure occurs, you know it is either a prompt issue or a Gemini API issue -- not a missing vector or wrong embedding. This catches prompt formatting errors, API key issues, and grounding instruction weaknesses early.

## Experiments (Task 3)

### Experiment A -- Remove Grounding Instruction

Result when rules 1 and 2 were removed from the prompt and Q4 ("What is the refund policy?") was asked:

Gemini hallucinated a plausible-sounding refund policy: "I could not find a specific refund policy for NexusChat in the provided documents. However, based on general knowledge, most SaaS platforms offer refunds..." -- it started blending general knowledge.

After restoring the instruction, it correctly refused.

### Experiment B -- Change top_k

- top_k=1: Answer was too short, missed supporting details from other chunks.
- top_k=3: Good balance -- enough context for a complete answer without redundancy.
- top_k=6: Answer became repetitive with overlapping chunk content.

Best top_k value: 3. "Best" means the answer covers all relevant information from the docs without repetition or noise.

### Experiment C -- Add sample2.txt

The chatbot correctly answered "What does the Professional plan cost?" with "$200 USD per month" and cited sample2.txt as the source. This shows that expanding the knowledge base is as simple as adding a new file -- the entire pipeline re-indexes and the new information is immediately available.

## Reflection Questions

**What is one thing this chatbot still cannot do that a real production chatbot would need?**

Multi-turn conversation memory. Currently each question is treated independently -- it cannot remember previous questions or maintain context across a conversation. A production system needs conversation history tracking, session management, follow-up question handling, and the ability to distinguish new questions from clarifications.

**Which layer is the hardest to get right in production, and why?**

Retrieval quality is the hardest. Generation is relatively straightforward (prompt engineering + LLM call), but retrieval requires tuning chunk size, overlap, top_k, embedding model choice, and distance thresholds -- and these all interact differently depending on the document corpus. A change that improves one query type can break another. Production retrieval also needs hybrid search (keyword + semantic), reranking, and query expansion, which add significant complexity.
