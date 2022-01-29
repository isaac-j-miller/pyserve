from glob import escape
from typing import Any, DefaultDict, Dict, List, TypedDict, Union
import re

"""
The logic in this file was translated from the typescript here: https://github.com/pillarjs/path-to-regexp
"""

Path = Union[str, re.Pattern[Any], List[Union[str, re.Pattern[str]]]]
    
class LexToken(TypedDict):
    type: str
    index: int
    value: str

class Key(TypedDict):
    name: Union[str, int]
    prefix: str
    suffix: str
    pattern: str
    modifier: str

class MatchResultDict(TypedDict):
    path: str
    index: int
    params: Dict[str, Any]

MatchResult = Union[MatchResultDict, None]

Token = Union[str, Key]

class EncodeFunction:
    def __call__(self, string: str, token: Union[Token,None]=None) -> str:
        return string

OptionalEncodeFn = Union[EncodeFunction, None]

def lexer(string: str) -> List[LexToken]:
    tokens: List[LexToken] = []
    i = 0
    while i < len(string):
        char = string[i]
        if char in ["*","+","?"]:
            tokens.append({
                "type": "MODIFIER",
                "index": i,
                "value": char
            })
            i+=1
            continue
        if char == "\\":
            tokens.append({
                "type": "ESCAPED_CHAR",
                "index": i,
                "value": string[i+1]
            })
            i+=2
            continue
        if char == "{":
            tokens.append({
                "type": "OPEN",
                "index": i,
                "value": char
            })
            i+=1
            continue
        if char == "}":
            tokens.append({
                "type": "CLOSE",
                "index": i,
                "value": char
            })
            i+=1
            continue
        if char == ":":
            name = ""
            j = i+1
            while j < len(string):
                code = ord(string[j])
                if 48 <= code <=57 or 65 <= code <= 90 or 97 <= code <=122 or code == 95:
                    name += string[j]
                    j+=1
                    continue
                break   
            if not name:
                raise TypeError(f"Missing parameter name at {i}")
            tokens.append({
                "type": "NAME",
                "index": i,
                "value": name
            })
            i = j
            continue
        if char == "(":
            count = 1
            pattern = ""
            j = i + 1
            if string[j] == "?":
                raise TypeError(f'Pattern cannot start with "?" at {j}')
            while j < len(string):
                if string[j] == "\\":
                    pattern += string[j] + string[j+1]
                    j+=2
                    continue
                if string[j] == ")":
                    count -=1
                    if count == 0:
                        j+=1
                        break
                elif string[j] == "(":
                    count+=1
                    if string[j+1] != "?":
                        raise TypeError(f"Capturing groups are not allowed at {j}")
                pattern += string[j]
                j+=1
            if count:
                raise TypeError(f"Unbalanced pattern at {i}")
            if not pattern:
                raise TypeError(f"Missing pattern at {i}")
            tokens.append({
                "type": "PATTERN",
                "index": i,
                "value": pattern
            })
            i = j
            continue
        tokens.append({
            "type": "CHAR",
            "index": i,
            "value": string[i]
        })
        i+=1
    tokens.append({
        "type": "END",
        "index": i,
        "value": ""
    })
    return tokens

def parse(string: str, delimiter:Union[str, None]=None, prefixes:str="./") -> List[Token]:
    tokens = lexer(string)
    default_pattern = f'[^{escape(delimiter if delimiter is not None else "/#?")}]+?'
    result: List[Token] = []
    key = 0
    i = 0
    path = ""

    def try_consume(typ: str) -> Union[None,str]:
        nonlocal i
        nonlocal tokens
        if i < len(tokens) and tokens[i]["type"] == typ:
            v = tokens[i]["value"]
            i+=1
            return v
    
    def must_consume(typ: str) -> str:
        value = try_consume(typ)
        if value is not None:
            return value
        next_type = tokens[i]["type"]
        index = tokens[i]["index"]
        raise TypeError(f'Unexpected {next_type} at {index}, expected {type}')
    
    def consume_text() -> Union[None,str]:
        result = ""
        value: Union[None,str] = None
        # TODO: review this
        while value := try_consume("CHAR") or try_consume("ESCAPED_CHAR"):
            result += value
        return result
    
    while i < len(tokens):
        char = try_consume("CHAR")
        name = try_consume("NAME")
        pattern = try_consume("PATTERN")
        if name or pattern:
            prefix = char or ""
            if prefix in prefixes:
                path += prefix
                prefix = ""
            if path:
                result.append(path)
                path = ""
            result.append({
                "name": name or key,
                "prefix": prefix,
                "suffix": "",
                "pattern": pattern or default_pattern,
                "modifier": try_consume("MODIFIER") or ""
            })
            if not name:
                key+=1
            continue
        value = char or try_consume("ESCAPED_CHAR")
        if value:
            path+=value
            continue
        if path:
            result.append(path)
            path = ""
        open = try_consume("OPEN")
        if open:
            prefix = consume_text()
            name = try_consume("NAME") or ""
            pattern = try_consume("PATTERN") or ""
            suffix = consume_text()
            must_consume("CLOSE")
            result.append({
                "name": name or (pattern if key else ""),
                "prefix": prefix or "",
                "suffix": suffix or "",
                "pattern": default_pattern if name and not pattern else pattern,
                "modifier": try_consume("MODIFIER") or ""
            })
            if key and not name:
                key+=1
            continue
        must_consume("END")
    return result

