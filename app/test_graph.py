# python -m app.test_graph

from app.graph import app

QUERY = "Can I get sick pay if I'm on maternity leave?"

result = app.invoke(
    {
        "query": QUERY,
        "documents": [],
        "answer": "",
    }
)

print('Query:', result['query'])
print('Retrieved Documents:', result['documents'])
print('Answer:', result['answer'])
