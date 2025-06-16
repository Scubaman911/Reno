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

    st.button(
        "Add to Consolidator",
        key="add_release_note",
        type="primary",
        on_click=_on_add_click,
    )
    # Clear all notes and reset input
    def _on_clear_click():
        st.session_state["release_notes"] = []
        st.session_state["input_b64_sidebar"] = ""
        _safe_rerun()
    st.button(
        "Clear Form",
        key="clear_form",
        type="secondary",
        on_click=_on_clear_click,
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
    # ------------------------------------------------------------------
    # Inject card styling – ensure long content wraps inside the card
    # ------------------------------------------------------------------

    # We copy the list because we might mutate the session state while iterating.
    for note in list(st.session_state["release_notes"]):
        # Wrap each note in a styled card container – use custom CSS class so we can
        # control layout easily (e.g. wrapping of long content).
        data = note["data"]
        st.json(note)
        
        with st.container(border=True):
            st.subheader(f"Release Note: {data['release_date']}", divider="gray")

            service_names = list(data.get("services", {}).keys())
            services = " | ".join(service_names) or "-"
            st.text(f"Services in release:  {services}")
            st.text(f"Point of contact:  {data['contact']}")

            with st.expander("Release Details..."):
                tabs = st.tabs(service_names)
                for tab in tabs:
                    with tab:
                        st.text("words")

                


# ---------------------------------------------------------------------------
# Footer / house-keeping
# ---------------------------------------------------------------------------


with st.sidebar.expander("Debug – session state", expanded=False):
    # Helpful when developing the page – hidden by default.
    st.json({k: v for k, v in st.session_state.items() if k == "release_notes"})
