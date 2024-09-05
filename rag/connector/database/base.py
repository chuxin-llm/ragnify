
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 知识库默认存储路径
KB_ROOT_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(__file__)))
    ),
    "local_knowledge_base"
)
if not os.path.exists(KB_ROOT_PATH):
    os.mkdir(KB_ROOT_PATH)
# 数据库默认存储路径。
# 如果使用sqlite，可以直接修改DB_ROOT_PATH；如果使用其它数据库，请直接修改SQLALCHEMY_DATABASE_URI。
DB_ROOT_PATH = os.path.join(KB_ROOT_PATH, "info.db")
SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_ROOT_PATH}"


engine = create_engine(
    SQLALCHEMY_DATABASE_URI,
    json_serializer=lambda obj: json.dumps(obj, ensure_ascii=False),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def create_tables():
    Base.metadata.create_all(bind=engine)

