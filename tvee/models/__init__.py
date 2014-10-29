#!/usr/bin/env python
# coding=utf-8

import os
import json
from datetime import datetime
from urlparse import urlparse
from urllib2 import unquote

from peewee import Field, Model, Proxy, PrimaryKeyField, CharField,\
    ForeignKeyField, BooleanField, IntegerField, SelectQuery, DateTimeField

from tornado.web import HTTPError

database_proxy = Proxy()


class JSONField(Field):

    db_field = 'text'
    _json_type_ = None

    def db_value(self, value):
        if value:
            if not isinstance(value, self._json_type_):
                raise RuntimeError()
        else:
            value = self._json_type_()
        return json.dumps(value)

    def python_value(self, value):
        if not value:
            return self._json_type_()
        value = json.loads(value)
        if not isinstance(value, self._json_type_):
            value = self._json_type_()
        return value


class JSONListField(JSONField):

    _json_type_ = list


class JSONDictField(JSONField):

    _json_type_ = dict


def property_to_json(property_value, is_detail=False,
                     properties=None):
    if isinstance(property_value, datetime):
        property_value = property_value.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    elif isinstance(property_value, ResourceModel):
        property_value = property_value.get_json(is_detail, properties)
    elif isinstance(property_value, Exception):
        property_value = str(property_value)

    if isinstance(property_value, list) or isinstance(property_value, set) or\
       isinstance(property_value, SelectQuery):
        property_value = list_property_to_json(property_value, is_detail,
                                               properties)
    elif isinstance(property_value, dict):
        property_value = dict_property_to_json(property_value, is_detail,
                                               properties)
    return property_value


def list_property_to_json(list_property_value, is_detail=False,
                          properties=None):
    json_value = []
    for value in list_property_value:
        json_value.append(property_to_json(value, is_detail, properties))
    return json_value


def dict_property_to_json(dict_property_value, is_detail=False,
                          properties=None):
    json_value = {}
    for key, value in dict_property_value.items():
        json_value[key] = property_to_json(value, is_detail, properties)
    return json_value


class ResourceModel(Model):

    id = PrimaryKeyField()

    _properties_ = []
    _detail_properties_ = []

    class Meta:
        database = database_proxy
        order_by = ['-id']

    @classmethod
    def get_with_validate(cls, *query, **kwargs):
        try:
            resource = super(ResourceModel, cls).get(*query, **kwargs)
        except cls.DoesNotExist:
            raise HTTPError(404)
        return resource

    def get_json(self, is_detail, properties=None):
        if not properties:
            if is_detail:
                properties = self._detail_properties_
            else:
                properties = self._properties_
        json_value = {}
        for property_name in properties:
            if not hasattr(self, property_name):
                continue
            property_value = getattr(self, property_name)
            json_value[property_name] = property_to_json(property_value,
                                                         is_detail)
        return json_value

    @property
    def json(self):
        return self.get_json(False)

    @property
    def detail_json(self):
        return self.get_json(True)


_xunlei_lixian_path_ = os.path.join(os.path.dirname(os.path.dirname(
                                    os.path.dirname(__file__))),
                                    'xunlei-lixian', 'lixian_cli.py')
_rename_sh_path_ = os.path.realpath(os.path.join(
                                    os.path.dirname(os.path.dirname(__file__)),
                                    'hooks', 'rename.sh'))


class Setting(ResourceModel):

    _properties_ = ['xunlei_username', 'xunlei_password', 'aria2_rpc_path',
                    'aria2_opts', 'output_dir', 'auto_download']

    xunlei_username = CharField(default="")
    xunlei_password = CharField(default="")
    aria2_rpc_path = CharField(default='http://localhost:6800/rpc')
    aria2_opts = CharField(null=True)
    output_dir = CharField(null=True)
    auto_download = BooleanField(default=True)

    def reconfig(self):
        os.system('python {0} config username "{1}"'.
                  format(_xunlei_lixian_path_, self.xunlei_username))
        os.system('python {0} config password "{1}"'.
                  format(_xunlei_lixian_path_, self.xunlei_password))
        os.system('python {0} config tool aria2-rpc'.
                  format(_xunlei_lixian_path_))
        os.system('python {0} config -- aria2-rpc "{1}"'.
                  format(_xunlei_lixian_path_, self.aria2_rpc_path))
        aria2_opts = 'on-download-complete=' + _rename_sh_path_
        if self.aria2_opts:
            aria2_opts = aria2_opts + ' ' + self.aria2_opts
        os.system('python {0} config -- aria2c-rpc-opts "{1}"'.
                  format(_xunlei_lixian_path_, aria2_opts))
        if self.output_dir:
            os.system('python {0} config output-dir "{1}"'.
                      format(_xunlei_lixian_path_, self.output_dir))
        os.system('python {0} config continue'.
                  format(_xunlei_lixian_path_))
        os.system('python {0} config delete'.
                  format(_xunlei_lixian_path_))


