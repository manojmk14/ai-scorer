from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class TechnicalAnalysis:
    https: bool
    status_code: int | None
    response_time_ms: float | None

    content_type: str | None

    x_robots_tag: str | None
    noindex_detected: bool

    redirect_count: int

    final_url: str | None

    canonical_matches_final_url: bool | None


def analyze_technical(
    requested_url: str,
    final_url: str | None,
    status_code: int | None,
    headers: dict[str, str],
    response_time_ms: float | None,
    redirect_count: int,
    canonical: str | None,
) -> TechnicalAnalysis:

    https = requested_url.lower().startswith("https://")

    x_robots_tag = None

    for key, value in headers.items():

        if key.lower() == "x-robots-tag":
            x_robots_tag = value
            break

    noindex_detected = False

    if x_robots_tag:

        directives = x_robots_tag.lower()

        noindex_detected = (
            "noindex" in directives
        )

    canonical_matches = None

    if canonical and final_url:

        canonical_normalized = canonical.rstrip("/")
        final_normalized = final_url.rstrip("/")

        canonical_matches = (
            canonical_normalized
            == final_normalized
        )

    return TechnicalAnalysis(
        https=https,
        status_code=status_code,
        response_time_ms=response_time_ms,

        content_type=headers.get(
            "Content-Type"
        ),

        x_robots_tag=x_robots_tag,
        noindex_detected=noindex_detected,

        redirect_count=redirect_count,

        final_url=final_url,

        canonical_matches_final_url=canonical_matches,
    )
