import os
import redis
from rq import Worker, Queue, Connection
from dotenv import load_dotenv
from app import create_minimal_app, db, connect_with_retry

import logging

logger = logging.getLogger('BDB-2EB')

load_dotenv()

listen = ['default']

app = create_minimal_app()
app.app_context().push()

logger.info('Initialized worker app')

connect_with_retry(app)

redis_url = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
conn = redis.from_url(redis_url)
# logger.info(f'Worker connected to REDIS: {redis_url}')

# if __name__ == '__main__':
#     with Connection(conn):
#         worker = Worker(list(map(Queue, listen)), default_worker_ttl=600)
#         worker.work()


def process_jobs():
    with Connection(conn):
        queue = Queue('default')
        job = queue.dequeue()
        if job:
            job.perform()

if __name__ == '__main__':
    process_jobs()
