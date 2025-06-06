from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, Text, DateTime, func

Base = declarative_base()

class ResponseLog(Base):
    __tablename__ = "response_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_prompt = Column(Text, nullable=False)
    normal_response = Column(Text, nullable=False)
    chs_response = Column(Text, nullable=False)
    user_rating = Column(Integer, nullable=True)        # nullable, for future feedback
    user_feedback = Column(Text, nullable=True)         # nullable, for future feedback