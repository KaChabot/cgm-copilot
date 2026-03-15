from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.db import Base, engine, SessionLocal
from app.models import GlucoseReading, MealEvent, InsulinEvent

app = FastAPI(
    title="CGM Copilot API",
    description="Prototype API for glucose readings and simple analysis",
    version="0.1.0",
    servers=[{"url": "https://cgm-copilot-api.onrender.com"}]
)

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "CGM Copilot API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/glucose/current")
def glucose_current(db: Session = Depends(get_db)):
    latest = db.query(GlucoseReading).order_by(GlucoseReading.id.desc()).first()

    if latest:
        return {
            "glucose": {
                "value": latest.value,
                "unit": "mmol/L",
                "trend": latest.trend or "unknown"
            },
            "timestamp": latest.timestamp,
            "source": latest.source or "database"
        }

    return {
        "glucose": {
            "value": 7.8,
            "unit": "mmol/L",
            "trend": "stable"
        },
        "timestamp": "2026-03-14T12:05:00",
        "source": "mock"
    }


@app.get("/glucose/history")
def glucose_history(db: Session = Depends(get_db)):
    readings = db.query(GlucoseReading).order_by(GlucoseReading.id.desc()).limit(10).all()

    if readings:
        return {
            "readings": [
                {
                    "value": reading.value,
                    "timestamp": reading.timestamp
                }
                for reading in reversed(readings)
            ],
            "unit": "mmol/L"
        }

    return {
        "readings": [
            {"value": 7.1, "timestamp": "2026-03-14T08:00:00"},
            {"value": 7.8, "timestamp": "2026-03-14T09:00:00"},
            {"value": 8.2, "timestamp": "2026-03-14T10:00:00"},
            {"value": 7.9, "timestamp": "2026-03-14T11:00:00"}
        ],
        "unit": "mmol/L"
    }


@app.get("/glucose/analysis")
def glucose_analysis(db: Session = Depends(get_db)):
    readings = db.query(GlucoseReading).order_by(GlucoseReading.id.desc()).limit(4).all()

    if readings and len(readings) >= 2:
        values = [r.value for r in reversed(readings)]
    else:
        values = [7.1, 7.8, 8.2, 7.9]

    first_value = values[0]
    last_value = values[-1]
    delta = round(last_value - first_value, 1)

    if delta > 0.3:
        trend = "rising"
    elif delta < -0.3:
        trend = "falling"
    else:
        trend = "stable"

    if abs(delta) >= 1.0:
        risk = "moderate"
    else:
        risk = "low"

    if trend == "rising":
        insight = "Glucose is trending upward over the recent readings."
    elif trend == "falling":
        insight = "Glucose is trending downward over the recent readings."
    else:
        insight = "Glucose is relatively stable over the recent readings."

    return {
        "trend": trend,
        "delta": delta,
        "risk": risk,
        "insight": insight
    }


@app.post("/glucose/add")
def add_glucose_reading(
    value: float,
    timestamp: str,
    trend: str = "stable",
    source: str = "manual",
    db: Session = Depends(get_db)
):
    reading = GlucoseReading(
        value=value,
        timestamp=timestamp,
        trend=trend,
        source=source
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    return {
        "message": "Reading added successfully",
        "id": reading.id
    }


@app.post("/meal/add")
def add_meal(
    description: str,
    timestamp: str,
    carbs: float = 0,
    db: Session = Depends(get_db)
):
    meal = MealEvent(
        description=description,
        carbs=carbs,
        timestamp=timestamp
    )
    db.add(meal)
    db.commit()
    db.refresh(meal)

    return {
        "message": "Meal added successfully",
        "id": meal.id
    }


@app.post("/insulin/add")
def add_insulin(
    insulin_type: str,
    units: float,
    timestamp: str,
    db: Session = Depends(get_db)
):
    insulin = InsulinEvent(
        insulin_type=insulin_type,
        units=units,
        timestamp=timestamp
    )
    db.add(insulin)
    db.commit()
    db.refresh(insulin)

    return {
        "message": "Insulin added successfully",
        "id": insulin.id
    }


@app.get("/day/summary")
def day_summary(db: Session = Depends(get_db)):
    glucose = db.query(GlucoseReading).order_by(GlucoseReading.id.desc()).limit(10).all()
    meals = db.query(MealEvent).order_by(MealEvent.id.desc()).limit(10).all()
    insulin = db.query(InsulinEvent).order_by(InsulinEvent.id.desc()).limit(10).all()

    return {
        "glucose_readings": [
            {
                "value": g.value,
                "timestamp": g.timestamp,
                "trend": g.trend,
                "source": g.source
            }
            for g in reversed(glucose)
        ],
        "meals": [
            {
                "description": m.description,
                "carbs": m.carbs,
                "timestamp": m.timestamp
            }
            for m in reversed(meals)
        ],
        "insulin_events": [
            {
                "insulin_type": i.insulin_type,
                "units": i.units,
                "timestamp": i.timestamp
            }
            for i in reversed(insulin)
        ]
    }