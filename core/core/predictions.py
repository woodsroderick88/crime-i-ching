"""Save, load, and score predictions using Streamlit file storage."""
import json
import hashlib
from datetime import datetime
from pathlib import Path

PREDICTIONS_FILE = Path("predictions.json")


def _load_raw() -> dict:
    if PREDICTIONS_FILE.exists():
        try:
            return json.loads(PREDICTIONS_FILE.read_text())
        except Exception:
            return {}
    return {}


def _save_raw(data: dict):
    PREDICTIONS_FILE.write_text(json.dumps(data, indent=2))


def save_prediction(record: dict) -> str:
    """Save a prediction. Returns its unique ID."""
    seed  = (
        f"{record['target_date']}|"
        f"{record['target_time']}|"
        f"{record['address']}|"
        f"{datetime.now().isoformat()}"
    )
    pred_id = hashlib.md5(seed.encode()).hexdigest()[:8].upper()
    record["id"]           = pred_id
    record["locked_at"]    = datetime.now().isoformat()

    data          = _load_raw()
    data[pred_id] = record
    _save_raw(data)
    return pred_id


def load_all_predictions() -> list[dict]:
    """Return all predictions as a list, newest first."""
    data = _load_raw()
    return sorted(
        data.values(),
        key=lambda x: x.get("locked_at", ""),
        reverse=True,
    )


def load_prediction(pred_id: str) -> dict | None:
    data = _load_raw()
    return data.get(pred_id)


def score_prediction(
    pred_id: str,
    actual_score: int,
    actual_label: str,
    actual_top_types: list[str],
) -> dict:
    """Score a prediction and save result."""
    data = _load_raw()
    if pred_id not in data:
        raise ValueError(f"Prediction {pred_id} not found.")

    pred = data[pred_id]
    pred["actual_score"]     = actual_score
    pred["actual_label"]     = actual_label
    pred["actual_top_types"] = actual_top_types
    pred["scored_date"]      = datetime.now().isoformat()

    # Determine Hit / Miss / Partial
    if pred["predicted_label"] == actual_label:
        pred["hit_miss"] = "HIT"
    elif _adjacent(pred["predicted_label"], actual_label):
        pred["hit_miss"] = "PARTIAL"
    else:
        pred["hit_miss"] = "MISS"

    pred["status"] = "scored"

    data[pred_id] = pred
    _save_raw(data)
    return pred


def _adjacent(a: str, b: str) -> bool:
    """Good-Good and Mixed are adjacent; Mixed and Bad-Bad are adjacent."""
    order = ["Good–Good ✅", "Mixed ⚖️", "Bad–Bad ⚠️"]
    try:
        return abs(order.index(a) - order.index(b)) == 1
    except ValueError:
        return False
