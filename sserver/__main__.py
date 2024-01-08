from functools import partial
import os
from sanic import Sanic
from sanic.worker.loader import AppLoader

from .main import create_app, parseargs

if __name__ == "__main__":
    args = parseargs()
    loader = AppLoader(factory=partial(create_app, args.prefix))
    app = loader.load()
    ssl = {
        "cert": os.environ.get(
            "CERT_PATH", "/Users/ricardo/code/ricardo/ssl/sshug.cn/cert.crt"
        ),
        "key": os.environ.get(
            "KEY_PATH", "/Users/ricardo/code/ricardo/ssl/sshug.cn/privkey.key"
        ),
    }
    use_ssl = os.environ.get("USE_SSL", "False").lower() == "true"
    app.prepare(
        host=args.host,
        port=args.port,
        dev=os.environ.get("DEBUG", "False").lower() == "true",
        ssl=ssl if use_ssl else None,
    )
    Sanic.serve(primary=app, app_loader=loader)
