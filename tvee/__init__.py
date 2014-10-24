#!/usr/bin/env python
# coding=utf-8

import os
import sys

import wtforms_json

from playhouse.sqlite_ext import SqliteExtDatabase

import tornado.ioloop
import tornado.web
from tornado.options import options, define

from .models import database_proxy, TVShow, Episode, Setting
from .handlers import api_handlers, frontend_handlers
from .tasks import start_worker

define('debug', default=True, help='开启调试', type=bool)
define('port', default=8000, help='端口', type=int)
define('cookie_secret', default='<random>', help='Cookie 密钥', type=str)


__all__ = ['main']


def create_application():
    wtforms_json.init()

    static_path = os.path.join(os.path.dirname(__file__), "static")
    application = tornado.web.Application(
        api_handlers + frontend_handlers,
        debug=options.debug,
        cookie_secret=options.cookie_secret,
        static_path=static_path)

    # config database
    src_dir = os.path.dirname(os.path.dirname(__file__))
    database = SqliteExtDatabase(os.path.join(src_dir, 'database.db'),
                                 threadlocals=True)
    database_proxy.initialize(database)
    # database.connect()

    return application


__tables__ = [TVShow, Episode, Setting]


def clear_database():
    database_proxy.drop_tables(__tables__,
                               safe=True)


def prepare_database(default=None):
    database_proxy.create_tables(__tables__,
                                 safe=True)
    if not Setting.select().count():
        setting = Setting()
        setting.save()


def migrate_database():
    pass


def main():
    tornado.options.parse_config_file("config.conf")
    tornado.options.parse_command_line()
    application = create_application()
    if len(sys.argv) > 1:
        if sys.argv[1] == 'init':
            root_dir = os.path.dirname(os.path.dirname(__file__))
            log_dir = os.path.join(root_dir, 'log')
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            tmp_dir = os.path.join(root_dir, 'tmp')
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            prepare_database()
            return
        elif sys.argv[1] == 'clear':
            clear_database()
            return
        elif sys.argv[1] == 'migrate':
            migrate_database()
            return
        elif sys.argv[1] == 'worker':
            start_worker()
            return
    setting = Setting.get()
    setting.reconfig()
    application.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
