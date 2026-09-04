from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from time import perf_counter

import requests


DEFAULT_USER_AGENT = (
    "AIReadinessAuditor/0.1 "
    "(website-audit-tool; +https://example.com)"
)


@dataclass
class FetchResult:
    requested_url: str
    final_url: Optional[str] = None
    status_code: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    content: str = ""
    content_type: Optional[str] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    redirect_count: int = 0


def fetch_url(
    url: str,
    timeout: int = 15,
    user_agent: str = DEFAULT_USER_AGENT,
) -> FetchResult:

    start = perf_counter()

    headers = {
        "User-Agent": user_agent,
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.8",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True,
        )

        elapsed = (perf_counter() - start) * 1000

        content_type = response.headers.get("Content-Type", "")

        return FetchResult(
            requested_url=url,
            final_url=response.url,
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.text,
            content_type=content_type,
            response_time_ms=round(elapsed, 2),
            redirect_count=len(response.history),
        )

    except requests.RequestException as exc:
        elapsed = (perf_counter() - start) * 1000

        return FetchResult(
            requested_url=url,
            response_time_ms=round(elapsed, 2),
            error=str(exc),
        )
