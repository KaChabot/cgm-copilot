from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from datetime import datetime

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


def parse_dt(value: str):
    return datetime.fromisoformat(value)


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
    existing = db.query(GlucoseReading).filter(
    GlucoseReading.timestamp == timestamp,
    GlucoseReading.source == source
).first()

if existing:
    return {
        "message": "Reading already exists",
        "id": existing.id
    }
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


@app.get("/meal/analysis")
def meal_analysis(db: Session = Depends(get_db)):
    meals = db.query(MealEvent).order_by(MealEvent.id.desc()).limit(5).all()
    glucose = db.query(GlucoseReading).order_by(GlucoseReading.id.asc()).all()
    insulin = db.query(InsulinEvent).order_by(InsulinEvent.id.asc()).all()

    results = []

    for meal in reversed(meals):
        meal_time = parse_dt(meal.timestamp)

        glucose_before = None
        glucose_after = None
        insulin_match = None

        for g in glucose:
            g_time = parse_dt(g.timestamp)
            diff_minutes = (meal_time - g_time).total_seconds() / 60

            if 0 <= diff_minutes <= 60:
                glucose_before = g

        for g in glucose:
            g_time = parse_dt(g.timestamp)
            diff_minutes = (g_time - meal_time).total_seconds() / 60

            if 60 <= diff_minutes <= 180:
                glucose_after = g
                break

        for i in insulin:
            i_time = parse_dt(i.timestamp)
            diff_minutes = abs((meal_time - i_time).total_seconds() / 60)

            if diff_minutes <= 45:
                insulin_match = i

        delta = None
        assessment = "insufficient_data"

        if glucose_before and glucose_after:
            delta = round(glucose_after.value - glucose_before.value, 1)

            if delta > 3.0:
                assessment = "possible_underbolus_or_high_meal_impact"
            elif delta > 1.5:
                assessment = "moderate_post_meal_rise"
            else:
                assessment = "post_meal_response_seems_reasonable"

        results.append({
            "meal": {
                "description": meal.description,
                "carbs": meal.carbs,
                "timestamp": meal.timestamp
            },
            "matched_insulin": {
                "insulin_type": insulin_match.insulin_type,
                "units": insulin_match.units,
                "timestamp": insulin_match.timestamp
            } if insulin_match else None,
            "glucose_before": {
                "value": glucose_before.value,
                "timestamp": glucose_before.timestamp
            } if glucose_before else None,
            "glucose_after": {
                "value": glucose_after.value,
                "timestamp": glucose_after.timestamp
            } if glucose_after else None,
            "delta": delta,
            "assessment": assessment
        })

    return {"meal_analysis": results}


@app.get("/pattern/morning")
def pattern_morning(db: Session = Depends(get_db)):
    glucose = db.query(GlucoseReading).order_by(GlucoseReading.id.asc()).all()

    morning_readings = []

    for g in glucose:
        dt = parse_dt(g.timestamp)
        if 4 <= dt.hour <= 10:
            morning_readings.append({
                "value": g.value,
                "timestamp": g.timestamp,
                "hour": dt.hour
            })

    if len(morning_readings) < 2:
        return {
            "pattern": "insufficient_data",
            "message": "Not enough morning readings to detect a pattern.",
            "readings": morning_readings
        }

    first_value = morning_readings[0]["value"]
    last_value = morning_readings[-1]["value"]
    delta = round(last_value - first_value, 1)

    if delta >= 2.0:
        pattern = "possible_dawn_phenomenon"
        message = "Morning glucose appears to rise significantly across the morning period."
    elif delta >= 0.8:
        pattern = "mild_morning_rise"
        message = "Morning glucose shows a noticeable upward trend."
    else:
        pattern = "stable_morning_pattern"
        message = "Morning glucose appears relatively stable."

    return {
        "pattern": pattern,
        "message": message,
        "delta": delta,
        "readings": morning_readings
    }

