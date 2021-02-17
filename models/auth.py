from urllib.parse import urlparse, parse_qs, urlencode


class Auth:
    def __init__(self, json):
        self._json = json

    @property
    def json(self):
        return None

    def authenticate(self, url, headers, body=None):
        return (url, headers, body)


class QueryParameterAuth(Auth):
    def __init__(self, json):
        self._json = json

    @property
    def json(self):
        return {
            'type': 'query-parameter',
            'key': self.key,
            'value': self.value
        }

    @property
    def key(self):
        return self._json.get('key', None)

    @property
    def value(self):
        return self._json.get('value', None)

    def authenticate(self, url, headers, body=None):
        o = urlparse(url)
        query_parameters = parse_qs(o.query)
        query_parameters[self.key] = self.value

        final_url = f'{o.scheme}://{o.netloc}{o.path}?{urlencode(query_parameters)}'
        return (final_url, headers, body)


class BearerTokenAuth(Auth):
    def __init__(self, json):
        self._json = json

    @property
    def json(self):
        return {
            'type': 'bearer-token',
            'token': self.token
        }

    @property
    def token(self):
        return self._json.get('token', None)

    def authenticate(self, url, headers, body=None):
        if headers is None:
            headers = {}

        headers['Authorization'] = f'Bearer {self.token}'

        return (url, headers, body)
