"""
White Corporate Executive Theme for Project Allianz Data Quality Dashboard.
Maintains the exact corporate font from the reference screenshot ('Segoe UI', 'Plus Jakarta Sans', Arial).
Enforces strict color rules: Green for Passed, Red for Failed.
Forces light theme across all native Streamlit widgets (file uploader, buttons, radios, selects).
"""

def get_white_dashboard_css() -> str:
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global White Dashboard */
    .stApp, [data-testid="stAppViewContainer"] {
        background-color: #f7f9fc !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica Neue', Arial, sans-serif !important;
        color: #0f172a !important;
    }

    /* Force Light Theme Colors on Streamlit Main Block */
    .main .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3rem !important;
        max-width: 96% !important;
    }

    /* Top Executive Header */
    .allianz-top-header {
        background: #ffffff !important;
        border: 1px solid #dbeafe !important;
        border-top: 4px solid #003781 !important;
        border-radius: 10px !important;
        padding: 16px 24px !important;
        display: flex !important;
        justify-content: space-between !important;
        align-items: center !important;
        margin-bottom: 20px !important;
        box-shadow: 0 2px 8px rgba(0, 55, 129, 0.05) !important;
    }

    .header-left-title {
        font-size: 1.65rem !important;
        font-weight: 800 !important;
        color: #0f172a !important;
        letter-spacing: -0.02em !important;
        line-height: 1.15 !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', Arial, sans-serif !important;
    }

    .header-right-box {
        text-align: right !important;
    }

    .allianz-project-brand {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
        color: #003781 !important;
        letter-spacing: -0.01em !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-end !important;
        gap: 8px !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', Arial, sans-serif !important;
    }

    .header-user-info {
        font-size: 0.84rem !important;
        font-weight: 700 !important;
        color: #1e293b !important;
        margin-top: 2px !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }

    .header-current-time {
        font-size: 0.78rem !important;
        color: #64748b !important;
        margin-top: 2px !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Selector Card: styles the native st.container(border=True, key="source_selector_card")
       Streamlit adds the CSS class .st-key-<key> to keyed containers. */
    .st-key-source_selector_card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 16px 22px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03) !important;
    }

    .source-selector-title {
        font-weight: 700 !important;
        font-size: 0.90rem !important;
        color: #003781 !important;
        margin-bottom: 4px !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', Arial, sans-serif !important;
    }

    /* Clean Card-Style Radio Buttons (No Ugly Dots) */
    div[data-testid="stRadio"] > div {
        display: flex !important;
        flex-direction: row !important;
        gap: 16px !important;
        background-color: transparent !important;
        border: none !important;
    }

    div[data-testid="stRadio"] label {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        padding: 8px 18px !important;
        cursor: pointer !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        transition: all 0.15s ease !important;
    }

    div[data-testid="stRadio"] label:hover {
        border-color: #003781 !important;
        background-color: #f0f7ff !important;
    }

    div[data-testid="stRadio"] label p {
        font-size: 0.90rem !important;
        font-weight: 700 !important;
        color: #003781 !important;
    }

    /* Streamlit File Uploader Overrides (Force Pure White with Blue Dashed Border) */
    [data-testid="stFileUploader"] {
        background-color: transparent !important;
    }

    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"] {
        background-color: #ffffff !important;
        border: 2px dashed #003781 !important;
        border-radius: 10px !important;
        color: #0f172a !important;
        padding: 16px !important;
    }

    [data-testid="stFileUploadDropzone"] * {
        color: #0f172a !important;
    }

    [data-testid="stFileUploadDropzone"] small,
    [data-testid="stFileUploadDropzone"] span {
        color: #475569 !important;
    }

    /* Streamlit Selectboxes, Inputs & Dropdowns Overrides (Force Clean White) */
    div[data-baseweb="select"] > div,
    div[data-testid="stTextInput"] input,
    div[data-testid="stNumberInput"] input {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', Arial, sans-serif !important;
    }

    div[data-baseweb="select"] * {
        color: #0f172a !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', Arial, sans-serif !important;
    }

    div[data-baseweb="popover"],
    div[data-baseweb="menu"],
    ul[data-testid="stSelectboxMenu"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }

    div[data-baseweb="popover"] li,
    div[data-baseweb="menu"] li {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }

    div[data-baseweb="popover"] li:hover,
    div[data-baseweb="menu"] li:hover {
        background-color: #f0f7ff !important;
        color: #003781 !important;
    }

    /* Streamlit Buttons Overrides (Allianz Blue, High Contrast White Text) */
    div.stButton > button,
    button[kind="secondary"],
    button[kind="primary"],
    [data-testid="baseButton-secondary"],
    [data-testid="baseButton-primary"] {
        background-color: #003781 !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 10px 22px !important;
        font-size: 0.88rem !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
        box-shadow: 0 2px 6px rgba(0, 55, 129, 0.2) !important;
        transition: background-color 0.2s ease !important;
    }

    div.stButton > button:hover,
    button[kind="secondary"]:hover,
    button[kind="primary"]:hover {
        background-color: #002766 !important;
        color: #ffffff !important;
    }

    div.stButton > button p,
    button p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* ENLARGED Executive KPI Cards */
    .large-kpi-card {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 22px 24px !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
        min-height: 135px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease !important;
    }

    .large-kpi-card:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 20px rgba(0, 55, 129, 0.08) !important;
    }

    .kpi-title {
        font-size: 0.82rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: #475569 !important;
        margin-bottom: 6px !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }

    .kpi-value-huge {
        font-size: 2.35rem !important;
        font-weight: 800 !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', Arial, sans-serif !important;
        line-height: 1.05 !important;
        letter-spacing: -0.02em !important;
    }

    .kpi-subtext-large {
        font-size: 0.78rem !important;
        color: #64748b !important;
        margin-top: 6px !important;
        font-weight: 500 !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Strict Pass / Fail Color Styles */
    .color-pass { color: #15803d !important; }
    .color-fail { color: #dc2626 !important; }
    .color-allianz { color: #003781 !important; }

    .border-pass { border-left: 5px solid #16a34a !important; }
    .border-fail { border-left: 5px solid #dc2626 !important; }
    .border-allianz { border-left: 5px solid #003781 !important; }

    /* Check Cards Grid */
    .check-card {
        background: #ffffff !important;
        border-radius: 8px !important;
        padding: 15px 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        min-height: 125px !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: space-between !important;
        transition: transform 0.15s ease !important;
    }

    .check-card:hover {
        transform: translateY(-2px) !important;
    }

    .check-card-pass {
        border: 1px solid #bbf7d0 !important;
        border-left: 5px solid #16a34a !important;
        background: #ffffff !important;
    }

    .check-card-fail {
        border: 1px solid #fecaca !important;
        border-left: 5px solid #dc2626 !important;
        background: #fffafa !important;
    }

    /* Status Pills */
    .status-pill-pass {
        background: #dcfce7 !important;
        color: #15803d !important;
        border: 1px solid #86efac !important;
        padding: 3px 10px !important;
        border-radius: 4px !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }

    .status-pill-fail {
        background: #fee2e2 !important;
        color: #b91c1c !important;
        border: 1px solid #fca5a5 !important;
        padding: 3px 10px !important;
        border-radius: 4px !important;
        font-size: 0.72rem !important;
        font-weight: 800 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.04em !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Section Headings */
    .section-heading {
        font-size: 1.15rem !important;
        font-weight: 700 !important;
        color: #0f172a !important;
        margin-top: 20px !important;
        margin-bottom: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }

    /* Clean Streamlit DataFrames */
    div[data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background-color: #ffffff !important;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif !important;
    }
    </style>
    """
