# SPDX-FileCopyrightText: © 2023 Dominik George <nik@naturalnet.de>
#
# SPDX-License-Identifier: LGPL-3.0-or-later

import os
from typing import Callable, ClassVar

import prometheus_client
from prometheus_client import (
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    Gauge,
    Histogram,
    multiprocess,
)
from starlette.endpoints import HTTPEndpoint
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    ignored_paths: ClassVar[set[str]] = {"/_functional/metrics"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path in self.ignored_paths:
            return await call_next(request)

        pending_gauge = request.state.metrics_registry._names_to_collectors[
            "http_requests_pending"
        ].labels(request.url.netloc, request.method)
        latency_hist = request.state.metrics_registry._names_to_collectors[
            "http_requests_latency_seconds"
        ].labels(request.url.netloc, request.method)

        with pending_gauge.track_inprogress(), latency_hist.time():
            response = await call_next(request)

        return response


class MetricsEndpoint(HTTPEndpoint):
    async def get(self, request: Request) -> PlainTextResponse:
        text = prometheus_client.generate_latest(request.state.metrics_registry)
        return PlainTextResponse(text, media_type=CONTENT_TYPE_LATEST)


def get_metrics_registry(tmp_dir: str):
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = tmp_dir
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    Histogram(
        "http_requests_latency_seconds",
        "Request latency",
        ("domain", "method"),
        registry=registry,
    )
    Gauge(
        "http_requests_pending",
        "Currently pending requests",
        ("domain", "method"),
        registry=registry,
    )

    return registry
