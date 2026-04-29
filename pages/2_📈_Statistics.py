"""Statistics page — hit rate analysis and pattern detection."""
import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from core.predictions import load_all_predictions

st.set_page_config(
    page_title="Statistics", page_icon="📈", layout="wide"
)
st.title("📈 Synchronicity Statistics")
st.caption(
    "Rigorous analysis of your prediction hit rate vs. random baseline. "
    "Minimum 10 scored predictions recommended for meaningful results."
)

predictions = load_all_predictions()
scored = [p for p in predictions if p["status"] == "scored"]

if len(scored) < 3:
    st.warning(
        f"You have **{len(scored)} scored prediction(s)**. "
        "You need at least **10** for meaningful statistics. "
        "Keep logging and scoring!"
    )
    if len(scored) == 0:
        st.stop()

# ── Build dataframe ───────────────────────────────────────────
rows = []
for p in scored:
    rows.append({
        "id":               p["id"],
        "date":             p["target_date"],
        "address":          p["address"],
        "predicted_label":  p["predicted_label"],
        "actual_label":     p.get("actual_label", "Unknown"),
        "predicted_score":  p.get("predicted_score", 0),
        "actual_score":     p.get("actual_score", 0),
        "hexagram":         p.get("hexagram_number", 0),
        "tone":             p.get("hexagram_tone", "unknown"),
        "resonance":        p.get("resonance", "LOW"),
        "hit_miss":         p.get("hit_miss", "MISS"),
    })
df = pd.DataFrame(rows)

# ── Hit rate section ──────────────────────────────────────────
st.header("🎯 Hit Rate Analysis")

total    = len(df)
hits     = (df["hit_miss"] == "HIT").sum()
partials = (df["hit_miss"] == "PARTIAL").sum()
misses   = (df["hit_miss"] == "MISS").sum()

hit_rate      = hits / total
weighted_rate = (hits + 0.5 * partials) / total
baseline      = 1 / 3

c1, c2, c3, c4 = st.columns(4)
c1.metric("Hit rate",        f"{hit_rate:.1%}")
c2.metric("Weighted rate",   f"{weighted_rate:.1%}",
          help="Partial = 0.5 hit")
c3.metric("Random baseline", f"{baseline:.1%}")
c4.metric("Edge over random",
          f"{(hit_rate - baseline):+.1%}")

# ── Statistical significance ──────────────────────────────────
st.subheader("📐 Statistical Significance")

p_val = None
try:
    from scipy.stats import binomtest
    result = binomtest(int(hits), total, p=baseline, alternative="greater")
    p_val  = result.pvalue

    if p_val < 0.05:
        st.success(
            f"✅ **Statistically significant!** p = {p_val:.4f} "
            f"(threshold: 0.05). Your hit rate of {hit_rate:.1%} is "
            f"unlikely to be random chance."
        )
    elif p_val < 0.10:
        st.warning(
            f"〰️ **Marginal signal.** p = {p_val:.4f}. "
            f"Suggestive but not conclusive. Keep collecting data."
        )
    else:
        st.info(
            f"❌ **Not significant.** p = {p_val:.4f}. "
            f"Current hit rate of {hit_rate:.1%} is consistent with "
            f"random chance. Need more data or a stronger signal."
        )

    col1, col2 = st.columns(2)
    with col1:
        st.metric("p-value",     f"{p_val:.4f}")
        st.metric("Sample size", total)
    with col2:
        st.metric("Hits",     hits)
        st.metric("Partials", partials)
        st.metric("Misses",   misses)

except ImportError:
    st.warning("scipy not installed — add it to requirements.txt")

st.caption(
    "⚠️ With fewer than 30 scored predictions, treat all findings as "
    "exploratory. p-values are unreliable on small samples."
)
st.divider()

# ── Charts ────────────────────────────────────────────────────
st.header("📊 Pattern Charts")

col1, col2 = st.columns(2)

