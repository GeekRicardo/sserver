from functools import partial
import os
from sanic import Sanic
from sanic.worker.loader import AppLoader

from .main import create_app, parseargs

if __name__ == "__main__":
    args = parseargs()
    loader = AppLoader(factory=partial(create_app, args.prefix))
    app = loader.load()
    app.prepare(host=args.host, port=args.port, dev=os.environ.get("DEBUG", "False").lower() == "true")
    Sanic.serve(primary=app, app_loader=loader)