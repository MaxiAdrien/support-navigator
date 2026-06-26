from typing import TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.config import get_stream_writer
from langgraph.graph import START, END, StateGraph
from openai import OpenAI

from config import CHAT_MODEL, PROMPT_PATH
from app.schemas import RetrievedDocument
from app.search_docs import retrieve


class State(TypedDict):
    messages: list[BaseMessage]
    documents: list[RetrievedDocument]


load_dotenv()
client = OpenAI()

# Load prompt
SYSTEM_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


def retrieve_node(state: State) -> State:
    """Retrieve relevant documents for the latest user message."""
    query = next(
        message.content
        for message in reversed(state['messages'])
        if isinstance(message, HumanMessage)
    )

    documents = retrieve(query)

    return {
        **state,
        'documents': documents,
    }


def answer_node(state: State) -> State:
    """Generate an answer based on the conversation and retrieved documents."""

    # Format the retrieved documents into a string for the prompt
    documents = "\n\n---\n\n".join(
        (
            f"Title: {doc['title']}\n"
            f"URL: {doc['url']}\n"
            f"Heading: {doc['heading'] or 'N/A'}\n"
            f"Text: {doc['text']}"
        )
        for doc in state['documents']
    )

    # Read prompt template and format it with the query and documents
    system_prompt = SYSTEM_PROMPT.format(documents=documents)

    history = [
        {'role': 'system', 'content': system_prompt},
        *(
            {
                'role': ('user' if isinstance(message, HumanMessage) else 'assistant'),
                'content': message.content,
            }
            for message in state['messages']
            if not isinstance(message, SystemMessage)
        ),
    ]

    # Stream LLM response
    writer = get_stream_writer()
    response = client.responses.create(model=CHAT_MODEL, input=history, stream=True)

    answer = ''

    for event in response:
        if event.type == 'response.output_text.delta':
            answer += event.delta
            writer(event.delta)

    return {
        **state,
        'messages': [
            *state['messages'],
            AIMessage(content=answer),
        ],
    }


graph = StateGraph(State)

graph.add_node('retrieve', retrieve_node)
graph.add_node('answer', answer_node)

graph.add_edge(START, 'retrieve')
graph.add_edge('retrieve', 'answer')
graph.add_edge('answer', END)

app = graph.compile()
