"""Streamlit UI for the CV → job matching pipeline.

Run from the repo root: streamlit run app.py
"""

import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))
from rag_project_g2.config import get_settings  # noqa: E402
from rag_project_g2.pipeline import match_cv, read_cv_text  # noqa: E402

MAX_MATCHES = 1000
REGIONS = [
    "Stockholms län",
    "Uppsala län",
    "Södermanlands län",
    "Östergötlands län",
    "Jönköpings län",
    "Kronobergs län",
    "Kalmar län",
    "Gotlands län",
    "Blekinge län",
    "Skåne län",
    "Hallands län",
    "Västra Götalands län",
    "Värmlands län",
    "Örebro län",
    "Västmanlands län",
    "Dalarnas län",
    "Gävleborgs län",
    "Västernorrlands län",
    "Jämtlands län",
    "Västerbottens län",
    "Norrbottens län",
]


def extract_text(uploaded) -> str:
    with tempfile.NamedTemporaryFile(suffix=".pdf") as tmp:
        tmp.write(uploaded.getvalue())
        tmp.flush()
        return read_cv_text(tmp.name)


def place_of(job: dict) -> str:
    return (
        ", ".join(p for p in (job.get("municipality"), job.get("region")) if p)
        or "Location not specified"
    )


APP_CSS = """
<style>
:root { color-scheme: dark; }
.stApp {
  background: radial-gradient(ellipse at 5% 0%, rgba(57, 91, 173, .18), transparent 34%),
              radial-gradient(ellipse at 95% 0%, rgba(112, 59, 197, .16), transparent 32%),
              linear-gradient(145deg, #071326 0%, #08142a 56%, #0a1023 100%);
  color: #eef3ff;
}
[data-testid="stHeader"] { background: rgba(6, 14, 30, .65); }
.block-container { max-width: 1640px; padding-top: 2rem; padding-bottom: 3rem; }
h1 { font-size: clamp(2rem, 3vw, 2.8rem) !important; font-weight: 820 !important; letter-spacing: -.045em; }
h2 { font-size: 1.55rem !important; font-weight: 780 !important; letter-spacing: -.025em; }
[data-testid="stCaptionContainer"], [data-testid="stFileUploader"] small { color: #aab9d2 !important; }
/* Real Streamlit panel: widgets live inside this container, so the panel stays intact. */
.st-key-upload_panel {
  background: linear-gradient(135deg, rgba(15, 32, 59, .96), rgba(13, 24, 47, .96));
  border: 1px solid #2b456c; border-radius: 18px; padding: 1.1rem 1.25rem 1rem;
  margin: 1.2rem 0 1.1rem;
}
.st-key-upload_panel [data-testid="stFileUploader"] section {
  background: rgba(7, 20, 40, .62); border: 1px dashed #3b5a85; border-radius: 13px;
  padding: .75rem 1rem; min-height: 94px;
}
.st-key-upload_panel [data-testid="stFileUploaderDropzoneInstructions"] { color: #c6d5ed; }
.st-key-upload_panel [data-testid="stFileUploader"] section > button { border-radius: 9px; }
.stButton > button, .stLinkButton > a, [data-testid="stPopover"] > button {
  border-radius: 11px; border: 1px solid #355078; color: #edf4ff;
  background: rgba(14, 29, 53, .9); min-height: 43px; font-weight: 650;
  transition: border-color .15s ease, transform .15s ease, filter .15s ease;
}
.stButton > button:hover, .stLinkButton > a:hover, [data-testid="stPopover"] > button:hover {
  border-color: #82b4ff; color: white; transform: translateY(-1px);
}
.stButton > button[kind="primary"], .stLinkButton > a[kind="primary"] {
  border: 0; background: linear-gradient(110deg, #4b4bff, #8738ed 58%, #d82cb2);
  color: white; box-shadow: 0 7px 20px rgba(92, 70, 255, .2);
}
[data-testid="stPopoverBody"], [data-testid="stDialog"] > div > div {
  background: #0d1a31; border: 1px solid #2a4367; border-radius: 16px;
}
[data-testid="stProgress"] > div { background: #293750; border-radius: 999px; height: 8px; }
[data-testid="stProgress"] > div > div { background: linear-gradient(90deg, #11dda5, #27c9d5); border-radius: 999px; }
[data-testid="stAlert"] { border-radius: 12px; }
/* Card widths are controlled by the grid columns; never use a horizontal flex row here. */
[class*="st-key-card_"] {
  background: linear-gradient(150deg, rgba(15, 31, 56, .98), rgba(8, 19, 37, .98));
  border: 1px solid #2d476b !important; border-radius: 16px !important;
  padding: 1.1rem 1.05rem 1rem !important; min-height: 315px;
  box-shadow: 0 10px 24px rgba(0,0,0,.12);
}
[class*="st-key-card_"] [data-testid="stMarkdownContainer"] p { line-height: 1.45; }
[class*="st-key-card_"] [data-testid="stCaptionContainer"] { min-height: 3.1rem; }
[class*="st-key-card_"] [data-testid="stProgress"] { margin-top: .3rem; }
[class*="st-key-card_"] [data-testid="stHorizontalBlock"] { gap: .55rem; margin-top: .7rem; }
[class*="st-key-card_"] .stButton > button, [class*="st-key-card_"] .stLinkButton > a { width: 100%; padding-left: .35rem; padding-right: .35rem; }
.match-meta { color: #b6c5dd; padding: .3rem 0 1rem; font-size: .95rem; }
.search-pill { display:inline-block; padding:.22rem .65rem; margin:0 .25rem; border-radius:999px; background:#10284b; border:1px solid #244c80; color:#a9d6ff; }
.success-strip { display:flex; align-items:center; gap:.7rem; margin-top:.8rem; padding:.7rem .85rem;
  border-radius:11px; color:#35f0b1; font-weight:700; background:rgba(4, 87, 70, .2); border:1px solid #087b65; }
@media (max-width: 900px) { .block-container { padding-left: 1rem; padding-right: 1rem; } }
</style>
"""


