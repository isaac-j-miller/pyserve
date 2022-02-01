from src.handler import RequestHandler
from .. import Response, Request, Pyserve

class HealthCheck(RequestHandler):
    def __call__(self, req: Request, res: Response):
        print(req.query())
        print(req.body())
        res.send_json({
            "healthy": True
        })

class Middleware(RequestHandler):
    def __call__(self, req: Request, res: Response):
        print("middleware")
        print(f"{req.method} {req.path}")

if __name__ == "__main__":
    server = Pyserve("", 3100)
    
    server.use("*", Middleware())
    server.get("/health", HealthCheck())
    server.post("/health", HealthCheck())

    print("listening on :3100")
    server.listen()