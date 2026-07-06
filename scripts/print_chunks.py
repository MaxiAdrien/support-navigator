from argparse import ArgumentParser
from pathlib import Path

from ingest.models import read_chunks


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        description="Print chunks from a chunks.json file for quick QA."
    )
    parser.add_argument(
        "chunks_path",
        type=Path,
        help="Path to a chunks.json file.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    divider = "=" * 80

    chunks_path = args.chunks_path.expanduser().resolve()
    chunks = read_chunks(chunks_path)

    for i, chunk in enumerate(chunks):
        print(
            f"Page: {chunk.title}\n"
            f"Section: {chunk.heading or 'Introduction'}\n\n"
            f"{chunk.text}"
        )
        if i != len(chunks) - 1:
            print(f"\n{divider}\n")


if __name__ == "__main__":
    main()


