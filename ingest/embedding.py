from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from config import CHUNKS_JSON_FILENAME, EMBEDDING_MODEL
from ingest.models import Chunk, read_chunks, write_chunks


def embed_docs(doc_dirs: list[Path], batch_size: int = 128) -> list[Path]:
    """
    - Embeds the chunks of documents in the specified directories if they do not already have embeddings.
    - Uses batch processing to handle large numbers of chunks efficiently.
    - Updates the chunks with their embeddings and writes them back to the JSON files.
    - Returns a list of paths to the updated JSON files.
    """
    load_dotenv()
    client = OpenAI()

    docs: list[tuple[Path, list[Chunk]]] = []
    chunks_to_embed: list[Chunk] = []
    for doc_dir in doc_dirs:
        chunks = read_chunks(doc_dir / CHUNKS_JSON_FILENAME)
        docs.append((doc_dir, chunks))
        chunks_to_embed.extend([chunk for chunk in chunks if chunk.embedding is None])

    for i in range(0, len(chunks_to_embed), batch_size):
        batch = chunks_to_embed[i : i + batch_size]
        embedding_inputs = [
            (
                f"Page: {chunk.title}\n"
                f"Section: {chunk.heading or 'Introduction'}\n\n"
                f"{chunk.text}"
            )
            for chunk in batch
        ]

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=embedding_inputs,
        )

        for chunk, item in zip(batch, response.data):
            chunk.embedding = item.embedding

    output_paths: list[Path] = []
    for doc_dir, chunks in docs:
        output_path = doc_dir / CHUNKS_JSON_FILENAME
        write_chunks(output_path, chunks)
        output_paths.append(output_path)
    return output_paths
