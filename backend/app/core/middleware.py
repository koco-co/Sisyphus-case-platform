import logging
import time

from fastapi import Request
from fastapi.responses import Response
from starlette.middleware.base import RequestResponseEndpoint

logger = logging.getLogger(__name__)


async def request_logging_middleware(request: Request, call_next: RequestResponseEndpoint) -> Response:
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    logger.info(
        "%s %s %s %.3fs",
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response
