#!/usr/bin/env python
# coding=utf-8

from wtforms import form, validators, StringField, TextField, BooleanField,\
    IntegerField

from tornado.web import HTTPError


class BaseForm(form.Form):

    @classmethod
    def from_json_with_validate(cls, json):
        form = cls.from_json(json)
        if not form.validate():
            print(form.errors)
            raise HTTPError(400)
        return form


class SettingForm(BaseForm):

    xunlei_username = StringField('用户名', validators=[validators.required()])
    xunlei_password = StringField('密码', validators=[validators.required()])
    aria2_rpc_path = StringField('Aria2 JSON RPC',
                                 validators=[validators.required()])
    aria2_opts = StringField('Aria2 Options')
    output_dir = StringField('下载目录')
    auto_download = BooleanField(u'自动下载', default=True)


class TVShowForm(BaseForm):

    url = StringField(u'链接',
                      validators=[validators.length(max=2048)])
    blob = TextField(u'过滤')
    season = IntegerField(u'季度')
    refresh_interval = IntegerField(u'刷新频率')
    chinese_only = BooleanField(u'仅中文', default=True)
    allow_repeat = BooleanField(u'允许单集重复', default=False)
