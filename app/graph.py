from typing import TypedDict

from dotenv import load_dotenv
from langgraph.graph import START, END, StateGraph
from openai import OpenAI

from config import CHAT_MODEL, PROMPT_PATH
from search_docs import retrieve


class Document(TypedDict):
    title: str
    content: str
    score: float

class State(TypedDict):
    query: str
    documents: list[Document]
    answer: str


load_dotenv()
client = OpenAI()


def retrieve_node(state: State) -> State:
    """Retrieve relevant documents based on the query in the state."""
    documents = retrieve(state['query'])

    return {
        **state,
        'documents': documents,
    }


def answer_node(state: State) -> State:
    """Generate an answer based on the query and retrieved documents."""

    # Format the retrieved documents into a string for the prompt
    documents = '\n\n'.join(
        f"Title: {doc['title']}\nContent: {doc['content']}"
        for doc in state['documents']
    )

    # Read prompt template and format it with the query and documents
    prompt = PROMPT_PATH.read_text(encoding='utf-8').format(
        query=state['query'],
        documents=documents,
    )

    # Generate LLM response
    response = client.responses.create(
        model=CHAT_MODEL,
        input=prompt,
    )

    return {
        **state,
        'answer': response.output_text,
    }


graph = StateGraph(State)

graph.add_node('retrieve', retrieve_node)
graph.add_node('answer', answer_node)

graph.add_edge(START, 'retrieve')
graph.add_edge('retrieve', 'answer')
graph.add_edge('answer', END)

app = graph.compile()
