"""
Reno – Release Note Consolidator

This Streamlit page allows users to paste Base-64 encoded release note JSON
snippets (as produced by the *Release Note Generator* page) and build up a
collection of notes.  Every added note is rendered as a **Material style card**
showing the key metadata (date, contact, services).  Cards can be deleted at
any time – the UI updates immediately without losing the other entries.

The page only handles collecting / displaying the notes for now; the actual
"consolidation" logic (merging multiple notes into a single document) will be
implemented later.
"""

from __future__ import annotations

import base64
import json
import uuid
from typing import Dict, List

import streamlit as st


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------


st.set_page_config(page_title="Release Consolidator", page_icon="📄", layout="wide")

st.title("Reno – Release Note Consolidator")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_rerun():
    """Trigger a rerun whatever the Streamlit version is."""

    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


def _decode_b64_to_json(b64_str: str) -> Dict:
    """Decode a base-64 string produced by the generator back to a dict.

    Raises
    ------
    ValueError
        If the string cannot be decoded / parsed.
    """

    try:
        decoded = base64.b64decode(b64_str).decode()
        return json.loads(decoded)
    except Exception as err:
        raise ValueError("Invalid base64 encoded JSON.") from err


# Initialise session state
if "release_notes" not in st.session_state:
    # Each entry is {id: str, data: dict}
    st.session_state["release_notes"]: List[Dict] = []


# ---------------------------------------------------------------------------
# Sidebar – Add new release note via base64
# ---------------------------------------------------------------------------


st.sidebar.header("Add a Release Note")


with st.sidebar:
    st.text_area("Paste Base64 here", height=200, key="input_b64_sidebar")

    def _on_add_click():
        raw_input = st.session_state.get("input_b64_sidebar", "")

        if not raw_input.strip():
            st.warning("Please paste a Base64 string first.")
            return

        b64_strings = [line.strip() for line in raw_input.splitlines() if line.strip()]

        successes, failures = 0, 0

        for b64 in b64_strings:
            try:
                data = _decode_b64_to_json(b64)
                st.session_state["release_notes"].append(
                    {"id": str(uuid.uuid4()), "data": data}
                )
                successes += 1
            except ValueError:
                failures += 1

        if successes:
            st.success(f"Added {successes} release note(s) to the consolidator.")
        if failures:
            st.error(
                f"{failures} string(s) could not be decoded – please verify they are valid."
            )

        # Clear input for next add and rerun to refresh UI
        st.session_state["input_b64_sidebar"] = ""
        _safe_rerun()

    st.button(
        "Add to Consolidator",
        key="add_release_note",
        type="primary",
        on_click=_on_add_click,
    )


# ---------------------------------------------------------------------------
# Main area – Show cards & allow deletion
# ---------------------------------------------------------------------------


if not st.session_state["release_notes"]:
    st.info(
        "Use the sidebar to paste Base-64 encoded release notes (exported from the "
        "Release Note Generator).  They will appear here as individual cards."
    )
else:
    # Custom CSS for simple "Google material" style cards.
    st.markdown(
        """
        <style>
        .reno-card {
            border:1px solid #e0e0e0; border-radius:8px; padding:1rem; margin-bottom:1rem;
            background:#ffffff; box-shadow:0 1px 3px rgba(0,0,0,0.08);
        }
        .reno-card h4 {margin-top:0; margin-bottom:0.25rem;}
        .reno-meta {color:#555; font-size:0.9rem; margin-bottom:0.75rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # We copy the list because we might mutate the session state while iterating.
    for note in list(st.session_state["release_notes"]):
        data = note["data"]
        note_id = note["id"]

        # Build basic summary information
        date = data.get("release_date", "N/A")
        contact = data.get("contact", "-")

        # Prepare service list as comma-separated value for the metadata row
        service_names = list(data.get("services", {}).keys())
        services = ", ".join(service_names) or "-"

        # ------------------------------------------------------------------
        # Build per-service details (version & change description)
        # ------------------------------------------------------------------

        services_detail_html = ""

        if service_names:
            from html import escape

            services_detail_html += "<div style=\"margin-top:0.5rem\">"
            for svc in service_names:
                details = data.get("services", {}).get(svc, {}) or {}

                version = escape(str(details.get("version", "-")))
                change_desc_raw = details.get("change_description", "") or ""
                change_desc = escape(change_desc_raw).replace("\n", "<br/>")

                services_detail_html += (
                    f"<p style=\"margin:0 0 0.5rem 0;\"><b>{escape(svc)}</b> – {version}<br/>"
                    f"{change_desc}</p>"
                )

            services_detail_html += "</div>"

        # Render card contents
        col_remove, col_content = st.columns([0.1, 0.9])

        with col_remove:
            if st.button("✖", key=f"remove_{note_id}", help="Delete this release note"):
                st.session_state["release_notes"] = [n for n in st.session_state["release_notes"] if n["id"] != note_id]
                _safe_rerun()

        with col_content:
            st.markdown(
                f"""
                <div class="reno-card">
                    <h4>Release note – {date}</h4>
                    <div class="reno-meta"><b>Contact:</b> {contact} &nbsp;|&nbsp; <b>Services:</b> {services}</div>
                    {services_detail_html}
                """,
                unsafe_allow_html=True,
            )

            # Show the JSON inside an expander
            with st.expander("Show full JSON"):
                st.json(data, expanded=False)

            # Close div opened in markdown above
            st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer / house-keeping
# ---------------------------------------------------------------------------


with st.sidebar.expander("Debug – session state", expanded=False):
    # Helpful when developing the page – hidden by default.
    st.json({k: v for k, v in st.session_state.items() if k == "release_notes"})
