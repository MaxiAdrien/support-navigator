import argparse

from qdrant_client import QdrantClient

from config import COLLECTION_NAME, QDRANT_HOST, QDRANT_PORT


def build_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def list_points(client: QdrantClient, limit: int) -> None:
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    for point in points:
        print(f"ID={point.id}")
        print(point.payload)
        print("-" * 40)


def count_points(client: QdrantClient) -> None:
    result = client.count(
        collection_name=COLLECTION_NAME,
        exact=True,
    )
    print(result.count)


def delete_points(client: QdrantClient, ids: list[str]) -> None:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=ids,
    )
    print(f"Deleted {len(ids)} point(s).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manage points in Qdrant.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List points.")
    list_parser.add_argument("--limit", type=int, default=20, help="Max points to show.")

    subparsers.add_parser("count", help="Count points.")

    delete_parser = subparsers.add_parser("delete", help="Delete points by ID.")
    delete_parser.add_argument("--ids", nargs="+", required=True, help="Point IDs to delete.")

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    client = build_client()

    if args.command == "list":
        list_points(client, args.limit)
    elif args.command == "count":
        count_points(client)
    elif args.command == "delete":
        delete_points(client, args.ids)


if __name__ == "__main__":
    main()
