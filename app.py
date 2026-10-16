import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="CareTrace AI | The Forgotten Patient",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Soft pastel theme styling
st.markdown("""
<style>
.stApp { background: #FAF8FF; color: #40365B; }
[data-testid="stSidebar"] { background: #F0EBFC; }
.block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
h1, h2, h3 { color: #493B70; }
[data-testid="stMetric"] {
    background: white; border: 1px solid #E8E0F3;
    padding: 16px; border-radius: 16px;
    box-shadow: 0 5px 18px rgba(113, 91, 157, 0.06);
}
div[data-testid="stDataFrame"] { border: 1px solid #E8E0F3; border-radius: 12px; }
.small-note { color: #817795; font-size: 0.88rem; }
</style>
""", unsafe_allow_html=True)

ROOT = Path(__file__).parent

@st.cache_data
def load_data():
    patients = pd.read_csv(ROOT / "patients.csv")
    encounters = pd.read_csv(ROOT / "encounters.csv")
    departments = pd.read_csv(ROOT / "departments.csv")
    tests = pd.read_csv(ROOT / "diagnostic_tests.csv")

    # Parse timestamp fields where available
    for col in ["arrival_time", "service_start_time", "service_end_time", "discharge_time"]:
        if col in encounters.columns:
            encounters[col] = pd.to_datetime(encounters[col], errors="coerce")
    for col in ["requested_time", "completion_time"]:
        if col in tests.columns:
            tests[col] = pd.to_datetime(tests[col], errors="coerce")

    joined = encounters.merge(patients, on="patient_id", how="left")
    joined = joined.merge(departments, on="department_id", how="left")
    return patients, encounters, departments, tests, joined

try:
    patients, encounters, departments, tests, joined = load_data()
except Exception as e:
    st.error("Could not load the CSV files. Check that all four CSVs are in the same folder as app.py.")
    st.exception(e)
    st.stop()

st.title("🩺 CareTrace AI")
st.subheader("The Forgotten Patient | Patient Care Gap Monitoring")
st.markdown(
    "A data-driven prototype to help hospital teams review long waits, encounters that ended before care, "
    "and diagnostic-test turnaround. **Flags support human review; they are not clinical decisions.**"
)

st.warning(
    "Synthetic educational dataset only — not real patient data and not suitable for clinical decisions."
)

# Sidebar filters
st.sidebar.header("Explore encounters")
department_options = ["All departments"] + sorted(
    joined["department_name"].dropna().astype(str).unique().tolist()
)
selected_department = st.sidebar.selectbox("Department", department_options)

outcome_options = ["All outcomes"] + sorted(joined["outcome"].dropna().astype(str).unique().tolist())
selected_outcome = st.sidebar.selectbox("Encounter outcome", outcome_options)

triage_options = ["All triage levels"] + sorted(joined["triage_level"].dropna().astype(str).unique().tolist())
selected_triage = st.sidebar.selectbox("Triage level", triage_options)

wait_threshold = st.sidebar.slider("Long-wait threshold (minutes)", 15, 180, 60, 5)
search_id = st.sidebar.text_input("Search patient or encounter ID").strip().upper()

filtered = joined.copy()
if selected_department != "All departments":
    filtered = filtered[filtered["department_name"] == selected_department]
if selected_outcome != "All outcomes":
    filtered = filtered[filtered["outcome"].astype(str) == selected_outcome]
if selected_triage != "All triage levels":
    filtered = filtered[filtered["triage_level"].astype(str) == selected_triage]
if search_id:
    filtered = filtered[
        filtered["patient_id"].astype(str).str.upper().str.contains(search_id, na=False)
        | filtered["encounter_id"].astype(str).str.upper().str.contains(search_id, na=False)
    ]

left_before_care = filtered["outcome"].astype(str).str.lower().eq("left before care").sum()
long_wait = filtered["wait_minutes"].fillna(0).gt(wait_threshold).sum()
wait_rate = (long_wait / len(filtered) * 100) if len(filtered) else 0
avg_wait = filtered["wait_minutes"].mean() if len(filtered) else 0

m1, m2, m3, m4 = st.columns(4)
m1.metric("Patients in dataset", f"{patients['patient_id'].nunique():,}")
m2.metric("Filtered encounters", f"{len(filtered):,}")
m3.metric("Left before care", f"{left_before_care:,}")
m4.metric(f"Wait > {wait_threshold} min", f"{long_wait:,}", f"{wait_rate:.1f}% of filtered encounters")

st.caption("KPIs and charts respond to the filters in the sidebar.")

