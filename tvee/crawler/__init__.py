#!/usr/bin/env python
# coding=utf-8

import os
from urlparse import urlparse
import re
import imp


def _get_crawler(url):
    host = urlparse(url).hostname
    parts = host.split('.')
    if not parts:
        return
    if parts[0] == 'www':
        parts = parts[1:]
    name = '_'.join(parts)

    try:
        file, filename, data = imp.find_module(name,
                                               [os.path.dirname(__file__)])
        mod = imp.load_module(name, file, filename, data)
        return mod
    except ImportError as e:
        print(e)
        return


_patterns_ = [re.compile('s(\d+)\.?e(\d+)'),
              re.compile('season(\d+)\.?ep(\d+)'),
              re.compile('\D(\d{1,2})x(\d+)'),
              re.compile('\D(\d)(\d{1,2})\D'),
              re.compile('\.s(\d+)'),
              re.compile('series\.?(\d+)')]


def figure_season_and_episode(title):
    season = None
    episode = None
    lower_title = title.lower()
    for pattern in _patterns_:
        m = re.search(pattern, lower_title)
        if m:
            groups = m.groups()
            if len(groups) > 0:
                season = int(groups[0])
            if len(groups) > 1:
                episode = int(groups[1])
            return season, episode
    return season, episode


def crawl(url):
    crawler = _get_crawler(url)
    if not crawler:
        return None, None
    title, episodes = crawler.crawl(url)
    for episode_json in episodes:
        season, episode =\
            figure_season_and_episode(episode_json['title'])
        if not episode_json.get('season', None):
            episode_json['season'] = season
        if not episode_json.get('episode', None):
            episode_json['episode'] = episode
    return title, episodes
