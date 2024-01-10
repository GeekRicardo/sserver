from functools import partial
from glob import glob
import hashlib
from mimetypes import guess_type
import os
import argparse
from sanic import Blueprint, Sanic, Request
from sanic.response import html, text, file_stream
from sanic.worker.loader import AppLoader
from urllib.parse import unquote, quote

from dserver.utils import TimeStampToTime  # , file_stream


def create_bp(prefix: str = "/"):
    bp = Blueprint("app", prefix)

    @bp.get("/")
    def index(request: Request, show_time: bool = False, dd=""):
        index_html = get_file_list(
            request.app.config.static_path,
            request.app.config.static_path,
            show_time,
            dd,
        )
        return html(index_html)

    @bp.get("/robots.txt")
    def robots_txt(request: Request):
        return text("""User-Agent: *\nDisallow: /""")

    @bp.route("/upload", methods=["POST", "GET"])
    async def upload(request: Request):
        if request.method == "GET":
            return html(
                html(
                    """<form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" id="file">
            <input type="submit" value="上传">
        </form>"""
                )
            )

        else:
            file = request.files.get("uploaded_file")
            file_name = file.filename
            save_path = os.path.join(request.app.config.static_path, file_name)
            if not os.path.exists(save_path):
                with open(save_path, "wb") as f:
                    f.write(file.body)
            return text(file_name)

    @bp.get("/md5/{filename:path}")
    async def md5(request: Request):
        filename = request.args.get("filename")
        path = os.path.join(request.app.config.static_path, filename)
        if not os.path.exists(path):
            return text("file not exists!", status=404)
        elif os.path.isdir(path):
            return text("is a directory")

        with open(path, "rb") as f:
            data = f.read()
        file_md5 = hashlib.md5(data).hexdigest()
        return text(file_md5)

    @bp.get("/<filename:path>")
    async def get_file(request: Request, filename: str):
        # filename = request.args.get("filename")
        show_time = bool(int(request.args.get("st", "0")))
        direct_download = bool(int(request.args.get("dd", "0")))
        encoding = request.args.get("encoding")

        path = os.path.join(request.app.config.static_path, unquote(filename))
        if not os.path.exists(path):
            return text("file not exists!", status=404)
        elif os.path.isdir(path):
            return html(get_file_list(request.app.config.static_path, path, show_time, direct_download, encoding))

        content_type, e = guess_type(path)
        if direct_download:
            content_type = "application/octet-stream"
        if not content_type:
            content_type = "text/plain"
        content_type += f"; charset={(e or (encoding or 'utf-8').upper())}"

        headers = {"Content-Length": str(os.stat(path).st_size), "Content-Type": content_type}

        return await file_stream(path, chunk_size=4096, headers=headers)

    def get_file_list(static_path, path, st: bool = False, dd: bool = False, encoding: str = "utf-8"):
        sub_path = [it for it in path.replace(static_path, "").rsplit("/") if it]
        query_args = "&".join(
            [
                _
                for _ in [
                    f"dd={int(dd)}" if dd else "",
                    f"st={int(st)}" if st else "",
                    f"encoding={encoding}" if encoding else "",
                ]
                if _
            ]
        )
        html_str = """<html><head><style>span:hover{{background-color:#f2f2f2}}li{{weight:70%;}}</style></head><body><h2>{0}</h2><ul>{1}</ul></body></html>""".format(
            "→".join(
                [f'<a href="{prefix}"><span> / </span></a>']
                + [
                    f'<a href="{prefix}{"/".join([_ for _ in sub_path[:sub_path.index(it) + 1]])}/"><span>{it}</span></a>'
                    for it in sub_path
                ]
            ),
            "\n".join(
                [
                    "<li><a href='{0}{2}{4}'>{1}{2}</a><span style='margin=20px'>{3}</span></li>".format(
                        quote(os.path.basename(it)),
                        os.path.basename(it),
                        "/" if os.path.isdir(it) else "",
                        TimeStampToTime(os.path.getmtime(it)) if st != 0 else "",
                        f"?{query_args}" if query_args else "",
                    )
                    for it in sorted(glob(path + "/*"), key=lambda x: x.lower())
                ],
            ),
        )
        return html_str

    return bp


def create_app(prefix: str = "/", upload_dir: str = "./"):
    if not os.path.exists(upload_dir):
        raise FileNotFoundError(f"{upload_dir} not exists")

    bp = create_bp(prefix)
    app = Sanic(f"dserver")
    app.config.static_path = upload_dir
    app.blueprint(bp)
    return app


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "-H", type=str, default="0.0.0.0", help="host")
    parser.add_argument("--port", "-p", type=int, default=8000, help="port")
    parser.add_argument("--prefix", "-a", type=str, default="/", help="prefix")
    parser.add_argument("--path", "-P", type=str, default="./", help="dir path")
    return parser.parse_args()


def main():
    args = parseargs()
    loader = AppLoader(factory=partial(create_app, args.prefix, args.path))
    app = loader.load()
    ssl = {
        "cert": os.environ.get("CERT_PATH", ""),
        "key": os.environ.get("KEY_PATH", ""),
    }
    use_ssl = os.environ.get("USE_SSL", "False").lower() == "true"
    host = os.environ.get("HOST", "0.0.0.0") or args.host
    port = int(os.environ.get("PORT", "0")) or args.port
    app.prepare(
        host=host,
        port=port,
        dev=os.environ.get("DEBUG", "False").lower() == "true",
        ssl=ssl if use_ssl else None,
        access_log=True,
    )
    Sanic.serve(primary=app, app_loader=loader)


if __name__ == "__main__":
    main()
