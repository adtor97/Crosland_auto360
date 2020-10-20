import os

import redis
from rq import Worker, Queue, Connection

listen = ['high', 'default', 'low']

redis_url = os.getenv('redis://redistogo:7acd2afb36ddae5c4d83946cc59fff56@barb.redistogo.com:10270/', 'redis://localhost:10270')

conn = redis.from_url(redis_url)

if __name__ == '__main__':
    with Connection(conn):
        worker = Worker(map(Queue, listen))
        worker.work()
