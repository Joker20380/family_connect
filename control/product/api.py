"""Separate enrollment API factory. No admin mutation routes or VPN operations."""
import json
import os
import sqlite3

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .store import EnrollmentRejected, ProductStore

MAX_BODY = 8192


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate field')
        result[key] = value
    return result


async def _body(request):
    if request.headers.get('content-type', '').split(';')[0].strip() != 'application/json':
        raise ValueError('invalid content type')
    raw = bytearray()
    async for chunk in request.stream():
        if len(raw) + len(chunk) > MAX_BODY:
            raise ValueError('request too large')
        raw.extend(chunk)
    value = json.loads(raw, object_pairs_hook=_unique)
    if type(value) is not dict:
        raise ValueError('invalid body')
    return value


def create_app(store):
    app = FastAPI(title='Family Connect product enrollment', docs_url=None,
                  redoc_url=None, openapi_url=None)

    @app.middleware('http')
    async def no_store(request, call_next):
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(EnrollmentRejected)
    async def rejected(request, error):
        return JSONResponse({'code': 'REGISTRATION_REJECTED'}, status_code=403)

    @app.exception_handler(sqlite3.Error)
    async def unavailable(request, error):
        return JSONResponse({'code': 'REGISTRATION_UNAVAILABLE'}, status_code=503)

    async def parse(request, fields=None):
        try:
            value = await _body(request)
            if fields is not None and set(value) != fields:
                raise ValueError('invalid fields')
            return value
        except (ValueError, TypeError, UnicodeError, RecursionError):
            return None

    @app.post('/v2/registration/challenge')
    async def challenge(request: Request):
        value = await parse(request, {'invitation_token', 'public_identity', 'wireguard_public_key'})
        if value is None:
            return JSONResponse({'code': 'INVALID_REQUEST'}, status_code=400)
        return await run_in_threadpool(store.challenge, **value)

    @app.post('/v2/registration/complete')
    async def complete(request: Request):
        proof = await parse(request)
        if proof is None:
            return JSONResponse({'code': 'INVALID_REQUEST'}, status_code=400)
        return await run_in_threadpool(store.enroll, proof)

    return app


def app_from_env():
    # Installation must initialize the database explicitly. No implicit accounts,
    # entitlement grants, trust-on-first-use or writable legacy catalog mounts.
    store = ProductStore(os.environ['FC_PRODUCT_DB'])
    store.check_ready()
    return create_app(store)
