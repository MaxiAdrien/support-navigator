from pathlib import Path

import tiktoken

from config import CHUNKS_JSON_FILENAME, PARSED_JSON_FILENAME
from ingest.models import Chunk, hash_chunk_text, read_parsed_document, write_chunks

# TODO: Ensure links are preserved in the retrieved text, but do not include them in embeddings


def chunk_document(doc_dir: Path, max_tokens: int = 500) -> Path:
    """
    - Reads Citizens Advice parsed page JSON file from the specified directory.
    - Splits it into chunks based on sections and blocks, keeping chunks within the token limit.
    - Writes the resulting chunks to a JSON file in the same directory.
    """
    parsed = read_parsed_document(doc_dir / PARSED_JSON_FILENAME)

    document_id = parsed.id
    title = parsed.title
    url = parsed.url

    encoder = tiktoken.get_encoding("cl100k_base")
    chunks: list[Chunk] = []

    for section in parsed.sections:
        heading = section.heading
        units: list[tuple[str, str]] = []

        for block in section.blocks:
            if block.type == "paragraph" and block.text is not None:
                units.append(("paragraph", block.text))

            elif block.type == "subheading" and block.text:
                units.append(("subheading", block.text))

            elif block.type == "list":
                for item in block.items:
                    if item.text:
                        units.append(("list_item", f"- {item.text}"))

        current_units: list[str] = []
        current_tokens = 0
        last_non_list_unit: str | None = None

        for unit_type, unit in units:
            unit_tokens = len(encoder.encode(unit))
            if current_units and current_tokens + unit_tokens > max_tokens:
                text = "\n\n".join(current_units)
                chunk_id = f"{document_id}_{len(chunks)}"
                chunks.append(
                    Chunk(
                        chunk_id=chunk_id,
                        chunk_index=len(chunks),
                        title=title,
                        url=url,
                        heading=heading,
                        text=text,
                        content_hash=hash_chunk_text(text),
                    )
                )
                current_units = []
                current_tokens = 0

            # If chunk would start mid-list, start again with the last non-list unit to provide context
            if not current_units and unit_type == "list_item" and last_non_list_unit is not None:
                context_tokens = len(encoder.encode(last_non_list_unit))
                if context_tokens + unit_tokens <= max_tokens:
                    current_units.append(last_non_list_unit)
                    current_tokens += context_tokens

            current_units.append(unit)
            current_tokens += unit_tokens

            if unit_type != "list_item":
                last_non_list_unit = unit

        if current_units:
            text = "\n\n".join(current_units)
            chunk_id = f"{document_id}_{len(chunks)}"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    chunk_index=len(chunks),
                    title=title,
                    url=url,
                    heading=heading,
                    text=text,
                    content_hash=hash_chunk_text(text),
                )
            )

    output_path = doc_dir / CHUNKS_JSON_FILENAME
    write_chunks(output_path, chunks)

    return output_path
