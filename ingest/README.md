# Ingest Pipeline

Run from the project root:

```bash
# Run full pipeline (download -> parse -> chunk -> embed -> ingest) for a set of URLs from a file (one URL per line).
python3 -m ingest.pipeline all --urls-file data/urls.txt

# Run only selected steps in order for a set of URLs from a file (one URL per line).
# Any combination of steps works as long as the order is correct and previous steps have been run for the same URLs.
python3 -m ingest.pipeline run --steps download parse --urls-file data/urls.txt
python3 -m ingest.pipeline run --steps download parse chunk --urls-file data/urls.txt
python3 -m ingest.pipeline run --steps parse chunk --urls-file data/urls.txt
python3 -m ingest.pipeline run --steps embed ingest --urls-file data/urls.txt
```
