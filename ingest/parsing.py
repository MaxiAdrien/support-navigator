import re
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from config import PARSED_JSON_FILENAME, RAW_HTML_FILENAME
from ingest.models import Block, Link, ListItem, ParsedDocument, Section, write_parsed_document


def extract_text(element: Tag) -> str:
    """Extracts and cleans the text content from the given HTML element."""
    text = " ".join(element.stripped_strings)
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)
    return text.strip()


def extract_links(element: Tag, base_url: str) -> list[Link]:
    """Extracts all links from the given element and returns them as a list of Link objects."""
    return [
        Link(text=extract_text(anchor), url=urljoin(base_url, anchor["href"]))
        for anchor in element.find_all("a", href=True)
    ]


def iter_content_elements(parent: Tag):
    """Yield content tags in document order, including known nested wrappers."""
    for element in parent.children:
        if not isinstance(element, Tag):
            continue

        if element.name in {"h2", "h3", "h4", "p", "ul"}:
            yield element
            continue

        if element.name in {"div", "section"}:
            yield from iter_content_elements(element)


def extract_web_page(doc_dir: Path) -> Path:
    """
    Designed for Citizens Advice web pages only.
    Extracts the main content and metadata from the raw HTML file and saves it as a structured JSON file.
    """
    html = (doc_dir / RAW_HTML_FILENAME).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    canonical = soup.find("link", rel="canonical")
    url = canonical["href"] if canonical else ""

    main = soup.select_one("main.js-content")
    if main is None:
        raise ValueError("Could not find main content")

    for element in main.select(
        ".location-switcher,"
        "[data-testid='impact-survey'],"
        ".js-advice-feedback,"
        ".cads-page-review"
    ):
        element.decompose()

    title_element = main.find("h1")
    if title_element is None:
        raise ValueError("Could not find page title")

    title = extract_text(title_element)

    content = main.select_one(".cads-prose")
    if content is None:
        raise ValueError("Could not find article content")

    sections: list[Section] = []
    current_section = Section(heading=None, blocks=[])

    for element in iter_content_elements(content):
        if element.name == "h2":
            heading = extract_text(element)
            if not heading:
                continue
            if heading.lower() == "next steps":
                break
            if current_section.blocks:
                sections.append(current_section)
            current_section = Section(heading=heading, blocks=[])

        elif element.name in {"h3", "h4"}:
            text = extract_text(element)
            if not text:
                continue
            current_section.blocks.append(
                Block(type="subheading", text=text)
            )

        elif element.name == "p":
            text = extract_text(element)
            if not text:
                continue
            current_section.blocks.append(
                Block(
                    type="paragraph",
                    text=text,
                    links=extract_links(element, url),
                )
            )

        elif element.name == "ul":
            items: list[ListItem] = []
            for li in element.find_all("li", recursive=False):
                text = extract_text(li)
                if not text:
                    continue
                items.append(
                    ListItem(
                        text=text,
                        links=extract_links(li, url),
                    )
                )
            if items:
                current_section.blocks.append(Block(type="list", items=items))

    if current_section.blocks:
        sections.append(current_section)

    document = ParsedDocument(
        id=doc_dir.name,
        title=title,
        url=url,
        source="citizens_advice",
        sections=sections,
    )

    output_path = doc_dir / PARSED_JSON_FILENAME
    write_parsed_document(output_path, document)

    return output_path
