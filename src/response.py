from http.server import BaseHTTPRequestHandler
from mimetypes import guess_type
from json import dumps
from typing import Any, Dict, Tuple, Union

from .types import Headers

class Response:
    def __init__(self, handler: BaseHTTPRequestHandler):
        self.handler = handler
        self._status: int = 200
        self._headers = Headers()
        self._body: bytes = b''
        self._sent: bool = False

    def hasBeenSent(self) -> bool:
        return self._sent

    def header(self, name: str, value: str):
        self._headers[name] = value
    
    def _send(self, body: bytes):
        if self._sent:
            raise Exception("Cannot call send more than once!")
        self._body = body
        self.header("Content-Length", str(len(self._body)))
        self._sent = True

    def send_json(self, body: Dict[Any, Any]):
        json_body = dumps(body).encode(encoding="utf_8")
        self.header("Content-Type", "application/json; charset=UTF-8")
        self._send(json_body)

    def send_raw(self, body: bytes):
        self._send(body)

    def send_file(self, file_path: str, encoding: str="utf_8"):
        data = ''
        with open(file_path, "r") as f:
            data = f.read()
        encoded = data.encode(encoding=encoding)
        length = len(encoded)
        self.header("Content-Length", str(length))
        content_type, content_encoding = guess_type(file_path)
        if content_type is not None:
            self.header("Content-Type", content_type)
        if content_encoding is not None:
            self.header("Content-Encoding", content_encoding)
        self._send(encoded)
    
    def download(self, filename: Union[str,None] = None):
        self.header("Content-Disposition", f"attachment{f'; filename=\"{filename}\"' if filename is not None else ''}")

    def set_cookie(self, name: str, value: str):
        # TODO: implement this
        pass

    def redirect(self, redirect_path: str):
        # TODO: implement this
        pass

    def status(self, status: int):
        self._status = status

    def get_response(self) -> Tuple[int, Headers, bytes]:
        if self._sent:
            return (self._status, self._headers, self._body)
        raise Exception("Response has not been sent yet")