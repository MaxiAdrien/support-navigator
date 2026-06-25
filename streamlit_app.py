import streamlit as st

from app.graph import app

st.set_page_config(
    page_title='Support Navigator',
    layout='wide',
)

st.title('Support Navigator')

query = st.text_input(
    'Ask a question',
    placeholder='Can I get Universal Credit if I work part-time?',
)

if query:
    spinner = st.empty()
    spinner.info('Generating answer...')

    placeholder = st.empty()
    answer = ''

    # Stream answer from the graph
    for mode, chunk in app.stream(
        {'query': query},
        stream_mode=['custom', 'values'],
    ):
        if mode == 'custom':
            spinner.empty()
            answer += chunk
            placeholder.markdown(answer + '▌')

        elif mode == 'values':
            result = chunk

    placeholder.markdown(answer)

    # Retrieved chunks
    st.header('Retrieved Chunks')

    documents = sorted(
        result['documents'],
        key=lambda doc: doc['score'],
        reverse=True,
    )

    for i, doc in enumerate(documents, start=1):
        with st.expander(
            f"{i}. {doc['title']} - {doc['heading'] or 'Introduction'} (score={doc['score']:.3f})",
            expanded=(i == 1),
        ):
            st.markdown(f"**Score:** `{doc['score']:.3f}`")
            st.markdown(f"**Title:** {doc['title']}")
            st.markdown(f"**Heading:** {doc['heading'] or 'N/A'}")
            st.markdown(f"**URL:** {doc['url']}")

            st.markdown('**Text:**')
            st.text(doc['text'])
