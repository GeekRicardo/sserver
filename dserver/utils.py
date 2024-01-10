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
