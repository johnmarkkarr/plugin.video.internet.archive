from __future__ import unicode_literals

import xbmcgui
import sys
import requests
import md5
from bs4 import BeautifulSoup

from common import buildURL, makeRequest

class Pager(object):
    def __init__(self, args):
        self.page = int(args.get('page', 1))
        self.idx = int(args.get('idx', 0))
        if 25 * self.idx == 75:
            self.idx = 0
            self.page += 1
        self.start = self.idx * 25 + 1

def buildListFromList(addon, src):
    pager = Pager(addon.args)
    length = len(src)
    stop = False
    if not length or pager.page * 75 >= length:
        stop = True
    items = []
    for item in src:
        li = xbmcgui.ListItem(item['title'], iconImage='DefaultFolder.png')
        if item['folder']:
            items.append((item['url'], li, True))
        else:
            items.append((item['url'], li, False))
        actions = []
        actions.append(('Remove from favorites', 'RunPlugin(' + buildURL(addon.home, {'kind': 'removeFavorite', 'id': md5.md5(item['title']).hexdigest(), 'base': addon.args['base']}) + ')'))
        li.addContextMenuItems(actions, replaceItems=True)
    if not stop:
        url = buildURL(addon.home, {'kind': 'favorites', 'name': 'next page', 'page': pager.page, 'idx': pager.idx + 1, 'base': addon.args['base']})
        li = xbmcgui.ListItem('next page', iconImage='DefaultFolder.png')
        items.append((addon.url, li, True))
    return items

def buildListFromURL(addon, url=None, query={}):
    error = False
    pager = Pager(addon.args)
    if not 'url' in addon.args:
        thisURL = url
    else:
        thisURL = addon.args['url']
    query.update({'page': str(pager.page)})
    url = buildURL(addon.url + '/' + thisURL, query)
    success, response = makeRequest(url)
    if not success:
        xbmcgui.Dialog().notification('Results', response, xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit(1)
    soup = BeautifulSoup(response.text, 'html.parser')
    length = int(addon.args.get('length', 0))
    if not length:
        results = soup.find_all(class_='co-top-row')
        length = int(results[0].contents[0].strip().replace(',', ''))
    stop = False
    if not length or pager.page * 75 >= length:
        stop = True
    items = []
    for item in soup.find_all('div', class_='item-ia')[pager.start:pager.start + 25]:
        try:
            if 'collection-ia' in item['class']:
                info = item.find(class_='collection-title').find('a')
                title = [string for string in info.stripped_strings][0].encode('utf-8')
                url = buildURL(addon.home, {'kind': 'browse', 'name': title, 'url': info['href'], 'base': addon.args['base']})
            else:
                info = item.find(class_='item-ttl').find('a')
                title = info['title'].encode('utf-8')
                url = buildURL(addon.home, {'kind': 'item', 'name': title, 'url': info['href'].replace('/details', '/metadata', 1), 'base': addon.args['base'], 'sort': 0})
            li = xbmcgui.ListItem(title, iconImage='DefaultFolder.png')
            actions = []
            actions.append(('Add to favorites', 'RunPlugin(' + buildURL(addon.home, {'kind': 'addFavorite', 'url': url, 'title': title, 'base': addon.args['base'], 'folder': 1}) + ')'))
            li.addContextMenuItems(actions, replaceItems=True)
            items.append((url, li, True))
        except:
            error = True
    if not stop:
        url = buildURL(addon.home, {'kind': 'browse', 'name': 'Next Page', 'url': thisURL, 'page': pager.page, 'idx': pager.idx + 1, 'base': addon.args['base'], 'length': length})
        li = xbmcgui.ListItem('Next Page', iconImage='DefaultFolder.png')
        items.append((url, li, True))
    if error:
        xbmcgui.Dialog().notification('Results', 'Some results had errors and were skipped.', xbmcgui.NOTIFICATION_ERROR, 5000)
    return items
