"""Predictions page — view, score, and manage all locked predictions."""
import streamlit as st
import pandas as pd
from datetime import datetime
from core.geocoder import geocode
from core.empirical import compute_risk, timing_label, fetch_exact_window
from core.predictions import (
    load_all_predictions, score_prediction, load_prediction
)

st.set_page_config(page_title="Predictions", page_icon="📊", layout="wide")
st.title("📊 Predictions Dashboard")
st.caption("View locked predictions and score them after the target date passes.")

predictions = load_all_predictions()

if not predictions:
    st.info(
        "No predictions yet. Go to the main page, run an assessment "
        "on a FUTURE date, and click **Lock This as a Prediction**."
    )
    st.stop()

# ── Summary metrics ───────────────────────────────────────────
pending = [p for p in predictions if p["status"] == "pending"]
scored  = [p for p in predictions if p["status"] == "scored"]
hits    = [p for p in scored if p.get("hit_miss") == "HIT"]
partials= [p for p in scored if p.get("hit_miss") == "PARTIAL"]
misses  = [p for p in scored if p.get("hit_miss") == "MISS"]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total",    len(predictions))
c2.metric("Pending",  len(pending))
c3.metric("✅ Hits",  len(hits))
c4.metric("〰️ Partial", len(partials))
c5.metric("❌ Misses", len(misses))

if scored:
    hit_rate = len(hits) / len(scored)
    partial_rate = (len(hits) + 0.5 * len(partials)) / len(scored)
    st.progress(hit_rate, text=f"Hit rate: {hit_rate:.0%}  |  "
                               f"Weighted: {partial_rate:.0%}  |  "
                               f"Baseline (random): 33%")

st.divider()

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["⏳ Pending", "✅ Scored", "📋 All"])

# ── Pending predictions ───────────────────────────────────────
with tab1:
    if not pending:
        st.success("No pending predictions — all have been scored!")
    for pred in pending:
        target_dt = datetime.fromisoformat(
            f"{pred['target_date']}T{pred['target_time']}"
        )
        overdue = target_dt < datetime.now()
        badge   = "🔴 OVERDUE — ready to score!" if overdue else "🟡 Future"

        with st.expander(
            f"{badge}  |  {pred['target_date']} {pred['target_time']}  "
            f"|  {pred['address']}  |  ID: {pred['id']}"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Prediction (locked):**")
                st.markdown(f"- Label: `{pred['predicted_label']}`")
                st.markdown(f"- Score: `{pred['predicted_score']}/100`")
                st.markdown(
                    f"- Top types: "
                    f"`{', '.join(pred['predicted_top_types'][:2])}`"
                )
                st.markdown(f"- Hexagram: `{pred['hexagram_number']} "
                            f"— {pred['hexagram_name']}`")
                st.markdown(f"- Tone: `{pred['hexagram_tone']}`")
                st.markdown(f"- Resonance: `{pred['resonance']}`")
                if pred.get("note"):
                    st.markdown(f"- Note: *{pred['note']}*")

            with col2:
                if overdue:
                    st.markdown("**Score This Prediction:**")
                    st.caption(
                        "Fetch what ACTUALLY happened in the ±2 hour "
                        "window at this location."
                    )
                    if st.button(
                        f"🎯 Auto-score from Chicago data",
                        key=f"score_{pred['id']}",
                    ):
                        with st.spinner("Fetching actual crime data..."):
                            loc = geocode(pred["address"])
                            if not loc:
                                st.error("Could not geocode address.")
                            else:
                                lat, lon, _ = loc
                                actual = fetch_exact_window(
                                    lat, lon, target_dt,
                                    radius_m=pred.get("radius_m", 500),
                                    hours=2,
                                )
                                actual_score = min(
                                    100, len(actual) * 10
                                )
                                actual_label = timing_label(actual_score)
                                actual_types = list({
                                    c.get("primary_type", "UNKNOWN")
                                    for c in actual
                                })[:5]
                                result = score_prediction(
                                    pred["id"],
                                    actual_score,
                                    actual_label,
                                    actual_types,
                                )
                                verdict = result["hit_miss"]
                                emoji = {
                                    "HIT": "✅",
                                    "PARTIAL": "〰️",
                                    "MISS": "❌",
                                }[verdict]
                                st.success(
                                    f"{emoji} **{verdict}!**  "
                                    f"Predicted: `{pred['predicted_label']}`  "
                                    f"Actual: `{actual_label}`  "
                                    f"({len(actual)} incidents found)"
                                )
                                st.rerun()
                else:
                    days_left = (target_dt - datetime.now()).days
                    st.info(
                        f"⏳ {days_left} day(s) until this prediction "
                        f"can be scored."
                    )

# ── Scored predictions ────────────────────────────────────────
with tab2:
    if not scored:
        st.info("No scored predictions yet.")
    else:
        for pred in scored:
            verdict = pred.get("hit_miss", "?")
            emoji   = {"HIT": "✅", "PARTIAL": "〰️", "MISS": "❌"}.get(
                verdict, "❓"
            )
            with st.expander(
                f"{emoji} {verdict}  |  {pred['target_date']}  "
                f"|  {pred['address']}  |  ID: {pred['id']}"
            ):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Predicted:**")
                    st.markdown(f"- Label: `{pred['predicted_label']}`")
                    st.markdown(f"- Score: `{pred['predicted_score']}/100`")
                    st.markdown(
                        f"- Hexagram: `{pred['hexagram_number']} "
                        f"— {pred['hexagram_name']}`"
                    )
                    st.markdown(f"- Tone: `{pred['hexagram_tone']}`")
                with col2:
                    st.markdown("**Actual:**")
                    st.markdown(f"- Label: `{pred['actual_label']}`")
                    st.markdown(f"- Score: `{pred['actual_score']}/100`")
                    st.markdown(
                        f"- Types: "
                        f"`{', '.join(pred.get('actual_top_types', [])[:3])}`"
                    )
                    st.markdown(
                        f"- Scored: "
                        f"`{pred['scored_date'][:10] if pred.get('scored_date') else '?'}`"
                    )

# ── All predictions table ─────────────────────────────────────
with tab3:
    rows = []
    for p in predictions:
        rows.append({
            "ID":         p["id"],
            "Date":       p["target_date"],
            "Time":       p["target_time"],
            "Address":    p["address"][:30],
            "Predicted":  p["predicted_label"],
            "Hexagram":   p["hexagram_number"],
            "Tone":       p["hexagram_tone"],
            "Resonance":  p["resonance"],
            "Status":     p["status"].upper(),
            "Actual":     p.get("actual_label", "—"),
            "Hit/Miss":   p.get("hit_miss", "—"),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    # Download button
    df_export = pd.DataFrame(rows)
    csv = df_export.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV (for Julius AI / Claude analysis)",
        data=csv,
        file_name="synchronicity_log.csv",
        mime="text/csv",
    )
