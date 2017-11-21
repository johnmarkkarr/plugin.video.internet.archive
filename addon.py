from __future__ import unicode_literals

import xbmc
import xbmcgui
import xbmcplugin
import os
import sys
import json
import urllib
import urlparse
import requests
import md5

import lists
from common import buildURL, makeRequest, Media, Addon

addon = Addon(*sys.argv)
kind = addon.args.get('kind', None)

if not kind:
    content_type = addon.args.get('content_type', None)
    items = []
    for action in addon.ACTIONS:
        url = buildURL(addon.home, {'kind': action.lower(), 'name': action, 'base': addon.TYPES[content_type]})
        li = xbmcgui.ListItem(action, iconImage='DefaultFolder.png')
        items.append((url, li, True))
    xbmcplugin.addDirectoryItems(addon.handle, items)
    xbmcplugin.endOfDirectory(addon.handle)
elif kind == 'search':
    keyboard = xbmc.Keyboard('', 'Search')
    keyboard.doModal()
    search = ''
    if keyboard.isConfirmed():
        search = keyboard.getText()
    if not search:
        sys.exit(1)
    if not 'url' in addon.args:
        url = '/details/' + addon.MEDIA[int(addon.args['base'])]
    items = lists.buildListFromURL(addon, url, {'and[]': search})
    xbmcplugin.addDirectoryItems(addon.handle, items)
    xbmcplugin.endOfDirectory(addon.handle)
elif kind == 'browse':
    try:
        url = None
        if not 'url' in addon.args:
            url = '/details/' + addon.MEDIA[int(addon.args['base'])]
        items = lists.buildListFromURL(addon, url)
    except Exception as e:
        xbmcgui.Dialog().notification('Results', 'Could not display results.', xbmcgui.NOTIFICATION_ERROR, 5000)
    xbmcplugin.addDirectoryItems(addon.handle, items)
    xbmcplugin.endOfDirectory(addon.handle)
elif kind == 'favorites':
    path = os.path.join(xbmc.translatePath(addon.addon.getAddonInfo('profile')), 'favorites.json')
    try:
        file = open(path, 'r')
    except IOError:
        file = open(path, 'w')
    try:
        favorites = json.load(file)
    except:
        favorites = [[], [], []]
    items = lists.buildListFromList(addon, favorites[int(addon.args['base'])])
    xbmcplugin.addDirectoryItems(addon.handle, items)
    xbmcplugin.endOfDirectory(addon.handle)
    file.close()
elif kind == 'addFavorite':
    path = os.path.join(xbmc.translatePath(addon.addon.getAddonInfo('profile')), 'favorites.json')
    try:
        file = open(path, 'r')
    except IOError:
        file = open(path, 'w')
    try:
        favorites = json.load(file)
    except:
        favorites = [[], [], []]
    file.close()
    keyboard = xbmc.Keyboard(addon.args['title'], 'Name it')
    keyboard.doModal()
    title = ''
    if keyboard.isConfirmed():
        title = keyboard.getText()
    favorites[int(addon.args['base'])].append({'id': md5.md5(title).hexdigest(), 'url': addon.args['url'], 'title': title, 'folder': bool(int(addon.args['folder']))})
    file = open(path, 'w')
    json.dump(favorites, file)
    file.close()
    xbmcgui.Dialog().notification('Favorites', 'Added to favorites.', xbmcgui.NOTIFICATION_INFO, 5000)
elif kind == 'removeFavorite':
    path = os.path.join(xbmc.translatePath(addon.addon.getAddonInfo('profile')), 'favorites.json')
    file = open(path, 'r')
    try:
        favorites = json.load(file)
    except:
        xbmcgui.Dialog().notification('Favorites', 'You have no favorites to delete.', xbmcgui.NOTIFICATION_ERROR, 5000)
        favorites = None
    if favorites:
        file.close()
        for index, item in enumerate(favorites[int(addon.args['base'])]):
            if item['id'] == addon.args['id']:
                del favorites[int(addon.args['base'])][index]
                break
        file = open(path, 'w')
        json.dump(favorites, file)
        file.close()
        xbmcgui.Dialog().notification('Favorites', 'Removed from favorites.', xbmcgui.NOTIFICATION_INFO, 5000)
elif kind == 'picks':
    pass
elif kind == 'item':
    media = Media.factory(int(addon.args['base']))
    xbmcplugin.setContent(addon.handle, media.TYPE)
    url = addon.url + addon.args['url']
    success, response = makeRequest(url)
    if not success:
        xbmcgui.Dialog().notification('Results', response, xbmcgui.NOTIFICATION_ERROR, 5000)
        sys.exit(1)
    data = json.loads(response.text)
    items = {}
    formats = set(media.FORMATS)
    try:
        for file in data['files']:
            format = file['name'].split('.')[-1].lower()
            if format in formats and 'Thumb' not in file['format']:
                if format not in items:
                    items[format] = []
                downloadURL = url.replace('/metadata', '/download', 1) + '/' + file['name']
                if 'title' in file:
                    title = (file['title'] + ' ' + file['format']).encode('utf-8')
                else:
                    title = (file['name'] + ' ' + file['format']).encode('utf-8')
                li = xbmcgui.ListItem(title, iconImage='DefaultVideo.png')
                li.setInfo('pictures', {'title': title})
                actions = []
                actions.append(('Add to favorites', 'RunPlugin(' + buildURL(addon.home, {'kind': 'addFavorite', 'url': downloadURL, 'title': addon.args['name'], 'base': addon.args['base'], 'folder': 0}) + ')'))
                li.addContextMenuItems(actions, replaceItems=True)
                items[format].append((downloadURL, li, False))
    except Exception as e:
        xbmcgui.Dialog().notification('Results', 'Could not display results.', xbmcgui.NOTIFICATION_ERROR, 5000)
    items = media.filter(items)
    xbmcplugin.addDirectoryItems(addon.handle, items)
    xbmcplugin.endOfDirectory(addon.handle)
