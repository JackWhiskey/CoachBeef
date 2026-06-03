from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from db_client import Base


class DBActivity(Base):
    __tablename__ = "activities"

    # We will use the actual Strava numeric ID as our primary key!
    id = Column(Integer, primary_key=True, index=True) 
    name = Column(String, index=True)
    type = Column(String)
    start_date = Column(String)
    distance = Column(Float)
    moving_time = Column(Integer)
    average_speed = Column(Float)
    summary_polyline = Column(String, nullable=True)
    
    # Detailed stats (nullable because they might not be synced yet)
    calories = Column(Float, nullable=True)
    average_heartrate = Column(Float, nullable=True)

class DBChatMessage(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)  # 'user', 'assistant' (coach), 'system', or 'tool'
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    associated_activity_id = Column(Integer, nullable=True)

class PersistDBChatMessage(Base):
    __tablename__ = "persist_chat_history"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String)  # 'user', 'assistant' (coach), 'system', or 'tool'
    content = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    associated_activity_id = Column(Integer, nullable=True)
