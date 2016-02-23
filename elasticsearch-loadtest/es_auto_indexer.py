from random import randrange 
from time import sleep
from datetime import datetime
from elasticsearch import Elasticsearch
import logging
 
logging.basicConfig(level=logging.DEBUG)

# the list of active nodes, at diff host IPs. Default localhost
es = Elasticsearch(['MININT-418RB8M.us.int.genesyslab.com:9200'])

def generate_doc():
    doc = {
        'id': randrange(0,1000000),
        'timestamp': datetime(2014, 10, randrange(0,31), randrange(0,23), randrange(0,59), 30)
    }
    return doc

def index_doc():
    res = es.index(index="test", doc_type="data", body=generate_doc())
    logging.debug(res['created'])
  
    es.indices.refresh(index="test")


while (True):
    index_doc()
    
    sleep(2)
