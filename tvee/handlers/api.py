#!/usr/bin/env python
# coding=utf-8

from tornado.web import HTTPError

from ..models import TVShow, Setting, Episode, list_property_to_json
from ..forms import TVShowForm, SettingForm
from ..tasks import enqueue_crawl_tvshow, schedule_crawl_tvshow,\
    remove_crawl_tvshow_job, download_episode
from . import BaseHandler


class SettingHandler(BaseHandler):

    def initialize(self):
        self.model = Setting

    def get(self):
        setting = Setting.get()
        self.finish_with_json(setting.json)

    def put(self):
        form = SettingForm.from_json_with_validate(self.body_arguments)
        setting = Setting.get()
        form.populate_obj(setting)
        setting.reconfig()
        setting.save()
        self.finish_with_json(setting.json)


class TVShowHandler(BaseHandler):

    def initialize(self):
        self.model = TVShow

    def get(self, id=None):
        if id:
            tvshow = self.model.get_with_validate(self.model.id == id)
            self.finish_with_json(tvshow.detail_json)
        else:
            self.finish_with_json(list_property_to_json(self.list_query))

    def put(self, id, action=None):
        if id == 'refresh':
            for tvshow in self.list_query:
                enqueue_crawl_tvshow(tvshow.id)
            self.finish_with_json({'status': 200})
        else:
            tvshow = self.model.get_with_validate(self.model.id == id)
            if action is None:
                form = TVShowForm.from_json_with_validate(self.body_arguments)
                old_refresh_interval = tvshow.refresh_interval
                form.populate_obj(tvshow)
                tvshow.save()
                if old_refresh_interval == tvshow.refresh_interval:
                    enqueue_crawl_tvshow(tvshow.id)
                else:
                    schedule_crawl_tvshow(tvshow.id,
                                          tvshow.refresh_interval*60*60)
            elif action == 'pausing':
                remove_crawl_tvshow_job(tvshow.id)
            elif action == 'resuming':
                schedule_crawl_tvshow(tvshow.id,
                                      tvshow.refresh_interval*60*60)
            else:
                raise HTTPError(404)
            self.finish_with_json(tvshow.detail_json)

    def post(self):
        form = TVShowForm.from_json_with_validate(self.body_arguments)
        tvshow = TVShow()
        form.populate_obj(tvshow)
        tvshow.save()
        self.finish_with_json(tvshow.detail_json)
        schedule_crawl_tvshow(tvshow.id, tvshow.refresh_interval*60*60, False)

    def delete(self, id):
        self.delete_by_id(id)
        remove_crawl_tvshow_job(id)


class EpisodeHandler(BaseHandler):

    def initialize(self):
        self.model = Episode

    def put(self, id, action):
        episode = self.model.get_with_validate(self.model.id == id)
        if action == 'downloading':
            download_episode(episode)
        else:
            raise HTTPError(404)
        episode.save()
        self.finish_with_json(episode.json)

__api_prefix__ = '/api'

api_handlers = [(__api_prefix__ + r'/tvshows', TVShowHandler),
                (__api_prefix__ + r'/tvshows/([^/]+)', TVShowHandler),
                (__api_prefix__ + r'/tvshows/([^/]+)/([^/]+)', TVShowHandler),
                (__api_prefix__ + r'/episodes/([^/]+)/([^/]+)',
                 EpisodeHandler),
                (__api_prefix__ + r'/setting', SettingHandler)]
