from sqlalchemy import Column, Integer, ForeignKey, Text, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base
from pgvector.sqlalchemy import Vector
class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    embedding = Column(Vector(768))