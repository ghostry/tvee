#!/usr/bin/env python
# coding=utf-8

# import traceback

import os
import subprocess
from threading import Thread
from datetime import datetime, timedelta

from redis import Redis

from rq import Queue
from rq_scheduler import Scheduler

from peewee import IntegrityError

from ..models import TVShow, Episode, Setting
from ..crawler import crawl


_connection_ = Redis()
task_queue = Queue(connection=_connection_)
task_scheduler = Scheduler(connection=_connection_)

_xunlei_lixian_path_ = os.path.join(os.path.dirname(os.path.dirname(
                                    os.path.dirname(__file__))),
                                    'xunlei-lixian', 'lixian_cli.py')
_rename_sh_path_ = os.path.realpath(os.path.join(
                                    os.path.dirname(os.path.dirname(__file__)),
                                    'hooks', 'rename.sh'))
print(_rename_sh_path_)


def download_episode(episode):
    env = os.environ
    env['PATH'] = env['PATH'] + ':/opt/sbin:/opt/bin'
    process = subprocess.Popen([_xunlei_lixian_path_, 'download',
                                episode.ed2k, '--on-download-complete',
                                _rename_sh_path_],
                               env=env)
    thread = Thread(target=process.wait, args=[])
    thread.start()


def crawl_tvshow(tvshow_id, auto_download=True):
    setting = Setting.get()
    if auto_download and setting.xunlei_username and \
       setting.xunlei_password and setting.aria2_rpc_path and\
       setting.output_dir and setting.auto_download:
        auto_download = True
    else:
        auto_download = False
    tvshow = TVShow.get(TVShow.id == tvshow_id)
    title, raw_episodes = crawl(tvshow.url)
    if title:
        tvshow.title = title
        tvshow.save()
    changed = False
    if raw_episodes:
        for raw_episode in raw_episodes:
            need_download = False
            episode_title = raw_episode['title']
            if not tvshow.is_valid_episode(episode_title):
                continue
            season = raw_episode['season']
            if tvshow.season and tvshow.season != season:
                continue
            episode = raw_episode['episode']
            if not season and not episode:
                continue
            episode = Episode(tvshow=tvshow,
                              season=season,
                              episode=episode,
                              title=raw_episode['title'],
                              ed2k=raw_episode['ed2k'],
                              magnet=raw_episode['magnet'])
            try:
                episode.save()
                need_download = True
            except IntegrityError:
                # print(traceback.format_exc())
                try:
                    old_episode = Episode.get(Episode.tvshow == tvshow,
                                              Episode.season ==
                                              raw_episode['season'],
                                              Episode.episode ==
                                              raw_episode['episode'])
                except Episode.DoesNotExist:
                    continue
                if old_episode.update_from(episode):
                    try:
                        old_episode.save()
                        episode = old_episode
                        need_download = True
                    except IntegrityError:
                        continue
            if need_download:
                changed = True
                if auto_download:
                    download_episode(episode)
                    episode.save()
    if changed:
        tvshow.updated = datetime.utcnow()
        tvshow.save()


def remove_crawl_tvshow_job(tvshow_id):
    jobs = task_scheduler.get_jobs()
    for job in jobs:
        if tvshow_id not in job.args:
            continue
        task_scheduler.cancel(job)


def enqueue_crawl_tvshow(tvshow_id, auto_download=True):
    task_queue.enqueue(crawl_tvshow, tvshow_id, auto_download)


def schedule_crawl_tvshow(tvshow_id, interval=8*60*60, auto_download=True):
    remove_crawl_tvshow_job(tvshow_id)
    enqueue_crawl_tvshow(tvshow_id, auto_download)
    job = task_scheduler.schedule(
        scheduled_time=datetime.utcnow() +
        timedelta(seconds=interval),
        func=crawl_tvshow,
        args=[tvshow_id, True],
        interval=interval,
        repeat=None)
    return job


def start_worker():
    from rq import Connection, Worker
    with Connection():
        w = Worker([task_queue])
        w.work()
