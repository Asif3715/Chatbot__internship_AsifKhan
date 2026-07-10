import httpx
import json

BASE = 'http://localhost:8000'

print('=== Testing NexusChat RAG API ===')

r = httpx.get(f'{BASE}/health')
print(f'\n[1] Health: {r.status_code}')
print(json.dumps(r.json(), indent=2))

r = httpx.post(f'{BASE}/chat', json={'question': 'What is NexusChat?'}, timeout=60)
data = r.json()
print(f'\n[2] Chat: {r.status_code}')
print(f'Answer: {data["answer"][:200]}')
print(f'Sources: {[s["source"] for s in data["sources"]]}')
session_id = data['session_id']
print(f'Session ID: {session_id}')

r = httpx.post(f'{BASE}/chat', json={'question': 'What formats does it support?', 'session_id': session_id}, timeout=60)
data = r.json()
print(f'\n[3] Follow-up chat: {r.status_code}')
print(f'Answer: {data["answer"][:200]}')

new_doc = {
    'filename': 'team_handbook.txt',
    'content': 'NexusChat Team Handbook. All engineers must write unit tests for every new feature. Code reviews are mandatory before merging to main. Weekly syncs happen every Monday at 10 AM. Deadline: ship the production API by end of Week 4.',
}
r = httpx.post(f'{BASE}/ingest', json=new_doc, timeout=60)
print(f'\n[4] Ingest: {r.status_code}')
print(json.dumps(r.json(), indent=2))

r = httpx.post(f'{BASE}/chat', json={'question': 'What are the code review requirements?'}, timeout=60)
data = r.json()
print(f'\n[5] Query new doc: {r.status_code}')
print(f'Answer: {data["answer"][:200]}')
print(f'Sources: {[s["source"] for s in data["sources"]]}')

r = httpx.post(f'{BASE}/chat', json={'question': 'What is the capital of France?'}, timeout=60)
print(f'\n[6] Off-topic: {r.status_code}')
if r.status_code == 200:
    print(f'Answer: {r.json()["answer"][:200]}')
else:
    print(f'Error: {r.json()}')

print('\n=== All tests complete ===')
