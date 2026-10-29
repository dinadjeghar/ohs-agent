"""Streamlit dashboard for the OHS agent.

    streamlit run dashboard.py

Shows one agent sweep: readings against limits, zone trends, worker PPE/fatigue and prioritized findings.
Data is simulated; limits are illustrative (see ohs_agent/standards.py).
"""
import altair as alt
import pandas as pd
import streamlit as st

from export_data import build_snapshot
from ohs_agent.tools import LEVELS, _level_for, _oxygen_level

st.set_page_config(page_title="OHS Safety Monitor", layout="wide")

METRICS = ["co_ppm", "h2s_ppm", "lel_pct", "o2_pct", "noise_dba", "temp_c"]
LEVEL_COLOR = {"normal": "#2a78d6", "warning": "#fab219", "danger": "#ec835a", "critical": "#d03b3b"}
LEVEL_LABEL = {"normal": "Normal", "warning": "Warning", "danger": "Danger", "critical": "Critical"}
ZONE_COLORS = ["#2a78d6", "#eb6834", "#1baf7a"]
color_scale = alt.Scale(domain=list(LEVEL_COLOR), range=list(LEVEL_COLOR.values()))


@st.cache_data
def load():
    return build_snapshot()


def level(key, value):
    return _oxygen_level(value) if key == "o2_pct" else _level_for(key, value)


def short(zone):
    return zone.split(" - ", 1)[-1]


snap = load()
T = snap["thresholds"]

st.title("OHS Safety Monitor")
st.caption("One sweep by the OHS agent: 3 zones, 3 workers. Simulated data, illustrative limits. "
           "Decision support only; it does not authorize entry into hazardous areas.")

# ---- Summary (plain markdown, no custom widgets, so it also renders through simple tunnels) ----
counts = {lv: sum(1 for f in snap["findings"] if f["level"] == lv) for lv in ("critical", "danger", "warning")}
c0, c1, c2, c3 = st.columns([2, 1, 1, 1])
c0.markdown(f"<div style='font-size:64px;font-weight:650;line-height:1'>{len(snap['findings'])}</div>"
            "<div>open findings to review</div>", unsafe_allow_html=True)
for col, lv in zip((c1, c2, c3), ("critical", "danger", "warning")):
    col.markdown(f"<div style='font-size:32px;font-weight:650;line-height:1.1'>{counts[lv]}</div>"
                 f"<div><span style='color:{LEVEL_COLOR[lv]}'>&#9632;</span> {LEVEL_LABEL[lv]}</div>",
                 unsafe_allow_html=True)

# ---- Readings against limits ----
st.subheader("Readings against limits")
st.caption("Bar colour shows severity. Rules mark the warning and limit values.")
cols = st.columns(3)
for i, key in enumerate(METRICS):
    t = T[key]
    df = pd.DataFrame([{"zone": short(z["zone"]), "value": z["readings"][key],
                        "level": level(key, z["readings"][key])} for z in snap["zones"]])
    if key == "o2_pct":
        base = alt.Chart(df).mark_circle(size=220).encode(
            x=alt.X("value:Q", scale=alt.Scale(domain=[17, 25]), title=f"{t['name']} ({t['unit']})"),
            y=alt.Y("zone:N", title=None),
            color=alt.Color("level:N", scale=color_scale, legend=None),
            tooltip=["zone", "value", "level"])
        rules = alt.Chart(pd.DataFrame({"v": [t["low_danger"], t["high_danger"]]})).mark_rule(
            color="#ec835a", strokeWidth=1.5).encode(x="v:Q")
        caption = f"Safe band {t['low_danger']} to {t['high_danger']} {t['unit']}"
    else:
        base = alt.Chart(df).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4, size=16).encode(
            x=alt.X("value:Q", title=f"{t['name']} ({t['unit']})"),
            y=alt.Y("zone:N", title=None),
            color=alt.Color("level:N", scale=color_scale, legend=None),
            tooltip=["zone", "value", "level"])
        rules = alt.Chart(pd.DataFrame({"v": [t["warn"], t["danger"]], "c": ["#fab219", "#ec835a"]})).mark_rule(
            strokeWidth=1.5).encode(x="v:Q", color=alt.Color("c:N", scale=None))
        caption = f"Warning {t['warn']}, limit {t['danger']} {t['unit']}"
    with cols[i % 3]:
        st.markdown(f"**{t['name']}**")
        st.caption(caption)
        st.altair_chart((base + rules).properties(height=140, width="container"))

