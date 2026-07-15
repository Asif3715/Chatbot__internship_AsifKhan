# Day 13 Notes — Streaming Responses

## Latency Benchmark Results

Run `python day13/latency_benchmark.py` with the API running and paste results here:

```
(paste benchmark output here)
```

- **Non-streaming avg (user waits):** __s
- **Streaming TTFT avg (first word):** __s
- **Perceived speed improvement:** __s faster to first content

## Reflection Questions

### 1. Measured TTFT vs Non-Streaming Total Time

(paste your benchmark numbers here after running the script)

### 2. Making Retrieval Feel Faster

The retrieval phase (hybrid search + re-ranking) runs synchronously before the first token appears. To make this feel faster, I would show the user a "Searching documents..." status message or a skeleton loading animation while retrieval is running. This gives immediate visual feedback that something is happening. Additionally, I could stream the retrieval progress — for example, emit an SSE event like `{"status": "retrieving"}` right away, then `{"status": "reranking"}` after dense+BM25 search completes, and finally start streaming tokens. This breaks the perceived wait into smaller, labeled stages.

### 3. Mid-Stream Browser Closure

If the user closes the browser tab mid-stream, the `generate_and_save()` closure never reaches the `done` event, so `save_turn()` is never called. The answer is lost — it was streamed to the browser but never persisted to SQLite. This is acceptable for a chatbot because the user chose to leave, but in a production system I would save a partial turn with whatever tokens were generated before the disconnect. I could detect the disconnect by catching a `GeneratorExit` exception in the generator, and save the partial answer at that point.

### 4. Keeping Both /chat and /chat/stream

I would keep both endpoints. The `/chat` endpoint is simpler to call from server-side scripts, CI tests, and integrations that don't need streaming (like the latency benchmark's non-streaming measurement, or the Day 12 CI tests). Removing it would break existing callers and force every consumer to parse SSE. The `/chat/stream` endpoint is for the browser UI where perceived latency matters. Having both costs almost nothing to maintain since the retrieval logic is shared, and it gives API consumers the choice.
