from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import json
import re

from bs4 import BeautifulSoup


@dataclass
class HTMLAnalysis:
    title: str | None
    title_length: int

    meta_description: str | None
    meta_description_length: int

    h1_count: int
    h1_text: list[str]

    heading_counts: dict[str, int]
    heading_structure: list[dict[str, Any]]

    word_count: int
    paragraph_count: int
    sentence_count: int

    internal_links: int
    external_links: int

    image_count: int
    images_with_alt: int
    images_without_alt: int

    canonical: str | None
    robots_meta: str | None

    og_title: str | None
    og_description: str | None

    schema_present: bool
    schema_types: list[str]

    semantic_elements: dict[str, int]

    script_count: int
    javascript_heavy_signal: bool

    text_html_ratio: float


def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_words(text: str) -> list[str]:
    return re.findall(r"\b[\w'-]+\b", text)


def count_sentences(text: str) -> int:
    sentences = re.split(r"[.!?]+", text)
    return len([
        sentence
        for sentence in sentences
        if sentence.strip()
    ])


def get_domain(url: str) -> str:
    from urllib.parse import urlparse

    return urlparse(url).netloc.lower().split(":")[0]


def analyze_html(
    html: str,
    page_url: str,
) -> HTMLAnalysis:

    soup = BeautifulSoup(html, "lxml")

    title_tag = soup.find("title")
    title = (
        normalize_whitespace(title_tag.get_text())
        if title_tag
        else None
    )

    description_tag = soup.find(
        "meta",
        attrs={"name": re.compile("^description$", re.I)},
    )

    meta_description = (
        normalize_whitespace(
            description_tag.get("content", "")
        )
        if description_tag
        else None
    )

    h1_tags = soup.find_all("h1")

    h1_text = [
        normalize_whitespace(tag.get_text(" ", strip=True))
        for tag in h1_tags
    ]

    heading_counts = {}

    heading_structure = []

    for level in range(1, 7):

        tag_name = f"h{level}"

        tags = soup.find_all(tag_name)

        heading_counts[tag_name] = len(tags)

        for tag in tags:

            heading_structure.append({
                "tag": tag_name,
                "text": normalize_whitespace(
                    tag.get_text(" ", strip=True)
                ),
            })

    # Remove non-content elements.
    content_soup = BeautifulSoup(html, "lxml")

    for element in content_soup.find_all([
        "script",
        "style",
        "noscript",
        "svg",
        "template",
    ]):
        element.decompose()

    body = content_soup.body

    if body:
        visible_text = normalize_whitespace(
            body.get_text(" ", strip=True)
        )
    else:
        visible_text = normalize_whitespace(
            content_soup.get_text(" ", strip=True)
        )

    words = extract_words(visible_text)

    word_count = len(words)

    paragraph_count = len(
        soup.find_all("p")
    )

    sentence_count = count_sentences(visible_text)

    # Links
    page_domain = get_domain(page_url)

    internal_links = 0
    external_links = 0

    for link in soup.find_all("a", href=True):

        href = link["href"].strip()

        if (
            not href
            or href.startswith("#")
            or href.startswith("mailto:")
            or href.startswith("tel:")
            or href.startswith("javascript:")
        ):
            continue

        if href.startswith("/"):
            internal_links += 1
            continue

        try:
            from urllib.parse import urlparse

            link_domain = urlparse(href).netloc.lower()

            if not link_domain:
                internal_links += 1
            elif link_domain.split(":")[0] == page_domain:
                internal_links += 1
            else:
                external_links += 1

        except Exception:
            continue

    # Images
    images = soup.find_all("img")

    images_with_alt = 0
    images_without_alt = 0

    for image in images:

        if image.get("alt") is not None:
            images_with_alt += 1
        else:
            images_without_alt += 1

    # Canonical
    canonical_tag = soup.find(
        "link",
        attrs={"rel": lambda value: value and "canonical" in value},
    )

    canonical = (
        canonical_tag.get("href")
        if canonical_tag
        else None
    )

    # Robots meta
    robots_tag = soup.find(
        "meta",
        attrs={"name": re.compile("^robots$", re.I)},
    )

    robots_meta = (
        robots_tag.get("content")
        if robots_tag
        else None
    )

    # OpenGraph
    og_title_tag = soup.find(
        "meta",
        attrs={"property": "og:title"},
    )

    og_description_tag = soup.find(
        "meta",
        attrs={"property": "og:description"},
    )

    og_title = (
        og_title_tag.get("content")
        if og_title_tag
        else None
    )

    og_description = (
        og_description_tag.get("content")
        if og_description_tag
        else None
    )

    # Schema.org / JSON-LD
    schema_present = False
    schema_types: list[str] = []

    for script in soup.find_all(
        "script",
        attrs={"type": re.compile(
            r"application/ld\+json",
            re.I,
        )},
    ):

        raw = script.string or script.get_text()

        try:
            data = json.loads(raw)

            schema_present = True

            collect_schema_types(
                data,
                schema_types,
            )

        except (json.JSONDecodeError, TypeError):
            continue

    schema_types = sorted(set(schema_types))

    # Semantic HTML
    semantic_tags = [
        "header",
        "nav",
        "main",
        "article",
        "section",
        "aside",
        "footer",
    ]

    semantic_elements = {
        tag: len(soup.find_all(tag))
        for tag in semantic_tags
    }

    script_count = len(soup.find_all("script"))

    html_length = max(len(html), 1)

    text_html_ratio = round(
        len(visible_text) / html_length,
        4,
    )

    # This is only a heuristic.
    javascript_heavy_signal = (
        word_count < 150
        and script_count >= 8
    )

    return HTMLAnalysis(
        title=title,
        title_length=len(title) if title else 0,

        meta_description=meta_description,
        meta_description_length=(
            len(meta_description)
            if meta_description
            else 0
        ),

        h1_count=len(h1_tags),
        h1_text=h1_text,

        heading_counts=heading_counts,
        heading_structure=heading_structure,

        word_count=word_count,
        paragraph_count=paragraph_count,
        sentence_count=sentence_count,

        internal_links=internal_links,
        external_links=external_links,

        image_count=len(images),
        images_with_alt=images_with_alt,
        images_without_alt=images_without_alt,

        canonical=canonical,
        robots_meta=robots_meta,

        og_title=og_title,
        og_description=og_description,

        schema_present=schema_present,
        schema_types=schema_types,

        semantic_elements=semantic_elements,

        script_count=script_count,
        javascript_heavy_signal=javascript_heavy_signal,

        text_html_ratio=text_html_ratio,
    )


def collect_schema_types(
    data,
    output: list[str],
):
    if isinstance(data, dict):

        schema_type = data.get("@type")

        if isinstance(schema_type, str):
            output.append(schema_type)

        elif isinstance(schema_type, list):
            output.extend(
                item
                for item in schema_type
                if isinstance(item, str)
            )

        for value in data.values():
            collect_schema_types(value, output)

    elif isinstance(data, list):

        for item in data:
            collect_schema_types(item, output)
