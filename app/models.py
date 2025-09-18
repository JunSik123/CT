from typing import Optional

from sqlalchemy import JSON, Integer, LargeBinary, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, sessionmaker

DB_URL = "sqlite+aiosqlite:///./db/pillid.sqlite"
engine = create_async_engine(DB_URL, echo=False, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class Drug(Base):
    __tablename__ = "drugs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_seq: Mapped[str] = mapped_column(String(64), index=True)
    item_name: Mapped[str] = mapped_column(String(256), index=True)
    entp_name: Mapped[str] = mapped_column(String(256), index=True)
    drug_shape: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    color1: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    color2: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    line_front: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    line_back: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    print_front: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    print_back: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    feat_color: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    feat_shape: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    feat_texture: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    feat_embed: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)

    shape_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    scoreline_graph: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
