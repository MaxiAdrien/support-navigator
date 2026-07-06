import json

import requests
import streamlit as st
import structlog

from config import API_SHARED_KEY, API_TIMEOUT_SECONDS, API_URL, SUGGESTED_QUERIES
from app.logging_config import configure_logging

# Set up logging
configure_logging()
logger = structlog.get_logger('support_navigator.ui')

# Set up Streamlit page
st.set_page_config(page_title='Support Navigator', layout='wide')

# Set up conversation state
if 'history' not in st.session_state:
    st.session_state.history = []

# Set up current query
query = None

# Sidebar
with st.sidebar:

    # Query suggestions
    st.caption('Try one of these:')
    for index, suggested_query in enumerate(SUGGESTED_QUERIES):
        if st.button(suggested_query, key=f'suggested_query_{index}'):
            query = suggested_query

    st.divider()

    # Start new conversation button
    if st.button('Clear history'):
        st.session_state.history = []
        st.rerun()

st.chat_message('assistant').markdown(
    """👋 **Hi, I'm Support Navigator.**

I can help you understand UK support and your rights using information from Citizens Advice. You can ask me about:

* **Benefits** – Universal Credit, Housing Benefit, JSA, ESA, PIP, DLA, Pension Credit, Child Benefit, Carer's Allowance, Tax Credits, eligibility, payments, and how to claim.
* **Work** – pay, sick pay, working hours, holidays, maternity rights, dismissal, redundancy, discrimination, workplace rights, and the right to work.
* **Money** – cost of living support, debt, food banks, gambling-related financial problems, and help with essential costs.
* **Bills and consumer issues** – energy, water, phone and internet bills, insurance, switching energy supplier, and scams.
* **Housing** – renting, rent increases, eviction, homelessness, housing costs, Council Tax, and housing discrimination.
* **Other support** – health services, immigration-related benefit questions, support after separation, and help for victims of trafficking.
    """
)

# Display previous conversation
for turn in st.session_state.history:
    with st.chat_message('user'):
        st.markdown(turn['user'])

    with st.chat_message('assistant'):
        st.markdown(turn['assistant'])

    if turn['documents']:
        with st.expander('Most relevant web pages'):
            documents = sorted(turn['documents'], key=lambda doc: doc['score'], reverse=True)
            seen_urls = set()

            for doc in documents:
                url = doc.get('url')
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                st.markdown(f"- **{doc.get('title', 'Untitled')}**")
                st.markdown(f"{url}")

# New turn
query = query or st.chat_input('Ask about benefits, food banks, sick pay, right to work in the UK...')

if query:
    # Show user message
    with st.chat_message('user'):
        st.markdown(query)

    # Initialise answer and state (to be streamed from the graph)
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
            with requests.post(
                API_URL,
                json=request_payload,
                headers={'X-API-Key': API_SHARED_KEY},
                stream=True,
                timeout=API_TIMEOUT_SECONDS,
            ) as response:

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
