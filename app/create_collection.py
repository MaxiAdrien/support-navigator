from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from config import (
    COLLECTION_NAME,
    QDRANT_HOST,
    QDRANT_PORT,
    VECTOR_SIZE,
)


def main():
    # Initialise Qdrant client
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Create collection
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=VECTOR_SIZE,
            distance=Distance.COSINE,
        ),
    )


if __name__ == '__main__':
    main()
