#!/usr/bin/env python
# coding=utf-8

import urllib2
from bs4 import BeautifulSoup


def crawl(url):
    soup = BeautifulSoup(urllib2.urlopen(url).read())
    title = soup.title.text.split('|', 1)[0].strip()
    episodes = []
    resources = soup.select('dl.resource-list')
    for resource in resources:
        resource_items = resource.select('dd.resource-item')
        for resource_item in resource_items:
            infos = resource_item.select('a')
            title_infos = infos[:2]
            episode_title = ''.join([a.text.strip()
                                     for a in title_infos])
            link_infos = infos[2:]
            ed2k = None
            magnet = None
            for link_info in link_infos:
                type = link_info.get('data-download-type', None)
                link = link_info.get('href', None)
                if type == '1':
                    ed2k = link
                elif type == '2':
                    magnet = link
            episodes.append({
                'title': episode_title,
                'ed2k': ed2k,
                'magnet': magnet
            })
    return title, episodes
