from typing import DefaultDict, Literal, List, Union

from .request import Request
from .response import Response


## interface for request handler functions
class RequestHandler:
    def __call__(self, request: Request, response: Response) -> None:
        pass

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