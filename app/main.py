from fastapi import FastAPI

app = FastAPI(
    title="CGM Copilot API",
    description="Prototype API for glucose readings and simple analysis",
    version="0.1.0"
)


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.get("/glucose/current", summary="Get current glucose reading")
def glucose_current():
    return {
        "glucose": {
            "value": 7.8,
            "unit": "mmol/L",
            "trend": "stable"
        },
        "timestamp": "2026-03-14T12:05:00",
        "source": "mock"
    }


@app.get("/glucose/history", summary="Get recent glucose history")
def glucose_history():
    return {
        "readings": [
            {"value": 7.1, "timestamp": "2026-03-14T08:00:00"},
            {"value": 7.8, "timestamp": "2026-03-14T09:00:00"},
            {"value": 8.2, "timestamp": "2026-03-14T10:00:00"},
            {"value": 7.9, "timestamp": "2026-03-14T11:00:00"}
        ],
        "unit": "mmol/L"
    }


@app.get("/glucose/analysis", summary="Get simple glucose trend analysis")
def glucose_analysis():
    readings = [7.1, 7.8, 8.2, 7.9]

    first_value = readings[0]
    last_value = readings[-1]
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