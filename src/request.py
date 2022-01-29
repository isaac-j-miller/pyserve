from http.server import BaseHTTPRequestHandler
from json import loads
from urllib.parse import parse_qs

from .types import QueryParsed, Cookies, JsonBody, Params, Headers


class Request:
    _cookies: Cookies
    _json: JsonBody
    _params: Params
    _query_parsed: QueryParsed
    def __init__(self, pattern: str, handler: BaseHTTPRequestHandler):
        self.handler = handler
        self._pattern = pattern
        path_and_query = handler.path.split("?")
        self._query = path_and_query[1] if len(path_and_query) > 1 else None
        self.path = path_and_query[0]
        self.headers = self._parse_headers()
        self.method = handler.command
    
    def _parse_headers(self) -> Headers:
        headers = self.handler.headers
        d = Headers(None)
        for key, value in headers.items():
            d[key] = str(value)
        return d

    def _parse_body(self):
        content_type = self.headers.get('Content-Type')
        if content_type is None:
            return
        content_length_str = self.headers.get('Content-Length')
        content_len = int(content_length_str) if content_length_str is not None else None
        if content_len is None:
            return
        post_body = self.handler.rfile.read(content_len)
        encoding = "utf_8" # TODO: get encoding from content-type header
        if content_type.startswith("application/json"):
            self._json = loads(post_body)
        elif content_type.startswith("application/x-www-form-urlencoded"):
            parsed = parse_qs(post_body)
            json_body = JsonBody()
            for key, value in parsed.items():
                json_body[key.decode(encoding)] = [v.decode(encoding) for v in value]
            self._json = json_body


    def _parse_query(self):
        parsed = parse_qs(self._query)
        qs =  QueryParsed()
        qs.update(parsed.items())
        self._query_parsed = qs

    def _parse_params(self):
        params = Params()
        split_pattern = self._pattern.split("/")
        split_path = self.path.split("")
        for i, pattern_value in enumerate(split_pattern):
            is_param = pattern_value.startswith(":")
            if not is_param:
                continue
            end_index = -1
            optional = pattern_value.endswith("?")
            if optional:
                end_index -= 1
            wildcard = pattern_value.endswith("(*)?" if optional else "(*)")
            if wildcard:
                end_index -= 3
                param_value = "/".join(split_path[i:])
            else:
                param_value = split_path[i]
            param_name = pattern_value[1:end_index]
            params[param_name] = param_value
            if wildcard:
                break
    
    def _parse_cookies(self):
        # TODO: get cookies as dict
        self._cookies = Cookies()
    
    def get_all_cookies(self) -> Cookies:
        if self._cookies is None:
            self._parse_cookies()
        return self._cookies

    def get_cookie(self, name: str) -> str:
        if self._cookies is None:
            self._parse_cookies()
        return self._cookies[name]

    def params(self) -> Params:
        if self._params is None:
            self._parse_params()
        return self._params

    def body(self) -> JsonBody:
        if self._json is None:
            self._parse_body()
        return self._json
        
    def query(self) -> QueryParsed:
        if self._query_parsed is None:
            self._parse_query()
        return self._query_parsed