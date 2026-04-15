"""Prometheus metrics for the operator dashboard."""

from __future__ import annotations

from datetime import datetime

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

HTTP_REQUESTS_TOTAL = Counter(
    "ai_doc_assistant_http_requests_total",
    "HTTP requests handled by the API",
    ("method", "route", "status_code"),
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "ai_doc_assistant_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ("method", "route"),
)
AUTH_LOGIN_TOTAL = Counter(
    "ai_doc_assistant_auth_logins_total",
    "Authentication attempts recorded by outcome",
    ("outcome", "auth_method"),
)
DOCUMENT_OPERATION_TOTAL = Counter(
    "ai_doc_assistant_document_operations_total",
    "Document lifecycle operations recorded by outcome",
    ("operation", "outcome"),
)
QUERY_DECISION_TOTAL = Counter(
    "ai_doc_assistant_query_decisions_total",
    "Query decisions recorded by outcome",
    ("outcome",),
)
BUILD_INFO = Gauge(
    "ai_doc_assistant_build_info",
    "Application build metadata",
    ("app_name", "version"),
)
STARTED_AT_SECONDS = Gauge(
    "ai_doc_assistant_started_at_seconds",
    "Application start time as a Unix timestamp",
)
UPTIME_SECONDS = Gauge(
    "ai_doc_assistant_uptime_seconds",
    "Application uptime in seconds",
)
RUNTIME_DOCUMENTS_TOTAL = Gauge(
    "ai_doc_assistant_runtime_documents_total",
    "Total documents tracked by the runtime",
)
RUNTIME_DOCUMENTS_READY = Gauge(
    "ai_doc_assistant_runtime_documents_ready",
    "Documents that reached a completed or warning state",
)
RUNTIME_INDEXED_DOCUMENTS = Gauge(
    "ai_doc_assistant_runtime_indexed_documents",
    "Documents indexed into the vector store",
)
RUNTIME_CHUNKS_TOTAL = Gauge(
    "ai_doc_assistant_runtime_chunks_total",
    "Document chunks persisted locally",
)
RUNTIME_AUDIT_EVENTS_TOTAL = Gauge(
    "ai_doc_assistant_runtime_audit_events_total",
    "Audit events stored locally",
)
RUNTIME_BLOCKED_QUERIES_TOTAL = Gauge(
    "ai_doc_assistant_runtime_blocked_queries_total",
    "Blocked query attempts recorded locally",
)
RUNTIME_FAILED_LOGINS_TOTAL = Gauge(
    "ai_doc_assistant_runtime_failed_logins_total",
    "Failed logins recorded locally",
)


def initialize_metrics(app_name: str, version: str, started_at: datetime) -> None:
    """Seed static runtime gauges."""
    BUILD_INFO.labels(app_name=app_name, version=version).set(1)
    STARTED_AT_SECONDS.set(started_at.timestamp())


def record_http_request(method: str, route: str, status_code: int, duration_seconds: float) -> None:
    """Record one handled HTTP request."""
    HTTP_REQUESTS_TOTAL.labels(method=method, route=route, status_code=str(status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=method, route=route).observe(duration_seconds)


def record_auth_login(*, outcome: str, auth_method: str) -> None:
    """Record an authentication attempt."""
    AUTH_LOGIN_TOTAL.labels(outcome=outcome, auth_method=auth_method).inc()


def record_document_operation(*, operation: str, outcome: str) -> None:
    """Record a document lifecycle action."""
    DOCUMENT_OPERATION_TOTAL.labels(operation=operation, outcome=outcome).inc()


def record_query_decision(*, outcome: str) -> None:
    """Record a query outcome."""
    QUERY_DECISION_TOTAL.labels(outcome=outcome).inc()


def update_runtime_gauges(
    *,
    uptime_seconds: int,
    documents_total: int,
    documents_ready: int,
    indexed_documents: int,
    chunks_total: int,
    audit_events_total: int,
    blocked_queries_total: int,
    failed_logins_total: int,
) -> None:
    """Expose the latest runtime snapshot through Prometheus gauges."""
    UPTIME_SECONDS.set(uptime_seconds)
    RUNTIME_DOCUMENTS_TOTAL.set(documents_total)
    RUNTIME_DOCUMENTS_READY.set(documents_ready)
    RUNTIME_INDEXED_DOCUMENTS.set(indexed_documents)
    RUNTIME_CHUNKS_TOTAL.set(chunks_total)
    RUNTIME_AUDIT_EVENTS_TOTAL.set(audit_events_total)
    RUNTIME_BLOCKED_QUERIES_TOTAL.set(blocked_queries_total)
    RUNTIME_FAILED_LOGINS_TOTAL.set(failed_logins_total)


def render_metrics() -> str:
    """Render the current Prometheus payload."""
    return generate_latest().decode("utf-8")


def metrics_content_type() -> str:
    """Return the Prometheus content type."""
    return CONTENT_TYPE_LATEST
