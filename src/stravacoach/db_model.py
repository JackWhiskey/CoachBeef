from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
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
    workout_type = Column(String, nullable=True)
    workout_type_num = Column(Integer, nullable=True)
    
    # Detailed stats (nullable because they might not be synced yet)
    calories = Column(Float, nullable=True)
    average_heartrate = Column(Float, nullable=True)
    detail = relationship("DBActivityDetail", back_populates="activity", uselist=False, cascade="all, delete")

class DBActivityDetail(Base):
    __tablename__ = "activity_details"

    id = Column(Integer, ForeignKey("activities.id", ondelete="CASCADE"), primary_key=True)
    # Storing raw lists of dicts directly as JSON
    laps = Column(JSON, nullable=True)          # Distance, time, avg HR per lap
    splits = Column(JSON, nullable=True)        # Kilometer/mile splits
    streams = Column(JSON, nullable=True)       # Second-by-second time-series (Optional)
    updated_at = Column(DateTime, nullable=False)

    # Establish a relationship back to your basic activity table
    activity = relationship("DBActivity", back_populates="detail")


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