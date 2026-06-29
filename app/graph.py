import structlog
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.config import get_stream_writer
from langgraph.graph import START, END, StateGraph
from openai import OpenAI

from config import ANSWER_PROMPT_PATH, CHAT_MODEL, REWRITE_PROMPT_PATH
from app.graph_helpers import build_messages, format_documents
from app.search_docs import retrieve
from app.schemas import State


# Set-up
load_dotenv()
client = OpenAI()
logger = structlog.get_logger('support_navigator.graph')

# Load prompts
REWRITE_PROMPT = REWRITE_PROMPT_PATH.read_text(encoding='utf-8')
ANSWER_PROMPT = ANSWER_PROMPT_PATH.read_text(encoding='utf-8')


def rewrite_query(state: State) -> State:
    """Rewrite the latest user query to improve document retrieval."""

    # Build messages for LLM
    messages = build_messages(REWRITE_PROMPT, state)

    # Log LLM call
    logger.info('llm_called', stage='rewrite', model=CHAT_MODEL, messages=len(messages))

    # Call LLM to rewrite the query
    rewritten_query = client.responses.create(model=CHAT_MODEL, input=messages).output_text

    # Log rewritten query
    logger.info('query_rewritten', chars=len(rewritten_query), preview=rewritten_query[:120])

    return {
        **state,
        'rewritten_query': rewritten_query,
    }


def retrieve_node(state: State) -> State:
    """Retrieve relevant documents for the latest user message."""

    # Retrieve documents
    documents = retrieve(state['rewritten_query'])

    # Log retrieval
    logger.info('docs_retrieved', count=len(documents), top_score=documents[0].get('score') if documents else None)

    return {
        **state,
        'documents': documents,
    }


def answer_node(state: State) -> State:
    """Generate an answer based on the conversation and retrieved documents."""

    # Format the retrieved documents into a string for the prompt
    documents = format_documents(state['documents'])

    # Read prompt template and format it with the query and documents
    system_prompt = ANSWER_PROMPT.format(documents=documents)

    # Build conversation history for LLM
    messages = build_messages(system_prompt, state)

    # Log LLM call
    logger.info('llm_called', stage='answer', model=CHAT_MODEL, messages=len(messages), docs=len(state['documents']))

    # Stream LLM response
    writer = get_stream_writer()
    response = client.responses.create(model=CHAT_MODEL, input=messages, stream=True)

    answer = ''

    for event in response:
        if event.type == 'response.output_text.delta':
            answer += event.delta
            writer(event.delta)

    # Log answer generation
    logger.info('answer_generated', chars=len(answer))

    return {
        **state,
        'messages': [
            *state['messages'],
            AIMessage(content=answer),
        ],
    }


graph = StateGraph(State)

graph.add_node('rewrite', rewrite_query)
graph.add_node('retrieve', retrieve_node)
graph.add_node('answer', answer_node)

graph.add_edge(START, 'rewrite')
graph.add_edge('rewrite', 'retrieve')
graph.add_edge('retrieve', 'answer')
graph.add_edge('answer', END)

app = graph.compile()