with st.expander("View readings as a table"):
    table = pd.DataFrame([{"Zone": short(z["zone"]), **{T[k]["name"] + f" ({T[k]['unit']})": z["readings"][k]
                                                       for k in METRICS}} for z in snap["zones"]])
    st.dataframe(table, hide_index=True)

# ---- Trend ----
st.subheader("Trend by zone")
metric = st.selectbox("Metric", METRICS, format_func=lambda k: T[k]["name"])
t = T[metric]
rows = [{"reading": i - 11, "zone": short(z), "value": r[metric]}
        for z, hist in snap["history"].items() for i, r in enumerate(hist)]
hist_df = pd.DataFrame(rows)
zones_short = [short(z["zone"]) for z in snap["zones"]]
line = alt.Chart(hist_df).mark_line(strokeWidth=2).encode(
    x=alt.X("reading:Q", title="Readings ago (0 = now)", axis=alt.Axis(tickMinStep=1)),
    y=alt.Y("value:Q", title=f"{t['name']} ({t['unit']})", scale=alt.Scale(zero=metric != "o2_pct")),
    color=alt.Color("zone:N", scale=alt.Scale(domain=zones_short, range=ZONE_COLORS)),
    tooltip=["zone", "reading", "value"])
ref_vals = [t["low_danger"], t["high_danger"]] if metric == "o2_pct" else [t["warn"], t["danger"]]
refs = alt.Chart(pd.DataFrame({"v": ref_vals, "c": ["#fab219", "#ec835a"] if metric != "o2_pct" else ["#ec835a"] * 2})
                 ).mark_rule(strokeWidth=1.5).encode(y="v:Q", color=alt.Color("c:N", scale=None))
st.caption(t["source"])
st.altair_chart((line + refs).properties(height=320, width="container"))

# ---- Workers ----
st.subheader("Workers on shift")
wdf = pd.DataFrame([{
    "Worker": w["worker"], "Zone": short(w["zone"]), "Task": w["task"].replace("_", " "),
    "Missing PPE": ", ".join(w["ppe_missing"]) or "none",
    "Fatigue (PERCLOS)": w["perclos"], "Fatigue level": LEVEL_LABEL[w["fatigue_level"]],
    "Shift hours": w["shift_hours"],
} for w in snap["workers"]])
st.dataframe(wdf, hide_index=True)
st.caption("PERCLOS is the share of time the eyes are mostly closed. Warning at 0.15, danger at 0.30.")

# ---- Findings ----
st.subheader("Prioritized findings")
fdf = pd.DataFrame([{"severity": f["level"], "location": short(f["location"]), "finding": f["title"],
                     "basis": f["basis"], "action": f["action"]} for f in snap["findings"]])
st.download_button("Download briefing (CSV)", fdf.to_csv(index=False), file_name="ohs_briefing.csv", mime="text/csv")
for f in snap["findings"]:
    with st.container(border=True):
        st.markdown(f"<span style='color:{LEVEL_COLOR[f['level']]}'>&#9632;</span> **{LEVEL_LABEL[f['level']]}** "
                    f"&middot; {short(f['location'])}", unsafe_allow_html=True)
        st.markdown(f"**{f['title']}**")
        st.caption(f"Why it matters: {f['basis']}")
        st.write(f"Next step: {f['action']}")

st.caption("Limits are illustrative defaults based on commonly cited OSHA and NIOSH values. "
           "Verify against your site and local regulations.")
