# Day 8 Notes — Evaluation Metrics & Week 2 Wrap-Up

## Task 1 — Observation Questions

### Faithfulness scores
- Faithful answer faithfulness: 1.0
- Hallucinated answer faithfulness: 0.5
- The evaluator correctly penalised the hallucinated answer (which added CSV, XLSX, MP3 not found in context).

### Same answer_relevance for both answers
Both answers scored similarly on answer_relevance (1.0) because both directly address the question "What file formats does NexusChat support?" — they are on-topic and responsive. Faithfulness checks if claims are grounded in context; relevance checks if the answer addresses the question. An answer can be relevant (on-topic) but unfaithful (hallucinated facts), which is exactly what happened here.

### Risk of LLM-as-a-Judge
One risk: **self-reinforcing bias** — Gemini may favour its own style of answers or miss subtle hallucinations because it shares the same knowledge base as the generator. Mitigation: use a different model as judge (e.g., judge with GPT-4 if generator is Gemini), include reference ground truths, and use multiple judges with agreement scoring.

## Task 2 — Report Card

| Chatbot Version | Faithfulness | Relevance | Context Recall | Mean |
|---|---|---|---|---|---|
| Week 1 — Dense Only | 0.7500 | 0.8200 | 0.6300 | 0.7333 |
| Week 2 — Hybrid | 0.8400 | 0.8600 | 0.7600 | 0.8200 |
| Week 2 — Advanced | 0.9200 | 0.9400 | 0.8900 | 0.9167 |



## Task 2 — Reflection Questions

1. **Which metric showed the biggest improvement?**
   Context recall improved the most (0.63 → 0.89, +0.26), followed by faithfulness (0.75 → 0.92, +0.17). This tells us hybrid search + re-ranking had the biggest impact on retrieval quality — the system is now finding the right documents more consistently.

2. **If context_recall is high but faithfulness is low?**
   Retrieval found the right documents, but the generator hallucinated. The generation/grounding prompt needs fixing.

3. **If faithfulness is high but context_recall is low?**
   The answer sticks to context but the context missed important information from the ground truth. This happens when the question is simple and the answer happens to be partially in retrieved chunks, but key details were missed. Possibly the generator answered conservatively with what it had.

4. **Would results differ with a stronger judge model?**
   Yes. A stronger model would better detect subtle hallucinations and nuance. Gemini 3 Flash is fast but may miss edge cases. Gemini 3 Pro would give stricter, more accurate scores.

5. **How often to run evaluation in production?**
   Every time a retrieval or generation change is made. Triggered by: new document types, embedding model updates, prompt changes, chunk strategy changes, or before any production deployment.
