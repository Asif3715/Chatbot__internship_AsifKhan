import httpx
import time

BASE = 'http://localhost:8000'
VALID_KEY = input('Paste your valid API key: ').strip()

passed = 0
failed = 0


def check(label, condition, detail=''):
    global passed, failed
    if condition:
        passed += 1
        print(f'  PASS  {label}')
    else:
        failed += 1
        print(f'  FAIL  {label} {detail}')


print('\n=== NexusChat Security Test Suite ===\n')

print('[Authentication]')
r = httpx.post(f'{BASE}/chat', json={'question': 'hi'})
check('No key -> 401', r.status_code == 401)
check('No key error message correct', 'Missing X-API-Key' in r.json().get('detail', ''))

r = httpx.post(f'{BASE}/chat', json={'question': 'hi'}, headers={'X-API-Key': 'nxc-totally-wrong-key'})
check('Wrong key -> 401', r.status_code == 401)
check('Wrong key error message correct', 'Invalid' in r.json().get('detail', ''))

r = httpx.post(f'{BASE}/chat', json={'question': 'What is NexusChat?'}, headers={'X-API-Key': VALID_KEY}, timeout=60)
check('Valid key -> 200', r.status_code == 200)
check('Valid key response has answer', 'answer' in r.json())

r = httpx.get(f'{BASE}/health')
check('/health public (no key) -> 200', r.status_code == 200)

print('\n[Rate Limiting]')
print('  Sending 22 rapid requests...')
statuses = []
for _ in range(22):
    r = httpx.post(f'{BASE}/chat', json={'question': 'rate-limit-test'}, headers={'X-API-Key': VALID_KEY}, timeout=10)
    statuses.append(r.status_code)

count_429 = statuses.count(429)
count_200 = statuses.count(200)
check(f'20 requests allowed (got {count_200})', count_200 >= 20)
check(f'Excess requests blocked 429 (got {count_429})', count_429 >= 2)

if 429 in statuses:
    r = httpx.post(f'{BASE}/chat', json={'question': 'ping'}, headers={'X-API-Key': VALID_KEY}, timeout=5)
    if r.status_code == 429:
        check('Retry-After header present', 'retry-after' in r.headers or 'Retry-After' in r.headers)
        check('retry_after in body', 'retry_after' in r.json())

print(f'\n=== Results: {passed} passed, {failed} failed ===')
