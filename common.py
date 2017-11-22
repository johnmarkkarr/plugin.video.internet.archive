from __future__ import unicode_literals

import xbmcaddon

import urllib
import urlparse
import requests

class Media(object):
    @classmethod
    def factory(cls, type):
        if type == 0:
            return Video()
        if type == 1:
            return Audio()
        if type == 2:
            return Image()

    def filter(self, items, sort):
        results = []
        for format in self.FORMATS:
            if format in items:
                if sort:
                    items[format].sort(key=lambda item: item[1].getLabel())
                    results.extend(items[format])
                else:
                    results.extend(items[format])
        return results

class Video(Media):
    FORMATS = ['mpeg', 'mp4', 'ogv', 'ogg', 'mkv', 'm4a']
    TYPE = 'movies'
    INFO = 'video'

class Audio(Media):
    FORMATS = ['ogg', 'mp3', 'oga', 'wav', 'mid', 'midi', 'flac', 'aiff', 'aac', 'shn']
    TYPE = 'songs'
    INFO = 'music'

class Image(Media):
    FORMATS = ['png', 'jpg', 'jpeg', 'jp2', 'tiff', 'gif', 'bmp']
    TYPE = 'images'
    INFO = 'pictures'

class Addon(object):
    TYPES = {'video': 0, 'audio': 1, 'image': 2}
    MEDIA = ['movies', 'audio', 'image']
    ACTIONS = ['Search', 'Browse', 'Favorites', 'Picks']

    def __init__(self, home, handle, args):
        addon = urlparse.urlparse(home).netloc
        self.addon = xbmcaddon.Addon(id=addon)
        self.home = home
        self.handle = int(handle)
        self.args = {}
        args = urlparse.parse_qs(args[1:])
        for key in args:
            self.args[key] = args[key][0]
        self.url = 'http://archive.org'

def buildURL(url, query):
    return url + '?' + urllib.urlencode(query)

def makeRequest(url):
    try:
        raw = requests.get(url)
    except requests.ConnectionError:
        return (False, 'Connection error.')
    except requests.Timeout:
        return (False, 'Connection timed out.')
    except:
        return (False, 'Failed to connect to server.')
    try:
        raw.raise_for_status()
    except requests.HTTPError as e:
        return (False, e.message)
    return (True, raw)
