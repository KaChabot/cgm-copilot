from sqlalchemy import Column, Integer, Float, String
from app.db import Base


class GlucoseReading(Base):
    __tablename__ = "glucose_readings"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)
    trend = Column(String, nullable=True)
    source = Column(String, nullable=True)