import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time as dtime
from core.geocoder import geocode
from core.empirical import compute_risk, timing_label
from core.iching import generate_hexagram, resonance

st.set_page_config(page_title="Chicago Crime + I-Ching", layout="wide", page_icon="☯️")

st.title("☯️  Chicago Risk Lens + I-Ching Reflection")
st.caption("Empirical crime risk (real data) paired with a symbolic I-Ching overlay. "
           "**Not a crime predictor.** A reflective awareness tool.")

with st.sidebar:
    st.header("📍 Inputs")
    date_in = st.date_input("Date", value=datetime.today())
    time_in = st.time_input("Time", value=dtime(23, 30))
    address = st.text_input("Street address", value="1200 N Clark St")
    radius = st.slider("Radius (meters)", 250, 2500, 1000, 250)
    days = st.slider("Look-back window (days)", 30, 365, 90, 30)
    go = st.button("🔮 Assess", type="primary", use_container_width=True)

if go:
    with st.spinner("Geocoding address..."):
        loc = geocode(address)
    if not loc:
        st.error("Could not geocode that address. Try a more specific Chicago address.")
        st.stop()
    lat, lon, full_addr = loc
    st.success(f"📌 {full_addr}")

    dt = datetime.combine(date_in, time_in)

    with st.spinner("Pulling Chicago crime data..."):
        risk = compute_risk(lat, lon, dt, radius_m=radius, days=days)

    hexa = generate_hexagram(str(date_in), str(time_in), address)
    label = timing_label(risk["score"])
    res = resonance(risk["score"], hexa["tone"])

    # Summary banner
    color = {"Bad–Bad ⚠️": "🔴", "Mixed ⚖️": "🟡", "Good–Good ✅": "🟢"}[label]
    st.markdown(f"## {color}  Timing: **{label}**")

    col1, col2 = st.columns([1, 1])

    # Empirical column
    with col1:
        st.subheader("📊 Empirical Risk")
        st.metric("Risk score", f"{risk['score']} / 100")
        st.metric("Confidence", risk["confidence"].upper())
        st.caption(f"Based on **{risk['n_window']}** incidents within ±1 hour, "
                   f"{radius}m radius, last {days} days.")

        if risk["top_types"]:
            df = pd.DataFrame(risk["top_types"])
            fig = px.bar(df, x="type", y="count",
                         text="pct", title="Top crime types at this space-time")
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No incidents recorded in this window.")

    # I-Ching column
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
        st.markdown(f"**Tone:** `{hexa['tone']}`  |  "
                    f"**Resonance with data:** `{res}`")
        st.caption("⚠️ The I-Ching layer is symbolic, not predictive. "
                   "It's offered as a reflective lens, not a forecast.")

    # Map
    if risk.get("raw"):
        st.subheader("🗺️ Recent incidents in radius")
        rows = []
        for c in risk["raw"]:
            if c.get("latitude") and c.get("longitude"):
                rows.append({
                    "lat": float(c["latitude"]),
                    "lon": float(c["longitude"]),
                    "type": c.get("primary_type", "?"),
                    "date": c.get("date", "")[:10],
                })
        if rows:
            mdf = pd.DataFrame(rows)
            fig = px.scatter_mapbox(
                mdf, lat="lat", lon="lon", color="type",
                hover_data=["date"], zoom=13, height=450,
                mapbox_style="open-street-map",
            )
            st.plotly_chart(fig, use_container_width=True)

    # Disclaimer
    with st.expander("ℹ️  Methodology & honest disclaimer"):
        st.markdown("""
- **Empirical layer** uses public Chicago Open Data Portal crime records.  
- **Risk score** is a heuristic from incident density at this space-time slice.  
- **I-Ching layer** is *deterministic* (same inputs → same hexagram) but has **no validated predictive power**.  
- This tool **must not** be used for policing, redlining, insurance, or discriminatory decisions.  
- Use it for personal awareness, education, or as a creative/contemplative artifact.
        """)
else:
    st.info("👈 Enter date, time, and a Chicago address, then click **Assess**.")
