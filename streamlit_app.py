import json

import requests
import streamlit as st
import structlog

from config import API_TIMEOUT_SECONDS, API_URL
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
        st.markdown(turn['user'])

    with st.chat_message('assistant'):
        st.markdown(turn['assistant'])

    if turn['documents']:
        with st.expander('Most relevant pages'):
            documents = sorted(turn['documents'], key=lambda doc: doc['score'], reverse=True)

            for i, doc in enumerate(documents, start=1):
                st.markdown(f"### {i}. {doc['title']}")
                st.markdown(f"**Heading:** {doc['heading'] or 'Introduction'}")
                st.markdown(f"**Relevance score:** `{doc['score']:.3f}`")
                st.markdown(f"**URL:** {doc['url']}")
                st.divider()

# New turn
if query := st.chat_input('Ask a question'):

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

        # Prepare payload for API
        request_payload = {
            'query': query,
            'history': [
                {'role': role, 'content': turn[role]}
                for turn in st.session_state.history
                for role in ('user', 'assistant')
            ],
        }

        # Send request to API
        try:
            with requests.post(API_URL, json=request_payload, stream=True, timeout=API_TIMEOUT_SECONDS) as response:

                # Check for HTTP errors
                response.raise_for_status()

                # Stream response from API
                for line in response.iter_lines(decode_unicode=True):
                    if not line:
                        continue

                    event = json.loads(line)

                    if event.get('type') == 'token':
                        spinner.empty()
                        answer += event['content']
                        placeholder.markdown(answer + '▌')

                    elif event.get('type') == 'final':
                        state = event
                        spinner.empty()

                    elif event.get('type') == 'error':
                        spinner.empty()
                        logger.error('api_stream_error_event')
                        st.error('Sorry, something went wrong while generating the response. Please try again.')
                        st.stop()

        except requests.RequestException:
            spinner.empty()
            logger.exception('api_request_failed')
            st.error('Could not reach the assistant service. Please try again.')
            st.stop()

        # Display final answer
        placeholder.markdown(answer)

    # Save completed turn
    st.session_state.history.append(
        {
            'user': query,
            'assistant': answer,
            'documents': state['documents'] if state else [],
        }
    )

    # Re-run Streamlit app to display conversation permanently
    st.rerun()
