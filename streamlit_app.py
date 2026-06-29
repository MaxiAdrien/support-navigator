from uuid import uuid4

import streamlit as st
import structlog
from langchain_core.messages import AIMessage, HumanMessage
from structlog.contextvars import bind_contextvars, clear_contextvars

from app.graph import app
from app.logging_config import configure_logging

# Set up logging
configure_logging()
logger = structlog.get_logger('support_navigator.ui')

# Set up Streamlit page
st.set_page_config(page_title='Support Navigator', layout='wide')
st.title('Support Navigator')

# Set up conversation state
if 'history' not in st.session_state:
    st.session_state.history = []

# Display previous conversation
for turn in st.session_state.history:
    with st.chat_message('user'):
        st.markdown(turn['user'].content)

    with st.chat_message('assistant'):
        st.markdown(turn['assistant'].content)

    if turn['documents']:
        with st.expander('Most relevant pages'):
            documents = sorted(turn['documents'], key=lambda doc: doc['score'], reverse=True)

            for i, doc in enumerate(documents, start=1):
                st.markdown(f"### {i}. {doc['title']}")
                st.markdown(f"**Heading:** {doc['heading'] or 'Introduction'}")
                st.markdown(f"**Relevance score:** `{doc['score']:.3f}`")
                st.markdown(f"**URL:** {doc['url']}")
                st.text(doc['text'])
                st.divider()

# New turn
if query := st.chat_input('Ask a question'):

    # Generate unique request ID for logging
    request_id = str(uuid4())
    clear_contextvars()
    bind_contextvars(request_id=request_id)

    # Log user query
    logger.info('user_query_received', chars=len(query), preview=query[:120])

    # Show user message
    with st.chat_message('user'):
        st.markdown(query)

    # Initialize answer and state (to be streamed from the graph)
    answer, state = '', {}

    # Assistant response
    with st.chat_message('assistant'):

        # Show spinner while generating answer
        spinner = st.empty()
        spinner.info('Generating answer...')

        # Create a placeholder for the answer to be streamed into
        placeholder = st.empty()

        # Prepare messages for the graph
        messages = [
            message
            for turn in st.session_state.history
            for message in (turn['user'], turn['assistant'])
        ]
        human_message = HumanMessage(content=query)
        messages.append(human_message)

        # Stream answer from the graph
        for mode, item in app.stream({'messages': messages}, stream_mode=['custom', 'values']):
            if mode == 'custom':
                spinner.empty()
                answer += item
                placeholder.markdown(answer + '▌')

            elif mode == 'values':
                state = item

        # Display final answer
        placeholder.markdown(answer)

    # Save completed turn
    st.session_state.history.append(
        {
            'user': human_message,
            'assistant': AIMessage(content=answer),
            'documents': state['documents'] if state else [],
        }
    )

    # Re-run Streamlit app to display conversation permanently
    st.rerun()
