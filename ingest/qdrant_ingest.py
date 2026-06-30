from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from config import CHUNKS_JSON_FILENAME, COLLECTION_NAME, QDRANT_API_KEY, QDRANT_URL, VECTOR_SIZE
from ingest.models import read_chunks


def point_id_for_chunk_id(chunk_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, chunk_id))


def ingest_docs(doc_dirs: list[Path], batch_size: int = 256) -> int:
    """
    - Ingests document chunks into a Qdrant collection.
    - If the collection does not exist, it will be created.
    - Batches upserts to improve performance.
    - If a chunk with the same content hash already exists in the collection, it will be skipped.
    - Returns the number of chunks that were upserted into the collection.
    """
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE,
            ),
        )

    all_chunks = []
    for doc_dir in doc_dirs:
        chunks = read_chunks(doc_dir / CHUNKS_JSON_FILENAME)
        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError(
                    f"Chunk '{chunk.chunk_id}' has no embedding. Run embed step first."
                )
        all_chunks.extend(chunks)

    upserted_count = 0
    for i in range(0, len(all_chunks), batch_size):
        chunk_batch = all_chunks[i : i + batch_size]
        point_ids = [point_id_for_chunk_id(chunk.chunk_id) for chunk in chunk_batch]
        existing_points = client.retrieve(
            collection_name=COLLECTION_NAME,
            ids=point_ids,
            with_payload=True,
            with_vectors=False,
        )
        existing_hashes = {
            str(point.id): point.payload.get("content_hash")
            for point in existing_points
            if point.payload is not None
        }

        points = []
        for chunk in chunk_batch:
            point_id = point_id_for_chunk_id(chunk.chunk_id)
            if existing_hashes.get(point_id) == chunk.content_hash:
                continue
            points.append(
                PointStruct(
                    id=point_id,
                    vector=chunk.embedding,
                    payload={
                        "chunk_id": chunk.chunk_id,
                        "chunk_index": chunk.chunk_index,
                        "title": chunk.title,
                        "url": chunk.url,
                        "heading": chunk.heading,
                        "text": chunk.text,
                        "content_hash": chunk.content_hash,
                    },
                )
            )

        if points:
            client.upsert(collection_name=COLLECTION_NAME, points=points)
            upserted_count += len(points)
    return upserted_count
