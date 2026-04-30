import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time as dtime
from core.geocoder import geocode
from core.empirical import compute_risk, timing_label
from core.iching import generate_hexagram, resonance
from core.predictions import save_prediction, load_all_predictions
from core.environment import get_environment

st.set_page_config(
    page_title="Chicago Risk Lens + I-Ching",
    layout="wide",
    page_icon="☯️",
)

st.title("☯️  Chicago Risk Lens + I-Ching Reflection")
st.caption(
    "Empirical crime risk + environmental context + I-Ching overlay. "
    "**Not a crime predictor.** A multi-layer reflective awareness tool."
)

# ── Sidebar inputs ────────────────────────────────────────────
with st.sidebar:
    st.header("📍 Inputs")
    date_in  = st.date_input("Date", value=datetime.today())
    time_in  = st.time_input("Time", value=dtime(23, 30))
    address  = st.text_input("Street address", value="1200 N Clark St")
    radius   = st.slider("Radius (meters)", 250, 2500, 1000, 250)
    days     = st.slider("Look-back window (days)", 30, 365, 90, 30)
    use_env  = st.checkbox("🌐 Include environmental factors", value=True)
    go       = st.button("🔮 Assess", type="primary", use_container_width=True)

# ── Main logic ────────────────────────────────────────────────
if go:
    with st.spinner("Geocoding address..."):
        loc = geocode(address)
    if not loc:
        st.error(
            "Could not geocode that address. "
            "Try a specific Chicago address like '7559 S State St'."
        )
        st.stop()
    lat, lon, full_addr = loc
    st.success(f"📌 {full_addr}")

    dt = datetime.combine(date_in, time_in)

    # ── Environmental data ────────────────────────────────────
    env = None
    env_mod = 0
    if use_env:
        with st.spinner("Fetching weather, sunset, lunar data..."):
            env = get_environment(lat, lon, dt)
            env_mod = env["modifiers"]["total"]

    # ── Crime risk ────────────────────────────────────────────
    with st.spinner("Pulling Chicago crime data..."):
        risk = compute_risk(
            lat, lon, dt, radius_m=radius,
            days=days, env_modifier=env_mod,
        )

    # ── I-Ching ───────────────────────────────────────────────
    hexa  = generate_hexagram(str(date_in), str(time_in), address)
    label = timing_label(risk["score"])
    res   = resonance(risk["score"], hexa["tone"])

    # ── Summary banner ────────────────────────────────────────
    color = {
        "Bad–Bad ⚠️":    "🔴",
        "Mixed ⚖️":      "🟡",
        "Good–Good ✅":  "🟢",
    }[label]
    st.markdown(f"## {color}  Timing: **{label}**")

    # ── Environmental context box ─────────────────────────────
    if env:
        with st.container(border=True):
            st.subheader("🌐 Environmental Context")
            ec1, ec2, ec3, ec4 = st.columns(4)

            w = env["weather"]
            ec1.metric(
                "🌡️ Weather",
                f"{w['temp_f']}°F" if w['temp_f'] else "Unknown",
                help=w["conditions"],
            )

            s = env["sun"]
            sunset_str = (
                s["sunset"].strftime("%H:%M")
                if s["sunset"] else "?"
            )
            ec2.metric(
                "🌅 Sunset / Dark",
                sunset_str,
                "🌙 Dark" if s["is_dark"] else "☀️ Daytime",
            )

            l = env["lunar"]
            ec3.metric(
                f"{l['emoji']} Lunar",
                l["phase_name"],
                f"{l['illumination']}% lit",
            )

            mods = env["modifiers"]
            ec4.metric(
                "📊 Risk Adjust",
                f"{mods['total']:+d}",
                help=(
                    f"Weather: {mods['weather']:+d} | "
                    f"Darkness: {mods['darkness']:+d} | "
                    f"Lunar: {mods['lunar']:+d}"
                ),
            )

    col1, col2 = st.columns(2)

    # ── Empirical column ──────────────────────────────────────
    with col1:
        st.subheader("📊 Empirical Risk")
        st.metric(
            "Risk score",
            f"{risk['score']} / 100",
            delta=(
                f"{risk['env_modifier']:+d} env adj."
                if risk['env_modifier'] != 0 else None
            ),
        )
        st.metric("Confidence", risk["confidence"].upper())
        st.caption(
            f"Base score: **{risk['base_score']}/100** "
            f"(from {risk['n_window']} incidents in ±1 hour, "
            f"{radius}m, {days} days). "
            f"Environmental adj: **{risk['env_modifier']:+d}**."
        )

        if risk["top_types"]:
            df  = pd.DataFrame(risk["top_types"])
            fig = px.bar(
                df, x="type", y="count", text="pct",
                title="Top crime types at this space-time",
            )
            fig.update_traces(
                texttemplate="%{text}%", textposition="outside",
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incidents recorded in this window.")

    # ── I-Ching column ────────────────────────────────────────
    with col2:
        st.subheader("☯️ I-Ching Reflection")
        st.markdown(
            f"### Hexagram {hexa['number']} — *{hexa['name']}* "
            f"({hexa['title']})"
        )
        st.code(hexa["ascii"], language="text")
        st.markdown(f"> {hexa['theme']}")
        if hexa["changing"]:
            st.markdown(f"**Changing lines:** {hexa['changing']}")
        st.markdown(
            f"**Tone:** `{hexa['tone']}`  |  "
            f"**Resonance with data:** `{res}`"
        )
        st.caption(
            "⚠️ The I-Ching layer is symbolic, not predictive. "
            "It is offered as a reflective lens, not a forecast."
        )

    # ── Map ───────────────────────────────────────────────────
    if risk.get("raw"):
        st.subheader("🗺️ Recent incidents in radius")
        rows = [
            {
                "lat":  float(c["latitude"]),
                "lon":  float(c["longitude"]),
                "type": c.get("primary_type", "?"),
                "date": c.get("date", "")[:10],
            }
            for c in risk["raw"]
            if c.get("latitude") and c.get("longitude")
        ]
        if rows:
            mdf = pd.DataFrame(rows)
            fig = px.scatter_mapbox(
                mdf, lat="lat", lon="lon", color="type",
                hover_data=["date"], zoom=13, height=450,
                mapbox_style="open-street-map",
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Lock Prediction ───────────────────────────────────────
    st.divider()
    st.subheader("🔒 Lock This as a Prediction")
    st.caption(
        "Save this reading NOW before the target date arrives. "
        "Return after the date passes to score it as Hit or Miss."
    )

    with st.expander("Lock this prediction →"):
        pred_note = st.text_area(
            "Optional note:",
            placeholder="e.g. I will be near here Saturday night...",
        )
        future_only = dt > datetime.now()
        if not future_only:
            st.warning(
                "⚠️ Target date is in the past. "
                "Predictions work best for FUTURE dates."
            )
        lock_btn = st.button("💾 Save Prediction", type="primary")
        if lock_btn:
            record = {
                "target_date":      str(date_in),
                "target_time":      str(time_in),
                "address":          address,
                "full_address":     full_addr,
                "lat":              lat,
                "lon":              lon,
                "radius_m":         radius,
                "days_lookback":    days,
                "predicted_score":  risk["score"],
                "base_score":       risk["base_score"],
                "env_modifier":     risk["env_modifier"],
                "predicted_label":  label,
                "predicted_top_types": [
                    t["type"] for t in risk["top_types"]
                ],
                "hexagram_number":  hexa["number"],
                "hexagram_name":    hexa["name"],
                "hexagram_tone":    hexa["tone"],
                "resonance":        res,
                "weather":          (
                    env["weather"]["conditions"] if env else None
                ),
                "temp_f":           (
                    env["weather"]["temp_f"] if env else None
                ),
                "is_dark":          (
                    env["sun"]["is_dark"] if env else None
                ),
                "lunar_phase":      (
                    env["lunar"]["phase_name"] if env else None
                ),
                "note":             pred_note,
                "status":           "pending",
                "actual_score":     None,
                "actual_label":     None,
                "actual_top_types": None,
                "hit_miss":         None,
                "scored_date":      None,
            }
            pred_id = save_prediction(record)
            st.success(
                f"✅ Prediction saved!  ID: `{pred_id}`  "
                f"Go to **📊 Predictions** page to score it later."
            )

    # ── Disclaimer ────────────────────────────────────────────
    with st.expander("ℹ️  Methodology & honest disclaimer"):
        st.markdown("""
- **Empirical layer:** Chicago Open Data Portal crime records.
- **Environmental layer:** NWS weather + astronomical calculations.
- **Symbolic layer:** Deterministic I-Ching hexagram (no validated predictive power).
- This tool **must not** be used for policing, insurance, or discrimination.
- Use it for personal awareness, education, or contemplative practice.
        """)

else:
    st.info("👈 Enter date, time, and a Chicago address, then click **Assess**.")
