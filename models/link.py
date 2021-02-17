class Link:
    def __init__(self, json={}):
        self._json = json

    @property
    def href(self):
        return self._json.get('href', None)

    @property
    def rel(self):
        return self._json.get('rel', None)

    @property
    def type(self):
        return self._json.get('type', None)

    @property
    def title(self):
        return self._json.get('title', None)

    @property
    def method(self):
        return self._json.get('method', None)

    @property
    def body(self):
        return self._json.get('body', None)
