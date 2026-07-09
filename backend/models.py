from sqlalchemy import Column, Integer, String, Text, DateTime
from pydantic import BaseModel
from typing import Optional
import datetime
from database import Base

class InteractionModel(Base):
    __tablename__ = "interactions_v2" 
    id = Column(Integer, primary_key=True, index=True)
    hcp_name = Column(String(100), nullable=True)
    interaction_type = Column(String(50), nullable=True) 
    interaction_date = Column(String(50), nullable=True)
    interaction_time = Column(String(50), nullable=True)
    attendees = Column(Text, nullable=True)
    topics_discussed = Column(Text, nullable=True)
    materials_shared = Column(Text, nullable=True)
    samples_distributed = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True) 
    outcomes = Column(Text, nullable=True)
    next_steps = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class InteractionCreate(BaseModel):
    text: str


class InteractionResponse(BaseModel):
    message: str
    action_type: str
    interaction_data: Optional[dict] = None