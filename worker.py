import os

import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

redis_url = os.getenv('redis://redistogo:7f57ac95140ba927ac4fc4e50de428cc@hammerjaw.redistogo.com:6379/', 'redis://localhost:9594')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
