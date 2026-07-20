"""
- User: one row per registered person. Passwords are never stored in plain
  text — only a bcrypt hash.
- QueryHistory: one row per question a user has asked. Stores the final
  report alongside a couple of summary fields so the dashboard's history
  panel can render a list without re-running the full pipeline.
"""

import os
from datetime import datetime

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/insightai.db")

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    queries = relationship("QueryHistory", back_populates="user")


class QueryHistory(Base):
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    query_text = Column(Text, nullable=False)
    report_json = Column(Text, nullable=True)
    source_agreement_summary = Column(Text, nullable=True)
    confidence_summary = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="queries")


def get_engine():
    return create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})


def init_db():
    """Create all tables if they don't exist yet. Safe to call repeatedly."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    engine = init_db()
    print(f"Database initialized at {DATABASE_URL}")
    print(f"Tables created: {list(Base.metadata.tables.keys())}")