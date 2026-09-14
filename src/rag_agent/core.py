import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def timing(func):
    def wrapper(*args, **kwargs):
        
        start = time.perf_counter()
        result = func(*args, **kwargs)

        elapsed = time.perf_counter() - start
        logging.info("do_work completed in %.4f seconds", elapsed)
        return result
    return wrapper

@timing
def do_work():
    time.sleep(0.1)

do_work()

class DocumentNotFoundError(Exception):
    pass

try:
    raise DocumentNotFoundError("Missing document")
except DocumentNotFoundError as e:
    logger.error("%s", e)

class DocumentSession:
    def __enter__(self):
        print("Entering session") 
    def __exit__(self, exc_type, exc_value, traceback):
        print("Exiting session")


with DocumentSession():
    print("Processing document")

def document_ids():
    for i in range(5):
        yield i

for doc_id in document_ids():
    print(doc_id)
