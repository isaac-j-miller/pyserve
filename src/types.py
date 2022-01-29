from typing import DefaultDict, Dict, Any, List

class Headers(DefaultDict[str, str]):
    pass

class JsonBody(DefaultDict[str, Any]):
    pass

class Params(Dict[str, str]):
    pass

class Cookies(DefaultDict[str, str]):
    pass

class QueryParsed(DefaultDict[str, List[str]]):
    pass