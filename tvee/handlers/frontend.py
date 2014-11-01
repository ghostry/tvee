#!/usr/bin/env python
# coding=utf-8

import os
from datetime import datetime
import PyRSS2Gen

from ..models import TVShow
from . import BaseHandler


class MainHandler(BaseHandler):

    def get(self):
        static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)))
        index_file = open(os.path.join(static_path, 'index.html'),
                          'r')
        self.write(index_file.read())
        index_file.close()


class RSSHandler(BaseHandler):

    def initialize(self):
        self.model = TVShow

    def get(self, ids=None):
        is_ed2k = self.get_argument('type', 'magnet') == 'ed2k'
        tvshows = self.model.select()
        if ids:
            ids = ids.split(',')
            tvshows = tvshows.where(self.model.id << ids)
        items = []
        count = 0
        for tvshow in tvshows:
            for episode in tvshow.episodes:
                item = PyRSS2Gen.RSSItem(
                    title=episode.title,
                    link=episode.ed2k if is_ed2k else episode.magnet,
                    guid=PyRSS2Gen.Guid(episode.magnet),
                    pubDate=episode.updated)
                items.append(item)
            count = count + 1
        if count > 0:
            updated = tvshows[0].updated
        else:
            updated = datetime.utcnow()
        rss = PyRSS2Gen.RSS2(
            title='rss',
            link='http://127.0.0.1:8000',
            description='',
            lastBuildDate=updated,
            items=items)
        self.set_header("Content-Type", 'application/rss+xml; charset="utf-8"')
        self.write(rss.to_xml())


class LOGHandler(BaseHandler):

    def get(self, type=None):
        if type:
            log_path = 'log/{}_stdout.log'.format(type)
        else:
            log_path = 'log/stdout.log'
        log = os.path.join(os.path.dirname(os.path.dirname(
            os.path.dirname(__file__))), log_path)
        content = ''
        if os.path.exists(log):
            with open(log, 'r') as f:
                content = f.read()
                content = content.replace('\n', '<br />')
        self.write(content)


__frontend_prefix__ = ''

frontend_handlers = [(__frontend_prefix__ + r"/", MainHandler),
                     (__frontend_prefix__ + r"/rss", RSSHandler),
                     (__frontend_prefix__ + r"/rss/([^/]+)", RSSHandler),
                     (__frontend_prefix__ + r"/log", LOGHandler),
                     (__frontend_prefix__ + r"/log/([^/]+)", LOGHandler)]
