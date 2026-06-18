from typing import TypedDict

class RetrievedDocument(TypedDict):
    url: str
    title: str
    heading: str | None
    text: str
    score: float
