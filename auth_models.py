import datetime
import uuid

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from database import Base


def gen_id() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_id)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    history = relationship(
        "ResearchHistory", back_populates="user", cascade="all, delete-orphan"
    )


class ResearchHistory(Base):
    __tablename__ = "research_history"

    id = Column(String, primary_key=True, default=gen_id)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    final_report = Column(Text, nullable=True)
    # Full pipeline state (sub_questions, research_results, critique, etc.)
    # stored as a JSON string so we don't need per-field columns.
    state_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)

    user = relationship("User", back_populates="history")
