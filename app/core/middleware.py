import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger('app.request')


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.request_id = str(uuid.uuid4())
        started = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - started) * 1000
        response.headers['X-Request-ID'] = request.state.request_id
        response.headers['X-Process-Time-MS'] = f'{elapsed_ms:.2f}'
        logger.info(
            'request_completed',
            extra={
                'request_id': request.state.request_id,
                'action': f'{request.method} {request.url.path}',
                'status': response.status_code,
            },
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response
