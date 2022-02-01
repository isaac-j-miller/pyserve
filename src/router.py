from .handler import PatternMiddlewares, RequestHandler, RequestHandlers


class Router:
    def __init__(self):
        self.pattern_middlewares = PatternMiddlewares()
        self.request_handlers = RequestHandlers()

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
