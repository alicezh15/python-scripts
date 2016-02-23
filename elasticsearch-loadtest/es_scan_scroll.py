from random import randrange 
from time import sleep
from datetime import datetime
from elasticsearch import Elasticsearch
import logging
 
logging.basicConfig(level=logging.INFO)

# the list of active nodes, at diff host IPs. Default localhost
es_data = Elasticsearch(['MININT-418RB8M.us.int.genesyslab.com:9200'])

query={"query" : {"match_all" : {}}}
scanResp= es_data.search(index="test", doc_type="data", body=query, search_type="scan", scroll="10m", size=10)  

results = []
hits = []

while (True) :
    try:
        scrollId= scanResp['_scroll_id']
        response= es_data.scroll(scroll_id=scrollId, scroll= "10m")
        
        hits = response['hits']['hits']

        results.extend(hits)
        print ('Results: ' + len(results).__str__())
        
        sleep(5)

    except:
        break

print ('Final hits scrolled: ' + len(results).__str__())
    