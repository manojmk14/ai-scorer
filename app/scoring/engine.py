from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class ScoreResult:
    score: int
    max_score: int
    findings: list[dict[str, Any]]


def finding(
    title: str,
    status: str,
    points: int,
    max_points: int,
    message: str,
) -> dict:

    return {
        "title": title,
        "status": status,
        "points": points,
        "max_points": max_points,
        "message": message,
    }


def score_crawlability(
    technical,
    robots,
    sitemap,
) -> ScoreResult:

    findings = []
    score = 0
    max_score = 30

    # HTTP
    if technical.status_code == 200:

        score += 8

        findings.append(
            finding(
                "HTTP accessibility",
                "pass",
                8,
                8,
                "Page returned HTTP 200.",
            )
        )

    elif technical.status_code in {301, 302, 307, 308}:

        score += 5

        findings.append(
            finding(
                "HTTP accessibility",
                "warning",
                5,
                8,
                f"Page returned HTTP {technical.status_code}.",
            )
        )

    else:

        findings.append(
            finding(
                "HTTP accessibility",
                "fail",
                0,
                8,
                f"Page returned HTTP {technical.status_code}.",
            )
        )

    # robots.txt
    if robots.found:

        score += 5

        findings.append(
            finding(
                "robots.txt",
                "pass",
                5,
                5,
                "robots.txt is accessible.",
            )
        )

    else:

        findings.append(
            finding(
                "robots.txt",
                "warning",
                0,
                5,
                "robots.txt could not be successfully read.",
            )
        )

    # Bot access
    bot_score = 0

    if robots.found:

        bots = robots.bots

        important_bots = [
            "GPTBot",
            "ClaudeBot",
            "Google-Extended",
            "PerplexityBot",
        ]

        for bot in important_bots:

            result = bots.get(bot)

            if result and result.allowed:
                bot_score += 1

        score += bot_score

        findings.append(
            finding(
                "AI crawler access",
                "pass" if bot_score >= 3 else "warning",
                bot_score,
                4,
                (
                    f"{bot_score}/4 selected AI crawler/product "
                    "tokens can access the submitted URL."
                ),
            )
        )

    # Sitemap
    if sitemap.found:

        score += 5

        findings.append(
            finding(
                "XML sitemap",
                "pass",
                5,
                5,
                f"Sitemap detected at {sitemap.url}.",
            )
        )

    else:

        findings.append(
            finding(
                "XML sitemap",
                "warning",
                0,
                5,
                "No accessible XML sitemap detected.",
            )
        )

    # HTTPS
    if technical.https:

        score += 3

        findings.append(
            finding(
                "HTTPS",
                "pass",
                3,
                3,
                "Page is served over HTTPS.",
            )
        )

    else:

        findings.append(
            finding(
                "HTTPS",
                "fail",
                0,
                3,
                "Page is not using HTTPS.",
            )
        )

    return ScoreResult(
        score=min(score, max_score),
        max_score=max_score,
        findings=findings,
    )


