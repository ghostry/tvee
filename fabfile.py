#!/usr/bin/env python
# coding=utf-8

import os

from fabric.context_managers import cd
from fabric.api import sudo, env
from fabric.contrib import files

env.shell = 'sh -c'
env.path = '$PATH:/opt/bin:/usr/local/bin'


def deploy(app_dir):
    if not files.exists(app_dir):
        app_dir_dir = os.path.dirname(app_dir)
        sudo('mkdir -p ' + app_dir_dir)
        with cd(app_dir_dir):
            sudo('git clone https://github.com/exherb/tvee.git ' +
                 os.path.basename(app_dir))
            sudo('pip install supervisor')
        with cd(app_dir):
            sudo('supervisord -c production/supervisord.conf')
    with cd(app_dir):
        sudo('pip install -r tvee/requirements.txt')
        sudo('git reset --hard')
        sudo('git pull origin master')
        sudo('supervisorctl -c production/supervisord.conf restart ' +
             'tvee tvee_worker')
