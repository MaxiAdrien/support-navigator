import json

from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from config import COLLECTION_NAME, EMBEDDED_DOCS_PATH, QDRANT_HOST, QDRANT_PORT


def main():
    # Initialise Qdrant client
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Load embeddings
    with open(EMBEDDED_DOCS_PATH) as f:
        docs = json.load(f)

    # Create points for Qdrant
    points = [
        PointStruct(
            id=doc['id'],
            vector=doc['embedding'],
            payload={
                'title': doc['title'],
                'content': doc['content'],
            },
        )
        for doc in docs
    ]

    # Upsert points into Qdrant
    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )


if __name__ == '__main__':
    main()
