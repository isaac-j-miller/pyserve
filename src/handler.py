
from .request import Request
from .response import Response


## interface for request handler functions
class RequestHandler:
    def __call__(self, request: Request, response: Response):
        pass