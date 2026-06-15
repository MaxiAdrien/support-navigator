from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

from config import (
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    QDRANT_HOST,
    QDRANT_PORT,
    TOP_K,
)
from graph import Document


def retrieve(query: str, top_k: int = TOP_K) -> list[Document]:
    """Retrieve the most relevant documents for a query."""

    # Load environment variables and initialise clients
    load_dotenv()
    openai_client = OpenAI()
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Generate embedding for query
    embedding = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=query,
    ).data[0].embedding

    # Query Qdrant for most similar documents
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=top_k,
    )

    return [
        {
            'title': point.payload['title'],
            'content': point.payload['content'],
            'score': point.score,
        }
        for point in results.points
    ]
