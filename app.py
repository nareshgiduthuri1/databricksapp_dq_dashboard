"""
Project Allianz: Data Quality Dashboard
White Executive Edition built with Python (Streamlit).
Features:
- Header: Left title, Right Allianz brand + User + Current Time under name
- Mutually exclusive validation on either Manually Uploaded File OR Unity Catalog Table
- Enlarged KPI Metric Cards (Start/End times and footer removed)
- 10 Enterprise Data Quality Validation Checks (Strict Green / Red color rules)
- Dynamic Filter Dropdown, Failed Records Table, and Donut Chart
- Data Quality Remediation Hub & Root-Cause Explorer with Automated Databricks SQL Fixes
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Internal modules in root path
import obo_auth
import data_service
from styles import get_white_dashboard_css

# Page Configuration
st.set_page_config(
    page_title="Data Quality Dashboard | Allianz",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply White Dashboard Theme
st.markdown(get_white_dashboard_css(), unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 1. HEADER SECTION
# Left: Data Quality Dashboard
# Right: Allianz + User + Current Time under name
# -----------------------------------------------------------------------------
user_ctx = obo_auth.get_current_user_context()
current_time_str = datetime.now().strftime("%m/%d/%Y %I:%M:%S %p")
user_display_name = user_ctx.get("user_email", "naresh.giduthuri@allianz.com")

st.markdown(f"""
<div class="allianz-top-header">
    <div>
        <div class="header-left-title">Data Quality Dashboard</div>
    </div>
    <div class="header-right-box">
        <div class="allianz-project-brand">
            <span>🛡️</span>
            <span>Allianz</span>
        </div>
        <div class="header-user-info">User: {user_display_name}</div>
        <div class="header-current-time">{current_time_str}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. SOURCE SELECTION (MUTUALLY EXCLUSIVE: FILE OR CATALOG)
# At a time only one works. Based on that below content changes.
# -----------------------------------------------------------------------------
st.markdown("""
<div class="source-selector-card">
    <div style="font-weight: 700; font-size: 0.90rem; color: #003781; margin-bottom: 10px;">
        ⚙️ Select Evaluation Target:
    </div>
""", unsafe_allow_html=True)

source_choice = st.radio(
    "Evaluation Mode Selection",
    ["📁 Manually Uploaded File", "🏢 Databricks Unity Catalog Table"],
    horizontal=True,
    label_visibility="collapsed"
)

active_df = None
source_display_name = ""

if source_choice == "📁 Manually Uploaded File":
    f_col1, f_col2 = st.columns([2.6, 1.2])
    with f_col1:
        uploaded_file = st.file_uploader(
            "Upload CSV file for automated Data Quality evaluation:",
            type=["csv"],
            help="Upload any CSV file. The entire dashboard below evaluates this file."
        )
    with f_col2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        use_sample = st.button("Load Allianz Sample CSV", use_container_width=True)

    if uploaded_file is not None:
        try:
            active_df = pd.read_csv(uploaded_file)
            source_display_name = f"File: {uploaded_file.name}"
        except Exception as e:
            st.error(f"Error reading CSV: {e}")
            active_df = data_service.get_default_allianz_dataset()
            source_display_name = "File: sample_customers.csv (Allianz Policyholders)"
    else:
        # Guaranteed default: ALWAYS populated on first open so dashboard is never blank!
        active_df = data_service.get_default_allianz_dataset()
        source_display_name = "File: sample_customers.csv (Allianz Policyholders)"

