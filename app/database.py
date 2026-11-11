import os
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///biblioteca.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def init_db() -> None:  # pragma: no cover
    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:  # pragma: no cover
    with Session(engine) as session:
        yield session