def flags(sensitive: Union[bool, None]) -> re.RegexFlag:
    if sensitive is not None and sensitive:
        return re.RegexFlag.I
    # TODO: review this
    return re.RegexFlag.U

def tokens_to_function(tokens: List[Token], sensitive:bool=False, encode: OptionalEncodeFn=None, validate: bool=True):
    re_flags = flags(sensitive)
    def default_encode(string: str, token: Token) -> str:
        return string
    encode_fn = encode if encode is not None else default_encode
    matches = [re.compile(f'^(?:{token["pattern"]})$', re_flags) if type(token) is Key else token for token in tokens]

    def return_func(data: DefaultDict[str, Any]):
        path = ""
        for i, token in enumerate(tokens):
            if isinstance(token, str):
                path += token
                continue
            value = data[str(token["name"])] if data is not None else None
            optional = token["modifier"] in ["?", "*"]
            repeat = token["modifier"] in ["*" or "+"]
            if type(value) is List[str]:
                if not repeat:
                    raise TypeError(f'Expected "{token["name"]} not to repeat, but got an array')
                if len(value) == 0:
                    if optional:
                        continue
                    raise TypeError(f'Expected {token["name"]} to not be empty')
                for unencoded_segment in value:
                    segment = encode_fn(unencoded_segment, token)
                    r = matches[i]
                    if validate and type(r) is re.Pattern[str] and r.match(segment) is None:
                        raise TypeError(f'Expected all {token["name"]} to match "{token["pattern"]}", but got {segment}')
                    path += token["prefix"] + segment + token["suffix"]
                continue
            if type(value) is str or type(value) is int or type(value) is float:
                segment = encode_fn(str(value), token)
                regex = matches[i]
                if validate and type(regex) is re.Pattern[str] and regex.match(segment) is None:
                    raise TypeError(f'Expected all {token["name"]} to match "{token["pattern"]}", but got {segment}')
                path += token["prefix"] + segment + token["suffix"]
                continue
            if optional:
                continue
            type_of_message = "an array" if repeat else "a string"
            raise TypeError(f'Expected "{token["name"]}" to be "{type_of_message}"')
        return path

    return return_func

def compile(string: str, sensitive:bool=False, encode: OptionalEncodeFn=None, validate: bool=True, delimiter:Union[str, None]=None, prefixes:str="./" ):
    return tokens_to_function(parse(string, delimiter=delimiter, prefixes=prefixes), sensitive=sensitive, encode=encode, validate=validate)

def regexp_to_function(regexp: re.Pattern[str], keys: List[Key], decode:OptionalEncodeFn=None):
    def default_func(string: str, token: Token) -> str:
        return string
    decodeFn = decode if decode is not None else default_func
    
    def return_func(pathname: str) -> MatchResult:
        m = regexp.match(pathname)
        if m is None: 
            return None
        path: str = m.group(0)
        index = m.start()
        params = Dict[str, Any]()
        groups = m.groups()
        for i, group in zip(range(1, len(groups)),groups):
            g: str = group
            key = keys[i - 1]
            if key["modifier"] in ["*", "+"]:
                params[str(key["name"])] = [decodeFn(value, key) for value in g.split(key["prefix"] + key["suffix"])]
            else:
                params[str(key["name"])] = decodeFn(g, key)
        return {
            "path": path,
            "index": index,
            "params": params
        }

    return return_func

