import httpx

BASE = 'http://localhost:8000'

r = httpx.get(f'{BASE}/health')
print(f'Health: {r.status_code} -> {r.json()}')

r = httpx.post(f'{BASE}/echo', json={'message': 'NexusChat', 'repeat': 3})
print(f'Echo: {r.status_code} -> {r.json()}')

r = httpx.post(f'{BASE}/calculate', json={'a': 22, 'b': 7, 'operation': 'divide'})
print(f'Calculate: {r.status_code} -> {r.json()}')

r = httpx.post(f'{BASE}/calculate', json={'a': 1, 'b': 2, 'operation': 'power'})
print(f'Bad operation: {r.status_code} -> {r.json()}')

r = httpx.post(f'{BASE}/echo', json={'repeat': 2})
print(f'Missing field: {r.status_code}')
