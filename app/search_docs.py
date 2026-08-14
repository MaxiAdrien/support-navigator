from openai import AsyncOpenAI
from qdrant_client import AsyncQdrantClient

from config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    QDRANT_API_KEY,
    QDRANT_URL,
    TOP_K,
)
from app.schemas import RetrievedDocument


async def retrieve(query: str, top_k: int = TOP_K) -> list[RetrievedDocument]:
    """Retrieve the most relevant documents for a query."""

    # Initialise clients
    openai_client = AsyncOpenAI()
    qdrant_client = AsyncQdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

    # Generate embedding for query
    embedding_response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    )
    embedding = embedding_response.data[0].embedding

    # Query Qdrant for most similar documents
    results = await qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=top_k,
    )

    return [
        {
            "url": point.payload["url"],
            "title": point.payload["title"],
            "heading": point.payload.get("heading"),
            "text": point.payload["text"],
            "score": point.score,
        }
        for point in results.points
    ]
