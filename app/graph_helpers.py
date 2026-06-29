from langchain_core.messages import HumanMessage, SystemMessage

from app.schemas import RetrievedDocument, State


def build_messages(prompt: str, state: State) -> list[dict[str, str]]:
    """Build the message history for the LLM, including the system prompt and user/assistant messages."""
    return [
        {'role': 'system', 'content': prompt},
        *(
            {
                'role': 'user' if isinstance(message, HumanMessage) else 'assistant',
                'content': message.content,
            }
            for message in state['messages']
            if not isinstance(message, SystemMessage)
        ),
    ]


def format_documents(documents: list[RetrievedDocument]) -> str:
    """Format retrieved documents into a single prompt-friendly string."""
    return "\n\n---\n\n".join(
        (
            f"Title: {doc['title']}\n"
            f"URL: {doc['url']}\n"
            f"Heading: {doc['heading'] or 'N/A'}\n"
            f"Text: {doc['text']}"
        )
        for doc in documents
    )
