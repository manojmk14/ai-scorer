from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from app.analyzers.html import analyze_html
from app.analyzers.technical import analyze_technical
from app.crawler.fetcher import fetch_url
from app.crawler.robots import analyze_robots
from app.crawler.sitemap import analyze_sitemap
from app.models.report import AuditReport, utc_now_iso
from app.scoring.engine import (
    calculate_overall,
    score_citation_readiness,
    score_crawlability,
    score_label,
    score_technical,
    score_understandability,
)


def normalize_url(url: str) -> str:

    url = url.strip()

    if not url:
        raise ValueError("URL cannot be empty.")

    if not url.startswith(
        ("http://", "https://")
    ):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.netloc:
        raise ValueError(
            f"Invalid URL: {url}"
        )

    if parsed.scheme not in {
        "http",
        "https",
    }:
        raise ValueError(
            "Only HTTP and HTTPS URLs are supported."
        )

    return url


def print_header(title: str):

    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def status_symbol(status: str) -> str:

    symbols = {
        "pass": "✓",
        "warning": "⚠",
        "fail": "✗",
    }

    return symbols.get(status, "•")


def print_findings(findings: list[dict]):

    for item in findings:

        symbol = status_symbol(
            item["status"]
        )

        print(
            f"{symbol} "
            f"{item['title']}: "
            f"{item['message']}"
        )


def print_report(report: AuditReport):

    print_header("AI READINESS AUDITOR")

    print(f"URL:        {report.url}")
    print(f"Final URL:  {report.final_url}")

    print_header("SCORES")

    print(
        f"Overall AI Readiness       "
        f"{report.overall_score}/100 "
        f"({report.overall_label})"
    )

    scores = report.scores

    print(
        f"AI Crawlability            "
        f"{scores['crawlability']}/30"
    )

    print(
        f"AI Understandability       "
        f"{scores['understandability']}/25"
    )

    print(
        f"Citation Readiness         "
        f"{scores['citation_readiness']}/25"
    )

    print(
        f"Technical Readiness        "
        f"{scores['technical']}/20"
    )

    print_header("AI CRAWLABILITY")

    print_findings(
        report.crawlability["findings"]
    )

    print_header("AI UNDERSTANDABILITY")

    print_findings(
        report.understandability["findings"]
    )

    print_header("CITATION READINESS")

    print_findings(
        report.citation_readiness["findings"]
    )

    print_header("TECHNICAL")

    print_findings(
        report.technical["findings"]
    )

    print_header("AI BOT ACCESS")

    bots = report.robots.get(
        "bots",
        {}
    )

    for bot_name, bot in bots.items():

        allowed = bot.get("allowed")

        if allowed is True:
            symbol = "✓"
            state = "Allowed"

        elif allowed is False:
            symbol = "✗"
            state = "Blocked"

        else:
            symbol = "?"
            state = "Unknown"

        print(
            f"{symbol} "
            f"{bot_name:<25} "
            f"{state}"
        )

    print_header("PAGE")

    page = report.page

    print(
        f"Title:              "
        f"{page.get('title')}"
    )

    print(
        f"H1 count:            "
        f"{page.get('h1_count')}"
    )

    print(
        f"Word count:          "
        f"{page.get('word_count')}"
    )

    print(
        f"Internal links:      "
        f"{page.get('internal_links')}"
    )

    print(
        f"External links:      "
        f"{page.get('external_links')}"
    )

    print(
        f"Schema types:        "
        f"{', '.join(page.get('schema_types', [])) or 'None'}"
    )

    print(
        f"Canonical:            "
        f"{page.get('canonical') or 'Missing'}"
    )

    print(
        f"JavaScript signal:    "
        f"{'Yes' if page.get('javascript_heavy_signal') else 'No'}"
    )

    print()


