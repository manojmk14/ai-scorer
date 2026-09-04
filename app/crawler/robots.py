from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, Optional
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser

import requests


AI_BOTS = {
    "GPTBot": "OpenAI",
    "ClaudeBot": "Anthropic",
    "Google-Extended": "Google",
    "Googlebot": "Google Search",
    "Google-GeminiNotebook": "Google Gemini Notebook",
    "PerplexityBot": "Perplexity",
    "Amazonbot": "Amazon",
    "Bytespider": "ByteDance",
}


@dataclass
class BotResult:
    user_agent: str
    company: str
    allowed: Optional[bool]
    matched_path: str


@dataclass
class RobotsResult:
    url: str
    found: bool
    status_code: Optional[int]
    content: str
    sitemap_urls: list[str]
    bots: Dict[str, BotResult]
    error: Optional[str] = None


def analyze_robots(
    page_url: str,
    timeout: int = 10,
) -> RobotsResult:

    parsed_url = page_url.rstrip("/") + "/robots.txt"

    try:
        response = requests.get(
            parsed_url,
            headers={
                "User-Agent": (
                    "AIReadinessAuditor/0.1 "
                    "(robots-analysis)"
                )
            },
            timeout=timeout,
        )

        if response.status_code != 200:
            return RobotsResult(
                url=parsed_url,
                found=False,
                status_code=response.status_code,
                content=response.text,
                sitemap_urls=[],
                bots={},
                error=f"robots.txt returned HTTP {response.status_code}",
            )

        content = response.text

        parser = RobotFileParser()
        parser.set_url(parsed_url)
        parser.parse(content.splitlines())

        bots: Dict[str, BotResult] = {}

        for bot, company in AI_BOTS.items():

            try:
                allowed = parser.can_fetch(bot, page_url)
            except Exception:
                allowed = None

            bots[bot] = BotResult(
                user_agent=bot,
                company=company,
                allowed=allowed,
                matched_path=page_url,
            )

        sitemap_urls = extract_sitemaps(content)

        return RobotsResult(
            url=parsed_url,
            found=True,
            status_code=response.status_code,
            content=content,
            sitemap_urls=sitemap_urls,
            bots=bots,
        )

    except requests.RequestException as exc:

        return RobotsResult(
            url=parsed_url,
            found=False,
            status_code=None,
            content="",
            sitemap_urls=[],
            bots={},
            error=str(exc),
        )


def extract_sitemaps(content: str) -> list[str]:

    sitemap_urls = []

    for line in content.splitlines():

        line = line.strip()

        if not line:
            continue

        if line.lower().startswith("sitemap:"):

            value = line.split(":", 1)[1].strip()

            if value:
                sitemap_urls.append(value)

    return sitemap_urls
