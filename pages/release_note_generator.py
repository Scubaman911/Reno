"""
Reno – Release Note Generator (moved from the original single-page app).

This is the exact content that previously lived in `app.py`.  Apart from
updating the title in `st.set_page_config` to match the page name, the
implementation is unchanged.
"""

import streamlit as st

# Page configuration MUST be set before any other Streamlit calls.
st.set_page_config(page_title="Release Note Generator", page_icon="📝", layout="wide")

import toml
import json
import base64
from datetime import date


# Utility to trigger a rerun regardless of Streamlit version.


def _safe_rerun():
    """Trigger a script rerun using whichever API is available."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# ---------------------------------------------------------------------------
# Load configuration
# ---------------------------------------------------------------------------


@st.cache_data
def load_config():
    return toml.load("config.toml")


config = load_config()

# ---------------------------------------------------------------------------
# Handle deferred base64 load (populate session_state before widgets build)
# ---------------------------------------------------------------------------


if "pending_load" in st.session_state:
    loaded = st.session_state.pop("pending_load")

    # Basic fields
    if "release_date" in loaded:
        try:
            st.session_state["release_date"] = date.fromisoformat(loaded["release_date"])
        except Exception:
            pass
    if "contact" in loaded:
        st.session_state["contact"] = loaded["contact"]

    # Services selections and per-service data
    services_loaded = loaded.get("services", {})
    st.session_state["selected_services"] = list(services_loaded.keys())

    for svc, details in services_loaded.items():
        st.session_state[f"{svc}_config_only"] = details.get("config_only", False)
        st.session_state[f"{svc}_risk_level"] = details.get("risk_level", "Low")
        st.session_state[f"{svc}_benefit_level"] = details.get("benefit_level", "Low")
        st.session_state[f"{svc}_version"] = details.get("version", "")
        st.session_state[f"{svc}_known_issues"] = details.get("known_issues", "")
        st.session_state[f"{svc}_pr_links"] = "\n".join(details.get("pr_links", []))
        st.session_state[f"{svc}_change_description"] = details.get("change_description", "")
        st.session_state[f"{svc}_design_links"] = "\n".join(details.get("design_links", []))
        st.session_state[f"{svc}_code_quality_links"] = "\n".join(details.get("code_quality_links", []))
        st.session_state[f"{svc}_additional_links"] = "\n".join(details.get("additional_links", []))


# ---------------------------------------------------------------------------
# Page layout & styling
# ---------------------------------------------------------------------------


st.title("Reno – Release Note Generator")

# Custom CSS tweaks (bold tab titles, grey card background)
st.markdown(
    """
    <style>
    div[data-testid=\"stTabs\"] button {font-weight:700 !important;}
    div[data-testid=\"stTabs\"] div[data-testid=\"stVerticalBlock\"] {
        background-color:#fafafa; padding:1rem; border-radius:4px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Clear form button
if st.button("Clear Form", type="primary"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]

# ---------------------------------------------------------------------------
# Basic inputs
# ---------------------------------------------------------------------------


if "release_date" not in st.session_state:
    st.session_state["release_date"] = date.today()

release_date = st.date_input(
    "Release note date", value=st.session_state["release_date"], key="release_date"
)

contact = st.selectbox(
    "Point of contact", config.get("contacts", {}).get("names", []), key="contact"
)

services = config.get("services", {}).get("names", [])

selected_services = st.multiselect("Select services", services, key="selected_services")

# Add spacing before tabs
st.markdown("<div style='margin-top:1.25rem'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Build per-service UI & assemble JSON
# ---------------------------------------------------------------------------


form_data = {"release_date": release_date.isoformat(), "contact": contact, "services": {}}


def _parse_links(text: str):
    return [l.strip() for l in text.splitlines() if l.strip()]


if selected_services:
    tabs = st.tabs(selected_services)

    for tab, svc in zip(tabs, selected_services):
        with tab:
            st.subheader(svc)

            config_only = st.checkbox("Config only", key=f"{svc}_config_only")

            # Move change description above risk level
            change_description = st.text_area(
                "Change description", key=f"{svc}_change_description"
            )

            # Risk level selection
            risk_level = st.selectbox(
                "Risk level",
                ["Low", "Medium", "High"],
                key=f"{svc}_risk_level",
                help=(
                    "Low – simple change, config only or small function tweaks.\n"
                    "Medium – more significant changes to larger application components.\n"
                    "High – major changes across multiple components or non-backwards compatible modifications."
                ),
            )

            # Explanatory caption for selected risk level.
            risk_info_map = {
                "Low": "Simple change, config only or small function tweaks.",
                "Medium": "More significant changes to larger application components.",
                "High": "Major changes across multiple components or non-backwards-compatible modifications.",
            }
            st.caption(f"{risk_level}: {risk_info_map.get(risk_level, '')}")

            # Benefit delivered by change (shown below risk description)
            benefit_level = st.selectbox(
                "Benefit delivered by change",
                ["Low", "Medium", "High"],
                key=f"{svc}_benefit_level",
                help=(
                    "Low – Minor improvements or maintenance.\n"
                    "Medium – Noticeable value or efficiency gains.\n"
                    "High – Significant new features or major customer impact."
                ),
            )

            # Additional per-service fields
            version = st.text_input("Version", key=f"{svc}_version")

            known_issues = st.text_area(
                "Known issues, risks and mitigations", key=f"{svc}_known_issues"
            )
            pr_links = st.text_area("PR links (one per line)", key=f"{svc}_pr_links")
            design_links = st.text_area("Design links (one per line)", key=f"{svc}_design_links")
            code_quality_links = st.text_area(
                "Code quality links (one per line)", key=f"{svc}_code_quality_links"
            )
            additional_links = st.text_area(
                "Additional links (one per line)", key=f"{svc}_additional_links"
            )

            form_data["services"][svc] = {
                "config_only": config_only,
                "risk_level": risk_level,
                "benefit_level": benefit_level,
                "version": version,
                "known_issues": known_issues,
                "change_description": change_description,
                "pr_links": _parse_links(pr_links),
                "design_links": _parse_links(design_links),
                "code_quality_links": _parse_links(code_quality_links),
                "additional_links": _parse_links(additional_links),
            }


# ---------------------------------------------------------------------------
# Show JSON & base64 export/import
# ---------------------------------------------------------------------------


st.write("### Form Data JSON")
json_str = json.dumps(form_data, indent=2)
st.code(json_str, language="json")

col1, col2 = st.columns(2)

with col1:
    if st.button("Export to base64", type="secondary"):
        b64 = base64.b64encode(json_str.encode()).decode()
        st.text_area("Base64 Encoded JSON", b64, height=200, key="export_b64")

with col2:
    input_b64 = st.text_area("Paste Base64", key="input_b64", height=200)
    if st.button("Load from base64"):
        try:
            decoded = base64.b64decode(input_b64).decode()
            data = json.loads(decoded)

            st.session_state["pending_load"] = data
            _safe_rerun()
        except Exception as e:
            st.error(f"Error loading data: {e}")
