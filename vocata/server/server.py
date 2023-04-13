import uvicorn

def run_server():
    config = uvicorn.Config("vocata.server.app:app")
    server = uvicorn.Server(config)
    server.run()
