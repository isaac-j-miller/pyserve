
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import DefaultDict, Literal, List, Tuple, Type, Union

from .handler import RequestHandler
from .request import Request
from .response import Response;


class PatternMiddlewares(DefaultDict[str, List[RequestHandler]]):
    pass

class ReqHandlerDefaultDict(DefaultDict[str, RequestHandler]):
    pass

HttpMethod = Union[Literal["get"], Literal["head"], Literal["put"], Literal["post"], Literal["patch"], Literal["delete"]]
class RequestHandlers:
    def __init__(self):
        self.get = ReqHandlerDefaultDict()
        self.head = ReqHandlerDefaultDict()
        self.put = ReqHandlerDefaultDict()
        self.post = ReqHandlerDefaultDict()
        self.patch = ReqHandlerDefaultDict()
        self.delete = ReqHandlerDefaultDict()

    # TODO: verify this works
    def __getitem__(self, name: HttpMethod) -> ReqHandlerDefaultDict:
        return self.__getattribute__(name)

class Pyserve:
    def __init__(self, host: str, port: int, server_class: Type[HTTPServer]=HTTPServer):
        self.host = host
        self.port = port
        self.pattern_middlewares = PatternMiddlewares()
        self.request_handlers = RequestHandlers()
        self.server_class = server_class
        self.server = None

    def use(self, pattern: str, middleware: RequestHandler):
        if pattern in self.pattern_middlewares.keys():
            self.pattern_middlewares[pattern] = [*self.pattern_middlewares[pattern], middleware]
        else:
            self.pattern_middlewares[pattern] = [middleware]
    
    def get(self, pattern: str, handler: RequestHandler):
        self.request_handlers.get[pattern] = handler

    def head(self, pattern: str, handler: RequestHandler):
        self.request_handlers.head[pattern] = handler

    def put(self, pattern: str, handler: RequestHandler):
        self.request_handlers.put[pattern] = handler

    def post(self, pattern: str, handler: RequestHandler):
        self.request_handlers.post[pattern] = handler

    def patch(self, pattern: str, handler: RequestHandler):
        self.request_handlers.patch[pattern] = handler

    def delete(self, pattern: str, handler: RequestHandler):
        self.request_handlers.delete[pattern] = handler

    def _pattern_matches(self, pattern: str, path: str) -> bool:
        # TODO: implement a matching function that actually does something
        return pattern == path or pattern == "*"

    def _get_middlewares(self, path: str) -> List[RequestHandler]: 
        middlewares: List[RequestHandler] = []
        for key, value in self.pattern_middlewares.items():
            if self._pattern_matches(key, path):
                middlewares.extend(value)
        return middlewares
    
    def _get_handler(self, path: str, method: HttpMethod) -> Union[None, Tuple[RequestHandler, str]]:
        for key, value in self.request_handlers[method].items():
            if self._pattern_matches(key, path):
                return value, key
        return None

    def _generate_http_request_handler(self):
        class Handler(BaseHTTPRequestHandler):
            def _generate_request(_self, pattern: str) -> Request:
                return Request(pattern, _self)
            def _generate_response(_self) -> Response:
                return Response(_self)
            
            def _handle_method(_self, method: HttpMethod):
                middlewares = self._get_middlewares(_self.path)
                handlerPattern = self._get_handler(_self.path, method)
                if handlerPattern is None:
                    _self.close_connection = True
                    return
                handler, pattern = handlerPattern
                all_handlers = [*middlewares, handler]
                if len(all_handlers) == 0:
                    _self.send_error(404, f"cannot {method.upper()} {_self.path}")
                    return
                request = _self._generate_request(pattern)
                response = _self._generate_response()
                try:
                    for handler_function in all_handlers:
                        handler_function(request, response)
                        if response.hasBeenSent():
                            break
                finally:
                    resp = response.get_response()
                    if resp is None:
                        return
                    
                    status, headers, body = resp
                    _self.send_response(status)
                    for header_name, header_value in headers.items():
                        _self.send_header(header_name, header_value)
                    _self.end_headers()
                    _self.wfile.write(body)
                    _self.close_connection = True
                    

            def do_GET(_self):
                return _self._handle_method("get")

            def do_HEAD(_self):
                return _self._handle_method("head")

            def do_PUT(_self):
                return _self._handle_method("put")

            def do_POST(_self):
                return _self._handle_method("post")

            def do_PATCH(_self):
                return _self._handle_method("patch")
                
            def do_DELETE(_self):
                return _self._handle_method("delete")
        
        return Handler

    def listen(self):
        handler = self._generate_http_request_handler()
        server_address = (self.host, self.port)
        self.server = self.server_class(server_address,handler)
        self.server.serve_forever()