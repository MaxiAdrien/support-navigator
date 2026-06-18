from pathlib import Path

# Retrieval
EMBEDDING_MODEL = 'text-embedding-3-small'
VECTOR_SIZE = 1536
COLLECTION_NAME = 'support_docs'
QDRANT_HOST = 'localhost'
QDRANT_PORT = 6333
TOP_K = 3

# Answer
PROMPT_PATH = Path('prompts/answer_prompt.txt')
CHAT_MODEL = 'gpt-5-mini'

# Ingest artifacts
DATA_DIR = Path("data")
DOCUMENTS_DIR = DATA_DIR / "documents"
LOGS_DIR = DATA_DIR / "logs"
RAW_HTML_FILENAME = "raw.html"
PARSED_JSON_FILENAME = "parsed.json"
CHUNKS_JSON_FILENAME = "chunks.json"
