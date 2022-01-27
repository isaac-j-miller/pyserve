from collections import defaultdict
from http.server import BaseHTTPRequestHandler
from json import loads
from urllib.parse import parse_qs
from typing import DefaultDict, Dict


class Request:
    def __init__(self, pattern: str, handler: BaseHTTPRequestHandler):
        self.handler = handler
        self._pattern = pattern
        path_and_query = handler.path.split("?")
        self._query = path_and_query[1] if len(path_and_query) > 1 else None
        self._json = None
        self._query_parsed = None
        self._params = None
        self.path = path_and_query[0]
        self.headers = self._parse_headers()
        self.method = handler.command
    
    def _parse_headers(self) -> DefaultDict:
        headers = self.handler.headers
        d = defaultdict(None)
        for key, value in headers.items():
            d[key] = str(value)
        return d

    def _parse_body(self):
        content_type = self.headers.get('Content-Type')
        if content_type is None:
            self._json = None
        content_length_str = self.headers.get('Content-Length')
        content_len = int(content_length_str) if content_length_str is not None else None
        if content_len is None:
            return
        post_body = self.handler.rfile.read(content_len)
        if content_type == "application/json":
            self._json = loads(post_body)
        elif content_type == "application/x-www-form-urlencoded":
            self._json = parse_qs(post_body)


    def _parse_query(self):
        if self._query is not None:
            self._query_parsed = parse_qs(self._query)

    def _parse_params(self):
        # TODO: use pattern and path to parse params
        return Dict()

    def params(self) -> Dict:
        if self._params is None:
            self._parse_params()
        return self._params
        

    def body(self) -> Dict:
        if self._json is None:
            self._parse_body()
        return self._json
        
    def query(self) -> Dict:
        if self._query_parsed is None:
            self._parse_query()
        return self._query_parsed