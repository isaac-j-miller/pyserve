from http.server import BaseHTTPRequestHandler
from json import dumps
from typing import Dict, Tuple


class Response:
    def __init__(self, handler: BaseHTTPRequestHandler):
        self.handler = handler
        self._status = 200
        self._headers = dict()
        self._body = ''

    def header(self, name: str, value: str):
        self._headers[name] = value
    
    def send(self, body: str):
        self._body = body

    def send_json(self, body: Dict):
        json_body = dumps(body)
        self.header("Content-Type", "application/json")
        self.send(json_body)

    def status(self, status: int):
        self._status = status

    def get_response(self) -> Tuple[int, Dict, str]:
        return (self._status, self._headers, self._body)