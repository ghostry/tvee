#!/usr/bin/env python
# coding=utf-8

from redis import Redis

from rq import Queue
from rq_scheduler import Scheduler


_connection_ = Redis()
task_queue = Queue(connection=_connection_)
task_scheduler = Scheduler(connection=_connection_)
