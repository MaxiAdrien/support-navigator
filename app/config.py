from pathlib import Path

# Retrieval
EMBEDDING_MODEL = 'text-embedding-3-small'
VECTOR_SIZE = 1536
COLLECTION_NAME = 'support_docs'
QDRANT_HOST = 'localhost'
QDRANT_PORT = 6333
RAW_DOCS_PATH = Path('data/raw_docs.json')
EMBEDDED_DOCS_PATH = Path('data/embedded_docs.json')
TOP_K = 3

# Answer
PROMPT_PATH = Path('prompts/answer_prompt.txt')
CHAT_MODEL = 'gpt-5-mini'
