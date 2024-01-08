from email.utils import formatdate
from functools import partial
from glob import glob
import hashlib
import os
import argparse
import re
from urllib.parse import quote
from sanic import Blueprint, Sanic, Request, app
from sanic.response import json, html, file as resp_file, text, file_stream
from sanic.worker.loader import AppLoader

from mimetypes import guess_type

from dserver.utils import TimeStampToTime, file_iterator


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
        show_time = request.args.get("show_time")
        direct_download = request.args.get("dd", "0")

        path = os.path.join(request.app.config.static_path, filename)
        if not os.path.exists(path):
            return text("file not exists!", status=404)
        elif os.path.isdir(path):
            return html(get_file_list(request.app.config.static_path, path, show_time, direct_download))

        # 断点续传
        start, end = 0, None
        if "Range" in request.headers:
            start_end = request.headers["Range"].strip().split("=")[-1]
            start, end = map(str.strip, start_end.split("-"))
            start = int(start)
            end = int(end) if end else None

        file_stat = os.stat(path)
        size = file_stat.st_size
        if end is None:
            end = size - 1
        else:
            end = min(size - 1, end)

        length = end - start + 1
        content_range = f"bytes {start}-{end}/{size}"

        # headers = {
        #     "Content-Length": f"{length}",
        #     "content-disposition": f'attachment; filename="{filename}"',
        #     "Content-Range": content_range,
        #     "Accept-Ranges": "bytes",
        #     "connection": "keep-alive",
        # }

        return await file_stream(path)

    def get_file_list(static_path, path, show_time: bool = False, dd: str = ""):
        sub_path = [it for it in path.replace(static_path, "").rsplit("/") if it]
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
                    "<li><a href='{0}{1}{3}'>{0}{1}</a><span style='margin=20px'>{2}</span></li>".format(
                        os.path.basename(it),
                        "/" if os.path.isdir(it) else "",
                        TimeStampToTime(os.path.getmtime(it)) if show_time != 0 else "",
                        f"?dd={dd}&show_time={show_time}" if dd is not None or show_time is not None else "",
                    )
                    for it in glob(path + "/*")
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
    parser.add_argument("--port", "-p", type=int, default=3001, help="port")
    parser.add_argument("--prefix", "-a", type=str, default="/", help="prefix")
    parser.add_argument("--path", "-P", type=str, default="./", help="dir path")
    return parser.parse_args()


if __name__ == "__main__":
    args = parseargs()
    loader = AppLoader(factory=partial(create_app, args.prefix, args.path))
    app = loader.load()
    ssl = {
        "cert": os.environ.get("CERT_PATH", "/Users/ricardo/code/ricardo/ssl/sshug.cn/cert.crt"),
        "key": os.environ.get("KEY_PATH", "/Users/ricardo/code/ricardo/ssl/sshug.cn/privkey.key"),
    }
    app.prepare(port=3001, dev=os.environ.get("DEBUG", "False").lower() == "true", ssl=ssl)
    Sanic.serve(primary=app, app_loader=loader)
