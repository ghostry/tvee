#!/usr/bin/env python
# coding=utf-8

import os

from fabric.context_managers import cd
from fabric.api import run, env
from fabric.contrib import files

env.shell = 'sh -c'
env.path = '$PATH:/opt/bin:/usr/local/bin'


def deploy(app_dir):
    if not files.exists(app_dir):
        app_dir_dir = os.path.dirname(app_dir)
        run('mkdir -p ' + app_dir_dir)
        with cd(app_dir_dir):
            run('git clone https://github.com/exherb/tvee.git ' +
                os.path.basename(app_dir))
            run('pip install supervisor')
        with cd(app_dir):
            run('cp config.sample.conf config.conf')
            run('supervisord -c production/supervisord.conf')
    with cd(app_dir):
        run('pip install -r tvee/requirements.txt')
        run('git reset --hard')
        run('git pull origin master')
        run('supervisorctl -c production/supervisord.conf restart ' +
            'tvee tvee_worker')
