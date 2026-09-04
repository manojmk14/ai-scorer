from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urljoin
import re

import requests


@dataclass
class SitemapResult:
    found: bool
    url: str | None
    status_code: int | None
    is_xml: bool
    error: str | None = None


def analyze_sitemap(
    page_url: str,
    robots_sitemaps: list[str] | None = None,
    timeout: int = 10,
) -> SitemapResult:

    robots_sitemaps = robots_sitemaps or []

    candidates = list(robots_sitemaps)

    base = page_url.rstrip("/") + "/"

    candidates.extend([
        urljoin(base, "sitemap.xml"),
        urljoin(base, "sitemap_index.xml"),
    ])

    seen = set()

    for sitemap_url in candidates:

        if sitemap_url in seen:
            continue

        seen.add(sitemap_url)

        try:
            response = requests.get(
                sitemap_url,
                headers={
                    "User-Agent": (
                        "AIReadinessAuditor/0.1 "
                        "(sitemap-analysis)"
                    )
                },
                timeout=timeout,
            )

            content_type = response.headers.get(
                "Content-Type",
                "",
            ).lower()

            body_start = response.text[:500].lower()

            looks_like_xml = (
                "xml" in content_type
                or "<urlset" in body_start
                or "<sitemapindex" in body_start
            )

            if response.status_code == 200 and looks_like_xml:

                return SitemapResult(
                    found=True,
                    url=sitemap_url,
                    status_code=response.status_code,
                    is_xml=True,
                )

        except requests.RequestException:
            continue

    return SitemapResult(
        found=False,
        url=None,
        status_code=None,
        is_xml=False,
        error="No accessible XML sitemap detected.",
    )
