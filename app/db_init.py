from sqlalchemy.engine import Engine

from .database import Base, engine


def init_db(db_engine: Engine = engine) -> None:
    Base.metadata.create_all(bind=db_engine)
