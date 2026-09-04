from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class AuditReport:

    url: str
    final_url: str | None
    audit_date: str

    overall_score: int
    overall_label: str

    scores: dict[str, Any]

    crawlability: dict[str, Any]
    understandability: dict[str, Any]
    citation_readiness: dict[str, Any]
    technical: dict[str, Any]

    page: dict[str, Any]
    robots: dict[str, Any]
    sitemap: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:

        return asdict(self)


def utc_now_iso() -> str:

    return datetime.now(
        timezone.utc
    ).isoformat()