tab1, tab2, tab3 = st.tabs(["Overview", "Care-gap review queue", "Diagnostic tests"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        outcome_counts = filtered["outcome"].fillna("Unknown").value_counts().rename_axis("Outcome").reset_index(name="Encounters")
        fig = px.bar(
            outcome_counts, x="Outcome", y="Encounters", color="Outcome",
            title="Encounter outcomes", color_discrete_sequence=["#A995E8", "#F2A8C8", "#9BCFF2", "#F5D98B"]
        )
        fig.update_layout(showlegend=False, plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        wait_data = filtered[filtered["wait_minutes"].notna()].copy()
        fig = px.histogram(
            wait_data, x="wait_minutes", nbins=30,
            title="Waiting-time distribution", labels={"wait_minutes": "Wait (minutes)"},
            color_discrete_sequence=["#9B83DF"]
        )
        fig.add_vline(x=wait_threshold, line_dash="dash", line_color="#C46C8D",
                      annotation_text="Selected threshold")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    c3, c4 = st.columns(2)
    with c3:
        dept_summary = filtered.groupby("department_name", dropna=False).agg(
            Encounters=("encounter_id", "count"),
            Average_wait=("wait_minutes", "mean")
        ).reset_index().sort_values("Encounters", ascending=False)
        fig = px.bar(
            dept_summary, x="department_name", y="Encounters",
            title="Encounters by department", color_discrete_sequence=["#9BCFF2"]
        )
        fig.update_layout(xaxis_title="", plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    with c4:
        st.metric("Average wait (minutes)", f"{avg_wait:.1f}" if pd.notna(avg_wait) else "N/A")
        st.markdown("**How to interpret this dashboard**")
        st.write(
            "- Long-wait flags identify encounters for review using the selected threshold.\n"
            "- “Left before care” is a recorded outcome, not proof of why the patient left.\n"
            "- Department comparisons are descriptive and do not establish causation."
        )

with tab2:
    st.markdown("### Encounters for staff review")
    queue = filtered.copy()
    queue["review_reason"] = ""
    queue.loc[queue["wait_minutes"].fillna(0).gt(wait_threshold), "review_reason"] += "Wait exceeds threshold; "
    queue.loc[queue["outcome"].astype(str).str.lower().eq("left before care"), "review_reason"] += "Left before care outcome; "
    queue["review_reason"] = queue["review_reason"].str.strip()
    queue = queue[queue["review_reason"] != ""].copy()
    queue = queue.sort_values(["wait_minutes"], ascending=False, na_position="last")

    st.caption(f"{len(queue):,} encounters meet at least one review rule in the current filter.")
    display_cols = [
        c for c in [
            "encounter_id", "patient_id", "arrival_time", "department_name",
            "triage_level", "wait_minutes", "outcome", "review_reason"
        ] if c in queue.columns
    ]
    st.dataframe(queue[display_cols], use_container_width=True, hide_index=True)
    if not queue.empty:
        st.download_button(
            "Download filtered review queue as CSV",
            data=queue[display_cols].to_csv(index=False).encode("utf-8"),
            file_name="caretrace_review_queue.csv",
            mime="text/csv",
        )

with tab3:
    st.markdown("### Diagnostic-test turnaround")
    test_view = tests.copy()
    if "requested_time" in test_view.columns and "completion_time" in test_view.columns:
        test_view["turnaround_minutes"] = (
            test_view["completion_time"] - test_view["requested_time"]
        ).dt.total_seconds() / 60
        test_view.loc[test_view["turnaround_minutes"] < 0, "turnaround_minutes"] = pd.NA

    test_encounters = encounters[["encounter_id", "patient_id", "department_id", "outcome"]].drop_duplicates()
    test_view = test_view.merge(test_encounters, on="encounter_id", how="left")
    if selected_department != "All departments":
        selected_dept_ids = departments.loc[
            departments["department_name"] == selected_department, "department_id"
        ].tolist()
        test_view = test_view[test_view["department_id"].isin(selected_dept_ids)]
    if "turnaround_minutes" in test_view.columns:
        valid_turnaround = test_view["turnaround_minutes"].dropna()
        avg_turnaround = valid_turnaround.mean() if len(valid_turnaround) else float("nan")
        st.metric("Average test turnaround (minutes)", f"{avg_turnaround:.1f}" if pd.notna(avg_turnaround) else "N/A")
        c1, c2 = st.columns(2)
        with c1:
            type_summary = test_view.groupby("test_type").agg(
                Tests=("test_id", "count"),
                Average_turnaround=("turnaround_minutes", "mean")
            ).reset_index().sort_values("Average_turnaround", ascending=False)
            fig = px.bar(type_summary, x="test_type", y="Average_turnaround",
                         title="Average turnaround by test type",
                         color_discrete_sequence=["#F2A8C8"])
            fig.update_layout(xaxis_title="", yaxis_title="Minutes", plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.histogram(test_view, x="turnaround_minutes", nbins=30,
                               title="Test turnaround distribution",
                               color_discrete_sequence=["#9BCFF2"])
            fig.update_layout(xaxis_title="Minutes", plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
    test_cols = [c for c in ["test_id", "encounter_id", "test_type", "priority", "requested_time", "completion_time", "turnaround_minutes"] if c in test_view.columns]
    st.dataframe(test_view[test_cols].head(500), use_container_width=True, hide_index=True)
    st.caption("Table is capped at 500 rows for readability.")

st.divider()
st.markdown(
    "<div class='small-note'>CareTrace AI · DATATHON Round 1 prototype · Synthetic data only · "
    "Use flags to support human review, not to make clinical decisions.</div>",
    unsafe_allow_html=True
)