def score_understandability(
    html,
) -> ScoreResult:

    findings = []
    score = 0
    max_score = 25

    # Title
    if html.title:

        score += 3

        findings.append(
            finding(
                "Page title",
                "pass",
                3,
                3,
                "Page has a title.",
            )
        )

    else:

        findings.append(
            finding(
                "Page title",
                "fail",
                0,
                3,
                "Page is missing a title.",
            )
        )

    # H1
    if html.h1_count == 1:

        score += 4

        findings.append(
            finding(
                "Primary heading",
                "pass",
                4,
                4,
                "Page contains exactly one H1.",
            )
        )

    elif html.h1_count > 1:

        score += 2

        findings.append(
            finding(
                "Primary heading",
                "warning",
                2,
                4,
                f"Page contains {html.h1_count} H1 elements.",
            )
        )

    else:

        findings.append(
            finding(
                "Primary heading",
                "fail",
                0,
                4,
                "Page has no H1.",
            )
        )

    # Description
    if html.meta_description:

        score += 3

        findings.append(
            finding(
                "Meta description",
                "pass",
                3,
                3,
                "Page has a meta description.",
            )
        )

    else:

        findings.append(
            finding(
                "Meta description",
                "warning",
                0,
                3,
                "Page is missing a meta description.",
            )
        )

    # Content
    # Content
    if html.word_count >= 1000:

        content_points = 5
        status = "pass"

    elif html.word_count >= 500:

        content_points = 4
        status = "pass"

    elif html.word_count >= 250:

        content_points = 3
        status = "warning"

    elif html.word_count >= 100:

        content_points = 1
        status = "warning"

    else:

        content_points = 0
        status = "fail"

    score += content_points

    findings.append(
        finding(
            "Content depth",
            status,
            content_points,
            5,
            f"{html.word_count} words of extracted page text.",
        )
    )


    findings.append(
        finding(
            "Content depth",
            status,
            score,
            5,
            f"{html.word_count} words of extracted page text.",
        )
    )

    # Headings
    # Headings
    heading_count = sum(
        html.heading_counts.values()
    )

    if heading_count >= 4:

        heading_points = 4
        status = "pass"

    elif heading_count >= 2:

        heading_points = 2
        status = "warning"

    else:

        heading_points = 0
        status = "fail"

    score += heading_points

    findings.append(
        finding(
            "Heading structure",
            status,
            heading_points,
            4,
            f"{heading_count} headings detected.",
        )
    )

    # Semantic HTML
    semantic_count = sum(
        html.semantic_elements.values()
    )

    if semantic_count >= 3:

        score += 3

        findings.append(
            finding(
                "Semantic HTML",
                "pass",
                3,
                3,
                "Semantic HTML elements are present.",
            )
        )

    else:

        findings.append(
            finding(
                "Semantic HTML",
                "warning",
                0,
                3,
                "Limited semantic HTML structure detected.",
            )
        )

    # JS heuristic
    if html.javascript_heavy_signal:

        findings.append(
            finding(
                "JavaScript dependency",
                "warning",
                0,
                0,
                (
                    "The HTTP response contains little text "
                    "despite substantial JavaScript. A browser-rendered "
                    "audit is recommended."
                ),
            )
        )

    return ScoreResult(
        score=min(score, max_score),
        max_score=max_score,
        findings=findings,
    )


def score_citation_readiness(
    html,
) -> ScoreResult:

    findings = []
    score = 0
    max_score = 25

    # Clear title/H1
    if html.title and html.h1_count == 1:

        score += 5

        findings.append(
            finding(
                "Page identity",
                "pass",
                5,
                5,
                "Title and primary heading provide a clear page identity.",
            )
        )

    else:

        score += 2

        findings.append(
            finding(
                "Page identity",
                "warning",
                2,
                5,
                "Page identity could be clearer.",
            )
        )

    # Content
    if html.word_count >= 500:

        score += 5

        findings.append(
            finding(
                "Extractable content",
                "pass",
                5,
                5,
                "Page contains substantial extractable text.",
            )
        )

    elif html.word_count >= 200:

        score += 3

        findings.append(
            finding(
                "Extractable content",
                "warning",
                3,
                5,
                "Page contains some extractable content.",
            )
        )

    else:

        findings.append(
            finding(
                "Extractable content",
                "fail",
                0,
                5,
                "Very little extractable text was found.",
            )
        )

    # Schema
    if html.schema_present:

        score += 5

        findings.append(
            finding(
                "Structured data",
                "pass",
                5,
                5,
                (
                    "JSON-LD structured data detected: "
                    + ", ".join(html.schema_types)
                ),
            )
        )

    else:

        findings.append(
            finding(
                "Structured data",
                "warning",
                0,
                5,
                "No JSON-LD structured data detected.",
            )
        )

    # Links
    if html.internal_links >= 5:

        score += 3

        findings.append(
            finding(
                "Internal context",
                "pass",
                3,
                3,
                f"{html.internal_links} internal links detected.",
            )
        )

    else:

        score += 1

        findings.append(
            finding(
                "Internal context",
                "warning",
                1,
                3,
                f"Only {html.internal_links} internal links detected.",
            )
        )

    # Images
    if html.image_count == 0:

        score += 2

        findings.append(
            finding(
                "Image accessibility",
                "pass",
                2,
                2,
                "No images requiring alt-text analysis.",
            )
        )

    elif html.images_without_alt == 0:

        score += 2

        findings.append(
            finding(
                "Image accessibility",
                "pass",
                2,
                2,
                "All detected images have alt attributes.",
            )
        )

    else:

        score += 1

        findings.append(
            finding(
                "Image accessibility",
                "warning",
                1,
                2,
                (
                    f"{html.images_without_alt} of "
                    f"{html.image_count} images lack alt attributes."
                ),
            )
        )

    # Explicitly identifiable content
    if html.paragraph_count >= 5:

        score += 5

        findings.append(
            finding(
                "Readable content structure",
                "pass",
                5,
                5,
                "Multiple paragraph blocks provide extractable content.",
            )
        )

    else:

        score += 2

        findings.append(
            finding(
                "Readable content structure",
                "warning",
                2,
                5,
                "Limited paragraph structure detected.",
            )
        )

    return ScoreResult(
        score=min(score, max_score),
        max_score=max_score,
        findings=findings,
    )


