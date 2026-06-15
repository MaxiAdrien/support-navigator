from graph import app

QUERY = "I lost my job"

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
