import json
from hashlib import sha256
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Link:
    text: str
    url: str

    @classmethod
    def from_dict(cls, data: dict) -> "Link":
        return cls(text=data["text"], url=data["url"])

    def to_dict(self) -> dict:
        return {"text": self.text, "url": self.url}


@dataclass
class ListItem:
    text: str
    links: list[Link] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "ListItem":
        return cls(
            text=data["text"],
            links=[Link.from_dict(link) for link in data.get("links", [])],
        )

    def to_dict(self) -> dict:
        item = {"text": self.text}
        if self.links:
            item["links"] = [link.to_dict() for link in self.links]
        return item


@dataclass
class Block:
    type: str
    text: str | None = None
    links: list[Link] = field(default_factory=list)
    items: list[ListItem] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Block":
        return cls(
            type=data["type"],
            text=data.get("text"),
            links=[Link.from_dict(link) for link in data.get("links", [])],
            items=[ListItem.from_dict(item) for item in data.get("items", [])],
        )

    def to_dict(self) -> dict:
        block = {"type": self.type}
        if self.text is not None:
            block["text"] = self.text
        if self.links:
            block["links"] = [link.to_dict() for link in self.links]
        if self.items:
            block["items"] = [item.to_dict() for item in self.items]
        return block


@dataclass
class Section:
    heading: str | None
    blocks: list[Block]

    @classmethod
    def from_dict(cls, data: dict) -> "Section":
        return cls(
            heading=data.get("heading"),
            blocks=[Block.from_dict(block) for block in data["blocks"]],
        )

    def to_dict(self) -> dict:
        return {
            "heading": self.heading,
            "blocks": [block.to_dict() for block in self.blocks],
        }


@dataclass
class ParsedDocument:
    id: str
    title: str
    url: str
    source: str
    sections: list[Section]

    @classmethod
    def from_dict(cls, data: dict) -> "ParsedDocument":
        return cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            source=data["source"],
            sections=[Section.from_dict(section) for section in data["sections"]],
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "sections": [section.to_dict() for section in self.sections],
        }


@dataclass
class Chunk:
    chunk_id: str
    chunk_index: int
    title: str
    url: str
    heading: str | None
    text: str
    content_hash: str
    embedding: list[float] | None = None

    @classmethod
    def from_dict(cls, data: dict) -> "Chunk":
        return cls(
            chunk_id=data["chunk_id"],
            chunk_index=data["chunk_index"],
            title=data["title"],
            url=data["url"],
            heading=data.get("heading"),
            text=data["text"],
            content_hash=data.get("content_hash", hash_chunk_text(data["text"])),
            embedding=data.get("embedding"),
        )

    def to_dict(self) -> dict:
        chunk = {
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "title": self.title,
            "url": self.url,
            "heading": self.heading,
            "text": self.text,
            "content_hash": self.content_hash,
        }
        if self.embedding is not None:
            chunk["embedding"] = self.embedding
        return chunk


def read_parsed_document(path: Path) -> ParsedDocument:
    return ParsedDocument.from_dict(json.loads(path.read_text(encoding="utf-8")))


def write_parsed_document(path: Path, document: ParsedDocument) -> None:
    path.write_text(
        json.dumps(document.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def read_chunks(path: Path) -> list[Chunk]:
    return [Chunk.from_dict(item) for item in json.loads(path.read_text(encoding="utf-8"))]


def write_chunks(path: Path, chunks: list[Chunk]) -> None:
    path.write_text(
        json.dumps([chunk.to_dict() for chunk in chunks], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def hash_chunk_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()
