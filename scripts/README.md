# Scripts

Qdrant point management CLI:

```bash
# List a small page of points (ID + payload) to inspect current data.
python3 -m scripts.qdrant_points list

# List more points in one call.
python3 -m scripts.qdrant_points list --limit 50

# Print total number of points in the collection.
python3 -m scripts.qdrant_points count

# Delete specific points by ID.
python3 -m scripts.qdrant_points delete --ids <id1> <id2>
```