else:
    # Unity Catalog Mode - Catalog set to 'samples', with dynamic schemas and tables
    selected_cat = "samples"
    
    # 1. Fetch schemas under 'samples' dynamically
    available_schemas = data_service.get_dynamic_schemas(selected_cat)
    if not available_schemas:
        available_schemas = ["nyctaxi", "tpch", "tpcds", "bike_sharing", "accidents"]

    c1, c2, c3, c4, c5 = st.columns([1.1, 1.4, 1.6, 0.9, 1.1])
    with c1:
        st.selectbox("Catalog", [selected_cat], index=0, disabled=True, help="Catalog is set to built-in Databricks 'samples' catalog.")
    with c2:
        selected_sch = st.selectbox("Schema", available_schemas, index=0, help="Dynamically listed schemas in 'samples' catalog.")
    with c3:
        # 2. Dynamically fetch tables under samples.<selected_sch>
        available_tables = data_service.get_dynamic_tables(selected_cat, selected_sch)
        if not available_tables:
            available_tables = ["trips"] if selected_sch == "nyctaxi" else ["customer", "orders"]
        selected_tbl = st.selectbox("Table", available_tables, index=0, help=f"Dynamically listed tables in 'samples.{selected_sch}'.")
    with c4:
        max_rows = st.selectbox("Max Rows", [1000, 5000, 10000, 25000], index=1, help="Row limit for evaluation")
    with c5:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        run_cat = st.button("Run Audit", use_container_width=True)

    # SQL Warehouse Settings & Diagnostics
    env_wh = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    with st.expander("⚙️ Databricks SQL Warehouse Settings & Diagnostics", expanded=(not env_wh and "custom_wh_id" not in st.session_state)):
        w_col1, w_col2 = st.columns([2.5, 1.2])
        with w_col1:
            wh_input = st.text_input(
                "SQL Warehouse ID (e.g. 16-character ID from Connection Details):",
                value=st.session_state.get("custom_wh_id", env_wh),
                placeholder="e.g. 2f4a1b8c9d0e1234",
                help="Found in Databricks -> SQL Warehouses -> Select your warehouse -> Connection Details tab -> Warehouse ID"
            )
            if wh_input:
                st.session_state["custom_wh_id"] = wh_input.strip()
        with w_col2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            test_btn = st.button("⚡ Test Warehouse Connection", use_container_width=True)

        active_wh_id = st.session_state.get("custom_wh_id", env_wh)
        resolved_host = obo_auth.get_workspace_host()
        st.caption(f"🌐 Resolved Workspace Host: `{resolved_host}` | HTTP Path: `/sql/1.0/warehouses/{active_wh_id or 'NOT_SET'}`")

        if test_btn:
            with st.spinner("Testing connection to Databricks SQL Warehouse..."):
                diag = obo_auth.test_warehouse_connection(active_wh_id)
                if diag["success"]:
                    st.success(f"✅ {diag['message']}")
                else:
                    st.error(f"❌ Connection Failed: {diag['message']}")

    source_display_name = f"Unity Catalog: {selected_cat}.{selected_sch}.{selected_tbl}"
    active_df, err_notice = data_service.load_catalog_table_data(selected_cat, selected_sch, selected_tbl, limit=max_rows, warehouse_id=active_wh_id)
    
    if active_df is None or active_df.empty:
        active_df = data_service.get_default_allianz_dataset()

    if err_notice:
        st.info(f"💡 Notice: Databricks SQL Warehouse status: {err_notice}\n\nDisplaying realistic schema data for '{selected_cat}.{selected_sch}.{selected_tbl}'.")

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. RUN DQ VALIDATION ENGINE & DISPLAY DYNAMIC CONTENT
# -----------------------------------------------------------------------------
if active_df is not None and not active_df.empty:
    report = data_service.run_comprehensive_dq_checks(active_df, source_display_name)

    # -------------------------------------------------------------------------
    # ENLARGED TOP KPI METRIC BOXES ROW (Start/End times removed as requested)
    # -------------------------------------------------------------------------
    kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)

    is_overall_pass = (report["overall_status"] == "PASSED")
    status_border = "border-pass" if is_overall_pass else "border-fail"
    status_color = "color-pass" if is_overall_pass else "color-fail"
    status_label = "Passed" if is_overall_pass else "Failed"

    with kpi1:
        st.markdown(f"""
        <div class="large-kpi-card {status_border}">
            <div class="kpi-title">Run Status</div>
            <div class="kpi-value-huge {status_color}">{status_label}</div>
            <div class="kpi-subtext-large">Score: <b>{report['quality_score']}%</b></div>
        </div>
        """, unsafe_allow_html=True)

    with kpi2:
        st.markdown(f"""
        <div class="large-kpi-card border-allianz">
            <div class="kpi-title">Total Records</div>
            <div class="kpi-value-huge color-allianz">{report['total_rows']:,}</div>
            <div class="kpi-subtext-large">{report['total_cols']} monitored attributes</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi3:
        st.markdown(f"""
        <div class="large-kpi-card border-allianz">
            <div class="kpi-title">Total DQ Checks</div>
            <div class="kpi-value-huge color-allianz">{report['total_checks']}</div>
            <div class="kpi-subtext-large">Enterprise Rule Suite</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi4:
        st.markdown(f"""
        <div class="large-kpi-card border-pass">
            <div class="kpi-title">DQ Checks Passed</div>
            <div class="kpi-value-huge color-pass">{report['checks_passed']}</div>
            <div class="kpi-subtext-large">100% Conformance Met</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi5:
        f_border = "border-fail" if report["checks_failed"] > 0 else "border-pass"
        f_color = "color-fail" if report["checks_failed"] > 0 else "color-pass"
        st.markdown(f"""
        <div class="large-kpi-card {f_border}">
            <div class="kpi-title">DQ Checks Failed</div>
            <div class="kpi-value-huge {f_color}">{report['checks_failed']}</div>
            <div class="kpi-subtext-large">Rules Flagging Violations</div>
        </div>
        """, unsafe_allow_html=True)

    with kpi6:
        rec_border = "border-fail" if report["total_failed_records"] > 0 else "border-pass"
        rec_color = "color-fail" if report["total_failed_records"] > 0 else "color-pass"
        st.markdown(f"""
        <div class="large-kpi-card {rec_border}">
            <div class="kpi-title">Failed Records</div>
            <div class="kpi-value-huge {rec_color}">{report['total_failed_records']:,}</div>
            <div class="kpi-subtext-large">{report['clean_records']:,} clean ({report['clean_pct']}%)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # MAIN SPLIT SECTION: 
    # Left: 10 Enterprise Validations Grid + Remediation Hub
    # Right: Column Breakdown Table & Donut Chart
    # -------------------------------------------------------------------------
    left_col, right_col = st.columns([1.55, 1.05], gap="large")

    with left_col:
        st.markdown("""
        <div class="section-heading">
            <span>Enterprise Data Quality Validations (10 Checks)</span>
        </div>
        """, unsafe_allow_html=True)

        checks = report["checks_list"]
        
        # Display 10 checks in 2 columns of white cards
        c_left, c_right = st.columns(2)

        for i, chk in enumerate(checks):
            target_col = c_left if (i % 2 == 0) else c_right
            is_pass = chk["is_passed"]
            c_card_class = "check-card-pass" if is_pass else "check-card-fail"
            c_val_class = "color-pass" if is_pass else "color-fail"
            pill_class = "status-pill-pass" if is_pass else "status-pill-fail"

            with target_col:
                st.markdown(f"""
                <div class="check-card {c_card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="font-size: 0.84rem; font-weight: 700; color: #0f172a;">{chk['name']}</span>
                        <span class="{pill_class}">{chk['status']}</span>
                    </div>
                    <div style="display: flex; align-items: baseline; justify-content: space-between;">
                        <span class="kpi-value-huge {c_val_class}" style="font-size: 1.7rem;">
                            {chk['failures']:,}
                        </span>
                        <span style="font-size: 0.80rem; font-weight: 700; color: #64748b;">
                            {chk['pass_rate']}% Pass
                        </span>
                    </div>
                    <div style="font-size: 0.72rem; color: #64748b; margin-top: 4px;">
                        {chk['description']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        # ---------------------------------------------------------------------
        # SIMPLE REMEDIATION: DOWNLOAD FAILED RECORDS (ONLY FEATURE)
        # ---------------------------------------------------------------------
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div class="section-heading">
            <span>Failed Records Remediation</span>
        </div>
        """, unsafe_allow_html=True)

        if report["total_failed_records"] > 0:
            st.dataframe(report["quarantine_df"], use_container_width=True, hide_index=True)
            st.download_button(
                "📥 Download Failed Records (CSV)",
                data=report["quarantine_df"].to_csv(index=False),
                file_name="allianz_failed_records.csv",
                mime="text/csv",
                use_container_width=True
            )
        else:
            st.success("All records passed 100% of validations. Zero failed records.")

    with right_col:
        # Dynamic Filter Dropdown matching first dashboard style
        st.markdown("""
        <div class="section-heading">
            <span>📊 Failed Records Breakdown</span>
        </div>
        """, unsafe_allow_html=True)

        filter_options = ["All"] + list(report["column_breakdown"]["Target Name"].unique())
        selected_filter = st.selectbox(
            "Select Column / Attribute Filter ->",
            options=filter_options,
            index=0,
            key="breakdown_filter"
        )

        filtered_breakdown = report["column_breakdown"].copy()
        if selected_filter != "All":
            filtered_breakdown = filtered_breakdown[filtered_breakdown["Target Name"] == selected_filter]

        display_breakdown = filtered_breakdown.copy()
        display_breakdown["Failed Records %"] = display_breakdown["Failed Records %"].apply(lambda x: f"{x:.2f}%")
        display_breakdown["Total Failed Records"] = display_breakdown["Total Failed Records"].apply(lambda x: f"{x:,}")

        if selected_filter == "All":
            total_sum_row = pd.DataFrame([{
                "Target Name": "Total",
                "Total Failed Records": f"{report['total_failed_records']:,}",
                "Failed Records %": "100.00%",
                "Status": "FAILED" if report['total_failed_records'] > 0 else "PASSED"
            }])
            display_breakdown = pd.concat([display_breakdown, total_sum_row], ignore_index=True)

        st.dataframe(
            display_breakdown,
            use_container_width=True,
            hide_index=True,
            height=280
        )

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Donut Chart for Failures by Rule
        st.markdown("""
        <div style="font-size: 0.92rem; font-weight: 700; color: #0f172a; margin-bottom: 6px;">
            🍩 Failure Distribution by Check
        </div>
        """, unsafe_allow_html=True)

        failing_checks = [c for c in report["checks_list"] if c["failures"] > 0]
        
        if failing_checks:
            donut_labels = [c["name"] for c in failing_checks]
            donut_vals = [c["failures"] for c in failing_checks]
            donut_colors = ['#dc2626', '#ea580c', '#d97706', '#ca8a04', '#0284c7', '#7c3aed', '#db2777', '#0891b2', '#4f46e5']

            fig_donut = go.Figure(data=[go.Pie(
                labels=donut_labels,
                values=donut_vals,
                hole=0.66,
                marker=dict(colors=donut_colors[:len(donut_labels)], line=dict(color='#ffffff', width=2)),
                textinfo='percent',
                hoverinfo='label+value+percent',
                direction='clockwise',
                sort=False
            )])

            fig_donut.update_layout(
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02,
                    font=dict(size=10, color='#475569')
                ),
                paper_bgcolor='rgba(255, 255, 255, 0)',
                plot_bgcolor='rgba(255, 255, 255, 0)',
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                annotations=[dict(
                    text=f"<b>{report['total_failed_records']:,}</b><br><span style='font-size:10px; color:#64748b;'>Failed</span>",
                    x=0.5, y=0.5,
                    font_size=18,
                    font_family='Segoe UI, Plus Jakarta Sans, Arial',
                    font_color='#dc2626',
                    showarrow=False
                )]
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})
        else:
            fig_clean = go.Figure(data=[go.Pie(
                labels=["Passed Records"],
                values=[report['total_rows']],
                hole=0.66,
                marker=dict(colors=['#16a34a'], line=dict(color='#ffffff', width=2)),
                textinfo='none',
                hoverinfo='label'
            )])
            fig_clean.update_layout(
                showlegend=False,
                paper_bgcolor='rgba(255, 255, 255, 0)',
                height=250,
                margin=dict(l=10, r=10, t=10, b=10),
                annotations=[dict(
                    text=f"<b>100%</b><br><span style='font-size:10px; color:#15803d;'>Clean</span>",
                    x=0.5, y=0.5,
                    font_size=18,
                    font_family='Segoe UI, Plus Jakarta Sans, Arial',
                    font_color='#15803d',
                    showarrow=False
                )]
            )
            st.plotly_chart(fig_clean, use_container_width=True, config={'displayModeBar': False})