def regexp_to_regexp(path: re.Pattern[str], keys:Union[List[Key], None]=None) -> re.Pattern[str]:
    if keys is None: 
        return path
    groupsRegex = re.compile('\\((?:\\?<(.*?)>)?(?!\\?)')
    index = 0
    exec_result = groupsRegex.search(path.pattern)
    while exec_result:
        keys.append({
            "name": exec_result.group(1) if exec_result is not None else index,
            "prefix": "",
            "suffix": "",
            "pattern": "",
            "modifier": ""
        })
        if exec_result is None:
            index +=1
        exec_result = groupsRegex.search(path.pattern)
    return path

def array_to_regexp(paths: List[Union[str, re.Pattern[str]]], keys:Union[List[Key], None]=None, encode: OptionalEncodeFn=None, sensitive:bool=False, delimiter:Union[str, None]=None, prefixes:str="./") -> re.Pattern[str]:
    parts = [ path_to_regex(path, keys, encode=encode, sensitive=sensitive, delimiter=delimiter, prefixes=prefixes).pattern for path in paths]
    return re.compile(f'(?:{"|".join(parts)})', flags(sensitive))

def tokens_to_regexp(tokens: List[Token], keys: Union[List[Key], None], sensitive: bool=False, strict: bool=False, end: bool = True, start: bool = True, delimiter:Union[str, None]=None, ends_with: str = "", encode: OptionalEncodeFn=None):
    ends_with_re=f'[{escape(ends_with or "")}]$'
    delimiter_re=f'[{escape(delimiter or "/#?")}]'
    def default_func(string: str, token: Union[Token,None]=None) -> str:
        return string
    encodeFn = encode if encode is not None else default_func
    route = "^" if start else ""
    for token in tokens:
        if isinstance(token, str):
            route += escape(encodeFn(token))
        else:
            prefix = escape(encodeFn(token["prefix"]))
            suffix = escape(encodeFn(token["suffix"]))
            if token["pattern"]:
                if keys:
                    keys.append(token)
                if prefix or suffix:
                    if token["modifier"] in[ "*", "+"]:
                        mod = "?" if token["modifier"] == "*" else ""
                        route += f'(?:{prefix}((?:{token["pattern"]})(?:{suffix}{prefix}(?:{token["pattern"]}))*){suffix}){mod}'
                    else:
                        route += f'(?:{prefix}({token["pattern"]}){suffix}){token["modifier"]}'
                else:
                    route += f'({token["pattern"]}){token["modifier"]}'
            else:
                route += f'(?:{prefix}{suffix}){token["modifier"]}'
    if end:
        if not strict:
            route += f'{delimiter}?'
        route += "$" if not ends_with_re else f'(?={ends_with_re})'
    else:
        end_token = tokens[-1]
        is_end_delimited = end_token[-1] in delimiter_re if isinstance(end_token, str) else end_token is None
        if not strict:
            route+=f'(?:{delimiter_re}(?={ends_with_re}))?'
        if not is_end_delimited:
            route += f'(?={delimiter_re}|{ends_with_re})'
    return re.compile(route, flags(sensitive))

def string_to_regexp(path: str, keys:Union[List[Key], None]=None, sensitive: bool=False, strict: bool=False, end: bool = True, start: bool = True, delimiter:Union[str, None]=None, ends_with: str = "", encode: OptionalEncodeFn=None, prefixes:str="./") -> re.Pattern[str]:
    return tokens_to_regexp(parse(path, delimiter=delimiter, prefixes=prefixes), keys, sensitive=sensitive, strict=strict, end=end, start=start, delimiter=delimiter, ends_with=ends_with, encode=encode)

def path_to_regex(path: Path, keys:Union[List[Key], None]=None, sensitive: bool=False, strict: bool=False, end: bool = True, start: bool = True, delimiter:Union[str, None]=None, ends_with: str = "", encode: OptionalEncodeFn=None, prefixes:str="./") -> re.Pattern[str]:
    if isinstance(path, re.Pattern):
        return regexp_to_regexp(path, keys)
    if isinstance(path, list):
        return array_to_regexp(path, keys, encode=encode)
    return string_to_regexp(path, keys,sensitive=sensitive, strict=strict, end=end, start=start, delimiter=delimiter, ends_with=ends_with, encode=encode, prefixes=prefixes)

def match(string: Path,encode:OptionalEncodeFn=None,decode:OptionalEncodeFn=None):
    keys = []
    regexp = path_to_regex(string, keys, encode=encode)
    return regexp_to_function(regexp, keys, decode=decode)
