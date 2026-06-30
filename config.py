import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API
API_URL = os.environ.get('API_URL', 'http://localhost:8000/chat/stream')
API_TIMEOUT_SECONDS = int(os.environ.get('API_TIMEOUT_SECONDS', 60))

# Rewrite query
REWRITE_PROMPT_PATH = Path('prompts/rewrite_query.txt')

# Retrieval
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-large')
VECTOR_SIZE = int(os.environ.get('VECTOR_SIZE', 1536))
COLLECTION_NAME = os.environ.get('COLLECTION_NAME', 'support_docs')
QDRANT_URL = os.environ.get('QDRANT_URL', 'http://localhost:6333')
QDRANT_API_KEY = os.environ.get('QDRANT_API_KEY')
TOP_K = int(os.environ.get('TOP_K', 3))

# Answer
ANSWER_PROMPT_PATH = Path('prompts/answer_query.txt')
CHAT_MODEL = os.environ.get('CHAT_MODEL', 'gpt-5-mini')

# Ingest artifacts
DATA_DIR = Path('data')
DOCUMENTS_DIR = DATA_DIR / 'documents'
LOGS_DIR = DATA_DIR / 'logs'
RAW_HTML_FILENAME = 'raw.html'
PARSED_JSON_FILENAME = 'parsed.json'
CHUNKS_JSON_FILENAME = 'chunks.json'
