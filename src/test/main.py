
from .. import Response, Request, Pyserve


if __name__ == "__main__":
    server = Pyserve("", 3100)
    def health(req: Request, res: Response):
        print(req.query())
        print(req.body())
        res.send_json({
            "healthy": True
        })

    def middleware(req: Request, res: Response):
        print("middleware")
        print(f"{req.method} {req.path}")

    server.use("*", middleware)
    server.get("/health", health)
    server.post("/health", health)

    print("listening on :3100")
    server.listen()