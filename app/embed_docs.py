import json

from dotenv import load_dotenv
from openai import OpenAI

from config import EMBEDDED_DOCS_PATH, EMBEDDING_MODEL, RAW_DOCS_PATH

def main():
    # Load environment variables and initialise OpenAI client
    load_dotenv()
    client = OpenAI()

    # Load raw documents
    with open(RAW_DOCS_PATH) as f:
        docs = json.load(f)
    contents = [d['content'] for d in docs]

    # Create embeddings
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=contents)
    for doc, item in zip(docs, response.data):
        doc['embedding'] = item.embedding

    # Save embedded documents
    with open(EMBEDDED_DOCS_PATH, 'w') as f:
        json.dump(docs, f)


if __name__ == '__main__':
    main()
