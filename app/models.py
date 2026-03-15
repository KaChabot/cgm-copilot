from sqlalchemy import Column, Integer, Float, String
from app.db import Base


class GlucoseReading(Base):
    __tablename__ = "glucose_readings"

    id = Column(Integer, primary_key=True, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)
    trend = Column(String, nullable=True)
    source = Column(String, nullable=True)


class MealEvent(Base):
    __tablename__ = "meal_events"

    id = Column(Integer, primary_key=True, index=True)
    description = Column(String, nullable=False)
    carbs = Column(Float, nullable=True)
    timestamp = Column(String, nullable=False)


class InsulinEvent(Base):
    __tablename__ = "insulin_events"

    id = Column(Integer, primary_key=True, index=True)
    insulin_type = Column(String, nullable=False)
    units = Column(Float, nullable=False)
    timestamp = Column(String, nullable=False)