@st.dialog("Job description", width="large")
def show_description(job: dict) -> None:
    st.subheader(job.get("title") or "Untitled position")
    st.caption(f"{job.get('employer') or 'Okänd arbetsgivare'} · {place_of(job)}")
    with st.container(height=380, border=True):
        st.markdown(
            (job.get("description") or "No description available.").replace(
                "\n", "  \n"
            )
        )
    st.link_button("↗  Apply for this job", job["url"], type="primary", width="stretch")


def job_card(job: dict, index: int) -> None:
    score = max(0.0, min(float(job.get("score", 0)), 1.0))
    title = job.get("title") or "Untitled position"
    employer = job.get("employer") or "Okänd arbetsgivare"
    with st.container(border=True, key=f"card_{job['id']}"):
        if index == 0:
            st.markdown(
                "<span style='display:inline-block;background:rgba(14,211,155,.15);border:1px solid #087d65;"
                "color:#39efb4;border-radius:999px;padding:3px 10px;font-size:.76rem;font-weight:750;margin-bottom:8px'>"
                "★ &nbsp; TOP MATCH</span>",
                unsafe_allow_html=True,
            )
        st.markdown(
            f"<div style='font-size:1.02rem;font-weight:760;line-height:1.4;min-height:2.8rem'>{title}</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"▦  {employer}\n\n⌖  {place_of(job)}")
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;gap:.5rem;align-items:center;color:#36edb0;"
            f"font-weight:750;margin-top:.6rem'><span>{job.get('match_level', 'Match')} ({score:.2f})</span><span>{score:.0%}</span></div>",
            unsafe_allow_html=True,
        )
        st.progress(score)
        desc_col, apply_col = st.columns(2, gap="small")
        if desc_col.button("▤ Description", key=f"desc_{job['id']}", width="stretch"):
            show_description(job)
        apply_col.link_button("➜ Apply", job["url"], type="primary", width="stretch")


st.set_page_config(page_title="CV Job Match", page_icon="💼", layout="wide")
st.markdown(APP_CSS, unsafe_allow_html=True)
st.markdown(
    "<h1>💼 <span style='background:linear-gradient(90deg,#f8fbff,#72b7ff 52%,#9a7bff);-webkit-background-clip:text;-webkit-text-fill-color:transparent'>CV Job Match</span></h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color:#b6c5dd;margin-top:-.6rem;font-size:1.02rem'>Upload your CV and discover relevant jobs from Arbetsförmedlingen (JobTech).</p>",
    unsafe_allow_html=True,
)

