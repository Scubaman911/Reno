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

    st.markdown(
        """
        <style>
        /* Base card styling */
        .reno-card {
            border:1px solid #e0e0e0;
            border-radius:8px;
            padding:1rem;
            margin-bottom:1rem;
            background:#ffffff;
            box-shadow:0 1px 3px rgba(0,0,0,0.08);
        }

        /* Ensure that *any* text (also inside links / list items) wraps within the card */
        .reno-card, .reno-card * {
            white-space: normal !important;
            overflow-wrap: anywhere !important;
            word-break: break-word !important;
        }

        .reno-card h4 {
            margin-top:0;
            margin-bottom:0.25rem;
        }

        .reno-meta {
            color:#555;
            font-size:0.9rem;
            margin-bottom:0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # We copy the list because we might mutate the session state while iterating.
    for note in list(st.session_state["release_notes"]):
        # Wrap each note in a styled card container – use custom CSS class so we can
        # control layout easily (e.g. wrapping of long content).
        st.markdown("<div class='reno-card'>", unsafe_allow_html=True)
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

        # Build an HTML snippet that lists **all** recorded information per service
        services_detail_html = ""

        if service_names:
            from html import escape

            field_order = [
                "version",
                "config_only",
                "risk_level",
                "benefit_level",
                "change_description",
                "known_issues",
                "pr_links",
                "design_links",
                "code_quality_links",
                "additional_links",
            ]

            field_labels = {
                "version": "Version",
                "config_only": "Config only",
                "risk_level": "Risk level",
                "benefit_level": "Benefit delivered",
                "change_description": "Change description",
                "known_issues": "Known issues / mitigations",
                "pr_links": "PR links",
                "design_links": "Design links",
                "code_quality_links": "Code quality links",
                "additional_links": "Additional links",
            }

            services_detail_html += "<div style=\"margin-top:0.5rem\">"

            for svc in service_names:
                details = data.get("services", {}).get(svc, {}) or {}

                services_detail_html += f"<h5 style=\"margin:0.25rem 0;\">{escape(svc)}</h5>"

                services_detail_html += "<ul style=\"margin:0 0 0.75rem 1rem; padding-left:0.5rem; font-size:0.9rem;\">"

                for field in field_order:
                    if field not in details:
                        continue

                    value = details.get(field)

                    # Normalise / format the value for display
                    if field == "config_only":
                        value_disp = "Yes" if value else "No"
                    elif isinstance(value, list):
                        if not value:
                            continue  # skip empty list
                        # Convert list to clickable links when they look like URLs
                        formatted_items = []
                        for item in value:
                            item = str(item).strip()
                            esc_item = escape(item)
                            if item.startswith("http://") or item.startswith("https://"):
                                formatted_items.append(f"<a href=\"{esc_item}\" target=\"_blank\">{esc_item}</a>")
                            else:
                                formatted_items.append(esc_item)
                        value_disp = "<br/>".join(formatted_items)
                    else:
                        # String / other scalar – escape & preserve line breaks
                        value_disp = escape(str(value)).replace("\n", "<br/>")

                    label = field_labels.get(field, field.title())
                    services_detail_html += f"<li><strong>{label}:</strong> {value_disp}</li>"

                services_detail_html += "</ul>"

            services_detail_html += "</div>"

        # Render card contents
        col_remove, col_content = st.columns([0.1, 0.9])

        with col_remove:
            if st.button("✖", key=f"remove_{note_id}", help="Delete this release note"):
                st.session_state["release_notes"] = [n for n in st.session_state["release_notes"] if n["id"] != note_id]
                _safe_rerun()

        with col_content:
            # Build a compact summary label for the collapsible card.
            summary_label = f"Release note – {date}  |  Contact: {contact}  |  Services: {services}"

            with st.expander(summary_label, expanded=False):
                # Full details only visible when expanded
                st.markdown(services_detail_html, unsafe_allow_html=True)

            # Close card wrapper
            st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Footer / house-keeping
# ---------------------------------------------------------------------------


with st.sidebar.expander("Debug – session state", expanded=False):
    # Helpful when developing the page – hidden by default.
    st.json({k: v for k, v in st.session_state.items() if k == "release_notes"})
