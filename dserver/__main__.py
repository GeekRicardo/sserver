from functools import partial
import os
from sanic import Sanic
from sanic.worker.loader import AppLoader

from .main import parseargs, create_app

if __name__ == "__main__":
    args = parseargs()
    loader = AppLoader(factory=partial(create_app, args.prefix, args.path))
    app = loader.load()
    ssl = {
        "cert": os.environ.get("CERT_PATH", "/Users/ricardo/code/ricardo/ssl/sshug.cn/cert.crt"),
        "key": os.environ.get("KEY_PATH", "/Users/ricardo/code/ricardo/ssl/sshug.cn/privkey.key"),
    }
    app.prepare(host=args.host, port=args.port, dev=os.environ.get("DEBUG", "False").lower() == "true", ssl=ssl)
    Sanic.serve(primary=app, app_loader=loader)