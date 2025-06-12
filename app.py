"""
Reno – Landing Page

This is the main entry point for the multi-page Streamlit application.
It simply acts as a landing page that lets the user pick between the
different tools bundled with Reno.  For now we expose two tools:

1. Release Note Generator – the original form that was previously in
   `app.py` (now moved to `pages/release_note_generator.py`).
2. Release Consolidator – placeholder page for upcoming functionality.
"""

import streamlit as st


# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------


st.set_page_config(
    page_title="Reno – Home",
    page_icon="🎛️",
)

# ---------------------------------------------------------------------------
# Landing page content
# ---------------------------------------------------------------------------


st.title("Reno")
st.subheader("Pick a tool to get started.")


def _switch_page(page_name: str):
    """Attempt to switch pages programmatically.

    This uses `st.switch_page` when available (Streamlit >= 1.20).
    When not available we display a short help message so that users
    can still navigate via the sidebar.
    """

    if hasattr(st, "switch_page"):
        try:
            st.switch_page(page_name)
        except Exception as e:  # pragma: no cover – defensive only
            st.error(f"Unable to open page: {e}")
    else:
        st.info("Use the navigation menu on the left to open the selected page.")


col1, col2 = st.columns(2)

with col1:
    if st.button("📝 Release Note Generator", use_container_width=True):
        # File names are used for navigation, but Streamlit also accepts the
        # human-readable page title. We go with the title to remain stable if
        # the file gets renamed.
        _switch_page("pages/release_note_generator.py")

with col2:
    if st.button("📄 Release Consolidator", use_container_width=True):
        _switch_page("pages/release_consolidator.py")


st.markdown(
    """
---

ℹ️  You can always access the same pages from the navigation menu on the left.
"""
)
