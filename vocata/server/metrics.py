import os
from time import time
from typing import Callable

import prometheus_client
from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    multiprocess,
)
from starlette.endpoints import HTTPEndpoint
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request.state._time_start = time()
        response = await call_next(request)
        request.state._time_end = time()

        request.state.metrics_registry._names_to_collectors["request_latency_seconds"].labels(
            request.url.netloc, request.method, response.status_code
        ).observe(request.state._time_end - request.state._time_start)
        request.state.metrics_registry._names_to_collectors["request_count"].labels(
            request.url.netloc, request.method, response.status_code
        ).inc()

        return response


class MetricsEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> PlainTextResponse:
        text = prometheus_client.generate_latest(request.state.metrics_registry)
        return PlainTextResponse(text, media_type=CONTENT_TYPE_LATEST)


def get_metrics_registry(tmp_dir: str):
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = tmp_dir
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    Counter("request_count", "Request count", ("domain", "method", "status"), registry=registry)
    Histogram(
        "request_latency_seconds",
        "Request latency",
        ("domain", "method", "status"),
        registry=registry,
    )

    return registry