def score_technical(
    html,
    technical,
) -> ScoreResult:

    findings = []
    score = 0
    max_score = 20

    # Canonical
    if html.canonical:

        score += 4

        findings.append(
            finding(
                "Canonical URL",
                "pass",
                4,
                4,
                "Canonical URL is present.",
            )
        )

    else:

        findings.append(
            finding(
                "Canonical URL",
                "warning",
                0,
                4,
                "No canonical URL detected.",
            )
        )

    # Schema
    if html.schema_present:

        score += 4

        findings.append(
            finding(
                "Structured data",
                "pass",
                4,
                4,
                "JSON-LD structured data detected.",
            )
        )

    else:

        findings.append(
            finding(
                "Structured data",
                "warning",
                0,
                4,
                "No JSON-LD structured data detected.",
            )
        )

    # OpenGraph
    if html.og_title and html.og_description:

        score += 3

        findings.append(
            finding(
                "OpenGraph metadata",
                "pass",
                3,
                3,
                "OpenGraph title and description are present.",
            )
        )

    elif html.og_title or html.og_description:

        score += 1

        findings.append(
            finding(
                "OpenGraph metadata",
                "warning",
                1,
                3,
                "Some OpenGraph metadata is present.",
            )
        )

    else:

        findings.append(
            finding(
                "OpenGraph metadata",
                "warning",
                0,
                3,
                "OpenGraph metadata was not detected.",
            )
        )

    # Response time
    if (
        technical.response_time_ms is not None
        and technical.response_time_ms < 1000
    ):

        score += 3

        findings.append(
            finding(
                "HTTP response time",
                "pass",
                3,
                3,
                (
                    f"Initial HTTP response took "
                    f"{technical.response_time_ms:.0f} ms."
                ),
            )
        )

    elif (
        technical.response_time_ms is not None
        and technical.response_time_ms < 2500
    ):

        score += 2

        findings.append(
            finding(
                "HTTP response time",
                "warning",
                2,
                3,
                (
                    f"Initial HTTP response took "
                    f"{technical.response_time_ms:.0f} ms."
                ),
            )
        )

    else:

        findings.append(
            finding(
                "HTTP response time",
                "warning",
                0,
                3,
                "HTTP response was relatively slow.",
            )
        )

    # Noindex
    if technical.noindex_detected:

        findings.append(
            finding(
                "Indexing directives",
                "fail",
                0,
                3,
                "noindex was detected in an HTTP robots directive.",
            )
        )

    else:

        score += 3

        findings.append(
            finding(
                "Indexing directives",
                "pass",
                3,
                3,
                "No HTTP noindex directive detected.",
            )
        )

    # Content type
    if technical.content_type:

        if "text/html" in technical.content_type.lower():

            score += 3

            findings.append(
                finding(
                    "HTML content type",
                    "pass",
                    3,
                    3,
                    "Page is served as HTML.",
                )
            )

        else:

            findings.append(
                finding(
                    "HTML content type",
                    "warning",
                    0,
                    3,
                    (
                        "Response content type is "
                        f"{technical.content_type}."
                    ),
                )
            )

    return ScoreResult(
        score=min(score, max_score),
        max_score=max_score,
        findings=findings,
    )


def calculate_overall(
    crawlability: ScoreResult,
    understandability: ScoreResult,
    citation: ScoreResult,
    technical: ScoreResult,
) -> int:

    crawl = (
        crawlability.score
        / crawlability.max_score
        * 30
    )

    understand = (
        understandability.score
        / understandability.max_score
        * 25
    )

    citation_score = (
        citation.score
        / citation.max_score
        * 25
    )

    technical_score = (
        technical.score
        / technical.max_score
        * 20
    )

    return round(
        crawl
        + understand
        + citation_score
        + technical_score
    )


def score_label(score: int) -> str:

    if score >= 90:
        return "Excellent"

    if score >= 80:
        return "Very Good"

    if score >= 70:
        return "Good"

    if score >= 60:
        return "Needs Improvement"

    if score >= 40:
        return "Poor"

    return "Critical"
