import httpx
import time
import json

BASE = 'http://localhost:8000'
QUESTION = 'What is NexusChat and what file formats does it support?'
RUNS = 3

print(f'Benchmarking with question: {QUESTION}')
print(f'Runs per method: {RUNS}\n')

non_stream_times = []
for i in range(RUNS):
    start = time.time()
    r = httpx.post(f'{BASE}/chat', json={'question': QUESTION}, timeout=60)
    elapsed = time.time() - start
    non_stream_times.append(elapsed)
    print(f'Non-streaming run {i+1}: {elapsed:.2f}s (full response)')

ttft_times = []
total_stream_times = []

for i in range(RUNS):
    start = time.time()
    first_token = None
    with httpx.stream('POST', f'{BASE}/chat/stream', json={'question': QUESTION}, timeout=60) as r:
        for line in r.iter_lines():
            if line.startswith('data: '):
                try:
                    event = json.loads(line[6:])
                    if 'token' in event and first_token is None:
                        first_token = time.time() - start
                    if event.get('done'):
                        break
                except Exception:
                    pass
    total = time.time() - start
    ttft_times.append(first_token or total)
    total_stream_times.append(total)
    print(f'Streaming run {i+1}: TTFT={first_token:.2f}s | total={total:.2f}s')

print(f'\n=== RESULTS ===')
print(f'Non-streaming avg (user waits): {sum(non_stream_times)/RUNS:.2f}s')
print(f'Streaming TTFT avg (first word): {sum(ttft_times)/RUNS:.2f}s')
improvement = ((sum(non_stream_times)/RUNS) - (sum(ttft_times)/RUNS))
print(f'Perceived speed improvement: {improvement:.2f}s faster to first content')