def main():

    parser = argparse.ArgumentParser(
        description=(
            "Analyze a webpage for AI crawlability, "
            "understandability, citation readiness, "
            "and technical readiness."
        )
    )

    parser.add_argument(
        "url",
        help="URL to audit",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of the human-readable report.",
    )

    parser.add_argument(
        "--output",
        help="Write JSON report to this file.",
    )

    args = parser.parse_args()

    try:

        url = normalize_url(args.url)

    except ValueError as exc:

        print(
            f"Error: {exc}",
            file=sys.stderr,
        )

        sys.exit(1)

    print(
        f"Auditing {url}...",
        file=sys.stderr,
    )

    # ---------------------------------------------------------
    # 1. Fetch page
    # ---------------------------------------------------------

    page_response = fetch_url(url)

    if page_response.error:

        print(
            f"Failed to fetch page: "
            f"{page_response.error}",
            file=sys.stderr,
        )

        sys.exit(2)

    # ---------------------------------------------------------
    # 2. Robots
    # ---------------------------------------------------------

    robots = analyze_robots(
        page_response.final_url or url
    )

    # ---------------------------------------------------------
    # 3. Sitemap
    # ---------------------------------------------------------

    sitemap = analyze_sitemap(
        page_response.final_url or url,
        robots.sitemap_urls,
    )

    # ---------------------------------------------------------
    # 4. HTML analysis
    # ---------------------------------------------------------

    html_analysis = analyze_html(
        page_response.content,
        page_response.final_url or url,
    )

    # ---------------------------------------------------------
    # 5. Technical analysis
    # ---------------------------------------------------------

    technical = analyze_technical(
        requested_url=url,
        final_url=page_response.final_url,
        status_code=page_response.status_code,
        headers=page_response.headers,
        response_time_ms=page_response.response_time_ms,
        redirect_count=page_response.redirect_count,
        canonical=html_analysis.canonical,
    )

    # ---------------------------------------------------------
    # 6. Scores
    # ---------------------------------------------------------

    crawlability = score_crawlability(
        technical,
        robots,
        sitemap,
    )

    understandability = score_understandability(
        html_analysis,
    )

    citation_readiness = score_citation_readiness(
        html_analysis,
    )

    technical_score = score_technical(
        html_analysis,
        technical,
    )

    overall = calculate_overall(
        crawlability,
        understandability,
        citation_readiness,
        technical_score,
    )

    # ---------------------------------------------------------
    # 7. Build report
    # ---------------------------------------------------------

    report = AuditReport(
        url=url,
        final_url=page_response.final_url,
        audit_date=utc_now_iso(),

        overall_score=overall,
        overall_label=score_label(overall),

        scores={
            "crawlability": crawlability.score,
            "understandability": understandability.score,
            "citation_readiness": citation_readiness.score,
            "technical": technical_score.score,
        },

        crawlability={
            "score": crawlability.score,
            "max_score": crawlability.max_score,
            "findings": crawlability.findings,
        },

        understandability={
            "score": understandability.score,
            "max_score": understandability.max_score,
            "findings": understandability.findings,
        },

        citation_readiness={
            "score": citation_readiness.score,
            "max_score": citation_readiness.max_score,
            "findings": citation_readiness.findings,
        },

        technical={
            "score": technical_score.score,
            "max_score": technical_score.max_score,
            "findings": technical_score.findings,
        },

        page={
            "title": html_analysis.title,
            "title_length": html_analysis.title_length,

            "meta_description": html_analysis.meta_description,
            "meta_description_length": (
                html_analysis.meta_description_length
            ),

            "h1_count": html_analysis.h1_count,
            "h1_text": html_analysis.h1_text,

            "heading_counts": html_analysis.heading_counts,

            "word_count": html_analysis.word_count,
            "paragraph_count": html_analysis.paragraph_count,
            "sentence_count": html_analysis.sentence_count,

            "internal_links": html_analysis.internal_links,
            "external_links": html_analysis.external_links,

            "image_count": html_analysis.image_count,
            "images_with_alt": html_analysis.images_with_alt,
            "images_without_alt": html_analysis.images_without_alt,

            "canonical": html_analysis.canonical,
            "robots_meta": html_analysis.robots_meta,

            "og_title": html_analysis.og_title,
            "og_description": html_analysis.og_description,

            "schema_present": html_analysis.schema_present,
            "schema_types": html_analysis.schema_types,

            "semantic_elements": html_analysis.semantic_elements,

            "script_count": html_analysis.script_count,
            "javascript_heavy_signal": (
                html_analysis.javascript_heavy_signal
            ),

            "text_html_ratio": html_analysis.text_html_ratio,
        },

        robots={
            "url": robots.url,
            "found": robots.found,
            "status_code": robots.status_code,
            "sitemap_urls": robots.sitemap_urls,
            "error": robots.error,

            "bots": {
                name: {
                    "company": result.company,
                    "allowed": result.allowed,
                    "matched_path": result.matched_path,
                }
                for name, result in robots.bots.items()
            },
        },

        sitemap={
            "found": sitemap.found,
            "url": sitemap.url,
            "status_code": sitemap.status_code,
            "is_xml": sitemap.is_xml,
            "error": sitemap.error,
        },
    )

    report_dict = report.to_dict()

    # ---------------------------------------------------------
    # 8. JSON output
    # ---------------------------------------------------------

    if args.output:

        output_path = Path(args.output)

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(
                report_dict,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        print(
            f"JSON report written to "
            f"{output_path}",
            file=sys.stderr,
        )

    if args.json:

        print(
            json.dumps(
                report_dict,
                indent=2,
                ensure_ascii=False,
            )
        )

    else:

        print_report(report)


if __name__ == "__main__":
    main()