class TVShow(ResourceModel):

    _properties_ = ['id', 'title', 'episodes_count']
    _detail_properties_ = ['id', 'title', 'url', 'blob', 'allow_repeat',
                           'episodes', 'chinese_only', 'season',
                           'refresh_interval']
    _chinese_indicators_ = [u'中', u'双语']

    class Meta:
        order_by = ['-updated', '-id']

    url = CharField(max_length=2048, unique=True, index=True)
    season = IntegerField(null=True)
    refresh_interval = IntegerField(null=True)
    title = CharField(index=True)
    blob = CharField()
    chinese_only = BooleanField(default=True)
    allow_repeat = BooleanField(default=False)
    plugins = JSONListField(null=True)
    updated = DateTimeField(null=True, index=True)

    def is_valid_episode(self, episode_title):
        if self.chinese_only:
            has_chinese = False
            for chinese_indicator in self._chinese_indicators_:
                if episode_title.find(chinese_indicator) != -1:
                    has_chinese = True
                    break
            if not has_chinese:
                return False
        if self.blob and episode_title.find(self.blob) == -1:
            return False
        return True

    def __setattr__(self, key, value):
        if key == 'url':
            if value.find('http://') != 0 and value.find('https://') != 0:
                value = 'http://' + value
            parts = urlparse(value)
            host = ''.join([x for x in parts.hostname.split('.')[0:-1]
                            if x != 'www'])
            resource = parts.path.split('/')[-1]
            if not self.title:
                self.title = ':'.join([host, resource])
        super(TVShow, self).__setattr__(key, value)

    @property
    def episodes_count(self):
        return self.episodes.count()


class Episode(ResourceModel):

    _properties_ = ['id', 'title', 'season', 'episode', 'ed2k', 'magnet',
                    'is_downloaded']
    _detail_properties_ = _properties_
    _format_priorities_ = ['1080p', '720p', 'hdtv', 'hr-hdtv', 'mp4']

    class Meta:
        order_by = ['-season', '-episode', '-updated', '-id']

    tvshow = ForeignKeyField(TVShow, related_name='episodes')
    title = CharField()
    season = IntegerField(null=True, index=True)
    episode = IntegerField(null=True, index=True)
    unique = CharField(null=True, unique=True)
    ed2k = CharField(null=True, max_length=2048)
    ed2k_unique = CharField(null=True, unique=True)
    magnet = CharField(null=True, max_length=2048)
    magnet_unique = CharField(null=True, unique=True)
    updated = DateTimeField(null=True, index=True)

    def __init__(self, *args, **kwargs):
        super(Episode, self).__init__(*args, **kwargs)
        if kwargs:
            self.season = kwargs['season']
            self.episode = kwargs['episode']
            self.ed2k = kwargs['ed2k']
            self.magnet = kwargs['magnet']
            self.updated = datetime.utcnow()

    @property
    def is_downloaded(self):
        setting = Setting.get()
        file_name = self.ed2k.split('|')[2]
        if isinstance(file_name, unicode):
            file_name = file_name.encode('utf-8')
        file_name = unquote(file_name).decode('utf-8')
        file_path = os.path.join(setting.output_dir, file_name)
        file_ariac_path = file_path + u'.aria2'
        return os.path.exists(file_path) and \
            not os.path.exists(file_ariac_path)

    def __setattr__(self, key, value):
        if value:
            try:
                self.tvshow
            except TVShow.DoesNotExist:
                pass
            else:
                if key == 'season' or key == 'episode':
                    if key == 'season':
                        season = value
                        episode = self.episode
                    else:
                        season = self.season
                        episode = value
                    if not season:
                        season = ''
                    if not episode:
                        episode = ''
                    if season or episode and not self.tvshow.allow_repeat:
                        self.unique = u'{0}:{1}:{2}'.format(self.tvshow.id,
                                                            season, episode)
                elif key == 'ed2k':
                    self.ed2k_unique = u'{0}:{1}'.format(self.tvshow.id, value)
                elif key == 'magnet':
                    self.magnet_unique = u'{0}:{1}'.format(self.tvshow.id,
                                                           value)
        super(Episode, self).__setattr__(key, value)

    def update_from(self, episode):
        if self.ed2k == episode.ed2k and\
           self.magnet == episode.magnet:
            return False
        need_update = False
        left_lower_title = self.title.lower()
        right_lower_title = episode.title.lower()
        for priority in self._format_priorities_:
            left = left_lower_title.find(priority) != -1
            right = right_lower_title.find(priority) != -1
            if left and not right:
                return False
            if right and not left:
                print(left_lower_title, right_lower_title, priority)
                need_update = True
                break
        if need_update:
            self.title = episode.title
            self.ed2k = episode.ed2k
            self.magnet = episode.magnet
            self.updated = datetime.utcnow()
        return need_update