with col1:
    verdict_counts = df["hit_miss"].value_counts().reset_index()
    verdict_counts.columns = ["Verdict", "Count"]
    fig = px.pie(
        verdict_counts, names="Verdict", values="Count",
        title="Hit / Partial / Miss Distribution",
        color="Verdict",
        color_discrete_map={
            "HIT":     "#22c55e",
            "PARTIAL": "#eab308",
            "MISS":    "#ef4444",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    tone_hits = (
        df.groupby("tone")
        .apply(lambda g: (g["hit_miss"] == "HIT").mean())
        .reset_index()
    )
    tone_hits.columns = ["Tone", "Hit Rate"]
    fig2 = px.bar(
        tone_hits, x="Tone", y="Hit Rate",
        title="Hit Rate by I-Ching Tone",
        color="Tone",
        color_discrete_map={
            "harmony": "#22c55e",
            "neutral": "#eab308",
            "danger":  "#ef4444",
        },
    )
    fig2.add_hline(
        y=baseline, line_dash="dash",
        annotation_text="Random baseline (33%)",
    )
    fig2.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    res_hits = (
        df.groupby("resonance")
        .apply(lambda g: (g["hit_miss"] == "HIT").mean())
        .reset_index()
    )
    res_hits.columns = ["Resonance", "Hit Rate"]
    fig3 = px.bar(
        res_hits, x="Resonance", y="Hit Rate",
        title="Hit Rate by Resonance Level",
        color="Resonance",
        color_discrete_map={
            "HIGH": "#22c55e",
            "LOW":  "#94a3b8",
        },
    )
    fig3.add_hline(y=baseline, line_dash="dash",
                   annotation_text="Baseline")
    fig3.update_yaxes(tickformat=".0%")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    fig4 = px.scatter(
        df, x="predicted_score", y="actual_score",
        color="hit_miss",
        title="Predicted Score vs. Actual Score",
        labels={
            "predicted_score": "Predicted Risk Score",
            "actual_score":    "Actual Risk Score",
            "hit_miss":        "Verdict",
        },
        color_discrete_map={
            "HIT":     "#22c55e",
            "PARTIAL": "#eab308",
            "MISS":    "#ef4444",
        },
    )
    max_val = max(
        df["predicted_score"].max(),
        df["actual_score"].max(), 1
    )
    fig4.add_shape(
        type="line", x0=0, y0=0, x1=max_val, y1=max_val,
        line=dict(dash="dash", color="gray"),
    )
    st.plotly_chart(fig4, use_container_width=True)

# ── Hexagram frequency ────────────────────────────────────────
st.subheader("☯️ Hexagram Frequency")
hex_counts = df["hexagram"].value_counts().reset_index()
hex_counts.columns = ["Hexagram", "Count"]
fig5 = px.bar(
    hex_counts.head(20), x="Hexagram", y="Count",
    title="Most Common Hexagrams in Your Readings",
)
st.plotly_chart(fig5, use_container_width=True)

expected = total / 64
if len(hex_counts) >= 5:
    st.caption(
        f"Expected frequency if uniform: ~{expected:.1f} per hexagram. "
        f"Any hexagram appearing much more often may indicate a "
        f"pattern — or just clustering in your address/time choices."
    )

# ── Honest assessment ─────────────────────────────────────────
st.divider()
st.subheader("🧠 Honest Assessment")

if total < 10:
    st.warning(
        "**Too early to draw conclusions.** "
        f"You have {total} scored prediction(s). "
        "Stats become meaningful at 30+."
    )
elif hit_rate > baseline + 0.15 and p_val is not None and p_val < 0.05:
    st.success(
        "**Promising signal detected.** Your system is outperforming "
        "random chance at a statistically significant level. "
        "Continue collecting data to validate. "
        "Consider running a control: same predictions WITHOUT I-Ching."
    )
elif hit_rate > baseline + 0.05:
    st.info(
        "**Slight edge over baseline.** Not yet significant. "
        "Keep logging — if this holds, it becomes interesting at 50+ samples."
    )
else:
    st.info(
        "**No signal detected above baseline.** "
        "This is the expected result for most divination systems. "
        "The tool still has reflective and contemplative value "
        "independent of statistical prediction power."
    )
