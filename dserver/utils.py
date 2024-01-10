from typing import Dict, Optional, Union
import os
import time
from os import path
from pathlib import PurePath
from mimetypes import guess_type

from sanic.response.types import ResponseStream
from sanic.models.protocol_types import Range
from sanic.compat import open_async

def TimeStampToTime(timestamp):
    timeStruct = time.localtime(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", timeStruct)


def file_iterator(file_path, offset, chunk_size):
    """
    文件生成器
    :param file_path: 文件绝对路径
    :param offset: 文件读取的起始位置
    :param chunk_size: 文件读取的块大小
    :return: yield
    """
    with open(file_path, "rb") as f:
        f.seek(offset, os.SEEK_SET)
        while True:
            data = f.read(chunk_size)
            if data:
                yield data
            else:
                break


async def file_stream(
    location: Union[str, PurePath],
    status: int = 200,
    chunk_size: int = 4096,
    mime_type: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
    filename: Optional[str] = None,
    _range: Optional[Range] = None,
    encoding: str = "utf-8"
) -> ResponseStream:
    """Return a streaming response object with file data.

    :param location: Location of file on system.
    :param chunk_size: The size of each chunk in the stream (in bytes)
    :param mime_type: Specific mime_type.
    :param headers: Custom Headers.
    :param filename: Override filename.
    :param _range:

    Args:
        location (Union[str, PurePath]): Location of file on system.
        status (int, optional): HTTP response code. Won't enforce the passed in status if only a part of the content will be sent (206) or file is being validated (304). Defaults to `200`.
        chunk_size (int, optional): The size of each chunk in the stream (in bytes). Defaults to `4096`.
        mime_type (Optional[str], optional): Specific mime_type.
        headers (Optional[Dict[str, str]], optional): Custom HTTP headers.
        filename (Optional[str], optional): Override filename.
        _range (Optional[Range], optional): The range of bytes to send.
    """  # noqa: E501
    headers = headers or {}
    if filename:
        headers.setdefault(
            "Content-Disposition", f'attachment; filename="{filename}"'
        )
    filename = filename or path.split(location)[-1]
    mime_type = mime_type or guess_type(filename)[0] or "text/plain"
    if _range:
        start = _range.start
        end = _range.end
        total = _range.total

        headers["Content-Range"] = f"bytes {start}-{end}/{total}"
        status = 206

    async def _streaming_fn(response):
        async with await open_async(location, mode="rb") as f:
            if _range:
                await f.seek(_range.start)
                to_send = _range.size
                while to_send > 0:
                    content = await f.read(min((_range.size, chunk_size)))
                    if len(content) < 1:
                        break
                    to_send -= len(content)
                    await response.write(content)
            else:
                while True:
                    content = await f.read(chunk_size)
                    if len(content) < 1:
                        break
                    await response.write(content)

    return ResponseStream(
        streaming_fn=_streaming_fn,
        status=status,
        headers=headers,
        content_type=mime_type,
    )
