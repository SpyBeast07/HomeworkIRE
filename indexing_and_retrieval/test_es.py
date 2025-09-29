# Verify Connection from Python to Elasticsearch
from elasticsearch import Elasticsearch

es = Elasticsearch("http://localhost:9200")
print(es.info())

# Run
# source venv/bin/activate
# python test_es.py