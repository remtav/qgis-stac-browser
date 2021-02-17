import re
from urllib.parse import urlparse
from .collection import Collection
from .link import Link
from .auth import Auth, QueryParameterAuth, BearerTokenAuth
from .search_result import SearchResult
from ..utils import network


class API:
    def __init__(self, json=None):
        self._json = json
        self._data = self._json.get('data', None)
        self._collections = [
            Collection(self, c) for c in self._json.get('collections', [])
        ]

    def load(self):
        self._data = network.request(self, f'{self.href}/collections')
        self._collections = [Collection(self, c) for c in self._data['collections']]

    def load_next_page(self, next_link, on_next_page=None, current_page=2, max_pages=10):
        if current_page > max_pages:
            return []

        if on_next_page is not None:
            on_next_page(self)

        items = []
        if next_link.method == 'GET':
            search_result = SearchResult(self,
                                         network.request(
                                             self,
                                             next_link.href))
        elif next_link.method == 'POST':
            search_result = SearchResult(self,
                                         network.request(
                                             self,
                                             next_link.href,
                                             next_link.body))

        next_link = search_result.next
        if next_link is not None:
            items.extend(self.load_next_page(next_link, on_next_page, current_page+1, max_pages))

        items.extend(search_result.items)

        return items

    def search_collection(self, collections=[], bbox=[], start_time=None,
                          end_time=None, query=None, on_next_page=None, limit=50):
        if end_time is None:
            time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
        else:
            start = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            end = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')
            time = f'{start}/{end}'

        body = {
            'collections': [c.id for c in collections],
            'bbox': bbox,
            'time': time,
            'limit': limit,
        }

        if query is not None:
            body['query'] = query

        search_result = SearchResult(self,
                                     network.request(
                                         self,
                                         f'{self.href}/search',
                                         data=body))
        items = search_result.items
        if search_result.next is not None:
            items.extend(self.load_next_page(search_result.next, on_next_page))

        return items

    def collection_id_from_href(self, href):
        p = re.compile(r'\/collections\/(.*)')
        m = p.match(urlparse(href).path)
        if m is None:
            return None

        if m.groups() is None:
            return None

        return m.groups()[0]

    @property
    def json(self):
        return {
            'id': self.id,
            'title': self.title,
            'auth': self.auth.json,
            'href': self.href,
            'data': self.data,
            'collections': [c.json for c in self.collections],
        }

    @property
    def id(self):
        return self._json.get('id', None)

    @property
    def title(self):
        return self._json.get('title', None)

    @property
    def href(self):
        return self._json.get('href', None)

    @property
    def version(self):
        return 'v1.0.0b2'

    @property
    def description(self):
        return 'Description'

    @property
    def auth(self):
        d = self._json.get('auth', None)
        if d is None:
            return Auth(d)

        if d['type'] == 'query-parameter':
            return QueryParameterAuth(d)
        elif d['type'] == 'bearer-token':
            return BearerTokenAuth(d)

        return Auth(d)

    @property
    def data(self):
        if self._data is None:
            return {}
        return self._data

    @property
    def links(self):
        return [Link(link) for link in self.data.get('links', [])]

    @property
    def collection_ids(self):
        collection_ids = []
        p = re.compile(r'\/collections\/(.*)')

        for link in self.links:
            m = p.match(urlparse(link.href).path)
            if m is None:
                continue

            if m.groups() is None:
                continue

            collection_ids.append(m.groups()[0])

        return collection_ids

    @property
    def collections(self):
        return sorted(self._collections)

    def __lt__(self, other):
        return self.title.lower() < other.title.lower()
