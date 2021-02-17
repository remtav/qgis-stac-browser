from .item import Item
from .link import Link


class SearchResult:
    def __init__(self, api=None, json={}):
        self._api = api
        self._json = json

    @property
    def api(self):
        return self._api

    @property
    def type(self):
        return self._json.get('type', None)

    @property
    def context(self):
        return self._json.get('context', None)

    @property
    def next(self):
        for link in self.links:
            if link.rel == 'next':
                return link

        return None

    @property
    def items(self):
        return [Item(self.api, f) for f in self._json.get('features', [])]

    @property
    def links(self):
        return [Link(l) for l in self._json.get('links', [])]
