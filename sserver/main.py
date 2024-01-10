from functools import partial
from glob import glob
import os
import argparse
import shutil
from sanic import Blueprint, Sanic, Request, response, app
from sanic.response import json, html, file as resp_file
from sanic.worker.loader import AppLoader

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sanic_routing import Route
import ulid

from sserver.model import get_db, MsgRecord, FileRecord
from sserver.filters import datetime_format, format_size, register_filters
from sserver.utils import get_media_type

jinja_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")),
    auto_reload=True,
    autoescape=select_autoescape(["html"]),
)
register_filters(jinja_env)


def create_bp(prefix: str = "/"):
    bp = Blueprint("app", prefix)

    @bp.route("/")
    async def index(request: Request):
        files = await FileRecord.get_list()
        msg_list = await MsgRecord.get_list()

        file_list = []
        for file in files:
            file_path = os.path.join(request.app.config.UPLOAD_DIR, file.id)
            exists = os.path.exists(file_path)
            file_size = -1 if not exists else os.path.getsize(file_path)
            file_list.append(
                {
                    "id": file.id,
                    "original_name": file.filename,
                    "created_at": file.created_at,
                    "size": file_size,
                }
            )

        return html(
            jinja_env.get_template("index.html").render(
                url_for=request.app.url_for,
                **{"request": request, "files": file_list, "msgs": msg_list},
            )
        )

    @bp.route("/upload", methods=["POST", "GET"])
    async def upload(request: Request):
        if request.method == "GET":
            return html(jinja_env.get_template("upload.html").render())

        else:
            file = request.files.get("uploaded_file")
            file_record = FileRecord(file.name)
            with open(os.path.join(request.app.config.UPLOAD_DIR, file_record.id), "wb") as f:
                f.write(file.body)

            await file_record.save()

            return html(
                f"<tr><td><a href='/{file_record.id}' target='_blank'>{file_record.filename}"
                f"</a></td><td>{datetime_format(file_record.created_at)}</td><td>{format_size(len(file.body))}</td>"
                f"<td><a href='{request.app.url_for('app.delete',mode='file',id=file_record.id)}'>删除</a></td></tr>"
            )

    @bp.route("/msg", methods=["GET", "POST"])
    async def msg(request: Request):
        if request.method == "GET":
            msg_list = await MsgRecord.get_list()
            return html(jinja_env.get_template("message.html".render(**{"msgs": msg_list})))
        else:
            await MsgRecord(content=request.form.get("content")).save()
            return response.redirect(request.app.url_for("app.index"))

    @bp.route("/delete/<mode:str>/<id:str>", methods=["GET"])
    async def delete(request: Request, mode: str, id: str):
        model = None
        if mode == "file":
            model = await FileRecord.get(id)
            path = os.path.join(request.app.config.UPLOAD_DIR, model.id)
            if os.path.exists(path):
                os.remove(path)
        elif mode == "msg":
            model = await MsgRecord.get(id)
        if model and not model.protected:
            await model.delete()
        return response.redirect(request.app.url_for("app.index"))

    @bp.route("/<fid:path>")
    async def download(request: Request, fid: str):
        file = await FileRecord.get(fid)
        if not file:
            return json({"code": -1, "msg": "file not found.", "data": None})

        file_path = os.path.join(request.app.config.UPLOAD_DIR, file.id)
        if os.path.exists(file_path):
            return await resp_file(
                file_path,
                filename=file.filename,
                mime_type=get_media_type(file.filename.rsplit(".", 1)[-1]),
            )
        return json({"code": -2, "msg": "file not exists", "data": None})

    @bp.get("/make")
    async def make_record(request: Request):
        newf = []
        for f in glob(request.app.config.UPLOAD_DIR + "/*"):
            if not os.path.isfile(f):
                continue
            basename = os.path.basename(f)
            if not await FileRecord.get(basename) and not await FileRecord.get_by_filename(basename):
                newf.append(await FileRecord(basename).save())
                os.rename(f, os.path.join(os.path.dirname(f), newf[-1].id))
        return json({"code": 0, "msg": "success", "data": [it.filename for it in newf]})

    return bp


def create_app(prefix: str = "/"):
    bp = create_bp(prefix)
    app = Sanic(f"sserver")
    app.config.UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(os.getcwd(), "upload"))
    app.config.REQUEST_MAX_SIZE = int(os.environ.get("REQUEST_MAX_SIZE", 10 * 1024 * 1024 * 1024))
    app.blueprint(bp)

    @app.listener("before_server_start")
    async def setup(app, loop):
        await get_db()

        if not os.path.exists(app.config.UPLOAD_DIR):
            os.makedirs(app.config.UPLOAD_DIR)
        if not await FileRecord.get("favicon.ico"):
            await FileRecord("favicon.ico", "favicon.ico", True).save()
        if not os.path.exists(app.config.UPLOAD_DIR + "/favicon.ico"):
            shutil.copy(
                os.path.join(os.path.dirname(__file__), "upload", "favicon.ico"),
                os.path.join(app.config.UPLOAD_DIR, "favicon.ico"),
            )

    return app


def parseargs():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", "-H", type=str, default="0.0.0.0", help="host")
    parser.add_argument("--port", "-p", type=int, default=3001, help="port")
    parser.add_argument("--prefix", "-a", type=str, default="/", help="prefix")
    return parser.parse_args()


def main():
    args = parseargs()
    loader = AppLoader(factory=partial(create_app, args.prefix))
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
