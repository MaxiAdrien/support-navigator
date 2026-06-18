from hashlib import sha256
from pathlib import Path

import requests

from config import DOCUMENTS_DIR, RAW_HTML_FILENAME


def doc_dir_for_url(url: str) -> Path:
    # Generate a directory path for a given URL (same URL always maps to same directory)
    doc_id = sha256(url.encode()).hexdigest()[:20]

    return DOCUMENTS_DIR / doc_id


def download_page(url: str) -> Path:
    # Download the page
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    # Create directory for the document
    doc_dir = doc_dir_for_url(url)
    doc_dir.mkdir(parents=True, exist_ok=True)

    # Save the raw HTML to a file
    (doc_dir / RAW_HTML_FILENAME).write_text(response.text, encoding="utf-8")

    return doc_dir
