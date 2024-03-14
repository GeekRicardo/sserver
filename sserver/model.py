import ulid
from datetime import datetime
from dataclasses import dataclass, field
import os

from motor.motor_asyncio import AsyncIOMotorClient


@dataclass
class FileRecord:
    filename: str
    id: str = field(default_factory=lambda: str(ulid.new()))
    protected: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def get_col(cls):
        return db["files"]

    @classmethod
    async def get(cls, id_: str):
        ret = await cls.get_col().find_one({"id": id_}, {"_id": 0})
        if ret:
            return cls(**ret)
        return None

    @classmethod
    async def get_list(cls, page: int = 1, size: int = 100):
        ret = cls.get_col().find({}, {"_id": 0}).sort({"created_at": -1}).skip((page - 1) * size).limit(size)
        return [cls(**r) async for r in ret]

    @classmethod
    async def get_by_filename(cls, filename: str, page: int = 1, size: int = 100):
        ret = (
            cls.get_col()
            .find({"filename": filename}, {"_id": 0})
            .sort({"created_at": -1})
            .skip((page - 1) * size)
            .limit(size)
        )
        return [cls(**r) async for r in ret]

    async def save(self):
        await self.get_col().insert_one(self.__dict__)
        self.__dict__.pop("_id", None)

    async def delete(self):
        await self.get_col().delete_one({"id": self.id})

    def json(self):
        data = self.__dict__
        data["created_at"] = data["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return data


@dataclass
class MsgRecord:
    content: str
    id: str = field(default_factory=lambda: str(ulid.new()))
    protected: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def get_col(cls):
        return db["msg"]

    @classmethod
    async def get(cls, id_: str):
        ret = await cls.get_col().find_one({"id": id_}, {"_id": 0})
        if ret:
            return cls(**ret)
        return None

    @classmethod
    async def get_list(cls, page: int = 1, size: int = 30):
        ret = cls.get_col().find({}, {"_id": 0}).sort({"created_at": -1}).skip((page - 1) * size).limit(size)
        return [cls(**r) async for r in ret]

    async def save(self):
        await self.get_col().insert_one(self.__dict__)

    async def delete(self):
        await self.get_col().delete_one({"id": self.id})

    def json(self):
        data = self.__dict__
        data["created_at"] = data["created_at"].strftime("%Y-%m-%d %H:%M:%S")
        return data


db = None


async def get_db():
    global db
    if db:
        return db

    client = AsyncIOMotorClient(os.environ.get("MONGOURI", "mongodb://localhost:27017/"))
    db = client["sserver"]
    await create_indexes(db)
    return db


async def create_indexes(db):
    db["files"].create_index([("id", 1)])
    db["msg"].create_index([("id", 1)])
