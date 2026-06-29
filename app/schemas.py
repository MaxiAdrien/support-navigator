from typing import TypedDict

from langchain_core.messages import BaseMessage

class RetrievedDocument(TypedDict):
    url: str
    title: str
    heading: str | None
    text: str
    score: float

class State(TypedDict):
    messages: list[BaseMessage]
    rewritten_query: str
    documents: list[RetrievedDocument]
