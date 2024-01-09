from functools import partial
import os
from sanic import Sanic
from sanic.worker.loader import AppLoader

from .main import main

if __name__ == "__main__":
    main()
