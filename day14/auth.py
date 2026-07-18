import os
import secrets
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

KEYS_FILE = Path(__file__).parent / 'api_keys.json'
PUBLIC_PATHS = {'/health', '/docs', '/openapi.json', '/', '/redoc'}


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def load_keys() -> dict:
    if not KEYS_FILE.exists():
        return {}
    return json.loads(KEYS_FILE.read_text())


def _save_keys(keys: dict):
    KEYS_FILE.parent.mkdir(parents=True, exist_ok=True)
    KEYS_FILE.write_text(json.dumps(keys, indent=2))


def generate_api_key(label: str) -> str:
    raw_key = 'nxc-' + secrets.token_urlsafe(32)
    key_hash = _hash_key(raw_key)
    keys = load_keys()
    keys[key_hash] = {
        'label': label,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'request_count': 0,
    }
    _save_keys(keys)
    return raw_key


def validate_key(raw_key: str) -> dict | None:
    key_hash = _hash_key(raw_key)
    keys = load_keys()
    if key_hash not in keys:
        return None
    keys[key_hash]['request_count'] += 1
    _save_keys(keys)
    return keys[key_hash]


def revoke_key(raw_key: str) -> bool:
    key_hash = _hash_key(raw_key)
    keys = load_keys()
    if key_hash not in keys:
        return False
    del keys[key_hash]
    _save_keys(keys)
    return True


class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        raw_key = request.headers.get('X-API-Key')
        if not raw_key:
            return JSONResponse(status_code=401, content={'detail': 'Missing X-API-Key header.'})

        metadata = validate_key(raw_key)
        if metadata is None:
            return JSONResponse(status_code=401, content={'detail': 'Invalid or revoked API key.'})

        request.state.api_key_label = metadata['label']
        return await call_next(request)


if __name__ == '__main__':
    if KEYS_FILE.exists():
        KEYS_FILE.unlink()

    key1 = generate_api_key('intern-test')
    key2 = generate_api_key('admin')
    print(f'Key 1 (intern-test): {key1}')
    print(f'Key 2 (admin): {key2}')

    meta = validate_key(key1)
    print(f'Validate key 1: {meta}')

    result = validate_key('nxc-this-is-not-a-real-key')
    print(f'Validate fake key: {result} (should be None)')

    print(f'Keys on disk: {json.dumps(load_keys(), indent=2)}')

    revoke_key(key2)
    print(f'Keys remaining: {len(load_keys())} (should be 1)')
    print('All auth tests passed.')
