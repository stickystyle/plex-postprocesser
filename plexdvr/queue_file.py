#!/usr/bin/env python
import re
import datetime
import time
import subprocess
import tempfile
import os
import shutil
import logging
import json
import sys

from rq import Queue
from redis import StrictRedis

RQ_TIMEOUT = os.getenv("RQ_TIMEOUT", "6h")
RQ_REDIS_URL = os.getenv("RQ_REDIS_URL", "redis://localhost:6379")

logging.basicConfig(level=logging.INFO)

r = StrictRedis().from_url(url=RQ_REDIS_URL)

transcode_queue = Queue('transcode', connection=r)
default_queue = Queue(connection=r)


if __name__ == '__main__':
    input_file = '/data/XXXX/.grab/aa7001b606692bd67acbf97bacc4046311674b6c/{}'.format(sys.argv[1])
    default_queue.enqueue('postprocess.post_process', input_file, result_ttl="6h", timeout="6h")
