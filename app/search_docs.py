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

QUERY = 'I lost my job'


def main():
    # Load environment variables and initialise clients
    load_dotenv()
    openai_client = OpenAI()
    qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Generate embedding for query
    embedding = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=QUERY,
    ).data[0].embedding

    # Query Qdrant for most similar documents
    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=TOP_K,
    )

    # Display results
    for i, point in enumerate(results.points, start=1):
        print(f'\n{i}. {point.payload['title']}')
        print(f'Score: {point.score:.3f}')
        print(point.payload['content'])


if __name__ == '__main__':
    main()
