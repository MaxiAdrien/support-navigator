import argparse
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from config import LOGS_DIR

STEPS = ("download", "parse", "chunk", "embed", "ingest")
CHUNK_MAX_TOKENS = 500
EMBED_BATCH_SIZE = 128
INGEST_BATCH_SIZE = 256


@dataclass
class RunContext:
    urls: list[str] | None
    doc_dirs: list[Path] | None
    urls_file: Path | None
    status_log: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingestion pipeline CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    all_parser = subparsers.add_parser("all", help="Run all steps.")
    all_parser.add_argument("--urls-file", type=Path, required=True, help="Text file containing one URL per line.")

    run_parser = subparsers.add_parser("run", help="Run selected steps in order.")
    run_parser.add_argument("--steps", nargs="+", required=True, choices=STEPS)
    run_parser.add_argument("--urls-file", type=Path, required=True, help="Text file containing one URL per line.")

    return parser.parse_args()


def read_urls_file(path: Path) -> list[str]:
    urls: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip()
        if value and not value.startswith("#"):
            urls.append(value)
    return urls


def collect_urls(context: RunContext) -> list[str]:
    return list(dict.fromkeys(read_urls_file(context.urls_file)))


def ensure_doc_dirs(context: RunContext) -> list[Path]:
    if context.doc_dirs:
        return context.doc_dirs
    from ingest.download import doc_dir_for_url

    context.doc_dirs = [doc_dir_for_url(url) for url in context.urls]
    return context.doc_dirs


def append_status_log(path: Path, entry: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def build_status_log_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return LOGS_DIR / f"ingest-{timestamp}.jsonl"


def run_all_from_file(context: RunContext) -> int:
    urls = context.urls

    from ingest.chunking import chunk_document
    from ingest.download import download_page
    from ingest.embedding import embed_docs
    from ingest.parsing import extract_web_page
    from ingest.qdrant_ingest import ingest_docs

    context.status_log = build_status_log_path()
    print(f"Status log: {context.status_log}")

    failed_count = 0
    prepared: list[tuple[str, Path]] = []

    for url in urls:
        try:
            doc_dir = download_page(url)
            extract_web_page(doc_dir)
            chunk_document(doc_dir, max_tokens=CHUNK_MAX_TOKENS)
            prepared.append((url, doc_dir))
            print(f"Prepared {url} -> {doc_dir}")
        except Exception as error:
            failed_count += 1
            entry = {
                "url": url,
                "status": "error",
                "error": f"download-parse-chunk stage failed: {error}",
            }
            print(f"ERROR {url}: {error}")
            append_status_log(context.status_log, entry)

    if not prepared:
        return failed_count

    prepared_urls = [url for url, _ in prepared]
    prepared_doc_dirs = [doc_dir for _, doc_dir in prepared]

    try:
        embed_docs(prepared_doc_dirs, batch_size=EMBED_BATCH_SIZE)
    except Exception as error:
        for url in prepared_urls:
            entry = {
                "url": url,
                "status": "error",
                "error": f"embed stage failed: {error}",
            }
            append_status_log(context.status_log, entry)
        return failed_count + len(prepared_urls)

    try:
        upserted = ingest_docs(prepared_doc_dirs, batch_size=INGEST_BATCH_SIZE)
    except Exception as error:
        for url in prepared_urls:
            entry = {
                "url": url,
                "status": "error",
                "error": f"ingest stage failed: {error}",
            }
            append_status_log(context.status_log, entry)
        return failed_count + len(prepared_urls)

    print(f"Upserted {upserted} chunks")
    for url, doc_dir in prepared:
        entry = {
            "url": url,
            "status": "ok",
            "doc_dir": str(doc_dir),
        }
        append_status_log(context.status_log, entry)

    return failed_count


def run_step(step: str, context: RunContext) -> RunContext:
    if step == "download":
        from ingest.download import download_page

        context.doc_dirs = []
        for url in context.urls:
            doc_dir = download_page(url)
            context.doc_dirs.append(doc_dir)
            print(doc_dir)
    elif step == "parse":
        from ingest.parsing import extract_web_page

        for doc_dir in ensure_doc_dirs(context):
            print(extract_web_page(doc_dir))
    elif step == "chunk":
        from ingest.chunking import chunk_document

        for doc_dir in ensure_doc_dirs(context):
            print(chunk_document(doc_dir, max_tokens=CHUNK_MAX_TOKENS))
    elif step == "embed":
        from ingest.embedding import embed_docs

        outputs = embed_docs(ensure_doc_dirs(context), batch_size=EMBED_BATCH_SIZE)
        for output in outputs:
            print(output)
    elif step == "ingest":
        from ingest.qdrant_ingest import ingest_docs

        upserted = ingest_docs(ensure_doc_dirs(context), batch_size=INGEST_BATCH_SIZE)
        print(f"Upserted {upserted} chunks")
    return context


def main() -> None:
    args = parse_args()
    context = RunContext(
        urls=None,
        doc_dirs=None,
        urls_file=getattr(args, "urls_file", None),
        status_log=None,
    )
    context.urls = collect_urls(context)

    if args.command == "all":
        failed_count = run_all_from_file(context)
        if failed_count > 0:
            raise RuntimeError(f"all finished with {failed_count} failed URL(s).")
    elif args.command == "run":
        for step in args.steps:
            context = run_step(step, context)


if __name__ == "__main__":
    main()