DEFAULT_REGION = "Hela Sverige"
DEFAULT_MIN_SCORE = get_settings().min_similarity
active_filters = sum(
    [
        st.session_state.get("region", DEFAULT_REGION) != DEFAULT_REGION,
        st.session_state.get("min_score", DEFAULT_MIN_SCORE) != DEFAULT_MIN_SCORE,
        st.session_state.get("remote_only", False),
    ]
)

with st.container(border=True, key="upload_panel"):
    st.markdown(
        "<div style='font-weight:750;color:#dce8fb;margin-bottom:.65rem'>▣ &nbsp; CV (PDF)</div>",
        unsafe_allow_html=True,
    )
    cv_col, filters_col, find_col = st.columns(
        [5.8, 1.25, 1.25], vertical_alignment="bottom", gap="medium"
    )
    uploaded = cv_col.file_uploader(
        "Choose a PDF", type=["pdf"], label_visibility="collapsed"
    )
    with filters_col.popover(
        f"Filters ({active_filters})" if active_filters else "Filters",
        icon=":material/tune:",
        key="filters",
        width="stretch",
    ):
        region = st.selectbox("Region", [DEFAULT_REGION, *REGIONS], key="region")
        min_score = st.slider(
            "Minimum match score",
            0.30,
            0.80,
            DEFAULT_MIN_SCORE,
            0.01,
            help="Weak ≥ 0.35 · Good ≥ 0.50 · Strong ≥ 0.60",
            key="min_score",
        )
        remote_only = st.checkbox("Remote only", key="remote_only")
    find = find_col.button(
        "⌕  Find jobs", type="primary", disabled=uploaded is None, width="stretch"
    )
    if uploaded is not None:
        st.markdown(
            f"<div class='success-strip'><span>✓</span><span>{uploaded.name} &nbsp;·&nbsp; {uploaded.size / 1024:.1f} KB</span>"
            "<span style='margin-left:auto'>Ready to match</span></div>",
            unsafe_allow_html=True,
        )

if find and uploaded:
    with st.status("Matching your CV…", expanded=True) as status:
        st.write("Reading CV…")
        cv_text = extract_text(uploaded)
        if not cv_text:
            status.update(label="Could not read any text from the PDF", state="error")
            st.stop()
        st.write("Searching JobTech, embedding new ads and ranking…")
        st.session_state.result = match_cv(
            cv_text,
            region=None if region == DEFAULT_REGION else region,
            remote_only=remote_only,
            top_k=MAX_MATCHES,
            min_score=min_score,
        )
        status.update(label="Done", state="complete", expanded=False)

result = st.session_state.get("result")
if result is not None:
    st.markdown(
        f"<div class='match-meta'>⌕ &nbsp; Search term <span class='search-pill'>{result.search_term}</span> · &nbsp;"
        f"{result.fetched} ads fetched &nbsp;·&nbsp; <span style='color:#37efb0;font-weight:700'>{result.stored} new ads stored</span></div>",
        unsafe_allow_html=True,
    )
    if not result.jobs:
        st.info(
            "No matching jobs found. Try a lower minimum score, another region, or turn off the remote filter."
        )
    else:
        head, sort_col = st.columns([5, 1.7], vertical_alignment="center")
        head.subheader(f"▤  {len(result.jobs)} matches")
        sort_by = sort_col.selectbox(
            "Sort jobs", ["Best match", "Lowest match"], label_visibility="collapsed"
        )
        jobs = sorted(
            result.jobs,
            key=lambda item: item.get("score", 0),
            reverse=sort_by == "Best match",
        )
        # Four equal-width cards per row. This prevents Streamlit's horizontal flex layout from shrinking cards.
        for start in range(0, len(jobs), 4):
            cols = st.columns(4, gap="medium")
            for col, (index, job) in zip(
                cols, enumerate(jobs[start : start + 4], start=start)
            ):
                with col:
                    job_card(job, index)
else:
    st.markdown(
        "<div style='margin-top:1rem;color:#8295b5;font-size:.94rem'>Your best matches will appear here once you upload a CV and select <b>Find jobs</b>.</div>",
        unsafe_allow_html=True,
    )
