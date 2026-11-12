"""
White Corporate Executive Theme for Project Allianz Data Quality Dashboard.
Maintains the exact corporate font from the reference screenshot ('Segoe UI', 'Plus Jakarta Sans', Arial).
Enforces strict color rules: Green for Passed, Red for Failed.
"""

def get_white_dashboard_css() -> str:
    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    /* Global White Dashboard - Font matching reference screenshot */
    .stApp {
        background-color: #f7f9fc;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Roboto', 'Helvetica Neue', Arial, sans-serif;
        color: #0f172a;
    }

    /* Top Executive Header */
    .allianz-top-header {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-top: 4px solid #003781;
        border-radius: 10px;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
    }

    .header-left-title {
        font-size: 1.65rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.02em;
        line-height: 1.15;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    }

    .header-right-box {
        text-align: right;
    }

    .allianz-project-brand {
        font-size: 1.45rem;
        font-weight: 800;
        color: #003781;
        letter-spacing: -0.01em;
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 8px;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
    }

    .header-user-info {
        font-size: 0.84rem;
        font-weight: 700;
        color: #1e293b;
        margin-top: 2px;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }

    .header-current-time {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 2px;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }

    /* Mutually Exclusive Selector Card */
    .source-selector-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px 22px;
        margin-bottom: 20px;
        box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
    }

    /* ENLARGED Executive KPI Cards */
    .large-kpi-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 22px 24px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        min-height: 135px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }

    .large-kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 55, 129, 0.08);
    }

    .kpi-title {
        font-size: 0.82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #475569;
        margin-bottom: 6px;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }

    .kpi-value-huge {
        font-size: 2.35rem;
        font-weight: 800;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
        line-height: 1.05;
        letter-spacing: -0.02em;
    }

    .kpi-subtext-large {
        font-size: 0.78rem;
        color: #64748b;
        margin-top: 6px;
        font-weight: 500;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }

    /* Strict Pass / Fail Color Styles */
    .color-pass {
        color: #15803d !important;
    }

    .color-fail {
        color: #dc2626 !important;
    }

    .color-allianz {
        color: #003781 !important;
    }

    .border-pass {
        border-left: 5px solid #16a34a !important;
    }

    .border-fail {
        border-left: 5px solid #dc2626 !important;
    }

    .border-allianz {
        border-left: 5px solid #003781 !important;
    }

    /* Check Cards Grid */
    .check-card {
        background: #ffffff;
        border-radius: 8px;
        padding: 15px 16px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
        min-height: 125px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        transition: transform 0.15s ease;
    }

    .check-card:hover {
        transform: translateY(-2px);
    }

    .check-card-pass {
        border: 1px solid #bbf7d0;
        border-left: 5px solid #16a34a;
        background: #ffffff;
    }

    .check-card-fail {
        border: 1px solid #fecaca;
        border-left: 5px solid #dc2626;
        background: #fffafa;
    }

    /* Status Pills */
    .status-pill-pass {
        background: #dcfce7;
        color: #15803d;
        border: 1px solid #86efac;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }

    .status-pill-fail {
        background: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fca5a5;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }

    /* Section Headings */
    .section-heading {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0f172a;
        margin-top: 20px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }

    /* Simple Download Box */
    .download-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 14px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }

    /* Clean Streamlit DataFrames */
    div[data-testid="stDataFrame"] {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background-color: #ffffff;
        font-family: 'Segoe UI', 'Plus Jakarta Sans', sans-serif;
    }
    </style>
    """
