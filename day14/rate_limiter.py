import time
from collections import defaultdict, deque
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

RATE_LIMIT_REQUESTS = 20
RATE_LIMIT_WINDOW = 60

_request_log: dict[str, deque] = defaultdict(deque)
EXEMPT_PATHS = {'/health', '/docs', '/openapi.json', '/', '/redoc', '/admin/keys'}


def _get_client_id(request: Request) -> str:
    label = getattr(request.state, 'api_key_label', None)
    if label:
        return label
    return request.client.host if request.client else 'unknown'


def is_rate_limited(client_id: str) -> tuple[bool, int]:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW
    log = _request_log[client_id]

    while log and log[0] < cutoff:
        log.popleft()

    if len(log) >= RATE_LIMIT_REQUESTS:
        retry_after = int(log[0] + RATE_LIMIT_WINDOW - now) + 1
        return True, max(retry_after, 1)

    log.append(now)
    return False, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in EXEMPT_PATHS:
            return await call_next(request)

        client_id = _get_client_id(request)
        limited, retry = is_rate_limited(client_id)

        if limited:
            return JSONResponse(
                status_code=429,
                content={
                    'detail': f'Rate limit exceeded — max {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW}s.',
                    'retry_after': retry,
                },
                headers={'Retry-After': str(retry)},
            )

        return await call_next(request)


if __name__ == '__main__':
    CLIENT = 'test-client'
    print(f'Sending 25 requests as client: {CLIENT}')
    print(f'Limit: {RATE_LIMIT_REQUESTS} per {RATE_LIMIT_WINDOW}s\n')

    allowed = blocked = 0
    for i in range(1, 26):
        limited, retry = is_rate_limited(CLIENT)
        if limited:
            blocked += 1
            print(f' Request {i:02d}: BLOCKED (retry in {retry}s)')
        else:
            allowed += 1
            print(f' Request {i:02d}: ALLOWED')

    print(f'\nSummary: {allowed} allowed, {blocked} blocked')
    print(f'Expected: 20 allowed, 5 blocked')
    assert allowed == RATE_LIMIT_REQUESTS
    assert blocked == 25 - RATE_LIMIT_REQUESTS
    print('All rate limiter tests passed.')
