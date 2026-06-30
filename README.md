# Support Navigator

## Prerequisites

- Python 3.13
- An OpenAI API key (`OPENAI_API_KEY`)
- A running Qdrant instance (default: `http://localhost:6333`)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configure environment

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

## Run the API

```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

Optional health check:

```bash
curl http://localhost:8000/health
```

## Run Streamlit

In a second terminal (same virtual environment):

```bash
streamlit run streamlit_app.py
```

Open the Streamlit URL shown in the terminal (usually `http://localhost:8501`).
