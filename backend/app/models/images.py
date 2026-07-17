import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import BYTEA, JSONB, UUID
from sqlalchemy.orm import Mapped, deferred, mapped_column, relationship

from ..database import Base

EMBEDDING_DIM = 512


class Image(Base):
    __tablename__ = "images"
    __table_args__ = (
        CheckConstraint("image_width > 0", name="ck_images_width_positive"),
        CheckConstraint("image_height > 0", name="ck_images_height_positive"),
        Index(
            "idx_images_embedding_cosine",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_with={"lists": 100},
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    image_bytes: Mapped[bytes] = deferred(mapped_column(BYTEA, nullable=False))
    image_width: Mapped[int] = mapped_column(Integer, nullable=False)
    image_height: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    boxes: Mapped[list["OcrBox"]] = relationship(
        back_populates="image",
        cascade="all, delete-orphan",
        order_by="OcrBox.box_order",
    )


class OcrBox(Base):
    __tablename__ = "ocr_boxes"
    __table_args__ = (Index("idx_ocr_boxes_image_id_order", "image_id", "box_order"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("images.id", ondelete="CASCADE"), nullable=False
    )
    box_order: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox: Mapped[dict] = mapped_column(JSONB, nullable=False)
    polygon: Mapped[list] = mapped_column(JSONB, nullable=False)

    image: Mapped[Image] = relationship(back_populates="boxes")
