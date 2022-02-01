from asyncio import start_server
from asyncio.streams import StreamReader, StreamWriter

from .singleton import Singleton



class AsyncPyserve(metaclass=Singleton):
    def __init__(self, port: int):
        self.port = port

    async def _route(self, reader: StreamReader, writer: StreamWriter):
        pass

    async def listen(self):
        await start_server(self._route,port=self.port)