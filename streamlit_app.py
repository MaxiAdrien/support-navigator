import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from app.graph import app

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
    human_message = HumanMessage(content=query)

    # Show user message
    with st.chat_message('user'):
        st.markdown(query)

    answer, state = '', {}

    # Assistant response
    with st.chat_message('assistant'):
        spinner = st.empty()
        spinner.info('Generating answer...')

        placeholder = st.empty()

        # Prepare messages for the graph
        messages = [
            message
            for turn in st.session_state.history
            for message in (turn['user'], turn['assistant'])
        ]
        messages.append(human_message)

        # Stream answer from the graph
        for mode, item in app.stream({'messages': messages}, stream_mode=['custom', 'values']):
            if mode == 'custom':
                spinner.empty()
                answer += item
                placeholder.markdown(answer + '▌')

            elif mode == 'values':
                state = item

        placeholder.markdown(answer)

    # Save completed turn
    st.session_state.history.append(
        {
            'user': human_message,
            'assistant': AIMessage(content=answer),
            'documents': state['documents'] if state else [],
        }
    )

    st.rerun()
