# Utility to request a rerun regardless of the Streamlit version.
def _safe_rerun():
    """Trigger a script rerun using whichever API is available."""
    try:
        st.experimental_rerun()
    except AttributeError:
        # Streamlit >=1.18 renamed the method to st.rerun(); fall back to that.
        try:
            st.rerun()
        except AttributeError:
            # As a last resort raise the private RerunException, which exists in older versions.
            try:
                from streamlit.runtime.scriptrunner import RerunException
            except Exception:
                RerunException = None
            if RerunException is not None:
                raise RerunException()
            else:
                st.warning("Unable to auto-refresh the form; please manually reload the page to see loaded values.")
import streamlit as st
import toml
import json
import base64
from datetime import date
import streamlit.components.v1 as components

@st.cache_data
def load_config():
    return toml.load('config.toml')

config = load_config()

# ---------------------------------------------------------------------------
# Handle deferred base64 load.
# When a user clicks the "Load from base64" button we store the decoded JSON
# in st.session_state['pending_load'] and trigger an `experimental_rerun()`. On
# the next script run (i.e. here, before any widgets are instantiated) we see
# that flag and hydrate the relevant session_state keys so that widgets pick
# up the correct default values.  This approach avoids Streamlit's restriction
# on modifying a widget's value *after* it has been created.
# ---------------------------------------------------------------------------

if 'pending_load' in st.session_state:
    loaded = st.session_state.pop('pending_load')

    # Basic fields
    if 'release_date' in loaded:
        try:
            st.session_state['release_date'] = date.fromisoformat(loaded['release_date'])
        except Exception:
            pass
    if 'contact' in loaded:
        st.session_state['contact'] = loaded['contact']

    # Services selections and per-service data
    services_loaded = loaded.get('services', {})
    st.session_state['selected_services'] = list(services_loaded.keys())

    for svc, details in services_loaded.items():
        st.session_state[f"{svc}_config_only"] = details.get('config_only', False)
        st.session_state[f"{svc}_risk_level"] = details.get('risk_level', 'Low')
        st.session_state[f"{svc}_pr_links"] = "\n".join(details.get('pr_links', []))
        st.session_state[f"{svc}_design_links"] = "\n".join(details.get('design_links', []))
        st.session_state[f"{svc}_code_quality_links"] = "\n".join(details.get('code_quality_links', []))
        st.session_state[f"{svc}_additional_links"] = "\n".join(details.get('additional_links', []))

st.title("Reno - Release Note Templating Tool")

if st.button("Clear Form"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]

default_date = date.today()
if 'release_date' not in st.session_state:
    st.session_state['release_date'] = default_date

release_date = st.date_input("Provisional release date", value=st.session_state['release_date'], key='release_date')

contact = st.selectbox("Point of contact", config.get('contacts', {}).get('names', []), key='contact')

services = config.get('services', {}).get('names', [])

selected_services = st.multiselect("Select services", services, key='selected_services')

form_data = {
    "release_date": release_date.isoformat(),
    "contact": contact,
    "services": {}
}

for idx, service in enumerate(selected_services):
    if idx > 0:
        st.write("---")
    st.subheader(service)
    config_only = st.checkbox("Config only", key=f"{service}_config_only")
    risk_level = st.selectbox("Risk level", ["Low", "Medium", "High"], key=f"{service}_risk_level")
    pr_links = st.text_area("PR links (one per line)", key=f"{service}_pr_links")
    design_links = st.text_area("Design links (one per line)", key=f"{service}_design_links")
    code_quality_links = st.text_area("Code quality links (one per line)", key=f"{service}_code_quality_links")
    additional_links = st.text_area("Additional links (one per line)", key=f"{service}_additional_links")

    def parse_links(text):
        return [l.strip() for l in text.splitlines() if l.strip()]

    form_data["services"][service] = {
        "config_only": config_only,
        "risk_level": risk_level,
        "pr_links": parse_links(pr_links),
        "design_links": parse_links(design_links),
        "code_quality_links": parse_links(code_quality_links),
        "additional_links": parse_links(additional_links)
    }

st.write("### Form Data JSON")
json_str = json.dumps(form_data, indent=2)
st.code(json_str, language='json')

col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Export to base64"):
        b64 = base64.b64encode(json_str.encode()).decode()
        st.text_area("Base64 Encoded JSON", b64, height=200, key='export_b64')

with col2:
    input_b64 = st.text_area("Paste Base64", key='input_b64', height=200)
    if st.button("Load from base64"):
        try:
            decoded = base64.b64decode(input_b64).decode()
            data = json.loads(decoded)

            # Store and rerun so we can safely modify session_state *before* widgets are built
            st.session_state['pending_load'] = data
            _safe_rerun()
        except Exception as e:
            st.error(f"Error loading data: {e}")

with col3:
    # This HTML component injects a button that captures the visible Streamlit
    # app (the parent document) using html2canvas and triggers a JPEG download.
    components.html(
        """
        <style>
            .capture-btn {padding:0.5rem 1rem;border:none;border-radius:4px;background:#4CAF50;color:#fff;font-weight:600;cursor:pointer;}
        </style>
        <button class='capture-btn' id='capture-btn'>Save Form as JPEG</button>

        <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
        <script>
        (function() {
            const btn = document.getElementById('capture-btn');
            btn.addEventListener('click', async () => {
                try {
                    const topDoc = window.top.document;
                    const body = topDoc.body;
                    if (!body) {
                        alert('Cannot find page body to capture');
                        return;
                    }
                    const htmlEl = topDoc.documentElement;
                    const fullWidth = Math.max(body.scrollWidth, body.offsetWidth, htmlEl.clientWidth, htmlEl.scrollWidth, htmlEl.offsetWidth);
                    const fullHeight = Math.max(body.scrollHeight, body.offsetHeight, htmlEl.clientHeight, htmlEl.scrollHeight, htmlEl.offsetHeight);

                    const canvas = await html2canvas(body, {
                        useCORS: true,
                        backgroundColor: '#ffffff',
                        width: fullWidth,
                        height: fullHeight,
                        scrollX: 0,
                        scrollY: 0,
                    });
                    const link = topDoc.createElement('a');
                    link.download = 'form_snapshot.jpg';
                    link.href = canvas.toDataURL('image/jpeg', 0.92);
                    link.style.display = 'none';
                    topDoc.body.appendChild(link);
                    link.click();
                    topDoc.body.removeChild(link);
                } catch (err) {
                    console.error('Screenshot failed', err);
                    alert('Screenshot failed. Check console for details.');
                }
            });
        })();
        </script>
        """,
        height=80,
    )