@app.get("/insulin/ratio_estimate")
def insulin_ratio_estimate(db: Session = Depends(get_db)):
    meals = db.query(MealEvent).order_by(MealEvent.id.desc()).limit(10).all()
    glucose = db.query(GlucoseReading).order_by(GlucoseReading.id.asc()).all()
    insulin = db.query(InsulinEvent).order_by(InsulinEvent.id.asc()).all()

    analyses = []
    ratio_samples = []

    for meal in reversed(meals):
        meal_time = parse_dt(meal.timestamp)

        glucose_before = None
        glucose_after = None
        insulin_match = None

        for g in glucose:
            g_time = parse_dt(g.timestamp)
            diff_minutes = (meal_time - g_time).total_seconds() / 60
            if 0 <= diff_minutes <= 60:
                glucose_before = g

        for g in glucose:
            g_time = parse_dt(g.timestamp)
            diff_minutes = (g_time - meal_time).total_seconds() / 60
            if 60 <= diff_minutes <= 180:
                glucose_after = g
                break

        for i in insulin:
            i_time = parse_dt(i.timestamp)
            diff_minutes = abs((meal_time - i_time).total_seconds() / 60)
            if diff_minutes <= 45:
                insulin_match = i

        if not meal.carbs or not insulin_match or not glucose_before or not glucose_after:
            analyses.append({
                "meal": meal.description,
                "timestamp": meal.timestamp,
                "status": "insufficient_data"
            })
            continue

        delta = round(glucose_after.value - glucose_before.value, 1)
        observed_ratio = round(meal.carbs / insulin_match.units, 1) if insulin_match.units > 0 else None

        comment = "ratio_seems_reasonable"
        adjustment_hint = "keep_observing"

        if delta > 3.0:
            comment = "possible_underbolus"
            adjustment_hint = "may_need_stronger_ratio"
        elif delta > 1.5:
            comment = "moderate_rise"
            adjustment_hint = "slightly_stronger_ratio_may_help"
        elif delta < -2.0:
            comment = "possible_overbolus"
            adjustment_hint = "may_need_weaker_ratio"

        ratio_samples.append(observed_ratio)

        analyses.append({
            "meal": meal.description,
            "timestamp": meal.timestamp,
            "carbs": meal.carbs,
            "insulin_units": insulin_match.units,
            "insulin_type": insulin_match.insulin_type,
            "glucose_before": glucose_before.value,
            "glucose_after": glucose_after.value,
            "delta": delta,
            "observed_ratio_g_per_unit": observed_ratio,
            "comment": comment,
            "adjustment_hint": adjustment_hint
        })

    usable_ratios = [r for r in ratio_samples if r is not None]

    if usable_ratios:
        average_ratio = round(sum(usable_ratios) / len(usable_ratios), 1)
    else:
        average_ratio = None

    overall_message = "Not enough usable meal data to estimate ratio."
    if average_ratio is not None:
        overall_message = f"Estimated observed ratio is around 1 unit per {average_ratio} g of carbs."

    return {
        "estimated_ratio_g_per_unit": average_ratio,
        "overall_message": overall_message,
        "meal_analyses": analyses
    }

@app.get("/meal/underbolused")
def meal_underbolused(db: Session = Depends(get_db)):
    meals = db.query(MealEvent).order_by(MealEvent.id.desc()).limit(10).all()
    glucose = db.query(GlucoseReading).order_by(GlucoseReading.id.asc()).all()
    insulin = db.query(InsulinEvent).order_by(InsulinEvent.id.asc()).all()

    flagged_meals = []

    for meal in reversed(meals):
        meal_time = parse_dt(meal.timestamp)

        glucose_before = None
        glucose_after = None
        insulin_match = None

        for g in glucose:
            g_time = parse_dt(g.timestamp)
            diff_minutes = (meal_time - g_time).total_seconds() / 60
            if 0 <= diff_minutes <= 60:
                glucose_before = g

        for g in glucose:
            g_time = parse_dt(g.timestamp)
            diff_minutes = (g_time - meal_time).total_seconds() / 60
            if 60 <= diff_minutes <= 180:
                glucose_after = g
                break

        for i in insulin:
            i_time = parse_dt(i.timestamp)
            diff_minutes = abs((meal_time - i_time).total_seconds() / 60)
            if diff_minutes <= 45:
                insulin_match = i

        if not glucose_before or not glucose_after or not insulin_match:
            continue

        delta = round(glucose_after.value - glucose_before.value, 1)

        if delta >= 2.5:
            flagged_meals.append({
                "meal": meal.description,
                "timestamp": meal.timestamp,
                "carbs": meal.carbs,
                "insulin_type": insulin_match.insulin_type,
                "insulin_units": insulin_match.units,
                "glucose_before": glucose_before.value,
                "glucose_after": glucose_after.value,
                "delta": delta,
                "flag": "possible_underbolus"
            })

    return {
        "count": len(flagged_meals),
        "flagged_meals": flagged_meals
    }